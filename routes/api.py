from functools import wraps
from flask import Blueprint, jsonify, request, session
from flask_login import current_user
from models import Product, Category, Team, CartItem, Order
from extensions import db
from sqlalchemy import func
from datetime import datetime

api_bp = Blueprint('api', __name__, url_prefix='/api')

def admin_api_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin:
            return jsonify({'error': 'Unauthorized. Administrator access required.'}), 403
        return f(*args, **kwargs)
    return decorated_function

@api_bp.route('/cart/count')
def cart_count():
    if current_user.is_authenticated:
        count = sum(item.quantity for item in current_user.cart_items.all())
    else:
        guest_cart = session.get('cart', {})
        count = sum(guest_cart.values())
    return jsonify({'count': count})

@api_bp.route('/search/autocomplete')
def search_autocomplete():
    q = request.args.get('q', '').strip()
    if not q or len(q) < 2:
        return jsonify([])

    results = Product.query.filter(Product.name.ilike(f'%{q}%')).limit(6).all()
    data = [{
        'id': p.id,
        'name': p.name,
        'slug': p.slug,
        'price': float(p.effective_price),
        'image': p.primary_image,
        'team': p.team.name if p.team else ''
    } for p in results]

    return jsonify(data)

@api_bp.route('/admin/sales-chart')
@admin_api_required
def admin_sales_chart():
    # Return last 6 months or 7 days labels & values
    # Group orders by date
    orders = db.session.query(
        func.date(Order.created_at).label('order_date'),
        func.sum(Order.total_amount).label('daily_revenue'),
        func.count(Order.id).label('daily_orders')
    ).filter(Order.status != 'Cancelled')\
     .group_by(func.date(Order.created_at))\
     .order_by(func.date(Order.created_at).desc())\
     .limit(14).all()

    orders.reverse() # chronological

    labels = [str(o.order_date) for o in orders]
    revenue = [float(o.daily_revenue) for o in orders]
    order_counts = [int(o.daily_orders) for o in orders]

    return jsonify({
        'labels': labels,
        'revenue': revenue,
        'orders': order_counts
    })
