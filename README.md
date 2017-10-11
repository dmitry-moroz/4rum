4RUM
======

This is social WEB application <b>Internet forum</b>.
An Internet forum, is an online discussion site where people can hold conversations in the form of posted messages.

The application implemented with Python WEB framework <b>Flask</b>.

To run application:
```
# Prepare all needed environment variables for WEB application
$ python manage.py db upgrade
$ python manage.py insert_initial_data
$ python manage.py insert_fake_data
$ pybabel compile -d translations
$ python manage.py runserver
```

To run application using docker and docker-compose:
```
# Prepare pg.env file with environment variables for DB
# Prepare web.env file with environment variables for WEB application
$ docker-compose up -d
$ docker-compose exec web python manage.py db upgrade
$ docker-compose exec web python manage.py insert_initial_dat
$ docker-compose exec web python manage.py insert_fake_data
```