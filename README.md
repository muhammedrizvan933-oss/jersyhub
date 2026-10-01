# ⚽ JerseyHub - Football Jersey E-Commerce Web Application
> **College DBMS Mini / Major Project**  
> Built with **Flask (Python 3)**, **MySQL / Flask-SQLAlchemy**, **Bootstrap 5**, and modern **JavaScript**.

---

## 📌 Project Overview
**JerseyHub** is a complete, fully functional full-stack e-commerce web platform specialized in official football kits and jerseys from world-class clubs (Real Madrid, Barcelona, Arsenal, Man City, Liverpool, Man United, Bayern Munich, PSG, AC Milan, etc.), national teams (Argentina, Brazil, France, Portugal, Spain, England), and iconic retro classics.

This project is tailored specifically for **DBMS (Database Management Systems) evaluation**, demonstrating normalized relational schema design, primary & foreign key constraints, cascading actions, transaction integrity, indexing, SQL views, and secure role-based access control.

---

## 🛠️ Tech Stack

### Frontend
- **HTML5 & CSS3**: Modern football-themed visual design with responsive layouts.
- **JavaScript (ES6+)**: Real-time autocomplete search, size variant selectors, dynamic asynchronous cart updates, toast notifications.
- **Bootstrap 5 & Bootstrap Icons**: Mobile-responsive UI components, cards, tables, modal dialogs.
- **Chart.js**: Interactive real-time sales dynamics chart on the administrator dashboard.

### Backend
- **Python 3.11**
- **Flask 3.x**: Modular architecture structured with blueprints (`main`, `auth`, `products`, `cart`, `checkout`, `orders`, `admin`, `api`).
- **Flask-SQLAlchemy**: Object-Relational Mapping (ORM) connecting directly to MySQL.
- **Flask-Login**: Session authentication and role authorization (`current_user.is_admin`).
- **Werkzeug**: Cryptographic password hashing (`generate_password_hash`, `check_password_hash`).

### Database
- **MySQL 8.0+ / MariaDB**: Fully normalized relational schema with foreign key constraints and database views.
- **Zero-Friction Fallback**: Automatically creates `jerseyhub_db` on MySQL, or seamlessly switches to local SQLite if MySQL service is not yet started, guaranteeing uninterrupted demonstration.
- **`schema.sql`**: Provided for direct import into MySQL Workbench / phpMyAdmin.

---

## 🗄️ Database Architecture (DBMS Highlights)

### Entity-Relationship Schema
1. **`users`**: Customer and administrator profiles, credentials, contact information, and shipping addresses.
2. **`categories`**: Leagues and tournament divisions (Premier League, La Liga, Serie A, Bundesliga, Ligue 1, National Teams, Retro Classics).
3. **`teams`**: Club and nation entities linked to leagues (`ON DELETE CASCADE`).
4. **`products`**: Official football jerseys with pricing, discount prices, kit types, seasons, and high-res imagery.
5. **`product_variants`**: Size-level inventory control (**S, M, L, XL, XXL**) with SKUs and stock tracking.
6. **`cart_items`**: User cart persistence linked to specific size variants.
7. **`orders`**: Order records with order numbers (`JH-YYMMDD-XXXXXX`), billing totals, shipment tracking statuses (`Pending`, `Processing`, `Shipped`, `Delivered`, `Cancelled`).
8. **`order_items`**: Itemized lines preserving purchase prices, sizes, and quantities.
9. **`payments`**: Payment transaction logs, simulated transaction IDs (`TXN-XXXXXXXXXXXX`), payment methods (Card, UPI, PayPal, COD), and authorization statuses.
10. **`reviews`**: 1-to-5 star supporter ratings and commentary linked to products.
11. **`contact_messages`**: Supporter inquiry logs received from the contact form.

### DBMS Views (in `schema.sql`)
- **`view_low_stock`**: Automatically aggregates products and sizes with 5 or fewer items remaining.
- **`view_sales_summary`**: Aggregates units sold and revenue per jersey for reporting.

---

## 📂 Project Directory Structure

