from functools import wraps

from flask import abort
from flask_login import current_user

from models import PAPEL_ADMIN, PAPEL_PROFESSOR


def papel_required(*papeis_permitidos):
    """Bloqueia o acesso à view se o usuário logado não tiver um dos papéis informados."""

    def decorator(view_func):
        @wraps(view_func)
        def wrapped_view(*args, **kwargs):
            if not current_user.is_authenticated:
                abort(401)
            if current_user.papel not in papeis_permitidos:
                abort(403)
            return view_func(*args, **kwargs)

        return wrapped_view

    return decorator


def admin_required(view_func):
    return papel_required(PAPEL_ADMIN)(view_func)


def professor_required(view_func):
    return papel_required(PAPEL_PROFESSOR)(view_func)
