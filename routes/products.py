from flask import Blueprint, render_template, request, flash, redirect, url_for, abort
from flask_login import login_required, current_user
from models import Product, Category, Team, ProductVariant, Review
from extensions import db
from sqlalchemy import or_

products_bp = Blueprint('products', __name__, url_prefix='/products')

@products_bp.route('/')
def list_products():
    page = request.args.get('page', 1, type=int)
    search_query = request.args.get('q', '').strip()
    category_slug = request.args.get('category', '').strip()
    team_slug = request.args.get('team', '').strip()
    kit_type = request.args.get('kit_type', '').strip()
    gender = request.args.get('gender', '').strip()
    size = request.args.get('size', '').strip().upper()
    min_price = request.args.get('min_price', type=float)
    max_price = request.args.get('max_price', type=float)
    sort_by = request.args.get('sort', 'featured')

    query = Product.query

    # Search keyword
    if search_query:
        search_filter = or_(
            Product.name.ilike(f'%{search_query}%'),
            Product.description.ilike(f'%{search_query}%'),
            Product.team.has(Team.name.ilike(f'%{search_query}%')),
            Product.category.has(Category.name.ilike(f'%{search_query}%'))
        )
        query = query.filter(search_filter)

    # Category filter
    if category_slug:
        query = query.filter(Product.category.has(Category.slug == category_slug))

    # Team filter
    if team_slug:
        query = query.filter(Product.team.has(Team.slug == team_slug))

    # Kit Type filter
    if kit_type:
        query = query.filter(Product.kit_type.ilike(kit_type))

    # Gender filter
    if gender:
        query = query.filter(Product.gender.ilike(gender))

    # Size filter
    if size:
        query = query.filter(Product.variants.any((ProductVariant.size == size) & (ProductVariant.stock_quantity > 0)))

    # Price range filter
    if min_price is not None:
        query = query.filter(Product.price >= min_price)
    if max_price is not None:
        query = query.filter(Product.price <= max_price)

    # Sorting
    if sort_by == 'price_asc':
        query = query.order_by(Product.price.asc())
    elif sort_by == 'price_desc':
        query = query.order_by(Product.price.desc())
    elif sort_by == 'newest':
        query = query.order_by(Product.created_at.desc())
    elif sort_by == 'popular':
        query = query.order_by(Product.is_bestseller.desc(), Product.is_featured.desc())
    else: # 'featured' default
        query = query.order_by(Product.is_featured.desc(), Product.created_at.desc())

    # Pagination: 12 per page
    pagination = query.paginate(page=page, per_page=12, error_out=False)
    products = pagination.items

    # Filter sidebar data
    all_categories = Category.query.order_by(Category.name.asc()).all()
    all_teams = Team.query.order_by(Team.name.asc()).all()
    available_sizes = ['S', 'M', 'L', 'XL', 'XXL']
    available_kit_types = ['Home', 'Away', 'Third', 'Retro', 'Special Edition']

    # Selected category or team object for page header info
    selected_category = Category.query.filter_by(slug=category_slug).first() if category_slug else None
    selected_team = Team.query.filter_by(slug=team_slug).first() if team_slug else None

    return render_template(
        'customer/products.html',
        products=products,
        pagination=pagination,
        categories=all_categories,
        teams=all_teams,
        available_sizes=available_sizes,
        available_kit_types=available_kit_types,
        search_query=search_query,
        category_slug=category_slug,
        team_slug=team_slug,
        kit_type=kit_type,
        gender=gender,
        size=size,
        min_price=min_price,
        max_price=max_price,
        sort_by=sort_by,
        selected_category=selected_category,
        selected_team=selected_team
    )

@products_bp.route('/<slug>')
def detail(slug):
    product = Product.query.filter_by(slug=slug).first_or_404()
    variants = product.variants.order_by(
        db.case(
            (ProductVariant.size == 'S', 1),
            (ProductVariant.size == 'M', 2),
            (ProductVariant.size == 'L', 3),
            (ProductVariant.size == 'XL', 4),
            (ProductVariant.size == 'XXL', 5),
            else_=6
        )
    ).all()

    # Related products from same team or same category
    related_products = Product.query.filter(
        Product.id != product.id,
        or_(Product.team_id == product.team_id, Product.category_id == product.category_id)
    ).limit(4).all()

    # User review eligibility
    has_reviewed = False
    if current_user.is_authenticated:
        has_reviewed = Review.query.filter_by(user_id=current_user.id, product_id=product.id).first() is not None

    return render_template(
        'customer/product_detail.html',
        product=product,
        variants=variants,
        related_products=related_products,
        has_reviewed=has_reviewed
    )

@products_bp.route('/<slug>/review', methods=['POST'])
@login_required
def add_review(slug):
    product = Product.query.filter_by(slug=slug).first_or_404()

    existing_review = Review.query.filter_by(user_id=current_user.id, product_id=product.id).first()
    if existing_review:
        flash('You have already submitted a review for this jersey.', 'warning')
        return redirect(url_for('products.detail', slug=slug))

    try:
        rating = int(request.form.get('rating', 5))
        if rating < 1 or rating > 5:
            rating = 5
    except ValueError:
        rating = 5

    comment = request.form.get('comment', '').strip()

    review = Review(
        user_id=current_user.id,
        product_id=product.id,
        rating=rating,
        comment=comment
    )
    db.session.add(review)
    db.session.commit()

    flash('Thank you! Your review has been published.', 'success')
    return redirect(url_for('products.detail', slug=slug))
