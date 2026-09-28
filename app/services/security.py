from functools import wraps
from flask import abort, g


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user is None:
            abort(401)
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @login_required
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.user.role != "admin":
            abort(403)
        return view(*args, **kwargs)
    return wrapped