```text
c:\Users\RISWAN\Downloads\project\
│
├── app.py                     # Flask application factory, DB setup, error handlers
├── config.py                  # Environment config loader (.env)
├── models.py                  # SQLAlchemy relational models (DBMS tables)
├── extensions.py              # db and LoginManager instances
├── schema.sql                 # Pure MySQL DDL schema script for DBMS submission
├── seed_data.py               # Pre-populates 24 official jerseys, teams, reviews, orders
├── requirements.txt           # Python dependencies
├── test_routes.py             # Automated unit/integration test suite
├── .env                       # Active environment configuration
├── .env.example               # Template environment configuration
│
├── routes/
│   ├── main.py                # Home, About, Contact
│   ├── auth.py                # Register, Login, Logout, Profile
│   ├── products.py            # Catalog, Search, Filters, Product Details, Reviews
│   ├── cart.py                # Cart view, add, update, delete
│   ├── checkout.py            # Checkout, simulated payment, atomic order creation
│   ├── orders.py              # My Orders, shipment tracking timeline, cancellation
│   ├── admin.py               # Complete admin dashboard, CRUD, stock, payments, sales
│   └── api.py                 # REST API endpoints (autocomplete, cart count, chart)
│
├── static/
│   ├── css/
│   │   ├── style.css          # Dark football stadium styling, jersey cards, badges
│   │   └── admin.css          # Admin sidebar, stat cards, tables, pills
│   └── js/
│       ├── main.js            # Size picker, AJAX cart, autocomplete, toasts
│       └── admin.js           # Chart.js integration, inline stock updater
│
└── templates/
    ├── base.html              # Customer master layout (Navbar, mega menu, footer)
    ├── customer/
    │   ├── home.html          # Hero, featured, popular clubs, national teams, best sellers
    │   ├── products.html      # Filterable catalog (league, team, size, price range)
    │   ├── product_detail.html# Image gallery, size selector, specs, customer reviews
    │   ├── cart.html          # Responsive shopping cart with live quantity updater
    │   ├── checkout.html      # Address collection, simulated payment gateway
    │   ├── order_confirmation.html # Order receipt & tracking link
    │   ├── orders.html        # Customer "My Orders" history
    │   ├── order_detail.html  # Live 4-stage tracking timeline & itemized receipt
    │   ├── profile.html       # Profile details & password updater
    │   ├── about.html         # Brand story, authenticity standards, stats
    │   ├── contact.html       # Contact form, HQ details, FAQ accordion
    │   ├── 404.html & 500.html# Custom error pages
    ├── auth/
    │   ├── login.html         # Customer login page
    │   └── register.html      # Registration page
    └── admin/
        ├── base.html          # Admin sidebar master layout
        ├── login.html         # Admin login portal
        ├── dashboard.html     # Stats, Chart.js graph, low stock alerts, recent orders
        ├── products.html      # Product list with search and action buttons
        ├── product_form.html  # Add/Edit product with size variant inventory inputs
        ├── categories.html    # League and club management
        ├── inventory.html     # Dedicated per-size stock manager with inline updates
        ├── orders.html        # Customer orders list with inline status updater
        ├── order_detail.html  # Admin order detail & shipment manager
        ├── customers.html     # Customer accounts table & status toggles
        ├── payments.html      # Transaction logs & revenue collected
        ├── sales.html         # Sales breakdown by league, bestsellers, payment methods
        └── messages.html      # Customer support messages inbox
```

---

## 🚀 Quickstart Guide

### 1. Prerequisites
- **Python 3.10+** (Python 3.11 is configured)
- **MySQL / XAMPP / WampServer** (Optional: SQLite auto-fallback enabled by default)

### 2. Activate Virtual Environment
Open PowerShell in the project directory:
```powershell
.\venv\Scripts\activate
```

### 3. Database Setup (MySQL)
To run with MySQL:
1. Start your local MySQL service (e.g. via XAMPP Control Panel or MySQL service).
2. Configure `.env` if your MySQL root has a password:
   ```env
    INITIAL_ADMIN_PASSWORD=choose_a_strong_unique_password
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=root
   DB_PASSWORD=your_password_here
   DB_NAME=jerseyhub_db
   USE_SQLITE_FALLBACK=True
   ```
3. Set `INITIAL_ADMIN_PASSWORD` in `.env` before the first launch. The application will **automatically create `jerseyhub_db` and all tables** on first launch.
4. *(Optional DBMS presentation step)*: You can also import `schema.sql` directly into phpMyAdmin or MySQL Workbench.

### 4. Run the Application
```powershell
.\venv\Scripts\python.exe app.py
```
Open your web browser and navigate to:
👉 **`http://localhost:5000`**

---

## ☁️ Deploy to Render

1. Create a **private GitHub repository** and upload the project source. Do not upload `.env`, `venv`, or `jerseyhub.db`; keep credentials out of GitHub.
2. In Render, choose **New → Blueprint**, connect the repository, and let Render read `render.yaml`.
3. When prompted for `INITIAL_ADMIN_PASSWORD`, provide a strong, unique password. Render generates `SECRET_KEY` and provisions the PostgreSQL database.
4. When deployment finishes, open the generated `onrender.com` URL. The first launch creates the tables and sample catalog.
5. Sign in at `/admin/login` using the password you supplied for `INITIAL_ADMIN_PASSWORD`.

Deployments use a PostgreSQL database; the local SQLite database is not uploaded. Do not set `USE_SQLITE_FALLBACK` for production. Uploaded images stored under `static/uploads` are on the web service filesystem and may not survive a redeploy; use externally hosted image URLs or configure persistent/object storage before relying on uploaded files.

---

---

## 🧪 Running Automated Tests
A complete automated test suite is provided to verify all 8 feature modules:
```powershell
.\venv\Scripts\python.exe -m unittest test_routes.py
```

---

## 📋 Features Checklist

- [x] **Customer Authentication**: Registration, Login, Logout, Profile update, Password change.
- [x] **Product Catalog**: Live search autocomplete, filtering by League, Team, Kit Type, Size, Price range, and Sorting.
- [x] **Product Details**: Image gallery, Size selection, Stock alert indicator, Customer reviews, Related kits.
- [x] **Shopping Cart**: Dynamic Add-to-cart, Quantity adjust, Stock cap enforcement, Item removal, Free shipping calculator.
- [x] **Checkout & Payment**: Address details, Simulated gateway (Cards, UPI, COD), Order number generation.
- [x] **Order Tracking**: Order confirmation, My Orders list, 4-stage live visual tracking timeline, Order cancellation.
- [x] **Admin Dashboard**: Real-time sales stats, Chart.js revenue trend, Low stock warnings, Top selling jerseys.
- [x] **Admin Inventory**: Per-size (S, M, L, XL, XXL) stock control with inline AJAX fast-save.
- [x] **Admin Products & Categories**: Full CRUD for jerseys, leagues, and teams.
- [x] **Admin Order Management**: Status updates (Pending &rarr; Processing &rarr; Shipped &rarr; Delivered &rarr; Cancelled).
- [x] **Admin Customer & Payment Logs**: View active accounts, transaction IDs, and sales performance by category.
