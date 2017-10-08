import hashlib
from datetime import datetime

import bleach
from flask import current_app
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from markdown import markdown
from markdown.extensions.tables import TableExtension
from sqlalchemy import func, or_, and_
from werkzeug.security import generate_password_hash, check_password_hash

# TODO: remove base_config
from config import base_config
from . import db, login_manager


class Permission:
    READ = 0x01
    PARTICIPATE = 0x02
    WRITE = 0x04
    MODERATE = 0x08
    ADMINISTER = 0x80


class Role(db.Model):
    __tablename__ = 'roles'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), unique=True)
    default = db.Column(db.Boolean, default=False, index=True)
    permissions = db.Column(db.Integer)
    users = db.relationship('User', backref='role', lazy='dynamic')

    @staticmethod
    def insert_roles():
        roles = {
            'Guest': (Permission.READ, False),
            'Participant': (Permission.READ | Permission.PARTICIPATE, False),
            'User': (Permission.READ | Permission.PARTICIPATE | Permission.WRITE, True),
            'Moderator': (Permission.READ | Permission.PARTICIPATE | Permission.WRITE | Permission.MODERATE, False),
            'Administrator': (0xff, False)
        }
        for r in roles:
            role = Role.query.filter_by(name=r).first()
            if role is None:
                role = Role(name=r)
            role.permissions = roles[r][0]
            role.default = roles[r][1]
            db.session.add(role)
        db.session.commit()

    def __repr__(self):
        return '<Role %r>' % self.name


class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    body = db.Column(db.Text)
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), index=True)
    author_deleted = db.Column(db.Boolean, index=True, default=False)
    receiver_deleted = db.Column(db.Boolean, index=True, default=False)
    unread = db.Column(db.Boolean, index=True, default=True)


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(32), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    topics = db.relationship('Topic', backref='author', lazy='dynamic')
    topic_groups = db.relationship('TopicGroup', backref='author', lazy='dynamic')
    comments = db.relationship('Comment', backref='author', lazy='dynamic')
    poll_votes = db.relationship('PollVote', backref='author', lazy='dynamic')
    sent_messages = db.relationship('Message', foreign_keys=[Message.author_id], backref='author', lazy='dynamic')
    received_messages = db.relationship('Message', foreign_keys=[Message.receiver_id], backref='receiver',
                                        lazy='dynamic')

    # Profile:
    name = db.Column(db.String(64))
    homeland = db.Column(db.String(64))
    about = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    # TODO: Add updated_at field
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    avatar = db.Column(db.String(256))

    def __init__(self, *args, **kwargs):
        super(User, self).__init__(*args, **kwargs)
        if self.role is None:
            if self.email == current_app.config['APP_ADMIN']:
                self.role = Role.query.filter_by(permissions=0xff).first()
            if self.role is None:
                self.role = Role.query.filter_by(default=True).first()
        if self.avatar is None and self.email is not None:
            self.avatar = self.gravatar()

    @property
    def password(self):
        raise AttributeError('password is not a readable attribute')

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password)

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_token(self, expiration=3600, **kwargs):
        s = Serializer(current_app.config['SECRET_KEY'], expiration)
        data = {'user_id': self.id}
        data.update(kwargs)
        return s.dumps(data)

    def confirm_token(self, token):
        s = Serializer(current_app.config['SECRET_KEY'])
        try:
            data = s.loads(token)
        except:
            return False, None
        if data.get('user_id') != self.id:
            return False, data
        return True, data

    def confirm_registration(self, token):
        result, _ = self.confirm_token(token)
        if not result:
            return False
        self.confirmed = True
        db.session.add(self)
        return True

    def confirm_new_email(self, token):
        result, data = self.confirm_token(token)
        if not result:
            return False
        new_email = data.get('new_email')
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        db.session.add(self)
        return True

    def confirm_reset(self, token, new_password):
        result, _ = self.confirm_token(token)
        if not result:
            return False
        self.password = new_password
        db.session.add(self)
        return True

    def can(self, permissions):
        return self.role is not None and (self.role.permissions & permissions) == permissions

    def is_administrator(self):
        return self.can(Permission.ADMINISTER)

    def is_moderator(self):
        return self.can(Permission.MODERATE)

    def ping(self):
        self.last_seen = datetime.utcnow()
        db.session.add(self)

    def gravatar(self, size=256, default='identicon', rating='g'):
        hash = hashlib.md5(self.email.encode('utf-8')).hexdigest()
        return '{url}/{hash}?s={size}&d={default}&r={rating}'.format(
            url=current_app.config['BASE_GRAVATAR_URL'], hash=hash, size=size, default=default, rating=rating)

    def is_voted(self, topic):
        if self.id in [v.author_id for v in topic.poll_votes.filter_by(deleted=False).all()]:
            return True
        else:
            return False

    def get_unread_messages_count(self):
        return db.session.query(func.count(Message.id)).filter(
            and_(Message.receiver_id == self.id, Message.unread == True, Message.receiver_deleted == False,)).scalar()

    def __repr__(self):
        return '<User %r>' % self.username


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

    def is_moderator(self):
        return False

    def is_voted(self, topic):
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Topic(db.Model):
    __tablename__ = 'topics'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128))
    body = db.Column(db.Text)
    body_html = db.Column(db.Text)
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('topic_groups.id'), index=True)
    deleted = db.Column(db.Boolean, index=True, default=False)
    comments = db.relationship('Comment', backref='topic', lazy='dynamic')
    poll = db.Column(db.String(256))
    poll_answers = db.relationship('PollAnswer', backref='topic', lazy='dynamic')
    poll_votes = db.relationship('PollVote', backref='topic', lazy='dynamic')
    interest = db.Column(db.Integer, default=0)

    @property
    def comments_count(self):
        return db.session.query(
            func.count(Comment.id)).filter(and_(Comment.topic_id == self.id, Comment.deleted == False)).scalar()

    @staticmethod
    def on_changed_body(target, value, oldvalue, initiator):
        html = markdown(value, extensions=[TableExtension()], output_format='html')
        clean_html = bleach.clean(html, tags=current_app.config['TOPIC_ALLOWED_TAGS'], strip=True)
        target.body_html = bleach.linkify(clean_html)

    def get_poll_results(self):
        votes = db.session.query(PollAnswer.body, func.count(PollVote.id)).outerjoin(
            PollVote, PollAnswer.id == PollVote.poll_answer_id).filter(
            and_(PollAnswer.topic_id == self.id, PollAnswer.deleted == False)).filter(
            or_(PollVote.deleted.is_(None), PollVote.deleted == False)).group_by(PollAnswer.body).all()
        total_votes = float(sum([v[1] for v in votes]))
        poll_results = [(v[0], v[1], round(float(v[1])/total_votes, 4)*100) for v in votes]
        return sorted(poll_results, key=lambda v: v[1], reverse=True)

    def update_poll_answers(self, new_answers):
        old_answers = self.poll_answers.all()
        for answer in [a for a in old_answers if a.body not in new_answers]:
            answer.poll_votes.update(dict(deleted=True))
            answer.deleted = True
            db.session.add(answer)
        old_answers_bodies = [a.body for a in old_answers]
        for answer in [a for a in new_answers if a not in old_answers_bodies]:
            db.session.add(PollAnswer(topic_id=self.id, body=answer))

    def add_vote(self, user, answer):
        new_vote = PollVote(topic_id=self.id, poll_answer_id=answer.id, author_id=user.id)
        db.session.add(new_vote)
        self.interest += 1
        db.session.add(self)

    def add_comment(self, user, comment):
        new_comment = Comment(body=comment, author_id=user.id, topic_id=self.id)
        db.session.add(new_comment)
        self.interest += 1
        db.session.add(self)


