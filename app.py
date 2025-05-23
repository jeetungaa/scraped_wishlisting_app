from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from bs4 import BeautifulSoup
from selenium import webdriver
from sqlalchemy.orm import Session
from sqlalchemy.orm import column_property
from sqlalchemy import Column, String
from flask import Flask, request, jsonify
from flask import make_response
from flask_login import login_required
import requests
from celery import Celery
import sqlite3
import jwt as pyjwt
import datetime
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from flask_mail import Mail
from celery.schedules import crontab
from flask import request, jsonify
from collections import OrderedDict




app = Flask(__name__)
app.secret_key = 'a03d88a45f8a4e19bb2e5c1de12fa654'  # Change this to a secure secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# app.config['MAIL_SERVER'] = 'smtp.gmail.com'  # Or your SMTP server
# app.config['MAIL_PORT'] = 587
# app.config['MAIL_USE_TLS'] = True
# app.config['MAIL_USERNAME'] = 'vaasumarothia45@gmail.com'  # Your email
# app.config['MAIL_PASSWORD'] = 'ywvp fntr qcui xnpj'  # App-specific password
# app.config['MAIL_DEFAULT_SENDER'] = 'vaasumarothia45@gmail.com'

app.config['HUGGINGFACE_API_KEY'] = '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' 
app.config['AI_MODEL'] = 'mistralai/Mistral-7B-Instruct-v0.1'  # Primary model
app.config['AI_MODEL_BACKUP'] = 'HuggingFaceH4/zephyr-7b-beta'


mail = Mail(app)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
CORS(app, resources={r"/*": {"origins": "http://localhost:5173"}}, supports_credentials=True)

def make_celery(app):
    celery = Celery(app.import_name, backend='redis://localhost:6379/0', broker='redis://localhost:6379/0')
    celery.conf.update(app.config)
    return celery

celery = make_celery(app)
celery.conf.beat_schedule = {
    'check-prices-every-day': {
        'task': 'app.check_price_changes',
        'schedule': crontab(hour=12, minute=0),  # Run daily at noon
    },
}

# Function to connect to the database
def get_db_connection():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    # email = db.Column(db.String(120), unique=True, nullable=False)

