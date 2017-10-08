4RUM
======

This is social WEB application <b>Internet forum</b>.
An Internet forum, is an online discussion site where people can hold conversations in the form of posted messages.

The application implemented with Python WEB framework <b>Flask</b>.

To run application for development:
```
$ python manage.py db upgrade
$ python manage.py insert_initial_data
$ python manage.py insert_fake_data
$ export MAIL_USERNAME=4rum@example.com
$ export MAIL_PASSWORD=password
$ export ADMIN_MAIL_USERNAME=4rum_admin@example.com
$ pybabel compile -d translations
$ python manage.py runserver
```