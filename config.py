import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', '<hard-to-guess-string>')
    SESSION_PROTECTION = 'basic'
    THEME = os.environ.get('THEME', 'gray')

    DEBUG = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    TESTING = False

    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    DB_USER = os.environ.get('DB_USER', 'postgres')
    DB_PASSWORD = os.environ.get('DB_PASSWORD', 'password')
    DB_HOST = os.environ.get('DB_HOST', 'pg')
    DB_PORT = os.environ.get('DB_PORT', '5432')
    DB_NAME = os.environ.get('DB_NAME', 'forum')
    PG_DATABASE_URI = 'postgresql://{user}:{password}@{hostname}:{port}/{db_name}'.format(
        user=DB_USER, password=DB_PASSWORD, hostname=DB_HOST, port=DB_PORT, db_name=DB_NAME
    )
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', PG_DATABASE_URI)

    MAIL_SERVER = 'smtp.googlemail.com'
    MAIL_PORT = 587
    MAIL_USE_TLS = True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME', '4rum@example.com')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', 'password')

    APP_MAIL_SUBJECT_PREFIX = '[4RUM]'
    APP_MAIL_SENDER = '4RUM Admin <name@example.com>'
    APP_ADMIN = os.environ.get('ADMIN_MAIL_USERNAME', '4rum_admin@example.com')

    BASE_GRAVATAR_URL = 'https://secure.gravatar.com/avatar'
    TOPIC_GROUP_PRIORITY = range(1, 11)
    TOPICS_PER_PAGE = 20
    COMMENTS_PER_PAGE = 20
    MESSAGES_PER_PAGE = 20
    USERS_PER_PAGE = 20
    ROOT_TOPIC_GROUP = 0
    IS_PROTECTED_ROOT_TOPIC_GROUP = True

    TOPIC_ALLOWED_TAGS = [
        'a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
        'h1', 'h2', 'h3', 'p', 'table', 'thead', 'tbody', 'tr', 'th', 'td'
    ]

    SUPPORTED_LANGUAGES = {'en': 'English', 'ru': 'Russian'}
    BABEL_DEFAULT_LOCALE = 'ru'
    BABEL_DEFAULT_TIMEZONE = 'Europe/Minsk'
    BABEL_TRANSLATION_DIRECTORIES = 'translations'

    @staticmethod
    def init_app(app):
        pass


config = Config()
