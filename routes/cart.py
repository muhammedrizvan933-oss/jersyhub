from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, session
from flask_login import current_user, login_required
from models import Product, ProductVariant, CartItem
from extensions import db

cart_bp = Blueprint('cart', __name__, url_prefix='/cart')

def get_guest_cart():
    if 'cart' not in session:
        session['cart'] = {}
    return session['cart']

def merge_guest_cart_to_db(user):
    """
    Transfers all items from the guest session cart into the authenticated user's database cart.
    Validates product and variant existence, caps quantity at available stock,
    and clears the guest session cart.
    """
    guest_cart = session.get('cart', {})
    if not guest_cart:
        return

    for variant_id_str, qty in list(guest_cart.items()):
        try:
            var_id = int(variant_id_str)
            qty = int(qty)
            if qty <= 0:
                continue
            variant = db.session.get(ProductVariant, var_id)
            if not variant or variant.stock_quantity <= 0 or not variant.product:
                continue

            existing_item = CartItem.query.filter_by(
                user_id=user.id,
                variant_id=variant.id
            ).first()

            if existing_item:
                new_qty = min(existing_item.quantity + qty, variant.stock_quantity)
                existing_item.quantity = new_qty
            else:
                final_qty = min(qty, variant.stock_quantity)
                new_item = CartItem(
                    user_id=user.id,
                    product_id=variant.product_id,
                    variant_id=variant.id,
                    quantity=final_qty
                )
                db.session.add(new_item)
        except (ValueError, TypeError):
            continue

    db.session.commit()
    session.pop('cart', None)
    session.modified = True

@cart_bp.route('/')
def view_cart():
    items_data = []
    subtotal = 0.0

    if current_user.is_authenticated:
        db_items = CartItem.query.filter_by(user_id=current_user.id).all()
        for item in db_items:
            # Validate variant still exists
            variant = item.variant
            prod = item.product
            if variant and prod:
                price = prod.effective_price
                line_total = price * item.quantity
                subtotal += line_total
                items_data.append({
                    'id': item.id,
                    'product': prod,
                    'variant': variant,
                    'size': variant.size,
                    'quantity': item.quantity,
                    'price': price,
                    'line_total': line_total,
                    'max_stock': variant.stock_quantity
                })
    else:
        guest_cart = get_guest_cart()
        for variant_id_str, qty in guest_cart.items():
            try:
                var_id = int(variant_id_str)
                variant = db.session.get(ProductVariant, var_id)
                if variant and variant.product:
                    prod = variant.product
                    price = prod.effective_price
                    line_total = price * qty
                    subtotal += line_total
                    items_data.append({
                        'id': var_id,
                        'product': prod,
                        'variant': variant,
                        'size': variant.size,
                        'quantity': qty,
                        'price': price,
                        'line_total': line_total,
                        'max_stock': variant.stock_quantity
                    })
            except (ValueError, TypeError):
                continue

    # Free shipping on orders over ₹6,000, otherwise ₹299
    shipping_fee = 0.00 if subtotal >= 6000.0 or subtotal == 0.0 else 299.00
    grand_total = subtotal + shipping_fee

    return render_template(
        'customer/cart.html',
        items=items_data,
        subtotal=round(subtotal, 2),
        shipping_fee=round(shipping_fee, 2),
        grand_total=round(grand_total, 2)
    )

