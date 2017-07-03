import hashlib
from datetime import datetime

from flask import current_app
from flask_login import UserMixin, AnonymousUserMixin
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from werkzeug.security import generate_password_hash, check_password_hash

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


class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(64), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'))
    password_hash = db.Column(db.String(128))
    confirmed = db.Column(db.Boolean, default=False)
    topics = db.relationship('Topic', backref='author', lazy='dynamic')
    topic_groups = db.relationship('TopicGroup', backref='author', lazy='dynamic')

    # Profile:
    name = db.Column(db.String(64))
    homeland = db.Column(db.String(64))
    about = db.Column(db.Text)
    # TODO: rename member_since -> created_at
    member_since = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    avatar = db.Column(db.String(256))

    @staticmethod
    def generate_fake(count=100):
        from sqlalchemy.exc import IntegrityError
        from random import seed
        import forgery_py

        seed()
        for i in range(count):
            u = User(email=forgery_py.internet.email_address(),
                     username=forgery_py.internet.user_name(True),
                     password=forgery_py.lorem_ipsum.word(),
                     confirmed=True,
                     name=forgery_py.name.full_name(),
                     homeland=forgery_py.address.city(),
                     about=forgery_py.lorem_ipsum.sentence(),
                     member_since=forgery_py.date.date(True))
            db.session.add(u)
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()

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

    def __repr__(self):
        return '<User %r>' % self.username


class AnonymousUser(AnonymousUserMixin):
    def can(self, permissions):
        return False

    def is_administrator(self):
        return False

    def is_moderator(self):
        return False


login_manager.anonymous_user = AnonymousUser


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


class Topic(db.Model):
    __tablename__ = 'topics'
    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text)
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('topic_groups.id'), default=0)

    @staticmethod
    def generate_fake(count=100):
        from random import seed, randint
        import forgery_py

        seed()
        user_count = User.query.count()
        group_count = TopicGroup.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            if group_count:
                g = TopicGroup.query.offset(randint(0, group_count - 1)).first()
            else:
                g = None
            p = Topic(body=forgery_py.lorem_ipsum.sentences(randint(1, 5)),
                      created_at=forgery_py.date.date(True),
                      author=u,
                      group=g)
            db.session.add(p)
            db.session.commit()


class TopicGroup(db.Model):
    __tablename__ = 'topic_groups'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64))
    priority = db.Column(db.Integer, default=base_config.TOPIC_GROUP_PRIORITY[-1])
    created_at = db.Column(db.DateTime, index=True, default=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    group_id = db.Column(db.Integer, db.ForeignKey('topic_groups.id'), default=0)
    topics = db.relationship('Topic', backref='group', lazy='dynamic')
    topic_groups = db.relationship('TopicGroup', backref=db.backref('group', remote_side=id), lazy='dynamic')

    @staticmethod
    def generate_fake(count=10):
        from random import seed, randint, choice
        import forgery_py

        seed()
        user_count = User.query.count()
        for i in range(count):
            u = User.query.offset(randint(0, user_count - 1)).first()
            g = TopicGroup(name=forgery_py.lorem_ipsum.sentence(),
                           priority=choice(base_config.TOPIC_GROUP_PRIORITY),
                           created_at=forgery_py.date.date(True),
                           author=u)
            db.session.add(g)
            db.session.commit()
