from flask import session, url_for
from werkzeug.utils import redirect


def sessions(view_function):
    def wrapper(*args, **kwargs):
        if 'username' in session:
            return view_function(*args, **kwargs)
        else:
            return redirect(url_for('auth'))
    return wrapper
