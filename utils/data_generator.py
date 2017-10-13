from random import seed, randint, choice

import forgery_py
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from app import db
from app.models import User, Topic, TopicGroup, Comment, Message, PollAnswer, PollVote
from config import config


def generate_fake_messages(count=1000):
    seed()
    for i in range(count):
        u1, u2 = User.query.order_by(func.random()).limit(2).all()
        m = Message(title=forgery_py.lorem_ipsum.title()[:128],
                    body=forgery_py.lorem_ipsum.sentences(randint(10, 20)),
                    created_at=forgery_py.date.date(True),
                    author=u1,
                    receiver=u2)
        db.session.add(m)
    db.session.commit()


def generate_fake_users(count=100):
    seed()
    for i in range(count):
        u = User(email=forgery_py.internet.email_address(),
                 username=forgery_py.internet.user_name(True)[:32],
                 password=forgery_py.lorem_ipsum.word(),
                 confirmed=True,
                 name=forgery_py.name.full_name()[:64],
                 homeland=forgery_py.address.city()[:64],
                 about=forgery_py.lorem_ipsum.sentence(),
                 created_at=forgery_py.date.date(True))
        db.session.add(u)
        try:
            db.session.commit()
        except IntegrityError:
            db.session.rollback()


def generate_fake_topics(count=100):
    seed()
    user_count = db.session.query(func.count(User.id)).scalar()
    group_count = db.session.query(func.count(TopicGroup.id)).scalar()
    for i in range(count):
        u = User.query.offset(randint(0, user_count - 1)).first()
        if group_count:
            g = TopicGroup.query.offset(randint(0, group_count - 1)).first()
        else:
            g = None
        now = forgery_py.date.date(True)
        p = Topic(title=forgery_py.lorem_ipsum.title()[:128],
                  body=forgery_py.lorem_ipsum.sentences(randint(20, 40)),
                  created_at=now,
                  updated_at=now,
                  author=u,
                  group=g)
        db.session.add(p)
    db.session.commit()


def generate_fake_topic_groups(count=10, parent_group_id=0):
    seed()
    user_count = db.session.query(func.count(User.id)).scalar()
    for i in range(count):
        u = User.query.offset(randint(0, user_count - 1)).first()
        g = TopicGroup(title=forgery_py.lorem_ipsum.title()[:64],
                       priority=choice(config.TOPIC_GROUP_PRIORITY),
                       created_at=forgery_py.date.date(True),
                       author=u,
                       group_id=parent_group_id)
        db.session.add(g)
    db.session.commit()


def generate_fake_comments(count=1000):
    seed()
    user_count = db.session.query(func.count(User.id)).scalar()
    topic_count = db.session.query(func.count(Topic.id)).scalar()
    for i in range(count):
        u = User.query.offset(randint(0, user_count - 1)).first()
        t = Topic.query.offset(randint(0, topic_count - 1)).first()
        now = forgery_py.date.date(True)
        c = Comment(body=forgery_py.lorem_ipsum.sentences(randint(10, 20)),
                    created_at=now,
                    updated_at=now,
                    author=u,
                    topic=t)
        db.session.add(c)
        t.interest += 1
        db.session.add(t)
    db.session.commit()


def generate_fake_polls(polls_count=40, answers_per_poll=4):
    seed()
    for i in range(polls_count):
        t = Topic.query.filter_by(poll=None).order_by(func.random()).first()
        t.poll = forgery_py.lorem_ipsum.sentence()[:256][:-1] + '?'
        for j in range(answers_per_poll):
            pa = PollAnswer(topic_id=t.id,
                            body=forgery_py.lorem_ipsum.sentence())
            db.session.add(pa)
    db.session.commit()


def generate_fake_votes(count=1000):
    seed()
    user_count = db.session.query(func.count(User.id)).scalar()
    for i in range(count):
        u = User.query.offset(randint(0, user_count - 1)).first()
        voted = [v.topic_id for v in u.poll_votes]
        pa = PollAnswer.query.filter(~PollAnswer.topic_id.in_(voted)).order_by(func.random()).first()
        t = pa.topic
        pv = PollVote(topic_id=t.id,
                      poll_answer_id=pa.id,
                      author_id=u.id,
                      created_at=forgery_py.date.date(True))
        db.session.add(pv)
        t.interest += 1
        db.session.add(t)
    db.session.commit()
