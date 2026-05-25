import mailbox
from flask import Flask, jsonify, render_template, request
from flask_mail import Mail, Message
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv
import os
import datetime  
from site import USER_BASE, USER_SITE
import sqlite3
import stripe
import json
from werkzeug.security import generate_password_hash
from email_validator import validate_email
current_date = datetime.date.today()
current_time = datetime.datetime.now().time()
from cs50 import SQL
from flask import Flask, flash, redirect, render_template, request, session, url_for
from flask_session import Session
from flask import Flask, jsonify, session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import  login_required
  

load_dotenv('sendgrid.env')
load_dotenv('.env', override=True)  # .env wins over old shell exports

# Configure application
app = Flask(__name__, static_folder='static')

# Stripe (set in .env — get fresh keys from https://dashboard.stripe.com/test/apikeys)
app.config['STRIPE_PUBLIC_KEY'] = os.environ.get('STRIPE_PUBLIC_KEY', '')
app.config['STRIPE_SECRET_KEY'] = os.environ.get('STRIPE_SECRET_KEY', '')
stripe.api_key = app.config['STRIPE_SECRET_KEY']

if app.config['STRIPE_SECRET_KEY']:
    print(f"Stripe: secret key loaded (...{app.config['STRIPE_SECRET_KEY'][-6:]})")
else:
    print("Stripe: NOT configured — create .env with STRIPE_SECRET_KEY (see .env.example)")

# Configure session to use filesystem (instead of signed cookies)
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)
endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')
#configure the contact 
app.config['MAIL_SERVER'] = 'smtp.sendgrid.net'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'apikey'  # Use 'apikey' as the username 
app.config['MAIL_PASSWORD'] = os.environ.get('SENDGRID_API_KEY')
mail = Mail(app)

# Configure CS50 Library to use SQLite database
db = SQL("sqlite:///users.db")
#list of users
user_ids = []  

@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response

YOUR_DOMAIN = 'http://127.0.0.1:5000'

# Price ID Mapping
product_prices = {
    'prod_Phru0KZd1aXRym': 'price_1OsSAvH4R8xQsOnyobXRYsIa',  
    'prod_PhrsHtNYVoIl8W': 'price_1OsS8JH4R8xQsOnyBa41KNFc',  
    'prod_PhrB2pu1PXwoee': 'price_1OsRSpH4R8xQsOnyjQTFaJZw'  
}

def get_db_connection():
    conn = sqlite3.connect('users.db')  # Adjust if your database name is different
    conn.row_factory = sqlite3.Row
    return conn

def get_cart_items(user_id):
    with get_db_connection() as conn:
        return conn.execute(
            "SELECT product_id, product_name, price, quantity FROM cart WHERE user_id = ?",
            (user_id,),
        ).fetchall()


def build_checkout_line_items(cart_items):
    """Build Stripe Checkout line items from cart prices (works with any Stripe account)."""
    line_items = []
    for item in cart_items:
        quantity = int(item["quantity"])
        unit_price = float(str(item["price"]).replace("£", "").strip())
        line_items.append({
            "price_data": {
                "currency": "gbp",
                "product_data": {"name": item["product_name"]},
                "unit_amount": int(round(unit_price * 100)),
            },
            "quantity": quantity,
        })
    return line_items


@app.route('/webhook', methods=['POST'])
def webhook():
    event = None
    payload = request.data
    sig_header = request.headers['STRIPE_SIGNATURE']

    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, endpoint_secret
        )
    except ValueError as e:
        # Invalid payload
        raise e
    except stripe.error.SignatureVerificationError as e:
        # Invalid signature
        raise e

    # Handle the event
    if event['type'] == 'payment_intent.succeeded':
      payment_intent = event['data']['object']
    # ... handle other event types
    else:
      print('Unhandled event type {}'.format(event['type']))

    return jsonify(success=True)
