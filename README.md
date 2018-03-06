4RUM
======

This is social WEB application <b>Internet forum</b>.
An Internet forum, is an online discussion site where people can hold conversations in the form of posted messages.

The application implemented with Python WEB framework <b>Flask</b>.

To run application:
```
# Prepare virtual environment
$ mkvirtualenv 4rum --python=/usr/bin/python2.7
$ pip install -r requirements/dev.txt
# Prepare all needed environment variables for WEB application
$ export MAIL_USERNAME=4rum@example.com
$ export MAIL_PASSWORD=secret1
$ export ADMIN_MAIL_USERNAME=4rum_admin@example.com
$ export DB_USER=forum_app
$ export DB_NAME=forum
$ export DB_PASSWORD=secret2
$ export DB_HOST=pg
# Prepare DB
$ python manage.py db upgrade
$ python manage.py insert_initial_data
$ python manage.py insert_fake_data
# Compile translations
$ pybabel compile -d forum/translations
# Run server
$ python manage.py runserver -h 0.0.0.0 -p 8000
```

To run application using docker and docker-compose:
```
# Install docker and docker-compose
# Prepare pg.env file with environment variables for DB
# Prepare web.env file with environment variables for WEB application
$ docker-compose up -d
$ docker-compose exec web python manage.py db upgrade
$ docker-compose exec web python manage.py insert_initial_data
$ docker-compose exec web python manage.py insert_fake_data
```

Go to http://127.0.0.1:8000/