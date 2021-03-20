import functools

from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from werkzeug.security import check_password_hash, generate_password_hash


bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/register', methods=('GET', 'POST'))
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        city = request.form['city']
        state = request.form['state']
        zip_code = request.form['zip_code']
        phone_number = request.form['phone_number']

        error = None

        if not username:
            error = 'Username is required.'
        elif not password:
            error = 'Password is required.'
        elif not email:
            error = 'Email is required.'
        elif not city:
            error = 'City is required.'
        elif not state:
            error = 'State is required.'
        elif not zip_code:
            error = 'Zip Code is required.'
        elif not phone_number:
            error = 'Phone Number is required.'
        elif g.conn.execute(
            'SELECT user_id FROM Application_User WHERE user_name = %s', username
        ).fetchone() is not None:
            error = 'User {} is already registered.'.format(username)
        if error is None:
            print("here 2")
            g.conn.execute(
                'INSERT INTO Application_User (user_id, first_name, last_name, user_email, city, zip, phone_number, user_name, password) VALUES (%d, %s, %s, %s, %s, %s, %s, %s, %s)',
                20, first_name, last_name, user_email, city, zip_code, phone_number, username, generate_password_hash(password)
            )
            g.conn.commit()
            return redirect(url_for('auth.login'))

        flash(error)

    return render_template('auth/register.html')

@bp.route('/login', methods=('GET', 'POST'))
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        error = None
        user = g.conn.execute(
            'SELECT * FROM Application_User WHERE user_name = ?', (username,)
        ).fetchone()

        if user is None:
            error = 'Incorrect username.'
        elif not check_password_hash(user['password'], password):
            error = 'Incorrect password.'

        if error is None:
            session.clear()
            session['user_id'] = user['id']
            return redirect(url_for('index'))

        flash(error)

    return render_template('auth/login.html')

@bp.before_app_request
def load_logged_in_user():
    user_id = session.get('user_id')

    if user_id is None:
        g.user = None
    else:
        g.user = g.conn.execute(
            'SELECT * FROM Application_User WHERE id = ?', (user_id,)
        ).fetchone()

def logout():
    session.clear()
    return redirect(url_for('index'))

def login_required(view):
    @functools.wraps(view)
    def wrapped_view(**kwargs):
        if g.user is None:
            return redirect(url_for('auth.login'))

        return view(**kwargs)

    return wrapped_view