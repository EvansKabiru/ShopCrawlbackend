from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from models import db, User  # Import db and User from models.py
from werkzeug.security import generate_password_hash, check_password_hash
from flask_migrate import Migrate  # For database migrations
from flask_jwt_extended import JWTManager, create_access_token  # For JWT authentication
from flask_cors import CORS  # For handling CORS
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import secrets
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enabling CORS for cross-origin requests

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://shopcrawl_db_user:qk7uMKmeDME51DVdEEtXeirPE7uUFBqt@dpg-cv5vg2in91rc73b9a390-a.oregon-postgres.render.com/shopcrawl_db'  # Path to your database
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Disable modification tracking

# Initialize db with the app
db.init_app(app)

# Initialize migrations with the app and db
migrate = Migrate(app, db)

# JWT configuration
app.config["JWT_SECRET_KEY"] = "fghsgdgfdsgf"  # Secret key for JWT
app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=2)  # Set the expiration time for access tokens
jwt = JWTManager(app)  # Initialize JWTManager

# Google OAuth2 configuration
app.secret_key = secrets.token_hex(16)
app.config['GOOGLE_CLIENT_ID'] = '414872029170-3u2c5nboldvniesjmkgm0fhtc54a0mld.apps.googleusercontent.com'
app.config['GOOGLE_CLIENT_SECRET'] = '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'
app.config['GOOGLE_REDIRECT_URI'] = 'https://shopcrawlbackend-2.onrender.com/google_login/callback'

client_secrets_file = os.path.join(os.path.dirname(__file__), 'client_secret.json')

# ✅ Google Login Authorization Route
@app.route("/authorize_google")
def authorize_google():
    """Initiates Google OAuth login."""
    flow = Flow.from_client_secrets_file(
        client_secrets_file=client_secrets_file,
        scopes=[
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
            "openid"
        ],
        redirect_uri=app.config['GOOGLE_REDIRECT_URI']
    )
    
    authorization_url, state = flow.authorization_url()
    session["state"] = state
    return redirect(authorization_url)

@app.route("/google_login/callback", methods=['GET', 'POST'])
def google_callback():
    if request.method == "POST":
        # Handle POST request (from React frontend)
        data = request.get_json()
        token = data.get("token")
        
        try:
            # Validate the Google ID token
            id_info = id_token.verify_oauth2_token(token, google_requests.Request(), app.config['GOOGLE_CLIENT_ID'])
            
            # Check if the user exists in your database
            user = User.query.filter_by(email=id_info["email"]).first()
            if not user:
                # Create a new user
                user = User(
                    username=id_info["name"],
                    email=id_info["email"],
                    password=generate_password_hash(secrets.token_urlsafe(16))  # Random password
                )
                db.session.add(user)
                db.session.commit()

            # Generate a JWT token for the user
            access_token = create_access_token(identity=user.id)
            return jsonify({"message": "Login successful", "token": access_token})
        
        except ValueError:
            return jsonify({"message": "Invalid token"}), 400
    
    # Handle GET request (from Google OAuth2 redirect)
    flow = Flow.from_client_secrets_file(
        client_secrets_file=client_secrets_file,
        scopes=[
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
            "openid"
        ],
        redirect_uri=app.config['GOOGLE_REDIRECT_URI']
    )

    flow.fetch_token(authorization_response=request.url)
    credentials = flow.credentials
    session["credentials"] = credentials_to_dict(credentials)

    user_info = get_user_info(credentials)

    user = User.query.filter_by(email=user_info["email"]).first()
    if not user:
        # Generate random secure password
        hashed_password = generate_password_hash(secrets.token_urlsafe(16))

        user = User(
            name=user_info["name"], 
            email=user_info["email"], 
            password=hashed_password
        )
        db.session.add(user)
        db.session.commit()

    access_token = create_access_token(identity=user.id)
    return redirect(f"https://shop-crawlfront.vercel.app/login?token={access_token}")

def credentials_to_dict(credentials):
    """Converts credentials to a dictionary."""
    return {
        "token": credentials.token,
        "refresh_token": credentials.refresh_token,
        "token_uri": credentials.token_uri,
        "client_id": credentials.client_id,
        "client_secret": credentials.client_secret,
        "scopes": credentials.scopes
    }

def get_user_info(credentials):
    """Fetches user info from Google API."""
    service = build("oauth2", "v2", credentials=credentials)
    user_info = service.userinfo().get().execute()
    return {
        "email": user_info["email"],
        "name": user_info["name"],
        "picture": user_info["picture"]
    }

# Import and register blueprints (Ensure these views exist)
from views import auth_bp, product_bp, search_bp, user_bp, shop_bp, search_history_bp

# Register blueprints with the app
app.register_blueprint(auth_bp)
app.register_blueprint(product_bp)
app.register_blueprint(search_bp)
app.register_blueprint(user_bp)
app.register_blueprint(shop_bp)
app.register_blueprint(search_history_bp)

# Ensure the app runs only when executed directly
if __name__ == "__main__":
    app.run(debug=True)  # Start the Flask app in debug mode