@app.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    load_dotenv('.env', override=True)
    app.config['STRIPE_SECRET_KEY'] = os.environ.get('STRIPE_SECRET_KEY', '')
    app.config['STRIPE_PUBLIC_KEY'] = os.environ.get('STRIPE_PUBLIC_KEY', '')

    if not app.config['STRIPE_SECRET_KEY']:
        flash("Stripe is not configured. Add STRIPE_SECRET_KEY to your .env file.", "danger")
        return redirect(url_for("cart"))

    stripe.api_key = app.config['STRIPE_SECRET_KEY']

    user_id = session.get("user_id")
    cart_items = get_cart_items(user_id)

    if not cart_items:
        flash("Your cart is empty.", "danger")
        return redirect(url_for("cart"))

    line_items = build_checkout_line_items(cart_items)

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="payment",
            line_items=line_items,
            success_url=f"{YOUR_DOMAIN}/success",
            cancel_url=f"{YOUR_DOMAIN}/cancel",
        )
        return redirect(checkout_session.url)

    except stripe.error.AuthenticationError as e:
        if getattr(e, "code", None) == "api_key_expired" or "Expired API Key" in str(e):
            flash(
                "Your Stripe secret key has expired. Create a new test key at "
                "https://dashboard.stripe.com/test/apikeys, add it to a .env file, "
                "then stop and restart the Flask server.",
                "danger",
            )
        else:
            flash(f"Stripe authentication error: {e}", "danger")
        return redirect(url_for("cart"))
    except stripe.error.StripeError as e:
        flash(f"Payment error: {e}", "danger")
        return redirect(url_for("cart"))


@app.route('/success')
def success():
    return render_template('success.html')


@app.route('/cancel')
def cancel():
    return render_template('cancel.html')

@app.route("/")
def home():
    """Show portfolio of stocks"""
    user_id = session.get("user_id")
    if user_id:
        user = db.execute("SELECT email FROM users WHERE id = ?", user_id)

        if len(user) == 0:
            # Handle the case where the user ID does not exist in the database
            flash("User not found", "danger")
        email = user[0].get("email", "Default Email")

        # ... rest of your logic to fetch the portfolio and render 'home.html' ...
    else:
        # Handle the case where the user is not logged in
        email = "Default Email"

    return render_template("home.html", email=email)

@app.route("/cart")
@login_required
def cart():
    user_id = session.get("user_id")
    total_sum = 0  # Initialize the total price to 0
    products = db.execute(
        "SELECT product_id, price, product_name, size, color, quantity FROM cart WHERE user_id = ?",
        user_id
    )

    for product in products:
        price = str(product["price"]).replace("£", "")  # Remove the currency symbol
        quantity = product["quantity"]
        subtotal = float(price) * quantity  # Calculate the subtotal for each product
        product["subtotal"] = subtotal  # Add the subtotal to the product dictionary
        total_sum += subtotal  # Add the subtotal to the total_sum
    
    
    return render_template(
        "cart.html",
        checkout_total=total_sum,
        products=products
    )

@app.route("/aboutus")
@login_required
def aboutus():

    return render_template("aboutus.html")


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':    
        # Get the form data
        firstname = request.form.get('firstname')
        lastname = request.form.get('lastname') 
        email = request.form.get('email')
        description = request.form.get('description')
        if not firstname or not lastname or not email or not description:
            flash("fill the inputs!","danger")
            return render_template("contact.html")
        else:
        # Send the email
             send_contact_email(firstname, lastname, email, description)  

        # Return a response or render a template
        flash("Thank you for contacting us!")
        return render_template("contact.html")

    else:  # GET request
        return render_template('contact.html')

# Send email function (outside the route)
def send_contact_email(firstname, lastname, email, message):
    message = Mail(
        from_email='selhabyaakoub55@gmail.com',  # Replace with your verified sender email
        to_emails='another_recipient@example.com', 
        subject='Contact Form Submission',
        html_content=f'<strong>FirstName:</strong> {firstname}<br><strong>LastName:</strong> {lastname}<br><strong>Email:</strong> {email}<br><strong>Message:</strong> {message}'
    )
    try:
        sg = SendGridAPIClient(app.config['MAIL_PASSWORD'])  
        response = sg.send(message)
        print(response.status_code)  # Check for success (e.g., 202)
    except Exception as e:
        print(e)  
    
 
