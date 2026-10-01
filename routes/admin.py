from functools import wraps
from datetime import datetime
import os
import re
import uuid
from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, current_app
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.utils import secure_filename
from models import User, Product, Category, Team, ProductVariant, Order, OrderItem, Payment, ContactMessage
from extensions import db
from sqlalchemy import func, desc

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

@admin_bp.after_request
def prevent_admin_page_caching(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, private'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            return redirect(url_for('admin.login', next=request.url))
        if not current_user.is_admin:
            flash('Access denied. Administrator privileges required.', 'danger')
            return redirect(url_for('main.home'))
        return f(*args, **kwargs)
    return decorated_function

def slugify(text):
    text = re.sub(r'[^\w\s-]', '', text).strip().lower()
    return re.sub(r'[-\s]+', '-', text)

def save_product_image(upload):
    if not upload or not upload.filename:
        return None

    extension = os.path.splitext(secure_filename(upload.filename))[1].lower().lstrip('.')
    if extension not in current_app.config.get('ALLOWED_EXTENSIONS', set()):
        raise ValueError('Please upload a PNG, JPG, JPEG, WEBP, or GIF image.')

    filename = f'{uuid.uuid4().hex}.{extension}'
    upload_folder = current_app.config['UPLOAD_FOLDER']
    os.makedirs(upload_folder, exist_ok=True)
    upload.save(os.path.join(upload_folder, filename))
    return url_for('static', filename=f'uploads/{filename}')

# --- ADMIN AUTHENTICATION ---

@admin_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(url_for('admin.dashboard'))

    if request.method == 'POST':
        identifier = request.form.get('identifier', '').strip()
        password = request.form.get('password', '')

        user = User.query.filter(
            ((User.username == identifier) | (User.email == identifier.lower())) & (User.is_admin == True)
        ).first()

        if not user or not user.check_password(password):
            flash('Invalid admin credentials. Please try again.', 'danger')
            return render_template('admin/login.html')

        if not user.is_active:
            flash('This admin account has been deactivated.', 'danger')
            return render_template('admin/login.html')

        login_user(user)
        flash(f'Welcome back, Administrator {user.username}!', 'success')
        return redirect(url_for('admin.dashboard'))

    return render_template('admin/login.html')

@admin_bp.route('/logout')
@admin_required
def logout():
    logout_user()
    flash('Admin session ended.', 'info')
    return redirect(url_for('main.home'))

# --- ADMIN DASHBOARD ---

@admin_bp.route('/')
@admin_bp.route('/dashboard')
@admin_required
def dashboard():
    total_sales = db.session.query(func.coalesce(func.sum(Order.total_amount), 0)).filter(Order.status != 'Cancelled').scalar()
    total_orders = Order.query.count()
    total_customers = User.query.filter_by(is_admin=False).count()
    total_products = Product.query.count()

    # Recent orders
    recent_orders = Order.query.order_by(Order.created_at.desc()).limit(7).all()

    # Low stock alerts (variant stock <= 5)
    low_stock_variants = ProductVariant.query.filter(ProductVariant.stock_quantity <= 5).all()

    # Top selling products
    top_selling = db.session.query(
        OrderItem.product_name,
        func.sum(OrderItem.quantity).label('units_sold'),
        func.sum(OrderItem.total_price).label('total_revenue')
    ).join(Order, OrderItem.order_id == Order.id)\
     .filter(Order.status != 'Cancelled')\
     .group_by(OrderItem.product_name)\
     .order_by(desc('units_sold'))\
     .limit(5).all()

    # Unread messages
    unread_messages = ContactMessage.query.filter_by(is_read=False).count()

    return render_template(
        'admin/dashboard.html',
        total_sales=float(total_sales),
        total_orders=total_orders,
        total_customers=total_customers,
        total_products=total_products,
        recent_orders=recent_orders,
        low_stock_variants=low_stock_variants,
        top_selling=top_selling,
        unread_messages=unread_messages
    )

# --- PRODUCTS MANAGEMENT ---

@admin_bp.route('/products')
@admin_required
def products():
    search = request.args.get('search', '').strip()
    category_id = request.args.get('category_id', type=int)
    team_id = request.args.get('team_id', type=int)

    query = Product.query
    if search:
        query = query.filter(Product.name.ilike(f'%{search}%'))
    if category_id:
        query = query.filter_by(category_id=category_id)
    if team_id:
        query = query.filter_by(team_id=team_id)

    all_products = query.order_by(Product.created_at.desc()).all()
    categories = Category.query.order_by(Category.name.asc()).all()
    teams = Team.query.order_by(Team.name.asc()).all()

    return render_template(
        'admin/products.html',
        products=all_products,
        categories=categories,
        teams=teams,
        search=search,
        selected_category=category_id,
        selected_team=team_id
    )

@admin_bp.route('/products/add', methods=['GET', 'POST'])
@admin_required
def add_product():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        slug = request.form.get('slug', '').strip() or slugify(name)
        team_id = request.form.get('team_id', type=int)
        category_id = request.form.get('category_id', type=int)
        description = request.form.get('description', '').strip()
        price = request.form.get('price', type=float)
        discount_price = request.form.get('discount_price', type=float) or None
        season = request.form.get('season', '2024/25').strip()
        kit_type = request.form.get('kit_type', 'Home').strip()
        gender = request.form.get('gender', 'Men').strip()
        primary_image = request.form.get('primary_image', '').strip()
        secondary_image = request.form.get('secondary_image', '').strip() or None

        is_featured = bool(request.form.get('is_featured'))
        is_bestseller = bool(request.form.get('is_bestseller'))
        is_new_arrival = bool(request.form.get('is_new_arrival'))

        # Check unique slug
        if Product.query.filter_by(slug=slug).first():
            slug = f"{slug}-{datetime.utcnow().strftime('%M%S')}"

        if not name or not team_id or not price:
            flash('Name, Team, and Price are required.', 'danger')
            return redirect(url_for('admin.add_product'))

        if discount_price is not None and discount_price >= price:
            flash('Discount price must be strictly less than regular price.', 'danger')
            return redirect(url_for('admin.add_product'))

        try:
            primary_image = save_product_image(request.files.get('primary_image_file')) or primary_image
            secondary_image = save_product_image(request.files.get('secondary_image_file')) or secondary_image
        except ValueError as error:
            flash(str(error), 'danger')
            return redirect(url_for('admin.add_product'))

        # Default fallback image if none provided
        if not primary_image:
            primary_image = 'https://images.unsplash.com/photo-1577223625816-7546f13df25d?w=800&auto=format&fit=crop&q=80'

        new_product = Product(
            name=name,
            slug=slug,
            team_id=team_id,
            category_id=category_id,
            description=description,
            price=price,
            discount_price=discount_price,
            season=season,
            kit_type=kit_type,
            gender=gender,
            primary_image=primary_image,
            secondary_image=secondary_image,
            is_featured=is_featured,
            is_bestseller=is_bestseller,
            is_new_arrival=is_new_arrival
        )
        db.session.add(new_product)
        db.session.flush()

        # Add variants for standard sizes
        sizes = ['S', 'M', 'L', 'XL', 'XXL']
        for s in sizes:
            stock = request.form.get(f'stock_{s}', 10, type=int)
            variant = ProductVariant(
                product_id=new_product.id,
                size=s,
                stock_quantity=max(0, stock),
                sku=f"{new_product.id}-{s}"
            )
            db.session.add(variant)

        db.session.commit()
        flash(f'Product "{new_product.name}" created successfully with stock variants!', 'success')
        return redirect(url_for('admin.products'))

    categories = Category.query.order_by(Category.name.asc()).all()
    teams = Team.query.order_by(Team.name.asc()).all()
    return render_template('admin/product_form.html', product=None, categories=categories, teams=teams)

@admin_bp.route('/products/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_product(id):
    product = Product.query.get_or_404(id)

    if request.method == 'POST':
        product.name = request.form.get('name', '').strip()
        slug_input = request.form.get('slug', '').strip()
        if slug_input and slug_input != product.slug:
            existing = Product.query.filter_by(slug=slug_input).first()
            if not existing or existing.id == product.id:
                product.slug = slug_input

        product.team_id = request.form.get('team_id', type=int)
        product.category_id = request.form.get('category_id', type=int)
        product.description = request.form.get('description', '').strip()
        new_price = request.form.get('price', type=float)
        disc = request.form.get('discount_price', '').strip()
        new_discount = float(disc) if disc else None

        if new_discount is not None and new_price is not None and new_discount >= new_price:
            flash('Discount price must be strictly less than regular price.', 'danger')
            return redirect(url_for('admin.edit_product', id=product.id))

        product.price = new_price
        product.discount_price = new_discount
        product.season = request.form.get('season', '2024/25').strip()
        product.kit_type = request.form.get('kit_type', 'Home').strip()
        product.gender = request.form.get('gender', 'Men').strip()
        
        img = request.form.get('primary_image', '').strip()
        sec_img = request.form.get('secondary_image', '').strip()
        try:
            uploaded_primary = save_product_image(request.files.get('primary_image_file'))
            uploaded_secondary = save_product_image(request.files.get('secondary_image_file'))
        except ValueError as error:
            flash(str(error), 'danger')
            return redirect(url_for('admin.edit_product', id=product.id))

        if uploaded_primary or img:
            product.primary_image = uploaded_primary or img
        product.secondary_image = uploaded_secondary or (sec_img if sec_img else None)

        product.is_featured = bool(request.form.get('is_featured'))
        product.is_bestseller = bool(request.form.get('is_bestseller'))
        product.is_new_arrival = bool(request.form.get('is_new_arrival'))

        # Update variant stocks
        for s in ['S', 'M', 'L', 'XL', 'XXL']:
            stock = request.form.get(f'stock_{s}', type=int)
            if stock is not None:
                variant = ProductVariant.query.filter_by(product_id=product.id, size=s).first()
                if variant:
                    variant.stock_quantity = max(0, stock)
                else:
                    new_variant = ProductVariant(
                        product_id=product.id,
                        size=s,
                        stock_quantity=max(0, stock),
                        sku=f"{product.id}-{s}"
                    )
                    db.session.add(new_variant)

        db.session.commit()
        flash(f'Product "{product.name}" updated successfully.', 'success')
        return redirect(url_for('admin.products'))

    categories = Category.query.order_by(Category.name.asc()).all()
    teams = Team.query.order_by(Team.name.asc()).all()
    variants_by_size = {v.size: v.stock_quantity for v in product.variants.all()}

    return render_template(
        'admin/product_form.html',
        product=product,
        categories=categories,
        teams=teams,
        variants_by_size=variants_by_size
    )

@admin_bp.route('/products/delete/<int:id>', methods=['POST'])
@admin_required
def delete_product(id):
    product = Product.query.get_or_404(id)
    name = product.name
    for img_val in [product.primary_image, product.secondary_image]:
        if img_val and '/static/uploads/' in img_val:
            fname = img_val.split('/static/uploads/')[-1]
            fpath = os.path.join(current_app.config['UPLOAD_FOLDER'], fname)
            if os.path.exists(fpath):
                try:
                    os.remove(fpath)
                except OSError:
                    pass
    db.session.delete(product)
    db.session.commit()
    flash(f'Product "{name}" deleted successfully.', 'info')
    return redirect(url_for('admin.products'))

# --- INVENTORY MANAGEMENT ---

@admin_bp.route('/inventory', methods=['GET', 'POST'])
@admin_required
def inventory():
    if request.method == 'POST':
        variant_id = request.form.get('variant_id', type=int)
        new_stock = request.form.get('stock_quantity', type=int)

        if variant_id and new_stock is not None:
            variant = db.session.get(ProductVariant, variant_id)
            if variant:
                variant.stock_quantity = max(0, new_stock)
                db.session.commit()
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({'success': True, 'new_stock': variant.stock_quantity})
                flash(f'Updated stock for {variant.product.name} (Size: {variant.size}) to {variant.stock_quantity}.', 'success')

        return redirect(url_for('admin.inventory'))

    low_only = bool(request.args.get('low_only'))
    if low_only:
        products_list = Product.query.filter(
            Product.variants.any(ProductVariant.stock_quantity <= 5)
        ).order_by(Product.name.asc()).all()
    else:
        products_list = Product.query.order_by(Product.name.asc()).all()

    return render_template('admin/inventory.html', products=products_list, low_only=low_only)

# --- CATEGORIES & TEAMS MANAGEMENT ---

@admin_bp.route('/categories', methods=['GET', 'POST'])
@admin_required
def categories():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add_category':
            name = request.form.get('name', '').strip()
            desc = request.form.get('description', '').strip()
            img = request.form.get('image_url', '').strip()
            if name:
                slug = slugify(name)
                if not Category.query.filter_by(slug=slug).first():
                    new_cat = Category(name=name, slug=slug, description=desc, image_url=img)
                    db.session.add(new_cat)
                    db.session.commit()
                    flash(f'Category "{name}" created.', 'success')
                else:
                    flash('A category with this name already exists.', 'warning')

        elif action == 'add_team':
            name = request.form.get('name', '').strip()
            cat_id = request.form.get('category_id', type=int)
            logo = request.form.get('logo_url', '').strip()
            country = request.form.get('country', '').strip()
            if name and cat_id:
                slug = slugify(name)
                new_team = Team(name=name, slug=slug, category_id=cat_id, logo_url=logo, country=country)
                db.session.add(new_team)
                db.session.commit()
                flash(f'Team "{name}" added.', 'success')

        elif action == 'delete_category':
            cat_id = request.form.get('category_id', type=int)
            cat = db.session.get(Category, cat_id)
            if cat:
                db.session.delete(cat)
                db.session.commit()
                flash(f'Category "{cat.name}" removed.', 'info')

        elif action == 'delete_team':
            team_id = request.form.get('team_id', type=int)
            tm = db.session.get(Team, team_id)
            if tm:
                db.session.delete(tm)
                db.session.commit()
                flash(f'Team "{tm.name}" removed.', 'info')

        return redirect(url_for('admin.categories'))

    all_categories = Category.query.order_by(Category.name.asc()).all()
    all_teams = Team.query.order_by(Team.name.asc()).all()
    return render_template('admin/categories.html', categories=all_categories, teams=all_teams)

# --- ORDERS MANAGEMENT ---

@admin_bp.route('/orders')
@admin_required
def orders():
    status_filter = request.args.get('status', '').strip()
    search = request.args.get('search', '').strip()

    query = Order.query
    if status_filter:
        query = query.filter_by(status=status_filter)
    if search:
        query = query.filter(
            (Order.order_number.ilike(f'%{search}%')) |
            (Order.shipping_name.ilike(f'%{search}%')) |
            (Order.shipping_phone.ilike(f'%{search}%'))
        )

    all_orders = query.order_by(Order.created_at.desc()).all()
    return render_template('admin/orders.html', orders=all_orders, status_filter=status_filter, search=search)

@admin_bp.route('/orders/<int:order_id>')
@admin_required
def order_detail(order_id):
    order = Order.query.get_or_404(order_id)
    return render_template('admin/order_detail.html', order=order)

@admin_bp.route('/orders/<int:order_id>/status', methods=['POST'])
@admin_required
def update_order_status(order_id):
    order = Order.query.get_or_404(order_id)
    new_status = request.form.get('status', '').strip()

    valid_statuses = ['Pending', 'Processing', 'Shipped', 'Delivered', 'Cancelled']
    if new_status in valid_statuses:
        # If moving to cancelled, restore stock and sync payment
        if new_status == 'Cancelled' and order.status != 'Cancelled':
            for item in order.items:
                if item.variant_id:
                    v = db.session.get(ProductVariant, item.variant_id)
                    if v:
                        v.stock_quantity += item.quantity
            if order.payment:
                order.payment.payment_status = 'Refunded' if order.payment.payment_status == 'Completed' else 'Cancelled'
        elif new_status != 'Cancelled' and order.status == 'Cancelled':
            for item in order.items:
                if item.variant_id:
                    v = db.session.get(ProductVariant, item.variant_id)
                    if v:
                        v.stock_quantity = max(0, v.stock_quantity - item.quantity)
            if order.payment and order.payment.payment_status in ['Refunded', 'Cancelled']:
                order.payment.payment_status = 'Completed' if order.payment.payment_method != 'Cash on Delivery' else 'Pending'

        order.status = new_status
        db.session.commit()
        flash(f'Order {order.order_number} status updated to {new_status}.', 'success')

    return redirect(request.referrer or url_for('admin.orders'))

# --- CUSTOMERS MANAGEMENT ---

@admin_bp.route('/customers')
@admin_required
def customers():
    search = request.args.get('search', '').strip()
    query = User.query.filter_by(is_admin=False)
    if search:
        query = query.filter(
            (User.username.ilike(f'%{search}%')) |
            (User.email.ilike(f'%{search}%')) |
            (User.full_name.ilike(f'%{search}%'))
        )
    customers_list = query.order_by(User.created_at.desc()).all()
    return render_template('admin/customers.html', customers=customers_list, search=search)

@admin_bp.route('/customers/<int:user_id>')
@admin_required
def customer_detail(user_id):
    customer = User.query.filter_by(id=user_id, is_admin=False).first_or_404()
    orders = customer.orders.order_by(Order.created_at.desc()).all()
    return render_template('admin/customer_detail.html', customer=customer, orders=orders)

@admin_bp.route('/customers/<int:user_id>/toggle-status', methods=['POST'])
@admin_required
def toggle_customer_status(user_id):
    customer = User.query.get_or_404(user_id)
    if not customer.is_admin:
        customer.is_active = not customer.is_active
        db.session.commit()
        status_word = "activated" if customer.is_active else "deactivated"
        flash(f'Customer {customer.username} has been {status_word}.', 'info')
    return redirect(url_for('admin.customers'))

# --- PAYMENTS MANAGEMENT ---

@admin_bp.route('/payments')
@admin_required
def payments():
    status_filter = request.args.get('status', '').strip()
    method_filter = request.args.get('method', '').strip()

    query = Payment.query
    if status_filter:
        query = query.filter_by(payment_status=status_filter)
    if method_filter:
        query = query.filter_by(payment_method=method_filter)

    all_payments = query.order_by(Payment.paid_at.desc()).all()
    total_collected = sum(float(p.amount) for p in all_payments if p.payment_status == 'Completed')

    return render_template(
        'admin/payments.html',
        payments=all_payments,
        total_collected=total_collected,
        status_filter=status_filter,
        method_filter=method_filter
    )

# --- SALES REPORTS ---

@admin_bp.route('/sales')
@admin_required
def sales():
    # Revenue by Category
    category_revenue = db.session.query(
        Category.name,
        func.coalesce(func.sum(OrderItem.total_price), 0).label('revenue'),
        func.coalesce(func.sum(OrderItem.quantity), 0).label('units')
    ).join(Product, Product.category_id == Category.id)\
     .join(OrderItem, OrderItem.product_id == Product.id)\
     .join(Order, OrderItem.order_id == Order.id)\
     .filter(Order.status != 'Cancelled')\
     .group_by(Category.name)\
     .order_by(desc('revenue')).all()

    # Bestselling jerseys
    bestsellers = db.session.query(
        OrderItem.product_name,
        func.sum(OrderItem.quantity).label('units_sold'),
        func.sum(OrderItem.total_price).label('revenue')
    ).join(Order, OrderItem.order_id == Order.id)\
     .filter(Order.status != 'Cancelled')\
     .group_by(OrderItem.product_name)\
     .order_by(desc('revenue'))\
     .limit(10).all()

    # Payment method breakdown
    method_breakdown = db.session.query(
        Payment.payment_method,
        func.count(Payment.id).label('count'),
        func.sum(Payment.amount).label('total')
    ).group_by(Payment.payment_method).all()

    total_gross = db.session.query(func.coalesce(func.sum(Order.total_amount), 0)).filter(Order.status != 'Cancelled').scalar()

    return render_template(
        'admin/sales.html',
        category_revenue=category_revenue,
        bestsellers=bestsellers,
        method_breakdown=method_breakdown,
        total_gross=float(total_gross)
    )

# --- CONTACT MESSAGES ---

@admin_bp.route('/messages')
@admin_required
def messages():
    all_msgs = ContactMessage.query.order_by(ContactMessage.created_at.desc()).all()
    return render_template('admin/messages.html', messages=all_msgs)

@admin_bp.route('/messages/<int:id>/mark-read', methods=['POST'])
@admin_required
def mark_message_read(id):
    msg = ContactMessage.query.get_or_404(id)
    msg.is_read = True
    db.session.commit()
    return redirect(url_for('admin.messages'))
