web: gunicorn 'forum.app:create_app()' --access-logfile - --error-logfile -
worker: celery worker -A forum.celery_worker.celery --loglevel=info --without-heartbeat
