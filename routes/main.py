from flask import Blueprint, render_template, request, flash, redirect, url_for
from models import Product, Category, Team, ContactMessage
from extensions import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    featured_jerseys = Product.query.filter_by(is_featured=True).limit(8).all()
    new_arrivals = Product.query.filter_by(is_new_arrival=True).order_by(Product.created_at.desc()).limit(8).all()
    best_sellers = Product.query.filter_by(is_bestseller=True).limit(8).all()
    
    # Popular Clubs & National Teams categories
    categories = Category.query.order_by(Category.display_order.asc()).all()
    popular_clubs = Team.query.filter(Team.category.has(Category.slug != 'national-teams')).limit(8).all()
    national_teams = Team.query.filter(Team.category.has(Category.slug == 'national-teams')).limit(8).all()
    
    # Special offer product (e.g. highest discount)
    special_offer = Product.query.filter(Product.discount_price.isnot(None), Product.discount_price > 0).first()

    return render_template(
        'customer/home.html',
        featured_jerseys=featured_jerseys,
        new_arrivals=new_arrivals,
        best_sellers=best_sellers,
        categories=categories,
        popular_clubs=popular_clubs,
        national_teams=national_teams,
        special_offer=special_offer
    )

@main_bp.route('/about')
def about():
    total_jerseys = Product.query.count()
    total_teams = Team.query.count()
    return render_template('customer/about.html', total_jerseys=total_jerseys, total_teams=total_teams)

@main_bp.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        email = request.form.get('email', '').strip()
        subject = request.form.get('subject', '').strip()
        message = request.form.get('message', '').strip()

        if not name or not email or not message:
            flash('Please fill in all required fields.', 'danger')
            return redirect(url_for('main.contact'))

        new_message = ContactMessage(
            name=name,
            email=email,
            subject=subject,
            message=message
        )
        db.session.add(new_message)
        db.session.commit()

        flash('Thank you! Your message has been sent successfully. We will get back to you shortly.', 'success')
        return redirect(url_for('main.contact'))

    return render_template('customer/contact.html')
