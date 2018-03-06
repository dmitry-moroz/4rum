from flask import current_app
from flask_mail import Message

from .app import mail, celery


@celery.task()
def send_email(recipients, subject, body, html):
    full_subject = ' '.join((current_app.config['APP_MAIL_SUBJECT_PREFIX'], subject))
    msg = Message(full_subject, sender=current_app.config['APP_MAIL_SENDER'], recipients=recipients)
    msg.body = body
    msg.html = html
    mail.send(msg)
