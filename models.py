from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    phone_number = db.Column(db.String(20), unique=True, nullable=True)
    password_hash = db.Column(db.String(128), nullable=True)  # Allow null for Google users
    profile_picture = db.Column(db.String(256), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)
    provider = db.Column(db.String(50), default="email")  # Default to "email", allow "google"

    
    search_history = db.relationship('SearchHistory', backref='user', lazy=True)
    tokens = db.relationship('AuthToken', back_populates='user', lazy=True)


class SearchHistory(db.Model):
    __tablename__ = 'search_history'
    id = db.Column(db.Integer, primary_key=True)
    search_query = db.Column(db.String(255), nullable=False)
    search_date = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    product_name = db.Column(db.String(100))
    product_price = db.Column(db.Float)
    product_rating = db.Column(db.Float)
    product_url = db.Column(db.String(255))
    delivery_cost = db.Column(db.Float)
    shop_name = db.Column(db.String(100))
    payment_mode = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    navigate_link = db.Column(db.String(255))  # New field for the navigation link

    shop_id = db.Column(db.Integer, db.ForeignKey('shops.id', name='fk_product_shop'), nullable=False)  # Specify constraint name
    comparisons = db.relationship('ComparisonResult', backref='product', lazy=True)
    
    # Change backref to avoid conflict with the existing 'products' in the Shop model
    shop = db.relationship('Shop', backref='shop_products')

class ProductSearch(db.Model):
    __tablename__ = 'product_searches'
    id = db.Column(db.Integer, primary_key=True)
    search_query = db.Column(db.String(255), nullable=False)
    query_results = db.Column(db.JSON, nullable=False)  
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


class AuthToken(db.Model):
    __tablename__ = 'auth_tokens'
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(512), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
   
    user = db.relationship('User', back_populates='tokens', lazy=True)


class PriceHistory(db.Model):
    __tablename__ = 'price_history'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    price = db.Column(db.Float, nullable=False)
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    product = db.relationship('Product', backref='price_history')


class ComparisonResult(db.Model):
    __tablename__ = 'comparison_results'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id', name='fk_comparison_product'), nullable=False)
    shop_x_id = db.Column(db.Integer, db.ForeignKey('shops.id', name='fk_comparison_shop_x'), nullable=False)
    shop_y_id = db.Column(db.Integer, db.ForeignKey('shops.id', name='fk_comparison_shop_y'), nullable=False)
    
    product_name = db.Column(db.String, nullable=False)
    shop_x_cost = db.Column(db.Float, nullable=False)
    shop_x_rating = db.Column(db.Float)
    shop_x_delivery_cost = db.Column(db.Float, nullable=False)
    shop_x_payment_mode = db.Column(db.String)
    
    shop_y_cost = db.Column(db.Float, nullable=False)
    shop_y_rating = db.Column(db.Float)
    shop_y_delivery_cost = db.Column(db.Float, nullable=False)
    shop_y_payment_mode = db.Column(db.String)
    
    marginal_benefit = db.Column(db.Float)
    cost_benefit = db.Column(db.Float)
    
    # Relationships with foreign_keys argument to specify which columns are used for the join
    shop_x = db.relationship('Shop', foreign_keys=[shop_x_id], backref=db.backref('comparison_shop_x', lazy=True), lazy=True)
    shop_y = db.relationship('Shop', foreign_keys=[shop_y_id], backref=db.backref('comparison_shop_y', lazy=True), lazy=True)

class Shop(db.Model):
    __tablename__ = 'shops'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String, nullable=False)
    url = db.Column(db.String, nullable=False)

    # Relationships to avoid conflict with backref names
    comparisons_x = db.relationship('ComparisonResult', foreign_keys='ComparisonResult.shop_x_id', backref='shop_x_comparison', lazy=True)
    comparisons_y = db.relationship('ComparisonResult', foreign_keys='ComparisonResult.shop_y_id', backref='shop_y_comparison', lazy=True)
