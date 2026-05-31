import os
import datetime
import stripe

from flask import Flask, flash, jsonify, redirect, render_template, request, session, url_for
from flask_session import Session
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail as SendGridMail
from dotenv import load_dotenv
from werkzeug.security import check_password_hash, generate_password_hash
from email_validator import validate_email, EmailNotValidError
from helpers import login_required

load_dotenv('.env', override=True)

app = Flask(__name__, static_folder='static')

# Database
database_url = os.environ.get('DATABASE_URL', 'sqlite:///users.db')
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# Session
app.config['SECRET_KEY'] = os.environ.get('SESSION_SECRET', 'fallback-dev-secret')
app.config['SESSION_PERMANENT'] = False
app.config['SESSION_TYPE'] = 'filesystem'
Session(app)

# Stripe
app.config['STRIPE_PUBLIC_KEY'] = os.environ.get('STRIPE_PUBLIC_KEY', '')
app.config['STRIPE_SECRET_KEY'] = os.environ.get('STRIPE_SECRET_KEY', '')
stripe.api_key = app.config['STRIPE_SECRET_KEY']
endpoint_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

# Mail
app.config['MAIL_SERVER'] = 'smtp.sendgrid.net'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'apikey'
app.config['MAIL_PASSWORD'] = os.environ.get('SENDGRID_API_KEY')
mail = Mail(app)

YOUR_DOMAIN = os.environ.get('YOUR_DOMAIN', 'http://127.0.0.1:5000')

# Models
class User(db.Model):
    __tablename__ = 'users'
    id        = db.Column(db.Integer, primary_key=True)
    email     = db.Column(db.String(255), unique=True, nullable=False)
    firstname = db.Column(db.String(100), nullable=False)
    lastname  = db.Column(db.String(100), nullable=False)
    hash      = db.Column(db.String(255), nullable=False)
    cart      = db.relationship('Cart', backref='user', lazy=True)
    shipping  = db.relationship('Shipping', backref='user', lazy=True)


class Cart(db.Model):
    __tablename__ = 'cart'
    id           = db.Column(db.Integer, primary_key=True)
    user_id      = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    product_id   = db.Column(db.String(100))
    product_name = db.Column(db.String(200))
    price        = db.Column(db.String(50))
    size         = db.Column(db.String(50))
    color        = db.Column(db.String(50))
    quantity     = db.Column(db.Integer)


class Shipping(db.Model):
    __tablename__ = 'shipping'
    id      = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    country = db.Column(db.String(100))
    city    = db.Column(db.String(100))
    zipcode = db.Column(db.String(20))
    address = db.Column(db.String(255))


with app.app_context():
    db.create_all()


def build_checkout_line_items(cart_items):
    line_items = []
    for item in cart_items:
        quantity = int(item.quantity)
        unit_price = float(str(item.price).replace('£', '').strip())
        line_items.append({
            'price_data': {
                'currency': 'gbp',
                'product_data': {'name': item.product_name},
                'unit_amount': int(round(unit_price * 100)),
            },
            'quantity': quantity,
        })
    return line_items


@app.after_request
def after_request(response):
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Expires'] = 0
    response.headers['Pragma'] = 'no-cache'
    return response


@app.route('/')
def home():
    user_id = session.get('user_id')
    email = 'Default Email'
    if user_id:
        user = User.query.get(user_id)
        if not user:
            flash('User not found', 'danger')
        else:
            email = user.email
    return render_template('home.html', email=email)


@app.route('/shop')
def shop():
    user_id = session.get('user_id')
    email = 'Default Email'
    if user_id:
        user = User.query.get(user_id)
        if user:
            email = user.email
    return render_template('shop.html', email=email)


@app.route('/shoping1')
def shoping1():
    product = {'id': 'prod_PhrB2pu1PXwoee', 'name': 'SIGNATURE HOODIE',
               'description': '80% cotton 20% polyester, 250gsm',
               'price': 49.99, 'image': 'static/product1_white.png',
               'category': 'Clothing', 'stock': 50}
    return render_template('shoping1.html', product=product)


