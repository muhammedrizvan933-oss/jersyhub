import uuid
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, flash, redirect, url_for, session
from flask_login import current_user, login_required
from models import Product, ProductVariant, CartItem, Order, OrderItem, Payment
from extensions import db

checkout_bp = Blueprint('checkout', __name__, url_prefix='/checkout')

def generate_order_number():
    timestamp = datetime.utcnow().strftime('%y%m%d')
    random_suffix = uuid.uuid4().hex[:6].upper()
    return f"JH-{timestamp}-{random_suffix}"

def generate_transaction_id():
    return f"TXN-{uuid.uuid4().hex[:12].upper()}"

@checkout_bp.route('/', methods=['GET', 'POST'])
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(user_id=current_user.id).all()
    if not cart_items:
        flash('Your cart is empty. Please add items before checking out.', 'warning')
        return redirect(url_for('cart.view_cart'))

    # Calculate totals and verify stock
    items_to_order = []
    subtotal = 0.0
    stock_errors = []

    for ci in cart_items:
        if ci.quantity > ci.variant.stock_quantity:
            stock_errors.append(f"Only {ci.variant.stock_quantity} left for {ci.product.name} (Size: {ci.variant.size}).")
        price = float(ci.product.effective_price)
        line_total = price * ci.quantity
        subtotal += line_total
        items_to_order.append({
            'cart_item': ci,
            'price': price,
            'line_total': line_total
        })

    if stock_errors:
        for err in stock_errors:
            flash(err, 'danger')
        return redirect(url_for('cart.view_cart'))

    shipping_fee = 0.00 if subtotal >= 6000.0 else 299.00
    grand_total = subtotal + shipping_fee

    if request.method == 'POST':
        shipping_name = request.form.get('shipping_name', '').strip()
        shipping_phone = request.form.get('shipping_phone', '').strip()
        shipping_address = request.form.get('shipping_address', '').strip()
        shipping_city = request.form.get('shipping_city', '').strip()
        shipping_state = request.form.get('shipping_state', '').strip()
        shipping_postal_code = request.form.get('shipping_postal_code', '').strip()
        shipping_country = request.form.get('shipping_country', 'India').strip()
        notes = request.form.get('notes', '').strip()
        payment_method = request.form.get('payment_method', 'Credit/Debit Card')

        if not shipping_name or not shipping_phone or not shipping_address or not shipping_city or not shipping_postal_code:
            flash('Please fill in all required shipping fields.', 'danger')
            return render_template(
                'customer/checkout.html',
                items=items_to_order,
                subtotal=round(subtotal, 2),
                shipping_fee=round(shipping_fee, 2),
                grand_total=round(grand_total, 2)
            )

        # Re-verify stock inside transaction before creating order
        insufficient_items = []
        for item in items_to_order:
            ci = item['cart_item']
            v = db.session.get(ProductVariant, ci.variant_id)
            if not v or v.stock_quantity < ci.quantity:
                avail = v.stock_quantity if v else 0
                insufficient_items.append(f"Sorry, only {avail} left for {ci.product.name} (Size: {ci.variant.size if ci.variant else 'Selected'}).")

        if insufficient_items:
            db.session.rollback()
            for err in insufficient_items:
                flash(err, 'danger')
            return redirect(url_for('cart.view_cart'))

        # 1. Create Order
        order_number = generate_order_number()
        new_order = Order(
            order_number=order_number,
            user_id=current_user.id,
            subtotal=subtotal,
            shipping_fee=shipping_fee,
            total_amount=grand_total,
            status='Processing' if payment_method != 'Cash on Delivery' else 'Pending',
            shipping_name=shipping_name,
            shipping_phone=shipping_phone,
            shipping_address=shipping_address,
            shipping_city=shipping_city,
            shipping_state=shipping_state,
            shipping_postal_code=shipping_postal_code,
            shipping_country=shipping_country,
            notes=notes
        )
        db.session.add(new_order)
        db.session.flush() # get new_order.id

        # 2. Create Order Items & Decrement Inventory
        for item in items_to_order:
            ci = item['cart_item']
            v = db.session.get(ProductVariant, ci.variant_id)
            order_item = OrderItem(
                order_id=new_order.id,
                product_id=ci.product_id,
                variant_id=ci.variant_id,
                product_name=ci.product.name,
                size=v.size if v else ci.variant.size,
                price=item['price'],
                quantity=ci.quantity,
                total_price=item['line_total']
            )
            db.session.add(order_item)

            # Reduce stock in ProductVariant
            if v:
                v.stock_quantity = max(0, v.stock_quantity - ci.quantity)

        # 3. Process Simulated Payment
        payment_status = 'Pending' if payment_method == 'Cash on Delivery' else 'Completed'
        transaction_id = generate_transaction_id()
        
        payment_record = Payment(
            order_id=new_order.id,
            transaction_id=transaction_id,
            payment_method=payment_method,
            amount=grand_total,
            payment_status=payment_status,
            payment_details=f"Simulated {payment_method} transaction authorized successfully."
        )
        db.session.add(payment_record)

        # 4. Clear User Cart
        CartItem.query.filter_by(user_id=current_user.id).delete()

        # Commit everything as a single atomic transaction
        db.session.commit()

        flash('Your order has been placed successfully!', 'success')
        return redirect(url_for('checkout.confirmation', order_number=order_number))

    # Pre-populate shipping with user's saved profile data if available
    return render_template(
        'customer/checkout.html',
        items=items_to_order,
        subtotal=round(subtotal, 2),
        shipping_fee=round(shipping_fee, 2),
        grand_total=round(grand_total, 2)
    )

@checkout_bp.route('/confirmation/<order_number>')
@login_required
def confirmation(order_number):
    order = Order.query.filter_by(order_number=order_number, user_id=current_user.id).first_or_404()
    est_delivery = (order.created_at + timedelta(days=4)).strftime('%A, %B %d, %Y')
    return render_template('customer/order_confirmation.html', order=order, est_delivery=est_delivery)
