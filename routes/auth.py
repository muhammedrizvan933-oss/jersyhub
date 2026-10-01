from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from models import User, Order
from extensions import db
import re

auth_bp = Blueprint('auth', __name__)

def is_safe_redirect(url):
    return bool(url and url.startswith('/') and not url.startswith('//') and not url.startswith('/\\'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip().lower()
        full_name = request.form.get('full_name', '').strip()
        phone = request.form.get('phone', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        # Validations
        if not username or not email or not password:
            flash('Username, email, and password are required.', 'danger')
            return render_template('auth/register.html')

        if len(password) < 6:
            flash('Password must be at least 6 characters long.', 'danger')
            return render_template('auth/register.html')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('auth/register.html')

        # Check existing user
        if User.query.filter_by(username=username).first():
            flash('Username is already taken. Please choose another one.', 'danger')
            return render_template('auth/register.html')

        if User.query.filter_by(email=email).first():
            flash('An account with this email address already exists. Please log in.', 'danger')
            return render_template('auth/register.html')

        # Create user
        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            phone=phone,
            is_admin=False
        )
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        from routes.cart import merge_guest_cart_to_db
        merge_guest_cart_to_db(new_user)

        flash(f'Welcome to JerseyHub, {new_user.username}! Your account has been created.', 'success')

        next_page = request.args.get('next')
        if is_safe_redirect(next_page):
            return redirect(next_page)
        return redirect(url_for('main.home'))

    return render_template('auth/register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.home'))

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip() # can be username or email
        password = request.form.get('password', '')
        remember = bool(request.form.get('remember'))

        if not identifier or not password:
            flash('Please provide both username/email and password.', 'danger')
            return render_template('auth/login.html')

        # Find user by username or email
        user = User.query.filter((User.username == identifier) | (User.email == identifier.lower())).first()

        if not user or not user.check_password(password):
            flash('Invalid username/email or password.', 'danger')
            return render_template('auth/login.html')

        if not user.is_active:
            flash('Your account has been deactivated. Please contact support.', 'danger')
            return render_template('auth/login.html')

        login_user(user, remember=remember)
        from routes.cart import merge_guest_cart_to_db
        merge_guest_cart_to_db(user)

        flash(f'Welcome back, {user.full_name or user.username}!', 'success')

        next_page = request.args.get('next')
        if is_safe_redirect(next_page):
            return redirect(next_page)
        if user.is_admin:
            return redirect(url_for('admin.dashboard'))
        return redirect(url_for('main.home'))

    return render_template('auth/login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('You have been logged out safely.', 'info')
    return redirect(url_for('main.home'))


@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_profile':
            current_user.full_name = request.form.get('full_name', '').strip()
            current_user.phone = request.form.get('phone', '').strip()
            current_user.address = request.form.get('address', '').strip()
            current_user.city = request.form.get('city', '').strip()
            current_user.state = request.form.get('state', '').strip()
            current_user.postal_code = request.form.get('postal_code', '').strip()
            current_user.country = request.form.get('country', '').strip()
            db.session.commit()
            flash('Your profile details have been updated.', 'success')

        elif action == 'change_password':
            old_password = request.form.get('old_password', '')
            new_password = request.form.get('new_password', '')
            confirm_new_password = request.form.get('confirm_new_password', '')

            if not current_user.check_password(old_password):
                flash('Current password is incorrect.', 'danger')
            elif len(new_password) < 6:
                flash('New password must be at least 6 characters long.', 'danger')
            elif new_password != confirm_new_password:
                flash('New passwords do not match.', 'danger')
            else:
                current_user.set_password(new_password)
                db.session.commit()
                flash('Password changed successfully!', 'success')

        return redirect(url_for('auth.profile'))

    recent_orders = current_user.orders.order_by(Order.created_at.desc()).limit(5).all()
    return render_template('customer/profile.html', recent_orders=recent_orders)
