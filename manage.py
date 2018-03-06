#!/usr/bin/env python

from flask_dbshell import DbShell
from flask_migrate import Migrate, MigrateCommand
from flask_script import Manager, Shell

from forum.app import create_app, db
from forum.models import User, Role, Permission, Topic, TopicGroup, Comment, PollVote, PollAnswer, Message

app = create_app()
manager = Manager(app)
migrate = Migrate(app, db)


def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role, Permission=Permission, Topic=Topic, TopicGroup=TopicGroup,
                Comment=Comment, PollVote=PollVote, PollAnswer=PollAnswer, Message=Message)


manager.add_command('shell', Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def dbshell():
    """Run DB shell."""
    # ~/.pgpass should exist
    shell = DbShell(url=app.config['SQLALCHEMY_DATABASE_URI'])
    shell.run_shell()


@manager.command
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def insert_initial_data():
    """Adds initial data to database."""
    Role.insert_roles()
    TopicGroup.insert_root_topic_group()


@manager.command
def insert_fake_data():
    """Adds fake data to database."""
    from utils import data_generator
    data_generator.generate_fake_users()
    data_generator.generate_fake_topic_groups()
    data_generator.generate_fake_topics()
    data_generator.generate_fake_comments()
    data_generator.generate_fake_messages()
    data_generator.generate_fake_polls()
    data_generator.generate_fake_votes()


if __name__ == '__main__':
    manager.run()
