import unittest
import os
import secrets
from app import create_app
from config import Config
from extensions import db
from models import User, Product, Category, Order

class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class JerseyHubTestSuite(unittest.TestCase):
    def setUp(self):
        self.admin_password = secrets.token_urlsafe(32)
        self.customer_password = secrets.token_urlsafe(32)
        os.environ['INITIAL_ADMIN_PASSWORD'] = self.admin_password
        self.app = create_app(TestConfig)
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        with self.app.app_context():
            customer = User.query.filter_by(username='john_doe').first()
            customer.set_password(self.customer_password)
            db.session.commit()
        self.client = self.app.test_client()

    def test_01_home_page(self):
        res = self.client.get('/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'JerseyHub', res.data)
        self.assertIn(b'Popular Football Clubs', res.data)
        self.assertIn(b'Featured Jerseys', res.data)
        self.assertIn(b'/static/images/messi-barcelona.jpg', res.data)
        self.assertIn('₹'.encode('utf-8'), res.data)

    def test_02_about_and_contact(self):
        res1 = self.client.get('/about')
        self.assertEqual(res1.status_code, 200)
        self.assertIn(b'Authentic Passion', res1.data)

        res2 = self.client.get('/contact')
        self.assertEqual(res2.status_code, 200)
        self.assertIn(b'Send Us a Message', res2.data)

        # POST contact message
        res3 = self.client.post('/contact', data={
            'name': 'Test Fan',
            'email': 'fan@test.com',
            'subject': 'Sizing Query',
            'message': 'Do you ship to California?'
        }, follow_redirects=True)
        self.assertEqual(res3.status_code, 200)
        self.assertIn(b'Your message has been sent successfully', res3.data)

    def test_03_products_catalog_and_filter(self):
        res = self.client.get('/products/')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Jerseys', res.data)

        # Filter by category
        res2 = self.client.get('/products/?category=la-liga')
        self.assertEqual(res2.status_code, 200)

        # Filter by team
        res3 = self.client.get('/products/?team=real-madrid')
        self.assertEqual(res3.status_code, 200)

        # Search query
        res4 = self.client.get('/products/?q=Madrid')
        self.assertEqual(res4.status_code, 200)
        self.assertIn(b'Real Madrid', res4.data)

    def test_04_product_detail(self):
        res = self.client.get('/products/real-madrid-2024-25-home-jersey')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Real Madrid 2024/25 Home Jersey', res.data)
        self.assertIn(b'Select Adult Size', res.data)
        self.assertIn(b'id="share-product-btn"', res.data)

        barcelona_res = self.client.get('/products/fc-barcelona-125th-anniversary-home-jersey')
        self.assertEqual(barcelona_res.status_code, 200)
        self.assertIn(b'FC Barcelona 125th Anniversary 2024/25 Home Jersey', barcelona_res.data)
        self.assertIn(b'id="main-product-img"', barcelona_res.data)

    def test_05_cart_and_guest_actions(self):
        # View empty cart
        res = self.client.get('/cart/')
        self.assertEqual(res.status_code, 200)

        # Fetch product and variant
        with self.app.app_context():
            prod = Product.query.filter_by(slug='real-madrid-2024-25-home-jersey').first()
            var = prod.variants.filter_by(size='M').first()
            prod_id = prod.id
            var_id = var.id

        # Add to cart
        res2 = self.client.post('/cart/add', data={
            'product_id': prod_id,
            'variant_id': var_id,
            'quantity': 2
        }, follow_redirects=True)
        self.assertEqual(res2.status_code, 200)
        self.assertIn(b'Real Madrid', res2.data)

    def test_06_customer_auth_and_checkout(self):
        # Login customer
        res = self.client.post('/login', data={
            'identifier': 'john_doe',
            'password': self.customer_password
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Welcome back', res.data)

        # View profile
        res_prof = self.client.get('/profile')
        self.assertEqual(res_prof.status_code, 200)
        self.assertIn(b'My Profile', res_prof.data)

        # Add item to user cart
        with self.app.app_context():
            prod = Product.query.first()
            var = prod.variants.first()
            prod_id = prod.id
            var_id = var.id

        self.client.post('/cart/add', data={
            'product_id': prod_id,
            'variant_id': var_id,
            'quantity': 1
        }, follow_redirects=True)

        # Checkout GET
        res_chk = self.client.get('/checkout/')
        self.assertEqual(res_chk.status_code, 200)
        self.assertIn(b'Secure Checkout', res_chk.data)

        # Checkout POST (Simulated Payment)
        res_order = self.client.post('/checkout/', data={
            'shipping_name': 'John Doe',
            'shipping_phone': '+1 555-234-5678',
            'shipping_address': '742 Evergreen Terrace',
            'shipping_city': 'Springfield',
            'shipping_state': 'IL',
            'shipping_postal_code': '62704',
            'shipping_country': 'India',
            'payment_method': 'Credit/Debit Card'
        }, follow_redirects=True)
        self.assertEqual(res_order.status_code, 200)
        self.assertIn(b'ORDER CONFIRMED', res_order.data)

        # View my orders
        res_orders = self.client.get('/orders/')
        self.assertEqual(res_orders.status_code, 200)
        self.assertIn(b'My Orders', res_orders.data)

    def test_07_admin_panel(self):
        admin_login = self.client.get('/admin/login')
        self.assertNotIn(b'admin123', admin_login.data)

        customer_login = self.client.get('/login')
        self.assertNotIn(b'admin123', customer_login.data)

        # Admin login
        res = self.client.post('/admin/login', data={
            'identifier': 'admin',
            'password': self.admin_password
        }, follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Dashboard & Analytics', res.data)
        self.assertIn('no-store', res.headers['Cache-Control'])
        with self.app.app_context():
            latest_order = Order.query.order_by(Order.created_at.desc()).first()
            if latest_order:
                order_date = latest_order.created_at.strftime('%b %d, %Y').encode()
                self.assertIn(order_date, res.data)

        # Admin Products
        res_prod = self.client.get('/admin/products')
        self.assertEqual(res_prod.status_code, 200)
        self.assertIn(b'Jersey Products Catalog', res_prod.data)

        # Admin Categories
        res_cat = self.client.get('/admin/categories')
        self.assertEqual(res_cat.status_code, 200)
        self.assertIn(b'Leagues & Clubs Management', res_cat.data)

        # Admin Inventory
        res_inv = self.client.get('/admin/inventory')
        self.assertEqual(res_inv.status_code, 200)
        self.assertIn(b'Inventory & Size Stock Management', res_inv.data)

        # Admin Orders
        res_ord = self.client.get('/admin/orders')
        self.assertEqual(res_ord.status_code, 200)
        self.assertIn(b'Customer Orders Management', res_ord.data)

        # Admin Customers
        res_cust = self.client.get('/admin/customers')
        self.assertEqual(res_cust.status_code, 200)
        self.assertIn(b'Customer Accounts Management', res_cust.data)
        with self.app.app_context():
            customer_id = User.query.filter_by(username='john_doe').first().id
        self.assertIn(f'/admin/customers/{customer_id}'.encode(), res_cust.data)
        customer_detail = self.client.get(f'/admin/customers/{customer_id}')
        self.assertEqual(customer_detail.status_code, 200)
        self.assertIn(b'john@example.com', customer_detail.data)
        self.assertIn(b'+91 99887 76654', customer_detail.data)
        self.assertIn(b'Order History', customer_detail.data)

        # Admin Payments
        res_pay = self.client.get('/admin/payments')
        self.assertEqual(res_pay.status_code, 200)
        self.assertIn(b'Payment Transactions Management', res_pay.data)

        # Admin Sales
        res_sale = self.client.get('/admin/sales')
        self.assertEqual(res_sale.status_code, 200)
        self.assertIn(b'Sales & Revenue Reports', res_sale.data)

        # Admin Messages
        res_msg = self.client.get('/admin/messages')
        self.assertEqual(res_msg.status_code, 200)
        self.assertIn(b'Support Inquiries', res_msg.data)

        logout_response = self.client.get('/admin/logout')
        self.assertEqual(logout_response.status_code, 302)
        self.assertEqual(logout_response.headers['Location'], '/')

        dashboard_response = self.client.get('/admin/dashboard')
        self.assertEqual(dashboard_response.status_code, 302)
        self.assertTrue(dashboard_response.headers['Location'].startswith('/admin/login?next='))

    def test_08_api_endpoints(self):
        # Cart count API
        res1 = self.client.get('/api/cart/count')
        self.assertEqual(res1.status_code, 200)
        self.assertIn('count', res1.get_json())

        # Autocomplete API
        res2 = self.client.get('/api/search/autocomplete?q=barca')
        self.assertEqual(res2.status_code, 200)
        self.assertIsInstance(res2.get_json(), list)

        # Sales chart API - unauthorized request returns 403
        res3 = self.client.get('/api/admin/sales-chart')
        self.assertEqual(res3.status_code, 403)
        self.assertEqual(res3.get_json(), {'error': 'Unauthorized. Administrator access required.'})

        # Sales chart API - admin authorized request returns 200
        self.client.post('/admin/login', data={
            'identifier': 'admin',
            'password': self.admin_password
        })
        res3_auth = self.client.get('/api/admin/sales-chart')
        self.assertEqual(res3_auth.status_code, 200)
        self.assertIn('revenue', res3_auth.get_json())

    def test_09_guest_cart_merge(self):
        # 1. Guest adds a product variant to cart
        with self.app.app_context():
            product = Product.query.first()
            variant = product.variants[0]
            product_id = product.id
            variant_id = variant.id

        # Guest adds 2 items to session cart
        res_add = self.client.post('/cart/add', data={
            'product_id': str(product_id),
            'variant_id': str(variant_id),
            'quantity': '2'
        }, follow_redirects=True)
        self.assertEqual(res_add.status_code, 200)

        # Check cart count API reflects 2 items in session
        res_count = self.client.get('/api/cart/count')
        self.assertEqual(res_count.get_json()['count'], 2)

        # 2. Guest registers a new account
        res_reg = self.client.post('/register', data={
            'username': 'cart_test_user',
            'email': 'cart_test@example.com',
            'password': 'password123',
            'confirm_password': 'password123',
            'full_name': 'Cart Tester'
        }, follow_redirects=True)
        self.assertEqual(res_reg.status_code, 200)

        # 3. Verify the item was merged from session into the user's DB cart
        with self.app.app_context():
            from models import CartItem
            user = User.query.filter_by(username='cart_test_user').first()
            self.assertIsNotNone(user)
            cart_item = CartItem.query.filter_by(user_id=user.id, variant_id=variant_id).first()
            self.assertIsNotNone(cart_item)
            self.assertEqual(cart_item.quantity, 2)

        # 4. Verify session cart was cleared after merge
        with self.client.session_transaction() as sess:
            self.assertNotIn('cart', sess)

if __name__ == '__main__':
    unittest.main()
