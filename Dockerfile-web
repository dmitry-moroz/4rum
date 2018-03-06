FROM python:2

MAINTAINER Dmitry Moroz "mds.freeman@gmail.com"

EXPOSE 8000

ADD forum /app/src/forum
ADD migrations /app/src/migrations
ADD requirements /app/src/requirements
ADD utils /app/src/utils
ADD manage.py /app/src/
WORKDIR /app/src/

RUN pip install -r requirements/dev.txt
RUN pybabel compile -d forum/translations

CMD ["gunicorn", "--reload", "-b", "0.0.0.0:8000", "forum.app:create_app()"]
