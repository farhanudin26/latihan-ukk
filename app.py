from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_bcrypt import Bcrypt
from flask_session import Session
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from config import Config
from models import db  # Import hanya db
from babel.numbers import format_currency
from datetime import date

# Inisialisasi Flask
app = Flask(__name__)
app.config.from_object(Config)

# Inisialisasi extensions
db.init_app(app)
bcrypt = Bcrypt(app)

# Session
app.config["SESSION_TYPE"] = "filesystem"
app.config["SESSION_PERMANENT"] = False
Session(app)

# Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Import model SETELAH db.init_app(app)
from models.models import User, Product
from routes.api import api_bp

app.register_blueprint(api_bp, url_prefix='/api')

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Route untuk login
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        name = request.form['name']
        password = request.form['password']
        user = User.query.filter_by(name=name).first()

        if user and bcrypt.check_password_hash(user.password, password):
            login_user(user)
            session['role'] = user.role
            return redirect(url_for('dashboard'))
        else:
            flash("Nama atau Password salah!", "error")
            return redirect(url_for('login'))

    return render_template('login.html')

# Filter untuk format mata uang IDR
@app.template_filter('currency')
def format_currency_filter(value, currency='IDR'):
    return format_currency(value, currency, locale='id_ID')

# Route untuk dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    current_date = date.today().strftime('%d %B %Y')
    products = Product.query.all() if current_user.role == 'employee' else []

    return render_template(
        'dashboard.html',
        current_date=current_date,
        products=products
    )

# Route untuk logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
