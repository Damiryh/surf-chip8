from flask import Blueprint
from flask import flash
from flask import g
from flask import redirect
from flask import render_template
from flask import request
from flask import session
from flask import url_for

from sqlalchemy import select

from .db import get_db_session
from .model import *

import functools

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/sign-up', methods=('GET', 'POST'))
def sign_up():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        dbs = get_db_session()
        error = None
        
        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'

        if error is None:
            user = User(username, password)
            dbs.add(user)

            try:
                dbs.commit()
            except:
                dbs.rollback()
                error = "Sign up error!"
            else:
                return redirect(url_for('auth.sign_in'))

        flash(error)
    return render_template('auth/sign-up.html')

@bp.route('/sign-in', methods=('GET', 'POST'))
def sign_in():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        dbs = get_db_session()
        error = None

        query = select(User).where(User.name == username)
        
        try:
            user = dbs.scalars(query).one()
        except:
            user = None
        
        if (user is None) or (not user.check_password(password)):
            error = 'Incorrect username or password.'

        if error is None:
            session.clear()
            session['user_id'] = user.id
            return redirect(url_for('index'))

        flash(error)
    return render_template('auth/sign-in.html')

@bp.before_app_request
def load_signed_in_user():
    user_id = session.get('user_id')
    g.user = None if (user_id is None) else get_db_session().get(User, user_id)

@bp.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(*args, **kwargs):
        if g.user is None:
            flash("Sign in for access to this page.")
            return redirect(url_for('auth.sign_in'))
        return view(*args, **kwargs)
    return wrapped_view