@app.route("/shop")
def shop():
    user_id = session.get("user_id")
    if user_id:
        user = db.execute("SELECT email FROM users WHERE id = ?", user_id)

        if len(user) == 0:
            # Handle the case where the user ID does not exist in the database
            flash("User not found", "danger")
        email = user[0].get("email", "Default Email")

        # ... rest of your logic to fetch the portfolio and render 'home.html' ...
    else:
        # Handle the case where the user is not logged in
        email = "Default Email"

    return render_template("shop.html", email=email)

@app.route('/shoping1')
def shoping1():
    # Retrieve the product data from the database or any other source
    product = {
        'id': 'prod_PhrB2pu1PXwoee',
        'name': 'SIGNATURE HOODIE',
        'description': '80% cotton 20% polyester, 250gsm',
        'price': 49.99,
        'image': 'static/product1_white.png',
        'category': 'Clothing',
        'stock': 50
    }

    # Pass the product data to the template
    return render_template("shoping1.html", product=product)


@app.route('/shoping2')
def shoping2():
    # Retrieve the product data from the database or any other source
    product = {
        'id': 'prod_PhrsHtNYVoIl8W',
        'name': 'SIGNATURE SWEATSHIRT',
        'description': '80% cotton 20% polyester, 250gsm',
        'price': 49.99,
        'image': 'static/product3_white.png',
        'category': 'Clothing',
        'stock': 50
    }

    # Pass the product data to the template
    return render_template("shoping2.html", product=product)


@app.route('/shoping3')
def shoping3():
    # Retrieve the product data from the database or any other source
    product = {
        'id': 'prod_Phru0KZd1aXRym',
        'name': 'SIGNATURE T-SHIRT',
        'description': '80% cotton 20% polyester, 250gsm',
        'price': 29.99,
        'image': 'static/product2_white.png',
        'category': 'Clothing',
        'stock': 50
    }

    # Pass the product data to the template
    return render_template("shoping3.html", product=product)

@app.route('/addtocart', methods=['POST'])
def add_to_cart():
    # Get the form data
    product_name = request.form.get('product_name')
    product_id = request.form.get('product_id')
    price = request.form.get('product_price')
    color = request.form.get('color')
    size = request.form.get('size') 
    quantity = request.form.get('quantity')
    if not color:
        flash("Please select a color.", "danger")  
        return redirect(url_for('cart'))  # Redirect to the cart page
    if not size:
        flash("Please choose a size", "danger")
        return redirect(url_for('cart'))  # Redirect to the cart page
    if not quantity:
        flash("Please choose quantity", "danger")
        return redirect(url_for('cart'))  # Redirect to the cart page
       
    # Insert the form data into the cart table
    user_id = session.get("user_id")
    if user_id:
        db.execute(
            "INSERT INTO cart (user_id, product_id, product_name, price, size, color, quantity) VALUES (:user_id, :product_id, :product_name, :price, :size, :color, :quantity)",
            user_id=user_id, product_id=product_id, product_name=product_name, price=price, color=color, size=size, quantity=quantity
        ) 
        # Commit the changes to the database
        flash("Added to Cart", "success")
        return redirect(url_for('cart'))  # Redirect to the cart page
        
    else:
        flash("Error occurred during adding to cart", "failed")
        return redirect(url_for('cart'))  # Redirect to the cart page
    

@app.route('/remove-from-cart', methods=['POST'])
@login_required
def remove_from_cart():
    user_id = session.get("user_id")
    if user_id:
        product_id = request.form.get('product_id')
        size = request.form.get('size')
        color = request.form.get('color')
        quantity = request.form.get('quantity')

        if product_id and size and color and quantity:
            product_id = product_id
            quantity = int(quantity)

            # Code to remove the product from the cart goes here
            conn = sqlite3.connect('users.db')
            cursor = conn.cursor()

            cursor.execute(
                "DELETE FROM cart WHERE user_id = ? AND product_id = ? AND size = ? AND color = ? AND quantity = ?",
                (user_id, product_id, size, color, quantity)
            )

            conn.commit()
            conn.close()

            # Redirect back to the shopping cart page
            flash("Removed from Cart", "success")
            return redirect('/cart')

    # Handle the case when any of the required parameters are missing
    return "Invalid request"