@app.route('/shoping2')
def shoping2():
    product = {'id': 'prod_PhrsHtNYVoIl8W', 'name': 'SIGNATURE SWEATSHIRT',
               'description': '80% cotton 20% polyester, 250gsm',
               'price': 49.99, 'image': 'static/product3_white.png',
               'category': 'Clothing', 'stock': 50}
    return render_template('shoping2.html', product=product)


@app.route('/shoping3')
def shoping3():
    product = {'id': 'prod_Phru0KZd1aXRym', 'name': 'SIGNATURE T-SHIRT',
               'description': '80% cotton 20% polyester, 250gsm',
               'price': 29.99, 'image': 'static/product2_white.png',
               'category': 'Clothing', 'stock': 50}
    return render_template('shoping3.html', product=product)


@app.route('/cart')
@login_required
def cart():
    user_id = session.get('user_id')
    products = Cart.query.filter_by(user_id=user_id).all()
    total_sum = 0
    items = []
    for item in products:
        price = float(str(item.price).replace('£', '').strip())
        subtotal = price * item.quantity
        total_sum += subtotal
        items.append({
            'product_id':   item.product_id,
            'product_name': item.product_name,
            'price':        item.price,
            'size':         item.size,
            'color':        item.color,
            'quantity':     item.quantity,
            'subtotal':     subtotal,
        })
    return render_template('cart.html', products=items, checkout_total=total_sum)


@app.route('/addtocart', methods=['POST'])
def add_to_cart():
    product_name = request.form.get('product_name')
    product_id   = request.form.get('product_id')
    price        = request.form.get('product_price')
    color        = request.form.get('color')
    size         = request.form.get('size')
    quantity     = request.form.get('quantity')

    if not color:
        flash('Please select a color.', 'danger')
        return redirect(url_for('cart'))
    if not size:
        flash('Please choose a size', 'danger')
        return redirect(url_for('cart'))
    if not quantity:
        flash('Please choose quantity', 'danger')
        return redirect(url_for('cart'))

    user_id = session.get('user_id')
    if user_id:
        item = Cart(user_id=user_id, product_id=product_id,
                    product_name=product_name, price=price,
                    size=size, color=color, quantity=int(quantity))
        db.session.add(item)
        db.session.commit()
        flash('Added to Cart', 'success')
    else:
        flash('Please log in to add items to cart', 'danger')
    return redirect(url_for('cart'))


@app.route('/remove-from-cart', methods=['POST'])
@login_required
def remove_from_cart():
    user_id    = session.get('user_id')
    product_id = request.form.get('product_id')
    size       = request.form.get('size')
    color      = request.form.get('color')
    quantity   = request.form.get('quantity')

    if product_id and size and color and quantity:
        Cart.query.filter_by(
            user_id=user_id, product_id=product_id,
            size=size, color=color, quantity=int(quantity)
        ).delete()
        db.session.commit()
        flash('Removed from Cart', 'success')
        return redirect('/cart')
    return 'Invalid request', 400


@app.route('/login', methods=['GET', 'POST'])
def login():
    if 'user_id' in session:
        session.clear()
    if request.method == 'POST':
        email    = request.form.get('email')
        password = request.form.get('password')
        if not email:
            flash('Must provide your email!', 'danger')
            return redirect('/login')
        if not password:
            flash('Must provide password', 'danger')
            return redirect('/login')
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.hash, password):
            flash('Invalid email and/or password', 'danger')
            return redirect('/register')
        session['user_id'] = user.id
        return redirect('/')
    return render_template('login.html')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email        = request.form.get('email')
        firstname    = request.form.get('firstname')
        lastname     = request.form.get('lastname')
        password     = request.form.get('password')
        confirmation = request.form.get('confirmation')

        if not all([email, firstname, lastname, password, confirmation]):
            flash('Please fill in all the required fields', 'danger')
            return redirect('/register')
        if password != confirmation:
            flash('Password inputs did not match', 'danger')
            return redirect('/register')
        try:
            validate_email(email)
        except EmailNotValidError:
            flash('Invalid email address', 'danger')
            return redirect('/register')
        if User.query.filter_by(email=email).first():
            flash('Email already registered', 'danger')
            return redirect('/register')
        try:
            user = User(email=email, firstname=firstname,
                        lastname=lastname, hash=generate_password_hash(password))
            db.session.add(user)
            db.session.commit()
            flash('You are registered and can now login', 'success')
            return redirect(url_for('login'))
        except Exception as e:
            db.session.rollback()
            flash(f'Registration failed. Error: {e}', 'danger')
            return redirect('/register')
    return render_template('signup.html')


