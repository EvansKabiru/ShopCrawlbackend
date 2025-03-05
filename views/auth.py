# views/Auth.py
from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from models import User, db
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_mail import Message
import logging

# Initialize serializer for generating tokens
serializer = URLSafeTimedSerializer("SECRET_KEY")  # Use your app's secret key

# Create the auth_bp blueprint
auth_bp = Blueprint('auth', __name__)

# Global variable to store the mail instance
mail_instance = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Function to set the mail instance
def set_mail_instance(mail):
    global mail_instance
    mail_instance = mail

# Login Route
@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.json
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"message": "Missing email or password"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"message": "Invalid credentials"}), 401

    # Generate JWT token for the user
    access_token = create_access_token(identity=user.id)
    return jsonify(access_token=access_token), 200

# Request Password Reset Token
@auth_bp.route('/request-password-reset', methods=['POST'])
def request_password_reset():
    data = request.json
    email = data.get('email')

    if not email:
        return jsonify({"message": "Email is required"}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"message": "User with this email does not exist"}), 404

    # Generate a password reset token
    token = serializer.dumps(email, salt="password-reset-salt")

    # Send the password reset email
    msg = Message(
        subject="Password Reset Request",
        recipients=[email],
        body=f"Click the link to reset your password: http://localhost:5000/reset-password/{token}"
    )

    try:
        mail_instance.send(msg)  # Use the globally stored mail instance
        logger.info(f"Password reset email sent to {email}")
        return jsonify({"message": "Password reset email sent successfully"}), 200
    except Exception as e:
        logger.error(f"Error sending email to {email}: {str(e)}")
        return jsonify({"message": "Error sending email", "error": str(e)}), 500

# Reset Password
@auth_bp.route('/reset-password/<token>', methods=['POST'])
def reset_password(token):
    data = request.json
    new_password = data.get('new_password')

    if not new_password:
        return jsonify({"message": "New password is required"}), 400

    try:
        email = serializer.loads(token, salt="password-reset-salt", max_age=3600)  # Token valid for 1 hour
    except SignatureExpired:
        return jsonify({"message": "Token expired"}), 400
    except Exception:
        return jsonify({"message": "Invalid token"}), 400

    user = User.query.filter_by(email=email).first()

    if not user:
        return jsonify({"message": "User with this email does not exist"}), 404

    # Update the user's password
    user.password_hash = generate_password_hash(new_password)
    db.session.commit()
    return jsonify({"message": "Password reset successfully"}), 200

@auth_bp.route("/login_with_google", methods=["POST"])
def login_with_google():
    data = request.get_json()
    email = data.get("email")

    if not email:
        print("Email required")
        return jsonify({"error": "Email is required"}), 400

    print("Processing Google login")
    user = User.query.filter_by(email=email).first()

    if user:
        access_token = create_access_token(identity=user.id)
        print("Access token generated")
        return jsonify({"access_token": access_token}), 200

    return jsonify({"error": "Email is incorrect"}), 404

    