@app.route("/login", methods=["GET", "POST"])
def login():
    """Log user in"""

    # Forget any user_id
    if "user_id" in session:  # Check if a user is already logged in
        session.clear()

    # User reached route via POST (as by submitting a form via POST)
    if request.method == "POST":
        # Ensure username was submitted
        if not request.form.get("email"):
            flash("must rovide your email!", "danger")
            return redirect("/login")
        # Ensure password was submitted
        elif not request.form.get("password"):
            flash("must provide password", "danger")
            return redirect("/login")
        # Query database for username
        rows = db.execute(
            "SELECT * FROM users WHERE email = ?", request.form.get("email")
        )

        # Ensure username exists and password is correct
        if len(rows) != 1 or not check_password_hash(
            rows[0]["hash"], request.form.get("password")
        ):
            flash("invalid email and/or password", "danger")
            return redirect("/register")
        # Remember which user has logged in
        session["user_id"] = rows[0]["id"]

        # Redirect user to home page
        return redirect("/")

    # User reached route via GET (as by clicking a link or via redirect)
    else:
        return render_template("login.html")


@app.route("/logout")
def logout():
    """Log user out"""

    # Forget any user_id
    session.clear()

    # Redirect user to login form
    return redirect("/")



@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        password = request.form.get("password")
        confirmation = request.form.get("confirmation")
        email = request.form.get("email")
        firstname = request.form.get("firstname")
        lastname = request.form.get("lastname")
        hash = generate_password_hash(password)

        # Server-side validation
        if not password or not email or not firstname or not lastname or not confirmation:
            flash("Please fill in all the required fields", "danger")
            return redirect("/register")
        if password != confirmation:
            flash("Password inputs did not match", "danger")
            return redirect("/register")
        if not validate_email(email):
            flash("Invalid email address", "danger")
            return redirect(url_for("register"))
        try:
            db.execute(
                "INSERT INTO users (email, firstname, lastname, hash) VALUES (:email, :firstname, :lastname, :hash)",
                email=email, firstname=firstname, lastname=lastname, hash=hash
            )
             # Commit the changes to the database
            flash("You are registered and can now login", "success")
            return redirect(url_for('login'))

        except Exception as e:
        # Delete the partially inserted record in case of errors 
            db.execute("DELETE FROM users WHERE email = :email", email=email) 
            flash(f"Registration failed. Error: {e}", "danger")
            return redirect("/register") 
    else:
        return render_template('signup.html')


@app.route("/account", methods=["GET", "POST"])
@login_required
def account():
    if request.method == "GET":
        user_id = session.get("user_id")
        firstname = db.execute(
            "SELECT firstname FROM users WHERE id = ?",
            (user_id,)
        )
        lastname = db.execute(
            "SELECT lastname FROM users WHERE id = ?",
            (user_id,)
        )
        email = db.execute(
            "SELECT email FROM users WHERE id = ?",
            (user_id,)
        )
        
        firstname = firstname[0]['firstname'] if firstname else None
        lastname = lastname[0]['lastname'] if lastname else None
        email = email[0]['email'] if email else None

        return render_template("myaccount.html", firstname=firstname, lastname=lastname, email=email)
    else:
        conn = sqlite3.connect("users.db")
        cursor = conn.cursor()

        user_id = session.get("user_id")

        country = request.form['country']
        city = request.form['city']
        zipcode = request.form['zipcode']
        address = request.form['address']
 

        # Check if shipping information already exists for the user
        cursor.execute("SELECT * FROM shipping WHERE user_id = ?", (user_id,))
        existing_data = cursor.fetchall()

        if existing_data:  # If data exists, update
            cursor.execute(
                "UPDATE shipping SET country=?, city=?, zipcode=?, address=? WHERE user_id=?",
                (country, city, zipcode, address, user_id),
            )
        else:  # Otherwise, insert
            cursor.execute(
                "INSERT INTO shipping (user_id, country, city, zipcode, address) VALUES (?, ?, ?, ?, ?)",
                (user_id, country, city, zipcode, address),
            )

        conn.commit()  # Commit the changes to the database
        conn.close()  # Close the database connection

        flash("Shipping address updated successfully", "success")
        return render_template("myaccount.html")
