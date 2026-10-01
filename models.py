from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin
from extensions import db, login_manager

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(25), nullable=True)
    address = db.Column(db.Text, nullable=True)
    city = db.Column(db.String(80), nullable=True)
    state = db.Column(db.String(80), nullable=True)
    postal_code = db.Column(db.String(20), nullable=True)
    country = db.Column(db.String(80), default='India')
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    orders = db.relationship('Order', backref='customer', lazy='dynamic', cascade='all, delete-orphan')
    cart_items = db.relationship('CartItem', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='author', lazy='dynamic', cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @property
    def orders_count(self):
        return self.orders.count()

    @property
    def total_spent(self):
        completed_orders = self.orders.filter(Order.status.in_(['Processing', 'Shipped', 'Delivered', 'Pending'])).all()
        return sum(float(order.total_amount) for order in completed_orders)

    def __repr__(self):
        return f'<User {self.username}>'


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    slug = db.Column(db.String(100), unique=True, nullable=False, index=True)
    description = db.Column(db.Text, nullable=True)
    image_url = db.Column(db.String(500), nullable=True)
    display_order = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    teams = db.relationship('Team', backref='category', lazy='dynamic', cascade='all, delete-orphan')
    products = db.relationship('Product', backref='category', lazy='dynamic')

    @property
    def products_count(self):
        return self.products.count()

    def __repr__(self):
        return f'<Category {self.name}>'


class Team(db.Model):
    __tablename__ = 'teams'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    slug = db.Column(db.String(100), nullable=False, index=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='CASCADE'), nullable=False)
    logo_url = db.Column(db.String(500), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    products = db.relationship('Product', backref='team', lazy='dynamic', cascade='all, delete-orphan')

    @property
    def products_count(self):
        return self.products.count()

    def __repr__(self):
        return f'<Team {self.name}>'


class Product(db.Model):
    __tablename__ = 'products'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False, index=True)
    slug = db.Column(db.String(160), unique=True, nullable=False, index=True)
    team_id = db.Column(db.Integer, db.ForeignKey('teams.id', ondelete='CASCADE'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id', ondelete='SET NULL'), nullable=True)
    description = db.Column(db.Text, nullable=True)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    discount_price = db.Column(db.Numeric(10, 2), nullable=True)
    season = db.Column(db.String(20), default='2024/25')
    kit_type = db.Column(db.String(30), default='Home') # Home, Away, Third, Retro, Goalkeeper
    gender = db.Column(db.String(20), default='Men')     # Men, Women, Kids, Unisex
    primary_image = db.Column(db.String(500), nullable=False)
    secondary_image = db.Column(db.String(500), nullable=True)
    is_featured = db.Column(db.Boolean, default=False, index=True)
    is_bestseller = db.Column(db.Boolean, default=False, index=True)
    is_new_arrival = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    variants = db.relationship('ProductVariant', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    reviews = db.relationship('Review', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    cart_items = db.relationship('CartItem', backref='product', lazy='dynamic', cascade='all, delete-orphan')
    order_items = db.relationship('OrderItem', backref='product', lazy='dynamic')

    @property
    def effective_price(self):
        if self.discount_price and self.discount_price > 0:
            return float(self.discount_price)
        return float(self.price)

    @property
    def has_discount(self):
        return bool(self.discount_price and self.discount_price > 0 and self.discount_price < self.price)

    @property
    def discount_percent(self):
        if self.has_discount:
            return int(round((1.0 - float(self.discount_price) / float(self.price)) * 100))
        return 0

    @property
    def total_stock(self):
        return sum(variant.stock_quantity for variant in self.variants.all())

    @property
    def in_stock(self):
        return self.total_stock > 0

    @property
    def average_rating(self):
        reviews_list = self.reviews.all()
        if not reviews_list:
            return 4.8  # Default store rating for unreviewed
        return round(sum(r.rating for r in reviews_list) / len(reviews_list), 1)

    @property
    def review_count(self):
        return self.reviews.count()

    def __repr__(self):
        return f'<Product {self.name}>'


class ProductVariant(db.Model):
    __tablename__ = 'product_variants'

    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    size = db.Column(db.String(10), nullable=False) # S, M, L, XL, XXL
    stock_quantity = db.Column(db.Integer, default=0, nullable=False)
    sku = db.Column(db.String(50), unique=True, nullable=True)

    # Relationships
    cart_items = db.relationship('CartItem', backref='variant', lazy='dynamic', cascade='all, delete-orphan')
    order_items = db.relationship('OrderItem', backref='variant', lazy='dynamic')

    def __repr__(self):
        return f'<ProductVariant {self.size} (Stock: {self.stock_quantity})>'


class CartItem(db.Model):
    __tablename__ = 'cart_items'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id', ondelete='CASCADE'), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    @property
    def item_total(self):
        return float(self.product.effective_price) * self.quantity

    def __repr__(self):
        return f'<CartItem user={self.user_id} product={self.product_id} qty={self.quantity}>'


class Order(db.Model):
    __tablename__ = 'orders'

    id = db.Column(db.Integer, primary_key=True)
    order_number = db.Column(db.String(30), unique=True, nullable=False, index=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    subtotal = db.Column(db.Numeric(10, 2), nullable=False)
    shipping_fee = db.Column(db.Numeric(10, 2), default=0.00, nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(30), default='Pending', nullable=False) # Pending, Processing, Shipped, Delivered, Cancelled
    
    # Shipping details
    shipping_name = db.Column(db.String(120), nullable=False)
    shipping_phone = db.Column(db.String(25), nullable=False)
    shipping_address = db.Column(db.Text, nullable=False)
    shipping_city = db.Column(db.String(80), nullable=False)
    shipping_state = db.Column(db.String(80), nullable=True)
    shipping_postal_code = db.Column(db.String(20), nullable=False)
    shipping_country = db.Column(db.String(80), default='India')
    notes = db.Column(db.Text, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    payment = db.relationship('Payment', backref='order', uselist=False, cascade='all, delete-orphan')

    @property
    def items_count(self):
        return sum(item.quantity for item in self.items.all())

    def __repr__(self):
        return f'<Order {self.order_number}>'


class OrderItem(db.Model):
    __tablename__ = 'order_items'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='SET NULL'), nullable=True)
    variant_id = db.Column(db.Integer, db.ForeignKey('product_variants.id', ondelete='SET NULL'), nullable=True)
    product_name = db.Column(db.String(150), nullable=False)
    size = db.Column(db.String(10), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    quantity = db.Column(db.Integer, default=1, nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)

    def __repr__(self):
        return f'<OrderItem {self.product_name} ({self.size}) x{self.quantity}>'


class Payment(db.Model):
    __tablename__ = 'payments'

    id = db.Column(db.Integer, primary_key=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False, unique=True)
    transaction_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    payment_method = db.Column(db.String(50), nullable=False) # 'Credit/Debit Card', 'UPI', 'PayPal', 'Cash on Delivery'
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    payment_status = db.Column(db.String(30), default='Completed', nullable=False) # 'Completed', 'Pending', 'Failed'
    payment_details = db.Column(db.Text, nullable=True)
    paid_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Payment {self.transaction_id} - {self.payment_status}>'


class Review(db.Model):
    __tablename__ = 'reviews'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', ondelete='CASCADE'), nullable=False)
    rating = db.Column(db.Integer, nullable=False) # 1 to 5
    comment = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<Review Product:{self.product_id} Rating:{self.rating}>'


class ContactMessage(db.Model):
    __tablename__ = 'contact_messages'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    subject = db.Column(db.String(150), nullable=True)
    message = db.Column(db.Text, nullable=False)
    is_read = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<ContactMessage {self.name} - {self.subject}>'
