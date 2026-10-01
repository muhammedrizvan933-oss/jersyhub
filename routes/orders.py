from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from models import Order, OrderItem, ProductVariant
from extensions import db

orders_bp = Blueprint('orders', __name__, url_prefix='/orders')

@orders_bp.route('/')
@login_required
def my_orders():
    user_orders = Order.query.filter_by(user_id=current_user.id).order_by(Order.created_at.desc()).all()
    return render_template('customer/orders.html', orders=user_orders)

@orders_bp.route('/<order_number>')
@login_required
def detail(order_number):
    order = Order.query.filter_by(order_number=order_number, user_id=current_user.id).first_or_404()
    
    # Tracking step index
    status_steps = {
        'Pending': 1,
        'Processing': 2,
        'Shipped': 3,
        'Delivered': 4,
        'Cancelled': 0
    }
    current_step = status_steps.get(order.status, 1)

    return render_template('customer/order_detail.html', order=order, current_step=current_step)

@orders_bp.route('/<order_number>/cancel', methods=['POST'])
@login_required
def cancel_order(order_number):
    order = Order.query.filter_by(order_number=order_number, user_id=current_user.id).first_or_404()
    
    if order.status not in ['Pending', 'Processing']:
        flash(f'Cannot cancel order with status "{order.status}". Please contact support.', 'danger')
        return redirect(url_for('orders.detail', order_number=order_number))

    # Restore inventory
    for item in order.items:
        if item.variant_id:
            variant = db.session.get(ProductVariant, item.variant_id)
            if variant:
                variant.stock_quantity += item.quantity

    order.status = 'Cancelled'
    if order.payment:
        order.payment.payment_status = 'Refunded' if order.payment.payment_status == 'Completed' else 'Cancelled'

    db.session.commit()
    flash(f'Order {order.order_number} has been cancelled successfully. Any inventory held has been restored.', 'info')
    return redirect(url_for('orders.detail', order_number=order_number))
