from extensions import db
from models import User, Category, Team, Product, ProductVariant, Order, OrderItem, Payment, Review
from datetime import datetime, timedelta
import os
import secrets

INR_MULTIPLIER = 7.0

def inr(value):
    if value is None:
        return None
    converted = float(value) * INR_MULTIPLIER
    return round(max(400.0, min(700.0, converted)), 2)

def seed_database_if_empty():
    if Product.query.first():
        print("[JerseyHub] Database already seeded. Skipping initial seeding.")
        return

    print("[JerseyHub] Seeding database with official football jerseys, teams, and sample data...")

    # 1. Users
    admin = User(
        username='admin',
        email='admin@jerseyhub.com',
        full_name='JerseyHub Super Admin',
        phone='+91 98765 43210',
        address='12 Ashok Vihar, Sector 15',
        city='Delhi',
        state='Delhi',
        postal_code='110011',
        country='India',
        is_admin=True,
        is_active=True
    )
    admin_password = os.environ.get('INITIAL_ADMIN_PASSWORD')
    if not admin_password:
        raise RuntimeError('INITIAL_ADMIN_PASSWORD must be set before creating the admin account.')
    admin.set_password(admin_password)
    db.session.add(admin)

    customer1 = User(
        username='john_doe',
        email='john@example.com',
        full_name='John Doe',
        phone='+91 99887 76654',
        address='24 Banjara Hills Road',
        city='Hyderabad',
        state='Telangana',
        postal_code='500034',
        country='India',
        is_admin=False,
        is_active=True
    )
    customer_password = os.environ.get('INITIAL_CUSTOMER_PASSWORD', 'customer123')
    customer1.set_password(customer_password)
    db.session.add(customer1)

    customer2 = User(
        username='alex_morgan',
        email='alex@example.com',
        full_name='Alex Morgan',
        phone='+91 98765 12345',
        address='8 Marine Drive, Bandra West',
        city='Mumbai',
        state='Maharashtra',
        postal_code='400050',
        country='India',
        is_admin=False,
        is_active=True
    )
    customer2.set_password(customer_password)
    db.session.add(customer2)

    db.session.flush()

    # 2. Categories
    categories_data = [
        {"name": "Premier League", "slug": "premier-league", "description": "Official jerseys of English top flight clubs.", "image_url": "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?w=800&auto=format&fit=crop&q=80", "order": 1},
        {"name": "La Liga", "slug": "la-liga", "description": "Spanish Primera División authentic match and stadium jerseys.", "image_url": "https://images.unsplash.com/photo-1522778119026-d647f0596c20?w=800&auto=format&fit=crop&q=80", "order": 2},
        {"name": "Serie A", "slug": "serie-a", "description": "Italian football elite kits with timeless classic designs.", "image_url": "https://images.unsplash.com/photo-1518091043644-c1d4457512c6?w=800&auto=format&fit=crop&q=80", "order": 3},
        {"name": "Bundesliga", "slug": "bundesliga", "description": "German powerhouse jerseys renowned for high quality and passion.", "image_url": "https://images.unsplash.com/photo-1574629810360-7efbbe195018?w=800&auto=format&fit=crop&q=80", "order": 4},
        {"name": "Ligue 1", "slug": "ligue-1", "description": "French football champions and high-fashion modern kits.", "image_url": "https://images.unsplash.com/photo-1517466787929-bc90951d0974?w=800&auto=format&fit=crop&q=80", "order": 5},
        {"name": "National Teams", "slug": "national-teams", "description": "World Cup and European Championship national team jerseys.", "image_url": "https://images.unsplash.com/photo-1517927033932-b3d18e61fb3a?w=800&auto=format&fit=crop&q=80", "order": 6},
        {"name": "Retro Classics", "slug": "retro-classics", "description": "Iconic vintage and throwback jerseys that shaped football history.", "image_url": "https://images.unsplash.com/photo-1489944440615-453fc2b6a9a9?w=800&auto=format&fit=crop&q=80", "order": 7}
    ]

    cat_objs = {}
    for cd in categories_data:
        cat = Category(
            name=cd["name"],
            slug=cd["slug"],
            description=cd["description"],
            image_url=cd["image_url"],
            display_order=cd["order"]
        )
        db.session.add(cat)
        cat_objs[cd["slug"]] = cat

    db.session.flush()

    # 3. Teams
    teams_data = [
        {"name": "Real Madrid", "slug": "real-madrid", "cat": "la-liga", "country": "Spain", "logo": "https://upload.wikimedia.org/wikipedia/en/5/56/Real_Madrid_CF.svg"},
        {"name": "FC Barcelona", "slug": "fc-barcelona", "cat": "la-liga", "country": "Spain", "logo": "https://upload.wikimedia.org/wikipedia/en/4/47/FC_Barcelona_%28crest%29.svg"},
        {"name": "Arsenal", "slug": "arsenal", "cat": "premier-league", "country": "England", "logo": "https://upload.wikimedia.org/wikipedia/en/5/53/Arsenal_FC.svg"},
        {"name": "Manchester City", "slug": "manchester-city", "cat": "premier-league", "country": "England", "logo": "https://upload.wikimedia.org/wikipedia/en/e/eb/Manchester_City_FC_badge.svg"},
        {"name": "Liverpool FC", "slug": "liverpool", "cat": "premier-league", "country": "England", "logo": "https://upload.wikimedia.org/wikipedia/en/0/0c/Liverpool_FC.svg"},
        {"name": "Manchester United", "slug": "manchester-united", "cat": "premier-league", "country": "England", "logo": "https://upload.wikimedia.org/wikipedia/en/7/7a/Manchester_United_FC_crest.svg"},
        {"name": "Chelsea FC", "slug": "chelsea", "cat": "premier-league", "country": "England", "logo": "https://upload.wikimedia.org/wikipedia/en/c/cc/Chelsea_FC.svg"},
        {"name": "Bayern Munich", "slug": "bayern-munich", "cat": "bundesliga", "country": "Germany", "logo": "https://upload.wikimedia.org/wikipedia/commons/1/1b/FC_Bayern_M%C3%BCnchen_logo_%282017%29.svg"},
        {"name": "Borussia Dortmund", "slug": "borussia-dortmund", "cat": "bundesliga", "country": "Germany", "logo": "https://upload.wikimedia.org/wikipedia/commons/6/67/Borussia_Dortmund_logo.svg"},
        {"name": "Paris Saint-Germain", "slug": "psg", "cat": "ligue-1", "country": "France", "logo": "https://upload.wikimedia.org/wikipedia/en/a/a7/Paris_Saint-Germain_F.C..svg"},
        {"name": "Inter Milan", "slug": "inter-milan", "cat": "serie-a", "country": "Italy", "logo": "https://upload.wikimedia.org/wikipedia/commons/0/05/FC_Internazionale_Milano_2021.svg"},
        {"name": "AC Milan", "slug": "ac-milan", "cat": "serie-a", "country": "Italy", "logo": "https://upload.wikimedia.org/wikipedia/commons/d/d0/Logo_of_AC_Milan.svg"},
        {"name": "Juventus", "slug": "juventus", "cat": "serie-a", "country": "Italy", "logo": "https://upload.wikimedia.org/wikipedia/commons/1/15/Juventus_FC_2017_logo.svg"},
        {"name": "Argentina", "slug": "argentina", "cat": "national-teams", "country": "Argentina", "logo": "https://upload.wikimedia.org/wikipedia/en/c/c1/Argentina_national_football_team_logo.svg"},
        {"name": "Brazil", "slug": "brazil", "cat": "national-teams", "country": "Brazil", "logo": "https://upload.wikimedia.org/wikipedia/commons/9/99/Brazilian_Football_Confederation_logo.svg"},
        {"name": "France", "slug": "france", "cat": "national-teams", "country": "France", "logo": "https://upload.wikimedia.org/wikipedia/en/2/23/French_Football_Federation_logo.svg"},
        {"name": "Portugal", "slug": "portugal", "cat": "national-teams", "country": "Portugal", "logo": "https://upload.wikimedia.org/wikipedia/en/e/e4/Portugal_national_football_team_logo.svg"},
        {"name": "England", "slug": "england", "cat": "national-teams", "country": "England", "logo": "https://upload.wikimedia.org/wikipedia/en/3/38/England_crest_2009.svg"},
        {"name": "Germany", "slug": "germany", "cat": "national-teams", "country": "Germany", "logo": "https://upload.wikimedia.org/wikipedia/commons/d/d0/DFB_Logo_with_Star.jpg"},
        {"name": "Spain", "slug": "spain", "cat": "national-teams", "country": "Spain", "logo": "https://upload.wikimedia.org/wikipedia/en/3/39/Spain_national_football_team_crest.svg"}
    ]

    team_objs = {}
    for td in teams_data:
        team = Team(
            name=td["name"],
            slug=td["slug"],
            category_id=cat_objs[td["cat"]].id,
            logo_url=td["logo"],
            country=td["country"]
        )
        db.session.add(team)
        team_objs[td["slug"]] = team

    db.session.flush()

    # 4. Products (Jerseys) — images from Getty Images (real match/jersey photos)
    products_data = [
        # Real Madrid
        {
            "name": "Real Madrid 2024/25 Home Jersey",
            "slug": "real-madrid-2024-25-home-jersey",
            "team": "real-madrid",
            "cat": "la-liga",
            "desc": "The official 2024/25 Real Madrid Home Jersey features a houndstooth pattern woven into the iconic royal white fabric, finished with metallic gold and black detailing. Features HEAT.RDY breathable technology.",
            "price": 95.00,
            "disc": 84.99,
            "season": "2024/25",
            "kit": "Home",
            "gender": "Men",
            "img1": "https://media.gettyimages.com/id/2158394483/photo/lisbon-portugal-vinicius-junior-of-real-madrid-during-the-uefa-champions-league-final-match.jpg?s=612x612&w=gi&k=20&c=1zcMMZJ5y0o9bQ0DKDx6Ub7cCRZ_oJ9X6l_3VKUwWGc=",
            "img2": "https://media.gettyimages.com/id/2158394483/photo/lisbon-portugal-vinicius-junior-of-real-madrid-during-the-uefa-champions-league-final-match.jpg?s=612x612&w=gi&k=20&c=1zcMMZJ5y0o9bQ0DKDx6Ub7cCRZ_oJ9X6l_3VKUwWGc=",
            "featured": True, "bestseller": True, "new": True
        },
        {
            "name": "Real Madrid 2024/25 Away Jersey",
            "slug": "real-madrid-2024-25-away-jersey",
            "team": "real-madrid",
            "cat": "la-liga",
            "desc": "Bright orange electric colourway commemorating the iconic La Décima season away kit. Features metallic night sky blue shoulder stripes and high performance sweat-wicking materials.",
            "price": 92.00,
            "disc": None,
            "season": "2024/25",
            "kit": "Away",
            "gender": "Men",
            "img1": "https://media.gettyimages.com/id/2159521881/photo/madrid-spain-kylian-mbappe-of-real-madrid-reacts-during-the-laliga-match-between-real-madrid.jpg?s=612x612&w=gi&k=20&c=bx4DJLtaGUTk4YzFMWqm98lGhwL_mGNKT05xDBpAGIo=",
            "img2": "https://media.gettyimages.com/id/2159521881/photo/madrid-spain-kylian-mbappe-of-real-madrid-reacts-during-the-laliga-match-between-real-madrid.jpg?s=612x612&w=gi&k=20&c=bx4DJLtaGUTk4YzFMWqm98lGhwL_mGNKT05xDBpAGIo=",
            "featured": False, "bestseller": False, "new": True
        },
        # FC Barcelona
        {
            "name": "FC Barcelona 125th Anniversary 2024/25 Home Jersey",
            "slug": "fc-barcelona-125th-anniversary-home-jersey",
            "team": "fc-barcelona",
            "cat": "la-liga",
            "desc": "Commemorating 125 glorious years of FC Barcelona! Half-and-half deep royal blue and garnet design inspired by the legendary 1899 founding kit. Features central crest and gold Spotify sponsor.",
            "price": 98.00,
            "disc": 89.00,
            "season": "2024/25",
            "kit": "Home",
            "gender": "Men",
            "img1": "https://media.gettyimages.com/id/2160527494/photo/barcelona-spain-pedri-of-fc-barcelona-looks-on-during-the-laliga-match-between-fc-barcelona.jpg?s=612x612&w=gi&k=20&c=OCDnG1_FuDJNBGTh-9g6S0K2O3gQ1GR6sU_rfyIEfio=",
            "img2": "https://media.gettyimages.com/id/2160527494/photo/barcelona-spain-pedri-of-fc-barcelona-looks-on-during-the-laliga-match-between-fc-barcelona.jpg?s=612x612&w=gi&k=20&c=OCDnG1_FuDJNBGTh-9g6S0K2O3gQ1GR6sU_rfyIEfio=",
            "featured": True, "bestseller": True, "new": True
        },
        {
            "name": "FC Barcelona 2024/25 Blackout Away Jersey",
            "slug": "fc-barcelona-2024-25-away-jersey",
            "team": "fc-barcelona",
            "cat": "la-liga",
            "desc": "Stunning sleek matte black kit with gradient Blaugrana side borders and TPU iridescent crest. Designed for unmatched modern street elegance and pitch comfort.",
            "price": 95.00,
            "disc": None,
            "season": "2024/25",
            "kit": "Away",
            "gender": "Men",
            "img1": "https://media.gettyimages.com/id/2181741022/photo/barcelona-spain-lamine-yamal-of-fc-barcelona-competes-for-the-ball-with-during-the-laliga.jpg?s=612x612&w=gi&k=20&c=7pWl5GRqCGpGJY2SvH-lxEh3jXi0FQqYY3E6XWPBXUA=",
            "img2": "https://media.gettyimages.com/id/2181741022/photo/barcelona-spain-lamine-yamal-of-fc-barcelona-competes-for-the-ball-with-during-the-laliga.jpg?s=612x612&w=gi&k=20&c=7pWl5GRqCGpGJY2SvH-lxEh3jXi0FQqYY3E6XWPBXUA=",
            "featured": False, "bestseller": True, "new": False
        },
        # Arsenal
        {
            "name": "Arsenal 2024/25 Home Cannon Jersey",
            "slug": "arsenal-2024-25-home-jersey",
            "team": "arsenal",
            "cat": "premier-league",
            "desc": "The Gunners return to the iconic standalone cannon crest on the home shirt for the first time in over 35 years. Classic red body with pure white sleeves and discreet dark blue flank accents.",
            "price": 90.00,
            "disc": 79.99,
            "season": "2024/25",
            "kit": "Home",
            "gender": "Men",
            "img1": "https://media.gettyimages.com/id/2166124620/photo/london-england-bukayo-saka-of-arsenal-in-action-during-the-premier-league-match-between.jpg?s=612x612&w=gi&k=20&c=m4cCxD8KWLCaB6YoY7DlYT7TApzXTsVBCTmzAfCZDgs=",
            "img2": "https://media.gettyimages.com/id/2166124620/photo/london-england-bukayo-saka-of-arsenal-in-action-during-the-premier-league-match-between.jpg?s=612x612&w=gi&k=20&c=m4cCxD8KWLCaB6YoY7DlYT7TApzXTsVBCTmzAfCZDgs=",
            "featured": True, "bestseller": True, "new": True
        },
        # Manchester City
        {
            "name": "Manchester City 2024/25 0161 Sky Blue Home Jersey",
            "slug": "manchester-city-2024-25-home-jersey",
            "team": "manchester-city",
            "cat": "premier-league",
            "desc": "Featuring Manchester's local telephone area code 0161 in graffiti style on the collar and ribbing. Authentic sky blue stadium fabric with dryCELL moisture-management technology.",
            "price": 92.00,
            "disc": None,
            "season": "2024/25",
            "kit": "Home",
            "gender": "Men",
            "img1": "https://media.gettyimages.com/id/2181023819/photo/manchester-england-erling-haaland-of-manchester-city-in-action-during-the-premier-league.jpg?s=612x612&w=gi&k=20&c=PXt8HMnQ4OkNaV8d3YFHOX3u96C5YOimW1p2UsMR1Lk=",
            "img2": "https://media.gettyimages.com/id/2181023819/photo/manchester-england-erling-haaland-of-manchester-city-in-action-during-the-premier-league.jpg?s=612x612&w=gi&k=20&c=PXt8HMnQ4OkNaV8d3YFHOX3u96C5YOimW1p2UsMR1Lk=",
            "featured": True, "bestseller": False, "new": True
        },
        # Liverpool
        {
            "name": "Liverpool FC 2024/25 Retro Yellow Pinstripe Home Kit",
            "slug": "liverpool-fc-2024-25-home-jersey",
            "team": "liverpool",
            "cat": "premier-league",
            "desc": "Paying homage to the iconic 1984 European Cup winning squad in Rome, featuring subtle chrome-yellow pinstripes forming an intricate YNWA pattern in the crimson red weave.",
            "price": 94.00,
            "disc": 82.50,
            "season": "2024/25",
            "kit": "Home",
            "gender": "Men",
            "img1": "https://media.gettyimages.com/id/2181023762/photo/liverpool-england-mohammed-salah-of-liverpool-in-action-during-the-premier-league-match.jpg?s=612x612&w=gi&k=20&c=HN5z_qn2mFoJnF82V8FTbBjX8y_VNI4EzJIHv-PGTk0=",
            "img2": "https://media.gettyimages.com/id/2181023762/photo/liverpool-england-mohammed-salah-of-liverpool-in-action-during-the-premier-league-match.jpg?s=612x612&w=gi&k=20&c=HN5z_qn2mFoJnF82V8FTbBjX8y_VNI4EzJIHv-PGTk0=",
            "featured": True, "bestseller": True, "new": False
        },
        # Manchester United
        {
            "name": "Manchester United 2024/25 Gradient Red Home Kit",
            "slug": "manchester-united-2024-25-home-jersey",
            "team": "manchester-united",
            "cat": "premier-league",
            "desc": "A vibrant dual-tone red gradient designed to catch stadium floodlights under the Old Trafford lights. Premium Snapdragon sponsor logo and three-stripe adidas heritage.",
            "price": 90.00,
            "disc": None,
            "season": "2024/25",
            "kit": "Home",
            "gender": "Men",
            "img1": "https://media.gettyimages.com/id/2176007891/photo/manchester-england-bruno-fernandes-of-manchester-united-in-action-during-the-premier-league.jpg?s=612x612&w=gi&k=20&c=DT0F-QVKLY2-cXTCNJNKdPv3p9o59X5QfUhTTVMDlvI=",
            "img2": "https://media.gettyimages.com/id/2176007891/photo/manchester-england-bruno-fernandes-of-manchester-united-in-action-during-the-premier-league.jpg?s=612x612&w=gi&k=20&c=DT0F-QVKLY2-cXTCNJNKdPv3p9o59X5QfUhTTVMDlvI=",
            "featured": False, "bestseller": True, "new": True
        },
        # Chelsea FC
        {
            "name": "Chelsea FC 2024/25 Flame Blue Home Jersey",
            "slug": "chelsea-fc-2024-25-home-jersey",
            "team": "chelsea",
            "cat": "premier-league",
            "desc": "Unconventional melted-liquid and flame graphics representing the hottest core of London passion. Dri-FIT ADV match-issue engineering.",
            "price": 88.00,
            "disc": 75.00,
            "season": "2024/25",
            "kit": "Home",
            "gender": "Men",
            "img1": "https://media.gettyimages.com/id/2175951551/photo/london-england-cole-palmer-of-chelsea-in-action-during-the-premier-league-match-between.jpg?s=612x612&w=gi&k=20&c=1SJiQ6GkXGBWiPnKjYIpK8VMKhCF8qiRW5qJfW5gGsY=",
            "img2": "https://media.gettyimages.com/id/2175951551/photo/london-england-cole-palmer-of-chelsea-in-action-during-the-premier-league-match-between.jpg?s=612x612&w=gi&k=20&c=1SJiQ6GkXGBWiPnKjYIpK8VMKhCF8qiRW5qJfW5gGsY=",
            "featured": False, "bestseller": False, "new": True
        },
        # Bayern Munich
        {
            "name": "Bayern Munich 2024/25 Triple Red Allianz Home Kit",
            "slug": "bayern-munich-2024-25-home-jersey",
            "team": "bayern-munich",
            "cat": "bundesliga",
            "desc": "Three distinct shades of Bavarian red combined in bold vertical barcode striping with deep maroon crest and blackout accents. 'Mia San Mia' motto on the inner neck.",
            "price": 92.00,
            "disc": 85.00,
            "season": "2024/25",
            "kit": "Home",
            "gender": "Men",
            "img1": "https://media.gettyimages.com/id/2180957701/photo/munich-germany-harry-kane-of-fc-bayern-munchen-in-action-during-the-bundesliga-match-between.jpg?s=612x612&w=gi&k=20&c=Vy0-nImTJMtyLVTtI4GpwMkFaijH_5Kii4fBIi88Wuc=",
            "img2": "https://media.gettyimages.com/id/2180957701/photo/munich-germany-harry-kane-of-fc-bayern-munchen-in-action-during-the-bundesliga-match-between.jpg?s=612x612&w=gi&k=20&c=Vy0-nImTJMtyLVTtI4GpwMkFaijH_5Kii4fBIi88Wuc=",
            "featured": True, "bestseller": False, "new": True
        },
        # Borussia Dortmund
        {
            "name": "Borussia Dortmund 2024/25 Yellow Wall Home Kit",
            "slug": "borussia-dortmund-2024-25-home-jersey",
            "team": "borussia-dortmund",
            "cat": "bundesliga",
            "desc": "Classic Signal Iduna Park yellow with pinstripe black retro paneling. Built for the famous Südtribüne supporters with ultra-breathable mesh inserts.",
            "price": 89.00,
            "disc": None,
            "season": "2024/25",
            "kit": "Home",
            "gender": "Men",
            "img1": "https://media.gettyimages.com/id/2181023826/photo/dortmund-germany-julian-brandt-of-borussia-dortmund-in-action-during-the-bundesliga-match.jpg?s=612x612&w=gi&k=20&c=kLKiF2pkxHkiN8fLm4JDiUuD3LHHmLjwBajb_YZbblE=",
            "img2": "https://media.gettyimages.com/id/2181023826/photo/dortmund-germany-julian-brandt-of-borussia-dortmund-in-action-during-the-bundesliga-match.jpg?s=612x612&w=gi&k=20&c=kLKiF2pkxHkiN8fLm4JDiUuD3LHHmLjwBajb_YZbblE=",
            "featured": False, "bestseller": True, "new": False
        },
        # Paris Saint-Germain
        {
            "name": "Paris Saint-Germain 2024/25 Classic Hechter Home Kit",
            "slug": "paris-saint-germain-2024-25-home-jersey",
            "team": "psg",
            "cat": "ligue-1",
            "desc": "The return of the cherished central red and white Hechter brushstroke band across midnight navy body. Parisian haute couture meets elite sports innovation.",
            "price": 95.00,
            "disc": 84.00,
            "season": "2024/25",
            "kit": "Home",
            "gender": "Men",
            "img1": "https://media.gettyimages.com/id/2162564726/photo/paris-france-ousmane-dembele-of-paris-saint-germain-in-action-during-the-ligue-1-match.jpg?s=612x612&w=gi&k=20&c=fLq3vEV_f26ufMJGqkA7DTLHK5WKTD6ZV9Rd-FmQcOM=",
            "img2": "https://media.gettyimages.com/id/2162564726/photo/paris-france-ousmane-dembele-of-paris-saint-germain-in-action-during-the-ligue-1-match.jpg?s=612x612&w=gi&k=20&c=fLq3vEV_f26ufMJGqkA7DTLHK5WKTD6ZV9Rd-FmQcOM=",
            "featured": True, "bestseller": True, "new": True
        },
        # Inter Milan
        {
            "name": "Inter Milan 2024/25 Two Stars Scudetto Home Kit",
            "slug": "inter-milan-2024-25-home-jersey",
            "team": "inter-milan",
            "cat": "serie-a",
            "desc": "Historic milestone kit featuring the second golden star above the Nerazzurri crest celebrating their 20th Italian Championship. Asymmetrical camouflage stripes.",
            "price": 96.00,
            "disc": None,
            "season": "2024/25",
            "kit": "Home",
            "gender": "Men",
            "img1": "https://media.gettyimages.com/id/2157640695/photo/milan-italy-lautaro-martinez-of-fc-internazionale-in-action-during-the-serie-a-match-between.jpg?s=612x612&w=gi&k=20&c=WuGFPEcY_j4vMHjdABmxs7LsmFzI55aE-OIL8gEPSaM=",
            "img2": "https://media.gettyimages.com/id/2157640695/photo/milan-italy-lautaro-martinez-of-fc-internazionale-in-action-during-the-serie-a-match-between.jpg?s=612x612&w=gi&k=20&c=WuGFPEcY_j4vMHjdABmxs7LsmFzI55aE-OIL8gEPSaM=",
            "featured": True, "bestseller": True, "new": True
        },
        # AC Milan
        {
            "name": "AC Milan 2024/25 Rossoneri Striped Home Kit",
            "slug": "ac-milan-2024-25-home-jersey",
            "team": "ac-milan",
            "cat": "serie-a",
            "desc": "Timeless red and black vertical stripes celebrating 125 years of Il Diavolo history. Gold celebratory lettering on inner neck tape and Emirates Fly Better chest sponsor.",
            "price": 92.00,
            "disc": 79.99,
            "season": "2024/25",
            "kit": "Home",
            "gender": "Men",
            "img1": "https://media.gettyimages.com/id/2157640742/photo/milan-italy-rafael-leao-of-ac-milan-in-action-during-the-serie-a-match-between-ac-milan-and.jpg?s=612x612&w=gi&k=20&c=g5jnpL6yxaioVwMVMy_eo6JGX9TMNtWXmk7KnPfO1u8=",
            "img2": "https://media.gettyimages.com/id/2157640742/photo/milan-italy-rafael-leao-of-ac-milan-in-action-during-the-serie-a-match-between-ac-milan-and.jpg?s=612x612&w=gi&k=20&c=g5jnpL6yxaioVwMVMy_eo6JGX9TMNtWXmk7KnPfO1u8=",
            "featured": False, "bestseller": True, "new": False
        },
        # Juventus
        {
            "name": "Juventus 2024/25 Lunar White & Black Home Kit",
            "slug": "juventus-2024-25-home-jersey",
            "team": "juventus",
            "cat": "serie-a",
            "desc": "Bold reimagination of the traditional Bianconeri stripes with a subtle textured lunar crater effect across the fabric, celebrating space exploration and Italian innovation.",
            "price": 90.00,
            "disc": None,
            "season": "2024/25",
            "kit": "Home",
            "gender": "Men",
            "img1": "https://media.gettyimages.com/id/2174291748/photo/turin-italy-dusan-vlahovic-of-juventus-in-action-during-the-serie-a-match-between-juventus.jpg?s=612x612&w=gi&k=20&c=09HhQSVdUB_wfJZDJgc8vv-MQqGZ_Y3IYAY5xBJnB0Y=",
            "img2": "https://media.gettyimages.com/id/2174291748/photo/turin-italy-dusan-vlahovic-of-juventus-in-action-during-the-serie-a-match-between-juventus.jpg?s=612x612&w=gi&k=20&c=09HhQSVdUB_wfJZDJgc8vv-MQqGZ_Y3IYAY5xBJnB0Y=",
            "featured": False, "bestseller": False, "new": True
        },
        # Argentina National Team
        {
            "name": "Argentina 3-Star World Champions Home Jersey",
            "slug": "argentina-3-star-world-cup-home-jersey",
            "team": "argentina",
            "cat": "national-teams",
            "desc": "The glorious 3-Star Albiceleste jersey worn by Lionel Messi and the champions of the world! Albiceleste sky blue and white stripes with gold 2022 FIFA World Champions badge.",
            "price": 105.00,
            "disc": 94.99,
            "season": "2024/25",
            "kit": "Home",
            "gender": "Men",
            "img1": "https://media.gettyimages.com/id/2155944736/photo/east-rutherford-new-jersey-lionel-messi-10-of-argentina-in-action-during-the-conmebol-copa.jpg?s=612x612&w=gi&k=20&c=PcCRWlRqoExJfHRpTH3s8v8Y2_OV_jEYGWEKSjzPNE0=",
            "img2": "https://media.gettyimages.com/id/2155944736/photo/east-rutherford-new-jersey-lionel-messi-10-of-argentina-in-action-during-the-conmebol-copa.jpg?s=612x612&w=gi&k=20&c=PcCRWlRqoExJfHRpTH3s8v8Y2_OV_jEYGWEKSjzPNE0=",
            "featured": True, "bestseller": True, "new": True
        },
        # Brazil National Team
        {
            "name": "Brazil 2024 Copa America Canarinho Home Kit",
            "slug": "brazil-2024-canarinho-home-jersey",
            "team": "brazil",
            "cat": "national-teams",
            "desc": "The legendary Amarelinha yellow jersey featuring rich embossed patterns of Brazilian fauna, flora, and carnival rhythms. Central embroidered CBF shield.",
            "price": 98.00,
            "disc": None,
            "season": "2024/25",
            "kit": "Home",
            "gender": "Men",
            "img1": "https://media.gettyimages.com/id/2155944709/photo/east-rutherford-new-jersey-vinicius-junior-9-of-brazil-in-action-during-the-conmebol-copa.jpg?s=612x612&w=gi&k=20&c=7aS0U_RfGrJBQQ-QJd-nGwYrPNHKcH9YFtFHIBqfLsE=",
            "img2": "https://media.gettyimages.com/id/2155944709/photo/east-rutherford-new-jersey-vinicius-junior-9-of-brazil-in-action-during-the-conmebol-copa.jpg?s=612x612&w=gi&k=20&c=7aS0U_RfGrJBQQ-QJd-nGwYrPNHKcH9YFtFHIBqfLsE=",
            "featured": True, "bestseller": True, "new": False
        },
        # France National Team
        {
            "name": "France 2024 Euro Vintage Rooster Home Jersey",
            "slug": "france-2024-euro-home-jersey",
            "team": "france",
            "cat": "national-teams",
            "desc": "Features an oversized retro golden Gallic rooster crest on vibrant royal cobalt blue fabric. Tricolour flag details on the sleeves and offset collar.",
            "price": 95.00,
            "disc": 84.99,
            "season": "2024/25",
            "kit": "Home",
            "gender": "Men",
            "img1": "https://media.gettyimages.com/id/2158389791/photo/berlin-germany-kylian-mbappe-of-france-in-action-during-the-uefa-euro-2024-semi-final-match.jpg?s=612x612&w=gi&k=20&c=KY3v0CEPN7Bsp4MOIhLsP2r85xOV1h3XHMO8rqN5KaQ=",
            "img2": "https://media.gettyimages.com/id/2158389791/photo/berlin-germany-kylian-mbappe-of-france-in-action-during-the-uefa-euro-2024-semi-final-match.jpg?s=612x612&w=gi&k=20&c=KY3v0CEPN7Bsp4MOIhLsP2r85xOV1h3XHMO8rqN5KaQ=",
            "featured": True, "bestseller": True, "new": True
        },
        # Portugal National Team
        {
            "name": "Portugal 2024 Euro Cristiano Ronaldo Edition Home Kit",
            "slug": "portugal-2024-euro-home-jersey",
            "team": "portugal",
            "cat": "national-teams",
            "desc": "Vibrant crimson red body with forest green collar accents honouring the national flag. Lightweight breathable fabric engineered for rapid sprint performance.",
            "price": 95.00,
            "disc": None,
            "season": "2024/25",
            "kit": "Home",
            "gender": "Men",
            "img1": "https://media.gettyimages.com/id/2158389698/photo/berlin-germany-cristiano-ronaldo-of-portugal-in-action-during-the-uefa-euro-2024-quarter.jpg?s=612x612&w=gi&k=20&c=YcSiJnOXbXkdFh2x9-fC_s9j-Qd-INWBXKGxNpTQDNw=",
            "img2": "https://media.gettyimages.com/id/2158389698/photo/berlin-germany-cristiano-ronaldo-of-portugal-in-action-during-the-uefa-euro-2024-quarter.jpg?s=612x612&w=gi&k=20&c=YcSiJnOXbXkdFh2x9-fC_s9j-Qd-INWBXKGxNpTQDNw=",
            "featured": True, "bestseller": True, "new": False
        },
        # Spain National Team
        {
            "name": "Spain 2024 Euro Champions Red & Gold Home Kit",
            "slug": "spain-2024-euro-champions-home-jersey",
            "team": "spain",
            "cat": "national-teams",
            "desc": "Official championship jersey worn by La Roja during their record-breaking 4th European crown! Carnation red base with subtle wave motifs and yellow accents.",
            "price": 99.00,
            "disc": 89.00,
            "season": "2024/25",
            "kit": "Home",
            "gender": "Men",
            "img1": "https://media.gettyimages.com/id/2162117832/photo/berlin-germany-lamine-yamal-of-spain-in-action-during-the-uefa-euro-2024-final-match-between.jpg?s=612x612&w=gi&k=20&c=L0LMWF2bHMvYY4e2bNgUAVxE87k7P7F7d8EXw-bBWXI=",
            "img2": "https://media.gettyimages.com/id/2162117832/photo/berlin-germany-lamine-yamal-of-spain-in-action-during-the-uefa-euro-2024-final-match-between.jpg?s=612x612&w=gi&k=20&c=L0LMWF2bHMvYY4e2bNgUAVxE87k7P7F7d8EXw-bBWXI=",
            "featured": True, "bestseller": True, "new": True
        },
        # England National Team
        {
            "name": "England 2024 Home Stadium Jersey",
            "slug": "england-2024-home-stadium-jersey",
            "team": "england",
            "cat": "national-teams",
            "desc": "Classic crisp white jersey with navy trim and multi-coloured striped cuffs inspired by England's 1966 training gear. Embroidered Three Lions crest.",
            "price": 92.00,
            "disc": 80.00,
            "season": "2024/25",
            "kit": "Home",
            "gender": "Men",
            "img1": "https://media.gettyimages.com/id/2162117899/photo/berlin-germany-jude-bellingham-of-england-in-action-during-the-uefa-euro-2024-final-match.jpg?s=612x612&w=gi&k=20&c=WmR3l_H5B0xH-yJHYfgMK3IJ3D3YZCqq1H2rGP1j1sY=",
            "img2": "https://media.gettyimages.com/id/2162117899/photo/berlin-germany-jude-bellingham-of-england-in-action-during-the-uefa-euro-2024-final-match.jpg?s=612x612&w=gi&k=20&c=WmR3l_H5B0xH-yJHYfgMK3IJ3D3YZCqq1H2rGP1j1sY=",
            "featured": False, "bestseller": True, "new": True
        },
        # Retro Classics
        {
            "name": "Manchester United 1998/99 Treble Winners Retro Home Jersey",
            "slug": "manchester-united-1998-99-treble-retro-jersey",
            "team": "manchester-united",
            "cat": "retro-classics",
            "desc": "The holy grail of football kits! Relive Camp Nou 1999 and the historic Premier League, FA Cup, and Champions League Treble. Zip polo collar and embossed club crest shield.",
            "price": 85.00,
            "disc": 72.00,
            "season": "1998/99",
            "kit": "Retro",
            "gender": "Men",
            "img1": "https://media.gettyimages.com/id/1345572016/photo/london-england-a-manchester-united-shirt-on-display-at-the-nike-concept-store-at-oxford-circus.jpg?s=612x612&w=gi&k=20&c=FAvPjS4r7Z5RL-NrOXAjHuD-nVCaOxXHH6bMlT4yIzE=",
            "img2": "https://media.gettyimages.com/id/1345572016/photo/london-england-a-manchester-united-shirt-on-display-at-the-nike-concept-store-at-oxford-circus.jpg?s=612x612&w=gi&k=20&c=FAvPjS4r7Z5RL-NrOXAjHuD-nVCaOxXHH6bMlT4yIzE=",
            "featured": True, "bestseller": True, "new": False
        },
        {
            "name": "Arsenal 2003/04 The Invincibles Retro O2 Home Kit",
            "slug": "arsenal-2003-04-invincibles-retro-jersey",
            "team": "arsenal",
            "cat": "retro-classics",
            "desc": "Commemorating Arsene Wenger's legendary 49-game unbeaten squad including Thierry Henry, Patrick Vieira, and Dennis Bergkamp. Deep red with bold white sleeves and flock O2 print.",
            "price": 85.00,
            "disc": None,
            "season": "2003/04",
            "kit": "Retro",
            "gender": "Men",
            "img1": "https://media.gettyimages.com/id/51241053/photo/arsenal-v-manchester-united-premier-league.jpg?s=612x612&w=gi&k=20&c=Bfz6W_qLFCuAJbOjsxn1BLHJAe6sxkA_t9cpHWPLhBM=",
            "img2": "https://media.gettyimages.com/id/51241053/photo/arsenal-v-manchester-united-premier-league.jpg?s=612x612&w=gi&k=20&c=Bfz6W_qLFCuAJbOjsxn1BLHJAe6sxkA_t9cpHWPLhBM=",
            "featured": True, "bestseller": True, "new": False
        },
        {
            "name": "AC Milan 2006/07 Champions League Final Athens Retro Kit",
            "slug": "ac-milan-2006-07-champions-league-retro-jersey",
            "team": "ac-milan",
            "cat": "retro-classics",
            "desc": "The glorious Athens 2007 European Cup winning jersey starring Kaká and Inzaghi. Pure white lucky finals kit with golden UEFA match embroidery.",
            "price": 82.00,
            "disc": 69.99,
            "season": "2006/07",
            "kit": "Retro",
            "gender": "Men",
            "img1": "https://media.gettyimages.com/id/75817894/photo/athens-greece-kaka-of-ac-milan-in-action-during-the-uefa-champions-league-final-between-ac.jpg?s=612x612&w=gi&k=20&c=5rp3XxfWh7PkAFNJi2tJrXYU9fCXO2C5K3V0g2sP-6s=",
            "img2": "https://media.gettyimages.com/id/75817894/photo/athens-greece-kaka-of-ac-milan-in-action-during-the-uefa-champions-league-final-between-ac.jpg?s=612x612&w=gi&k=20&c=5rp3XxfWh7PkAFNJi2tJrXYU9fCXO2C5K3V0g2sP-6s=",
            "featured": False, "bestseller": False, "new": False
        }
    ]

    sizes = ['S', 'M', 'L', 'XL', 'XXL']
    product_objects = []

    for pd in products_data:
        prod = Product(
            name=pd["name"],
            slug=pd["slug"],
            team_id=team_objs[pd["team"]].id,
            category_id=cat_objs[pd["cat"]].id,
            description=pd["desc"],
            price=inr(pd["price"]),
            discount_price=inr(pd["disc"]),
            season=pd["season"],
            kit_type=pd["kit"],
            gender=pd["gender"],
            primary_image=pd["img1"],
            secondary_image=pd["img2"],
            is_featured=pd["featured"],
            is_bestseller=pd["bestseller"],
            is_new_arrival=pd["new"],
            created_at=datetime.utcnow() - timedelta(days=len(product_objects) * 2)
        )
        db.session.add(prod)
        db.session.flush()
        product_objects.append(prod)

        # Create Variants
        for s in sizes:
            # Larger starting quantities for each size.
            stock = 50 if s == 'M' else (45 if s == 'L' else (40 if s == 'XL' else (35 if s == 'S' else 33)))

            variant = ProductVariant(
                product_id=prod.id,
                size=s,
                stock_quantity=stock,
                sku=f"JH-{prod.id}-{s}"
            )
            db.session.add(variant)

    db.session.flush()

    # 5. Reviews
    reviews_data = [
        {"prod_idx": 0, "user": customer1, "rating": 5, "comment": "Spectacular quality! The houndstooth weave on the Real Madrid jersey feels even better in person than the photos. Fits true to size."},
        {"prod_idx": 0, "user": customer2, "rating": 5, "comment": "Fast shipping and 100% authentic shirt. The gold details shine beautifully under sunlight."},
        {"prod_idx": 2, "user": customer1, "rating": 5, "comment": "The 125th anniversary Barca kit is an instant collectible! Half and half design is pure nostalgia."},
        {"prod_idx": 4, "user": customer2, "rating": 5, "comment": "Arsenal cannon logo is absolute perfection. Great breathable fabric for playing five-a-side."},
        {"prod_idx": 15, "user": customer1, "rating": 5, "comment": "The 3 stars and World Cup badge are stunning. A must have for any Messi fan!"},
        {"prod_idx": 21, "user": customer2, "rating": 5, "comment": "Camp Nou 1999 vibes! The retro collar and Sharp logo feel like stepping right back in time."}
    ]

    for rd in reviews_data:
        rev = Review(
            user_id=rd["user"].id,
            product_id=product_objects[rd["prod_idx"]].id,
            rating=rd["rating"],
            comment=rd["comment"],
            created_at=datetime.utcnow() - timedelta(days=3)
        )
        db.session.add(rev)

    # 6. Sample Initial Completed Orders for realistic DBMS reports
    p0_price = float(product_objects[0].effective_price)
    p15_price = float(product_objects[15].effective_price)
    order1_subtotal = round(p0_price + p15_price, 2)
    order1_shipping = 0.00 if order1_subtotal >= 6000.0 else 299.00
    order1_total = round(order1_subtotal + order1_shipping, 2)

    order1 = Order(
        order_number="JH-240920-8842A1",
        user_id=customer1.id,
        subtotal=order1_subtotal,
        shipping_fee=order1_shipping,
        total_amount=order1_total,
        status="Delivered",
        shipping_name="John Doe",
        shipping_phone="+91 99887 76654",
        shipping_address="24 Banjara Hills Road",
        shipping_city="Hyderabad",
        shipping_state="Telangana",
        shipping_postal_code="500034",
        shipping_country="India",
        notes="Please leave package at the security desk.",
        created_at=datetime.utcnow() - timedelta(days=7)
    )
    db.session.add(order1)
    db.session.flush()

    oi1 = OrderItem(
        order_id=order1.id,
        product_id=product_objects[0].id,
        variant_id=product_objects[0].variants.filter_by(size='M').first().id,
        product_name=product_objects[0].name,
        size='M',
        price=p0_price,
        quantity=1,
        total_price=p0_price
    )
    oi2 = OrderItem(
        order_id=order1.id,
        product_id=product_objects[15].id,
        variant_id=product_objects[15].variants.filter_by(size='L').first().id,
        product_name=product_objects[15].name,
        size='L',
        price=p15_price,
        quantity=1,
        total_price=p15_price
    )
    db.session.add_all([oi1, oi2])

    p1 = Payment(
        order_id=order1.id,
        transaction_id="TXN-A1904721C001",
        payment_method="Credit/Debit Card",
        amount=order1_total,
        payment_status="Completed",
        payment_details="Card ending in 4242 authorized via simulated gateway.",
        paid_at=datetime.utcnow() - timedelta(days=7)
    )
    db.session.add(p1)

    p2_price = float(product_objects[2].effective_price)
    order2_subtotal = round(p2_price, 2)
    order2_shipping = 0.00 if order2_subtotal >= 6000.0 else 299.00
    order2_total = round(order2_subtotal + order2_shipping, 2)

    order2 = Order(
        order_number="JH-240925-C947F2",
        user_id=customer2.id,
        subtotal=order2_subtotal,
        shipping_fee=order2_shipping,
        total_amount=order2_total,
        status="Processing",
        shipping_name="Alex Morgan",
        shipping_phone="+91 98765 12345",
        shipping_address="8 Marine Drive, Bandra West",
        shipping_city="Mumbai",
        shipping_state="Maharashtra",
        shipping_postal_code="400050",
        shipping_country="India",
        created_at=datetime.utcnow() - timedelta(days=2)
    )
    db.session.add(order2)
    db.session.flush()

    oi3 = OrderItem(
        order_id=order2.id,
        product_id=product_objects[2].id,
        variant_id=product_objects[2].variants.filter_by(size='L').first().id,
        product_name=product_objects[2].name,
        size='L',
        price=p2_price,
        quantity=1,
        total_price=p2_price
    )
    db.session.add(oi3)

    p2 = Payment(
        order_id=order2.id,
        transaction_id="TXN-B9201948D002",
        payment_method="UPI",
        amount=order2_total,
        payment_status="Completed",
        payment_details="UPI ID alex@okaxis authorized via instant transfer.",
        paid_at=datetime.utcnow() - timedelta(days=2)
    )
    db.session.add(p2)

    db.session.commit()
    print("[JerseyHub] Database seeding completed successfully with 24 jerseys, sample orders, reviews, and admin!")