@app.route('/account', methods=['GET', 'POST'])
@login_required
def account():
    user_id = session.get('user_id')
    user    = User.query.get(user_id)
    if request.method == 'GET':
        return render_template('myaccount.html',
                               firstname=user.firstname,
                               lastname=user.lastname,
                               email=user.email)
    country = request.form.get('country')
    city    = request.form.get('city')
    zipcode = request.form.get('zipcode')
    address = request.form.get('address')

    shipping = Shipping.query.filter_by(user_id=user_id).first()
    if shipping:
        shipping.country = country
        shipping.city    = city
        shipping.zipcode = zipcode
        shipping.address = address
    else:
        shipping = Shipping(user_id=user_id, country=country,
                            city=city, zipcode=zipcode, address=address)
        db.session.add(shipping)
    db.session.commit()
    flash('Shipping address updated successfully', 'success')
    return render_template('myaccount.html',
                           firstname=user.firstname,
                           lastname=user.lastname,
                           email=user.email)


@app.route('/aboutus')
@login_required
def aboutus():
    return render_template('aboutus.html')


@app.route('/contact', methods=['GET', 'POST'])
def contact():
    if request.method == 'POST':
        firstname   = request.form.get('firstname')
        lastname    = request.form.get('lastname')
        email       = request.form.get('email')
        description = request.form.get('description')
        if not all([firstname, lastname, email, description]):
            flash('Fill in all inputs!', 'danger')
            return render_template('contact.html')
        send_contact_email(firstname, lastname, email, description)
        flash('Thank you for contacting us!')
        return render_template('contact.html')
    return render_template('contact.html')


def send_contact_email(firstname, lastname, email, message):
    msg = SendGridMail(
        from_email='selhabyaakoub55@gmail.com',
        to_emails='selhabyaakoub55@gmail.com',
        subject='Contact Form Submission',
        html_content=(f'<strong>FirstName:</strong> {firstname}<br>'
                      f'<strong>LastName:</strong> {lastname}<br>'
                      f'<strong>Email:</strong> {email}<br>'
                      f'<strong>Message:</strong> {message}')
    )
    try:
        sg = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        sg.send(msg)
    except Exception as e:
        print(e)


@app.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    user_id    = session.get('user_id')
    cart_items = Cart.query.filter_by(user_id=user_id).all()
    if not cart_items:
        flash('Your cart is empty.', 'danger')
        return redirect(url_for('cart'))
    line_items = build_checkout_line_items(cart_items)
    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            mode='payment',
            line_items=line_items,
            success_url=f'{YOUR_DOMAIN}/success',
            cancel_url=f'{YOUR_DOMAIN}/cancel',
        )
        return redirect(checkout_session.url)
    except stripe.error.AuthenticationError as e:
        flash(f'Stripe authentication error: {e}', 'danger')
        return redirect(url_for('cart'))
    except stripe.error.StripeError as e:
        flash(f'Payment error: {e}', 'danger')
        return redirect(url_for('cart'))


@app.route('/webhook', methods=['POST'])
def webhook():
    payload    = request.data
    sig_header = request.headers.get('STRIPE_SIGNATURE')
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, endpoint_secret)
    except (ValueError, stripe.error.SignatureVerificationError) as e:
        return str(e), 400
    if event['type'] == 'payment_intent.succeeded':
        print('Payment succeeded:', event['data']['object'])
    return jsonify(success=True)


@app.route('/success')
def success():
    return render_template('success.html')


@app.route('/cancel')
def cancel():
    return render_template('cancel.html')