from flask import Blueprint

main = Blueprint('main', __name__)

from . import views, errors  # noqa: E402, F401
from ..models import Permission  # noqa: E402


@main.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)
