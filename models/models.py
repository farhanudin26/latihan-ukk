from datetime import datetime
from . import db 
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)

    @property
    def is_active(self):
        return self.role != 'inactive'

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Float, nullable=False)
    stock = db.Column(db.Integer, nullable=False)
    image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    detail_sales = db.relationship('DetailSale', back_populates='product', lazy=True)

class Customer(db.Model):
    __tablename__ = 'customers'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    no_hp = db.Column(db.String(20), nullable=False)
    point = db.Column(db.Integer, nullable=False, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sales = db.relationship('Sale', back_populates='customer', lazy=True)

class Sale(db.Model):
    __tablename__ = 'saless'
    id = db.Column(db.Integer, primary_key=True)
    sale_date = db.Column(db.DateTime, nullable=False, default=db.func.current_timestamp())
    total_price = db.Column(db.Float, nullable=False, default=0)
    total_pay = db.Column(db.Float, nullable=False, default=0)
    total_return = db.Column(db.Float, nullable=False, default=0)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    point = db.Column(db.Integer, nullable=False, default=0)
    total_point = db.Column(db.Integer, nullable=False, default=0)

    user = db.relationship('User', backref='sales', lazy=True)    
    customer = db.relationship('Customer', back_populates='sales', lazy=True)
    detail_sales = db.relationship('DetailSale', back_populates='sale', lazy=True)

class DetailSale(db.Model):
    __tablename__ = 'detail_sales'
    id = db.Column(db.Integer, primary_key=True)
    sale_id = db.Column(db.Integer, db.ForeignKey('saless.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    amount = db.Column(db.Integer, nullable=False)
    subtotal = db.Column(db.Float, nullable=False)

    sale = db.relationship('Sale', back_populates='detail_sales')
    product = db.relationship('Product', back_populates='detail_sales')
