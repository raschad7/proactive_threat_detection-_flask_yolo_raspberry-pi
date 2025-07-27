from flask import Blueprint, request, render_template, redirect, url_for, flash, session
import requests
from website.utils import log_event

auth = Blueprint('auth', __name__)

FIREBASE_API_KEY = 'AIzaSyC6iVcb6xk25qwVmbYDW6CFvrnNNCIq8UQ'  # Replace this in production

# ──────────────────────────────────────────────
# LOGIN ROUTE
# ──────────────────────────────────────────────
@auth.route('/login', methods=['GET', 'POST'])
def login_view():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        payload = {
            "email": email,
            "password": password,
            "returnSecureToken": True
        }

        try:
            r = requests.post(
                f"https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_API_KEY}",
                json=payload
            )
            data = r.json()

            if 'idToken' in data:
                session['user'] = data['email']
                log_event("auth", f"User {email} logged in")
                flash('Login successful', 'success')
                return redirect(url_for('views.dashboard'))
            else:
                error_msg = data.get('error', {}).get('message', 'Login failed')
                flash(error_msg, 'danger')
                log_event("auth", f"Failed login attempt for {email}: {error_msg}")

        except Exception as e:
            flash("Login error occurred", 'danger')
            log_event("auth", f"Login exception: {str(e)}")

    return render_template('login.html')

# ──────────────────────────────────────────────
# LOGOUT ROUTE
# ──────────────────────────────────────────────
@auth.route('/logout')
def logout_view():
    user = session.get('user')
    session.pop('user', None)
    if user:
        log_event("auth", f"User {user} logged out")
    flash('Logged out successfully', 'info')
    return redirect(url_for('auth.login_view'))
