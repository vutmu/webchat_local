from flask import session, url_for, request
from werkzeug.utils import redirect


def sessions(view_function):
    def wrapper(*args, **kwargs):
        if 'username' in session:
            return view_function(*args, **kwargs)
        else:
            return redirect(url_for('auth'))
    wrapper.__name__ = view_function.__name__
    return wrapper
