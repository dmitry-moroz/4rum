import os
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', '<hard-to-guess-string>')

    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

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
    ROOT_TOPIC_GROUP = 0
    IS_PROTECTED_ROOT_TOPIC_GROUP = True

    TOPIC_ALLOWED_TAGS = [
        'a', 'abbr', 'acronym', 'b', 'blockquote', 'code', 'em', 'i', 'li', 'ol', 'pre', 'strong', 'ul',
        'h1', 'h2', 'h3', 'p', 'table', 'thead', 'tbody', 'tr', 'th', 'td'
    ]

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    DEBUG_TB_INTERCEPT_REDIRECTS = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL',
                                             'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite'))


class TestingConfig(Config):
    DEBUG = False
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL',
                                             'sqlite:///' + os.path.join(basedir, 'data-test.sqlite'))


class ProductionConfig(Config):
    DEBUG = False
    TESTING = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL',
                                             'sqlite:///' + os.path.join(basedir, 'data.sqlite'))


config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
base_config = Config
