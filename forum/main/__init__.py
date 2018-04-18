from flask import Blueprint

main = Blueprint('main', __name__)

from flask_wtf.csrf import generate_csrf  # noqa: E402
from flask_babel import format_datetime, format_timedelta  # noqa: E402

from . import views, errors  # noqa: E402, F401
from ..models import Permission  # noqa: E402


@main.app_context_processor
def inject_variables_for_jinja():
    return dict(
        Permission=Permission,
        format_datetime=format_datetime,
        format_timedelta=format_timedelta,
        get_locale=views.get_locale,
        generate_csrf=generate_csrf,
    )
