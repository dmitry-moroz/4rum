4RUM
======

This is social WEB application <b>Internet forum</b>.
An Internet forum, is an online discussion site where people can hold conversations in the form of posted messages.

The application implemented with Python WEB framework <b>Flask</b>.

To run application for development:
```
$ python manage.py db upgrade
$ python manage.py shell
>>> Role.insert_roles()
>>> TopicGroup.insert_root_topic_group()
>>> User.generate_fake()
>>> TopicGroup.generate_fake()
>>> Topic.generate_fake()
>>> Comment.generate_fake()
$ export MAIL_USERNAME=4rum@example.com
$ export MAIL_PASSWORD=password
$ export ADMIN_MAIL_USERNAME=4rum_admin@example.com
$ python manage.py runserver
```