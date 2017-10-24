FROM python:2

MAINTAINER Dmitry Moroz "mds.freeman@gmail.com"

EXPOSE 8000

ADD app /app/src/app
ADD migrations /app/src/migrations
ADD requirements /app/src/requirements
ADD utils /app/src/utils
ADD config.py /app/src/
ADD manage.py /app/src/
WORKDIR /app/src/

RUN pip install -r requirements/dev.txt
RUN pybabel compile -d app/translations

CMD ["python", "manage.py", "runserver", "-h", "0.0.0.0", "-p", "8000"]