class Wishlist(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    price = db.Column(db.String(50))
    link = db.Column(db.String(300))
    image = db.Column(db.String(300))
    description = db.Column(db.String(500))
    site = Column(String, nullable=False)

class PriceHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    wishlist_id = db.Column(db.Integer, db.ForeignKey('wishlist.id'), nullable=False)
    price = db.Column(db.String(50), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    

@login_manager.user_loader
def load_user(user_id):
    return db.session.get(User, int(user_id))

def add_user_to_db(username, password):
    try:
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
    except Exception as e:
        print(f"Error adding user: {e}")
        db.session.rollback()

def get_user_from_db(username):
    return User.query.filter_by(username=username).first()


# price drop function ...........
def send_price_drop_email(user, item, old_price, new_price):
    try:
        subject = f"Price Drop Alert for {item.description}"
        body = f"""
        Hello {user.username},
        
        The price for {item.description} has dropped!
        
        Old Price: {old_price}
        New Price: {new_price}
        
        Check it out here: {item.link}
        
        Happy Shopping!
        """
        
        msg = MIMEMultipart()
        msg['Subject'] = subject
        msg['From'] = app.config['MAIL_DEFAULT_SENDER']
        msg['To'] = user.email
        
        msg.attach(MIMEText(body, 'plain'))
        
        with smtplib.SMTP(app.config['MAIL_SERVER'], app.config['MAIL_PORT']) as server:
            server.starttls()
            server.login(app.config['MAIL_USERNAME'], app.config['MAIL_PASSWORD'])
            server.send_message(msg)
            
    except Exception as e:
        print(f"Error sending email: {e}")


def get_local_response(user_message):
    lower_msg = user_message.lower().strip()
    
    # Greetings
    if any(g in lower_msg for g in ["hi", "hello", "hey"]):
        return "Hello! I'm your shopping assistant. How can I help today?"
    
    if "how are you" in lower_msg:
        return "I'm an AI, so I'm always ready to help you shop smarter!"
    
    if any(t in lower_msg for t in ["thank", "thanks"]):
        return "You're welcome! Happy to help with your shopping needs."
    
    # Product Comparisons - More flexible matching
    if ("iphone" in lower_msg and "13" in lower_msg and "14" in lower_msg) or ("compare iphone" in lower_msg):
        return """📱 iPhone 13 vs 14:

• Camera: iPhone 14 has better low-light photos
• Battery: iPhone 14 lasts 1 hour longer
• Price: 
  - iPhone 13: ₹59,900
  - iPhone 14: ₹79,900
• Best for: iPhone 14 if you want better camera, iPhone 13 for value"""
    
    if "smartwatch" in lower_msg or "smart watch" in lower_msg:
        if any(price_term in lower_msg for price_term in ["under", "₹", "rs", "rupee"]):
            return """⌚ Best Smartwatches Under ₹15,000:

1. Amazfit GTS 4 (₹12,999) - Best overall
2. Fire-Boltt Invincible (₹1,999) - Budget pick
3. Noise ColorFit Pro 4 (₹3,999) - Best display

🔗 Check Flipkart/Amazon for current deals"""
        else:
            return "Here are some popular smartwatch brands: Apple, Samsung, Amazfit. Ask me about specific models or price ranges!"
    
    # Shopping Help - More flexible matching
    if any(k in lower_msg for k in ["product", "item", "search"]):
        return "You can search for any product above. I'll compare prices across stores."
    
    if any(k in lower_msg for k in ["price", "cost", "₹", "rs", "rupee"]):
        return "Add items to your wishlist to track price drops automatically."
    
    # Handle single product mentions
    if "iphone 13" in lower_msg:
        return "The iPhone 13 (128GB) is currently priced around ₹59,900 in India. Would you like to compare it with other models?"
    
    if "iphone 14" in lower_msg:
        return "The iPhone 14 (128GB) costs approximately ₹79,900 in India. Would you like to compare features with other iPhones?"
    
    # Final fallback with more suggestions
    return ("I can help with:\n"
            "- Product comparisons (e.g. 'Compare iPhone 13 and 14')\n"
            "- Price information (e.g. 'iPhone 13 price')\n"
            "- Recommendations (e.g. 'Best smartwatch under ₹15,000')")

# 2. AI Fallback with proper error handling
def query_ai(user_message):
    try:
        headers = {
            "Authorization": f"Bearer {app.config['HUGGINGFACE_API_KEY']}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "inputs": f"""<s>[INST] <<SYS>>
            You are an expert shopping assistant for Indian customers.
            Today is {datetime.date.today()}.
            Give concise, factual answers with prices in INR.
            <</SYS>>
            {user_message} [/INST]""",
            "parameters": {"max_new_tokens": 200}
        }
        
        response = requests.post(
            f"https://api-inference.huggingface.co/models/{app.config['AI_MODEL']}",
            headers=headers,
            json=payload,
            timeout=8  # 8 second timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            if isinstance(result, list):
                return result[0]['generated_text'].split('[/INST]')[-1].strip()
    
    except Exception as e:
        print(f"AI Error: {str(e)}")
    return None

# 3. The Final Endpoint
@app.route('/ai-assistant', methods=['POST', 'OPTIONS'])
def ai_assistant():
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add("Access-Control-Allow-Headers", "Content-Type")
        response.headers.add("Access-Control-Allow-Methods", "POST")
        return response

    data = request.get_json()
    user_message = data.get('message', '').strip()
    
    if not user_message:
        return jsonify({"error": "Empty message"}), 400

    # Step 1: Always try local response first
    local_response = get_local_response(user_message)
    if local_response:
        return jsonify({"response": local_response}), 200

    # Step 2: Only use AI if local response wasn't specific
    ai_response = query_ai(user_message)
    if ai_response:
        return jsonify({"response": ai_response}), 200

    # Step 3: Ultimate fallback (should never happen)
    return jsonify({
        "response": "Please ask about products or shopping help. For example:\n"
        "- 'Compare iPhone 13 and 14'\n"
        "- 'Best smartwatch under ₹15,000'"
    }), 200



@app.route('/login', methods=['POST'])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return make_response(jsonify({"success": False, "message": "Username and password required"}), 400)

    user = get_user_from_db(username)
    if user and check_password_hash(user.password, password):  
        token = pyjwt.encode(
            {"user": username, "exp": datetime.datetime.utcnow() + datetime.timedelta(hours=1)},
            app.secret_key, algorithm="HS256"
        )
        response = make_response(jsonify({"success": True, "message": "Login successful", "token": token}))
        response.headers.add("Access-Control-Allow-Origin", "http://localhost:5173")
        response.headers.add("Access-Control-Allow-Credentials", "true")
        return response

    return make_response(jsonify({"success": False, "message": "Invalid username or password"}), 401)


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return make_response(jsonify({"success": False, "message": "Username and password required"}), 400)

    try:
        add_user_to_db(username, password)
        response = make_response(jsonify({"success": True, "message": "User registered successfully"}), 201)
        response.headers.add("Access-Control-Allow-Origin", "http://localhost:5173")
        response.headers.add("Access-Control-Allow-Credentials", "true")
        return response
    except Exception as e:
        print(f"Error during registration: {e}")  
        response = make_response(jsonify({"success": False, "message": str(e)}), 500)
        response.headers.add("Access-Control-Allow-Origin", "http://localhost:5173")
        response.headers.add("Access-Control-Allow-Credentials", "true")
        return response



@app.route('/logout', methods=['POST'])
def logout():
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"success": False, "message": "Authorization token required"}), 401

    try:
        token = token.split(" ")[1]  
        decoded_token = pyjwt.decode(token, app.secret_key, algorithms=["HS256"])
        user_username = decoded_token["user"]
        
        user = User.query.filter_by(username=user_username).first()
        if not user:
            return jsonify({"success": False, "message": "User not found"}), 404

        # Delete all wishlist items for this user
        Wishlist.query.filter_by(user_id=user.id).delete()
        db.session.commit()

        return jsonify({
            "success": True,
            "message": "Logged out successfully and wishlist cleared"
        }), 200

    except pyjwt.ExpiredSignatureError:
        return jsonify({"success": False, "message": "Token has expired"}), 401
    except pyjwt.InvalidTokenError:
        return jsonify({"success": False, "message": "Invalid token"}), 401
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


def scrape_flipkart(product_name):
    flipkart_url = f'https://www.flipkart.com/search?q={product_name.replace(" ", "+")}'
    response = requests.get(flipkart_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    product_element = soup.find("a", class_="CGtC98") 
    if product_element:
        product_link = "https://www.flipkart.com" + product_element['href']
        price_element = product_element.find("div", class_="Nx9bqj _4b5DiR")
        price = price_element.text.strip() if price_element else "Price not found"

        image_element = product_element.find("img", class_="DByuf4")
        product_image = image_element['src'] if image_element else None

        desc_element = product_element.find("div", class_="KzDlHZ")
        product_desc = desc_element.text.strip() if desc_element else "Description not available"

        return {
            'price': price,
            'link': product_link,
            'image': product_image,
            'description': product_desc,
            'site': "Flipkart"
        }
    else:
        return None

def scrape_amazon(product_name):
    amazon_url = f'https://www.amazon.in/s?k={product_name.replace(" ", "+")}'
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")  
    driver = webdriver.Chrome(options=options)

    driver.get(amazon_url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    product_element = soup.select_one("div.s-main-slot div[data-component-type='s-search-result']")
    if product_element:
        product_link = "https://www.amazon.in" + product_element.find("a", class_="a-link-normal")['href']
        price_element = product_element.select_one(".a-price .a-offscreen")
        price = price_element.text.strip() if price_element else "Price not found"

        image_element = product_element.find("img", class_="s-image")
        product_image = image_element['src'] if image_element else None
        desc_element = product_element.select_one("h2.a-size-medium span")
        product_desc = desc_element.text.strip() if desc_element else "Description not available"

        driver.quit()
        return {
            'price': price,
            'link': product_link,
            'image': product_image,
            'description': product_desc,
            'site': 'Amazon'
        }
    else:
        driver.quit()
        return None

def scrape_myntra(product_name):
    myntra_url = f'https://www.myntra.com/{product_name.replace(" ", "-")}'
    response = requests.get(myntra_url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(response.content, 'html.parser')

    product_element = soup.find("li", class_="product-base")
    if product_element:
        product_link = product_element.find("a", href=True)['href']
        price_element = product_element.find("span", class_="product-discountedPrice")
        price = price_element.text.strip() if price_element else "Price not found"

        image_element = product_element.find("img", class_="img-responsive")
        product_image = image_element['src'] if image_element else None

        desc_element = product_element.find("h4", class_="product-product")
        product_desc = desc_element.text.strip() if desc_element else "Description not available"

        return {
            'price': price,
            'link': f"https://www.myntra.com/{product_link}",
            'image': product_image,
            'description': product_desc,
            'site': "Myntra"
        }
    return {}

def scrape_snapdeal(product_name):
    snapdeal_url = f'https://www.snapdeal.com/search?keyword={product_name.replace(" ", "+")}'
    response = requests.get(snapdeal_url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(response.content, 'html.parser')

    product_element = soup.find("div", class_="product-tuple-listing")
    if product_element:
        product_link = product_element.find("a", class_="dp-widget-link")['href']
        price_element = product_element.find("span", class_="product-price")
        price = price_element.text.strip() if price_element else "Price not found"

        image_element = product_element.find("img", class_="product-image")
        product_image = image_element['src'] if image_element else None

        desc_element = product_element.find("p", class_="product-title")
        product_desc = desc_element.text.strip() if desc_element else "Description not available"

        return {
            'price': price,
            'link': product_link,
            'image': product_image,
            'description': product_desc,
            'site': "Snapdeal"
        }
    return {}

def scrape_ajio(product_name):
    ajio_url = f'https://www.ajio.com/search/?text={product_name.replace(" ", "%20")}'
    response = requests.get(ajio_url, headers={'User-Agent': 'Mozilla/5.0'})
    soup = BeautifulSoup(response.content, 'html.parser')

    product_element = soup.find("div", class_="item")
    if product_element:
        product_link = product_element.find("a", class_="rilrtl-products-list__link")['href']
        price_element = product_element.find("span", class_="price")
        price = price_element.text.strip() if price_element else "Price not found"

        image_element = product_element.find("img", class_="rilrtl-lazy-img")
        product_image = image_element.get('data-src') or image_element.get('src')

        desc_element = product_element.find("div", class_="name")
        product_desc = desc_element.text.strip() if desc_element else "Description not available"

        return {
            'price': price,
            'link': f"https://www.ajio.com{product_link}",
            'image': product_image,
            'description': product_desc,
            'site': 'Ajio'
        }
    return {}

def scrape_jiomart(product_name):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537.3'}
    jiomart_url = f'https://www.jiomart.com/search/{product_name.replace(" ", "%20")}'
    response = requests.get(jiomart_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    product_element = soup.find("div", class_="jm-product-card")
    if product_element:
        product_link = "https://www.jiomart.com" + product_element.find("a")['href']
        price_element = product_element.find("span", class_="jm-body-xs-bold")
        price = price_element.text.strip() if price_element else "Price not found"
        
        image_element = product_element.find("img", class_="jm-product-card__img")
        product_image = image_element['data-src'] if image_element else None
        
        desc_element = product_element.find("div", class_="jm-body-xs")
        product_desc = desc_element.text.strip() if desc_element else "Description not available"

        return {
            'price': price,
            'link': product_link,
            'image': product_image,
            'description': product_desc,
            'site': "Jiomart"
        }
    return None

def scrape_ebay(product_name):
    ebay_url = f'https://www.ebay.com/sch/i.html?_nkw={product_name.replace(" ", "+")}'
    response = requests.get(ebay_url)
    soup = BeautifulSoup(response.content, 'html.parser')

    product_element = soup.find("li", class_="s-item s-item_pl-on-bottom")
    if product_element:
        product_link = product_element.find("a", class_="s-item__link")['href']
        price_element = product_element.find("span", class_="s-item__price")
        price = price_element.text.strip() if price_element else "Price not found"
        
        image_element = product_element.find("img", class_="s-item__image-img")
        product_image = image_element['src'] if image_element else None
        
        desc_element = product_element.find("div", class_="s-item__title")
        product_desc = desc_element.text.strip() if desc_element else "Description not available"

        return {
            'price': price,
            'link': product_link,
            'image': product_image,
            'description': product_desc,
            'site': "eBay"
        }
    return None

def scrape_nykaa(product_name):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
    nykaa_url = f'https://www.nykaa.com/search/result/?q={product_name.replace(" ", "%20")}'
    response = requests.get(nykaa_url, headers=headers)
    soup = BeautifulSoup(response.content, 'html.parser')

    product_element = soup.find("div", class_="css-1x6nwtu")
    if product_element:
        product_link = "https://www.nykaa.com" + product_element.find("a")['href']
        price_element = product_element.find("span", class_="css-111z9ua")
        price = price_element.text.strip() if price_element else "Price not found"
        
        image_element = product_element.find("img", class_="css-11gn9r6")
        product_image = image_element['src'] if image_element else None
        
        desc_element = product_element.find("div", class_="css-1f6x78p")
        product_desc = desc_element.text.strip() if desc_element else "Description not available"

        return {
            'price': price,
            'link': product_link,
            'image': product_image,
            'description': product_desc,
            'site': "Nykaa"
        }
    return None

def scrape_meesho(product_name):
    options = webdriver.ChromeOptions()
    options.add_argument("--headless")
    driver = webdriver.Chrome(options=options)
    
    meesho_url = f'https://www.meesho.com/search/{product_name.replace(" ", "-")}'
    driver.get(meesho_url)
    soup = BeautifulSoup(driver.page_source, 'html.parser')

    product_element = soup.find("div", class_="ProductList__GridCol-sc-8lnc5o-0")
    if product_element:
        product_link = "https://www.meesho.com" + product_element.find("a")['href']
        price_element = product_element.find("div", class_="Text__StyledText-sc-oo0kvp-0")
        price = price_element.text.strip() if price_element else "Price not found"
        
        image_element = product_element.find("img", class_="ProductImage__ProductImageContainer-sc-1617l5e-0")
        product_image = image_element['src'] if image_element else None
        
        desc_element = product_element.find("p", class_="Text__StyledText-sc-oo0kvp-0")
        product_desc = desc_element.text.strip() if desc_element else "Description not available"

        driver.quit()
        return {
            'price': price,
            'link': product_link,
            'image': product_image,
            'description': product_desc,
            'site': "Meesho"
        }
    driver.quit()
    return None

@app.route('/search', methods=['POST'])
# @login_required
def search_product():
    data = request.json
    product_name = data.get("product_name")

    if not product_name:
        return jsonify({"success": False, "message": "Product name required"}), 400

    flipkart_data = scrape_flipkart(product_name)
    amazon_data = scrape_amazon(product_name)
    myntra_data = scrape_myntra(product_name)
    snapdeal_data = scrape_snapdeal(product_name)
    ajio_data = scrape_ajio(product_name)
    jiomart_data = scrape_jiomart(product_name)
    ebay_data = scrape_ebay(product_name)
    meesho_data = scrape_meesho(product_name)
    nykaa_data = scrape_nykaa(product_name)

    results = []
    if flipkart_data:
        results.append(flipkart_data)
    if amazon_data:
        results.append(amazon_data)
    if myntra_data:
        results.append(myntra_data)
    if snapdeal_data:
        results.append(snapdeal_data)
    if ajio_data:
        results.append(ajio_data)
    if jiomart_data:
        results.append(jiomart_data)
    if ebay_data:
        results.append(ebay_data)
    if meesho_data:
        results.append(meesho_data)
    if nykaa_data:
        results.append(nykaa_data)

    return jsonify(results), 200



@app.route("/wishlist", methods=["POST"])
def add_to_wishlist():
    token = request.headers.get("Authorization")
    
    if not token:
        return jsonify({"message": "Token is missing"}), 401
    
    try:
        # Extracting the token
        token = token.split(" ")[1]  
        decoded_token = pyjwt.decode(token, app.secret_key, algorithms=["HS256"])
        user_username = decoded_token["user"]
        
        # Fetchin the user from the database
        user = User.query.filter_by(username=user_username).first()
        if not user:
            return jsonify({"message": "User not found"}), 404

        data = request.json
        print(f"Received data: {data}")
        if not all(key in data for key in ["price", "link", "image", "description", "site"]):
            return jsonify({"message": "Missing required fields"}), 400

        new_item = Wishlist(
            user_id=user.id,
            price=data["price"],
            link=data["link"],
            image=data["image"],
            description=data["description"],
            site=data["site"]
        )
        db.session.add(new_item)
        db.session.commit()

        return jsonify({"message": "Added to Wishlist"}), 201

    except pyjwt.ExpiredSignatureError:
        return jsonify({"message": "Token has expired"}), 401
    except pyjwt.InvalidTokenError:
        return jsonify({"message": "Invalid token"}), 401
    except Exception as e:
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500

# Get wishlist items
@app.route("/wishlist", methods=["GET"])
def get_wishlist():
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"message": "Token is missing"}), 401
    try:
        token = token.split(" ")[1]
        decoded_token = pyjwt.decode(token, app.secret_key, algorithms=["HS256"])
        user_username = decoded_token["user"]
        user = User.query.filter_by(username=user_username).first()
        if not user:
            return jsonify({"message": "User not found"}), 404
        wishlist_items = Wishlist.query.filter_by(user_id=user.id).all()
        return jsonify([{
            "id": item.id,
            "price": item.price,
            "link": item.link,
            "image": item.image,
            "description": item.description,
            "site": item.site
        } for item in wishlist_items])
    except Exception as e:
        return e
    
@app.route("/wishlist/<int:item_id>", methods=["DELETE"])
def delete_wishlist_item(item_id):
    token = request.headers.get("Authorization")
    if not token:
        return jsonify({"message": "Token is missing"}), 401
    
    try:
        # Verify the token and get user
        token = token.split(" ")[1]
        decoded_token = pyjwt.decode(token, app.secret_key, algorithms=["HS256"])
        user_username = decoded_token["user"]
        user = User.query.filter_by(username=user_username).first()
        if not user:
            return jsonify({"message": "User not found"}), 404

        # Find the item and verify it belongs to the user
        item = Wishlist.query.filter_by(id=item_id, user_id=user.id).first()
        if not item:
            return jsonify({"message": "Item not found or doesn't belong to user"}), 404

        # Delete the item
        db.session.delete(item)
        db.session.commit()

        return jsonify({"message": "Item removed from wishlist"}), 200

    except pyjwt.ExpiredSignatureError:
        return jsonify({"message": "Token has expired"}), 401
    except pyjwt.InvalidTokenError:
        return jsonify({"message": "Invalid token"}), 401
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"An error occurred: {str(e)}"}), 500

@celery.task
def check_price_changes():
    with app.app_context():
        wishlist_items = Wishlist.query.all()

        for item in wishlist_items:
            user = User.query.get(item.user_id)
            if not user:
                continue

            old_price = item.price
            updated_price = None
            if item.site == "Amazon":
                updated_data = scrape_amazon(item.description)
            elif item.site == "Flipkart":
                updated_data = scrape_flipkart(item.description)
            elif item.site == "Myntra":
                updated_data = scrape_myntra(item.description)
            elif item.site == "Snapdeal":
                updated_data = scrape_snapdeal(item.description)
            elif item.site == "Ajio":
                updated_data = scrape_ajio(item.description)
            elif item.site == "Jiomart":
                updated_data = scrape_jiomart(item.description)
            elif item.site == "eBay":
                updated_data = scrape_ebay(item.description)
            elif item.site == "Nykaa":
                updated_data = scrape_nykaa(item.description)
            elif item.site == "Meesho":
                updated_data = scrape_meesho(item.description)
            else:
                continue

            if updated_data and updated_data['price'] != old_price:
                # Store new price in history
                price_entry = PriceHistory(wishlist_id=item.id, price=updated_data['price'])
                db.session.add(price_entry)

                #update wishlist
                item.price = updated_data['price']
                db.session.commit()

                if is_price_dropped(item.id):
                    send_price_drop_email(user, item, old_price, updated_data['price'])


# Function to check if price has dropped
def is_price_dropped(wishlist_id):
    price_entries = PriceHistory.query.filter_by(wishlist_id=wishlist_id).order_by(PriceHistory.timestamp.desc()).limit(2).all()
    if len(price_entries) < 2:
        return False  # Not enough data to compare
    return float(price_entries[-1].price.replace("₹", "").replace(",", "")) < float(price_entries[-2].price.replace("₹", "").replace(",", ""))







if __name__ == '__main__':
    with app.app_context():  
        db.create_all()  
        print("Database initialized successfully!")
    app.run(debug=True)