@cart_bp.route('/add', methods=['POST'])
def add_to_cart():
    product_id = request.form.get('product_id', type=int)
    variant_id = request.form.get('variant_id', type=int)
    quantity = request.form.get('quantity', 1, type=int)

    if quantity < 1:
        quantity = 1

    if not product_id or not variant_id:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Please select a size first.'}), 400
        flash('Please select a size before adding to cart.', 'warning')
        return redirect(request.referrer or url_for('products.list_products'))

    variant = ProductVariant.query.filter_by(id=variant_id, product_id=product_id).first()
    if not variant:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': 'Selected size is invalid.'}), 400
        flash('Selected size is invalid.', 'danger')
        return redirect(request.referrer or url_for('products.list_products'))

    if variant.stock_quantity <= 0:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({'success': False, 'message': f'Size {variant.size} is currently out of stock.'}), 400
        flash(f'Size {variant.size} is currently out of stock.', 'danger')
        return redirect(request.referrer or url_for('products.list_products'))

    if current_user.is_authenticated:
        cart_item = CartItem.query.filter_by(
            user_id=current_user.id,
            product_id=product_id,
            variant_id=variant_id
        ).first()

        if cart_item:
            new_qty = cart_item.quantity + quantity
            if new_qty > variant.stock_quantity:
                cart_item.quantity = variant.stock_quantity
                flash(f'Updated to maximum available stock ({variant.stock_quantity}).', 'info')
            else:
                cart_item.quantity = new_qty
        else:
            final_qty = min(quantity, variant.stock_quantity)
            cart_item = CartItem(
                user_id=current_user.id,
                product_id=product_id,
                variant_id=variant_id,
                quantity=final_qty
            )
            db.session.add(cart_item)

        db.session.commit()
        cart_count = sum(ci.quantity for ci in current_user.cart_items.all())
    else:
        guest_cart = get_guest_cart()
        curr_qty = guest_cart.get(str(variant_id), 0)
        new_qty = min(curr_qty + quantity, variant.stock_quantity)
        guest_cart[str(variant_id)] = new_qty
        session['cart'] = guest_cart
        session.modified = True
        cart_count = sum(guest_cart.values())

    msg = f'Added {variant.product.name} (Size: {variant.size}) to your cart!'
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return jsonify({'success': True, 'message': msg, 'cart_count': cart_count})

    flash(msg, 'success')
    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/update/<int:item_id>', methods=['POST'])
def update_cart(item_id):
    action = request.form.get('action') # 'increase', 'decrease', or 'set'
    qty_val = request.form.get('quantity', type=int)

    if current_user.is_authenticated:
        cart_item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first()
        if not cart_item:
            return redirect(url_for('cart.view_cart'))

        max_stock = cart_item.variant.stock_quantity

        if action == 'increase':
            if cart_item.quantity < max_stock:
                cart_item.quantity += 1
            else:
                flash(f'Only {max_stock} items available in stock.', 'warning')
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
            else:
                db.session.delete(cart_item)
        elif action == 'set' and qty_val is not None:
            if qty_val <= 0:
                db.session.delete(cart_item)
            else:
                cart_item.quantity = min(qty_val, max_stock)

        db.session.commit()
    else:
        guest_cart = get_guest_cart()
        var_key = str(item_id)
        if var_key in guest_cart:
            variant = db.session.get(ProductVariant, item_id)
            max_stock = variant.stock_quantity if variant else 99

            if action == 'increase':
                if guest_cart[var_key] < max_stock:
                    guest_cart[var_key] += 1
                else:
                    flash(f'Only {max_stock} items available in stock.', 'warning')
            elif action == 'decrease':
                if guest_cart[var_key] > 1:
                    guest_cart[var_key] -= 1
                else:
                    del guest_cart[var_key]
            elif action == 'set' and qty_val is not None:
                if qty_val <= 0:
                    del guest_cart[var_key]
                else:
                    guest_cart[var_key] = min(qty_val, max_stock)

            session['cart'] = guest_cart
            session.modified = True

    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/remove/<int:item_id>', methods=['POST', 'GET'])
def remove_from_cart(item_id):
    if current_user.is_authenticated:
        cart_item = CartItem.query.filter_by(id=item_id, user_id=current_user.id).first()
        if cart_item:
            product_name = cart_item.product.name
            db.session.delete(cart_item)
            db.session.commit()
            flash(f'Removed {product_name} from your cart.', 'info')
    else:
        guest_cart = get_guest_cart()
        var_key = str(item_id)
        if var_key in guest_cart:
            del guest_cart[var_key]
            session['cart'] = guest_cart
            session.modified = True
            flash('Removed item from your cart.', 'info')

    return redirect(url_for('cart.view_cart'))

@cart_bp.route('/clear', methods=['POST'])
def clear_cart():
    if current_user.is_authenticated:
        CartItem.query.filter_by(user_id=current_user.id).delete()
        db.session.commit()
    else:
        session['cart'] = {}
        session.modified = True

    flash('Your cart has been cleared.', 'info')
    return redirect(url_for('cart.view_cart'))
