import os
from flask import Flask, render_template, session
from config import Config
from extensions import db, login_manager
from models import Category, CartItem

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Ensure upload directory exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Try connecting to MySQL; if unreachable and fallback allowed, fallback to SQLite
    active_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if 'mysql' in active_uri.lower():
        try:
            import pymysql
            # Attempt to connect to MySQL host to ensure DB exists
            conn = pymysql.connect(
                host=app.config.get('DB_HOST', 'localhost'),
                port=int(app.config.get('DB_PORT', 3306)),
                user=app.config.get('DB_USER', 'root'),
                password=app.config.get('DB_PASSWORD', ''),
                connect_timeout=3
            )
            with conn.cursor() as cursor:
                cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{app.config.get('DB_NAME', 'jerseyhub_db')}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            conn.close()
            print(f"[JerseyHub] Connected to MySQL successfully. Using database: {app.config.get('DB_NAME')}")
        except Exception as e:
            if app.config.get('USE_SQLITE_FALLBACK', True):
                print(f"[JerseyHub Warning] MySQL connection failed ({e}). Falling back to SQLite for seamless local execution.")
                app.config['SQLALCHEMY_DATABASE_URI'] = app.config['SQLITE_URI']
            else:
                print(f"[JerseyHub Error] MySQL connection failed: {e}")

    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)

    # Register Blueprints
    from routes.main import main_bp
    from routes.auth import auth_bp
    from routes.products import products_bp
    from routes.cart import cart_bp
    from routes.checkout import checkout_bp
    from routes.orders import orders_bp
    from routes.admin import admin_bp
    from routes.api import api_bp

    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)
    app.register_blueprint(products_bp)
    app.register_blueprint(cart_bp)
    app.register_blueprint(checkout_bp)
    app.register_blueprint(orders_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(api_bp)

    # Template Context Processors
    @app.context_processor
    def inject_globals():
        try:
            all_categories = Category.query.order_by(Category.display_order.asc()).all()
        except Exception:
            all_categories = []

        # Cart item count calculation
        cart_count = 0
        try:
            from flask_login import current_user
            if current_user.is_authenticated:
                cart_count = sum(item.quantity for item in current_user.cart_items.all())
            else:
                guest_cart = session.get('cart', {})
                cart_count = sum(guest_cart.values())
        except Exception:
            cart_count = 0

        return dict(
            navbar_categories=all_categories,
            global_cart_count=cart_count,
            current_year=2024
        )

    # Error Handlers
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('customer/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('customer/500.html'), 500

    # Auto create tables and seed if empty
    with app.app_context():
        try:
            db.create_all()
            from seed_data import seed_database_if_empty
            seed_database_if_empty()
        except Exception as e:
            if os.environ.get('APP_ENV') == 'production':
                raise
            print(f"[JerseyHub Database Setup Notice] {e}")

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
