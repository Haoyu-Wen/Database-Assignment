from functools import wraps
from flask import g, redirect, url_for


def login_requried(func):
    # keep info of func
    @wraps(func)
    def inner(*args, **kwargs):
        if g.user:
            return func(*args, **kwargs)
        else:
            return redirect(url_for("account.login"))
    return inner
