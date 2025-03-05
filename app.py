from flask import Flask, session, redirect, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from datetime import timedelta
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager, create_access_token
from flask_cors import CORS
from flask_mail import Mail
from models import db, User
from werkzeug.security import generate_password_hash, check_password_hash
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import os
import secrets
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

# Initialize extensions (without app context)
migrate = Migrate()
jwt = JWTManager()
mail = Mail()

def create_app(config_class=None):
    app = Flask(__name__)
    CORS(app)

    # Load configuration
    if config_class:
        app.config.from_object(config_class)
    else:
        app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://shop_crawl_db_user:v4bSEhl4jKrMJNW0XEk61pzMCx0pYY4V@dpg-cv49m72j1k6c73bgvqa0-a.oregon-postgres.render.com/shop_crawl_db'
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        app.config["JWT_SECRET_KEY"] = "fghsgdgfdsgf"
        app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=2)
        app.config["MAIL_SERVER"] = 'smtp.gmail.com'
        app.config["MAIL_PORT"] = 587
        app.config["MAIL_USE_TLS"] = True
        app.config["MAIL_USE_SSL"] = False
        app.config["MAIL_USERNAME"] = "blessed.wesonga@student.moringaschool.com"
        app.config["MAIL_PASSWORD"] = "delu jsnj cjhz szqg"
        app.config["MAIL_DEFAULT_SENDER"] = "blessed.wesonga@student.moringaschool.com"
        app.secret_key = secrets.token_hex(16)
        app.config['GOOGLE_CLIENT_ID'] = '414872029170-3u2c5nboldvniesjmkgm0fhtc54a0mld.apps.googleusercontent.com'
        app.config['GOOGLE_CLIENT_SECRET'] = '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'
        app.config['GOOGLE_REDIRECT_URI'] = 'http://127.0.0.1:5000/google_login/callback'

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    mail.init_app(app)

    # Set mail instance for auth
    from views.auth import set_mail_instance
    set_mail_instance(mail)

    # Import and register blueprints
    from views import auth_bp, filter_bp, product_bp, search_bp, user_bp, shop_bp, search_history_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(filter_bp)
    app.register_blueprint(product_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(shop_bp)
    app.register_blueprint(search_history_bp)

    # Google OAuth2 configuration
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
        return redirect(f"http://localhost:5173/login?token={access_token}")

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

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
