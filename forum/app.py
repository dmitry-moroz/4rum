from flask import Flask
from flask_babel import Babel
from flask_babel import lazy_gettext
from flask_bootstrap import Bootstrap
from flask_login import LoginManager
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from werkzeug.contrib.fixers import ProxyFix

from .config import config

bootstrap = Bootstrap()
mail = Mail()
db = SQLAlchemy()
babel = Babel()
login_manager = LoginManager()
login_manager.localize_callback = lazy_gettext
login_manager.login_view = 'auth.login'


def create_app():
    app = Flask(__name__)
    app.config.from_object(config)
    config.init_app(app)

    bootstrap.init_app(app)
    mail.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    babel.init_app(app)

    if app.config['SSL_REDIRECT']:
        from flask_sslify import SSLify
        SSLify(app)

    app.wsgi_app = ProxyFix(app.wsgi_app)

    if app.debug:
        from flask_debugtoolbar import DebugToolbarExtension
        debug_toolbar = DebugToolbarExtension()
        debug_toolbar.init_app(app)

    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint, url_prefix='/auth')

    return app