db.event.listen(Topic.body, 'set', Topic.on_changed_body)


class TopicGroup(db.Model):
    __tablename__ = 'topic_groups'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(64))
    priority = db.Column(db.Integer, default=base_config.TOPIC_GROUP_PRIORITY[-1])
    protected = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('topic_groups.id'), index=True)
    topics = db.relationship('Topic', backref='group', lazy='dynamic')
    topic_groups = db.relationship('TopicGroup', backref=db.backref('group', remote_side=id), lazy='dynamic')

    @staticmethod
    def insert_root_topic_group():
        topic_group = TopicGroup.query.get(base_config.ROOT_TOPIC_GROUP)
        if topic_group:
            topic_group.priority = base_config.TOPIC_GROUP_PRIORITY[0]
            topic_group.protected = base_config.IS_PROTECTED_ROOT_TOPIC_GROUP
        else:
            topic_group = TopicGroup(id=base_config.ROOT_TOPIC_GROUP,
                                     title='root topic group',
                                     priority=base_config.TOPIC_GROUP_PRIORITY[0],
                                     protected=base_config.IS_PROTECTED_ROOT_TOPIC_GROUP)
        db.session.add(topic_group)
        db.session.commit()

    def is_root_topic_group(self):
        return self.id == current_app.config['ROOT_TOPIC_GROUP']


class Comment(db.Model):
    __tablename__ = 'comments'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), index=True)
    deleted = db.Column(db.Boolean, index=True, default=False)


class PollAnswer(db.Model):
    __tablename__ = 'polls_answers'
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), index=True)
    body = db.Column(db.Text)
    deleted = db.Column(db.Boolean, index=True, default=False)
    poll_votes = db.relationship('PollVote', backref='poll_answer', lazy='dynamic')


class PollVote(db.Model):
    __tablename__ = 'polls_votes'
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topics.id'), index=True)
    poll_answer_id = db.Column(db.Integer, db.ForeignKey('polls_answers.id'), index=True)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    deleted = db.Column(db.Boolean, index=True, default=False)
