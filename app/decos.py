from functools import wraps
from .db import User, Permission
from flask_login import current_user
from flask import redirect, url_for, abort

def permission_required(permission):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                return redirect(url_for('auth.login'))
            if not current_user.has_perm(permission):
                abort(404)
            return f(*args, **kwargs)
        return decorated_function
    return decorator
def admin_required(f):
    return permission_required(Permission.ADMINISTRATOR)(f)
