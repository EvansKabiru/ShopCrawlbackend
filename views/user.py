from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import jwt_required, create_access_token, get_jwt_identity
from models import User, db
from datetime import datetime

# Define the Blueprint
user_bp = Blueprint('user', __name__)

# Register a new user
@user_bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    phone_number = data.get('phone_number')
    password = data.get('password')
    profile_picture = data.get('profile_picture', None)  # Optional field
    is_admin = data.get('is_admin', False)  # Default to False

    # Check if the user already exists (by email or username)
    if User.query.filter((User.email == email) | (User.username == username)).first():
        return jsonify({"message": "User with this email or username already exists"}), 400

    # Hash the password and create a new user
    hashed_password = generate_password_hash(password)
    new_user = User(
        username=username,
        email=email,
        phone_number=phone_number,
        password_hash=hashed_password,
        profile_picture=profile_picture,
        is_admin=is_admin
    )
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": "User registered successfully"}), 201

# Login a user
@user_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    # Find the user by email
    user = User.query.filter_by(email=email).first()
    if user and check_password_hash(user.password_hash, password):
        # Create an access token for the user
        access_token = create_access_token(identity=user.id)
        return jsonify({
            "access_token": access_token,
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "phone_number": user.phone_number,
                "profile_picture": user.profile_picture,
                "is_admin": user.is_admin
            }
        }), 200
    else:
        return jsonify({"message": "Invalid credentials"}), 401

# Fetch the current user (requires authentication)
@user_bp.route('/me', methods=['GET'])
@jwt_required()
def get_current_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if user:
        return jsonify({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone_number": user.phone_number,
            "profile_picture": user.profile_picture,
            "is_admin": user.is_admin,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }), 200
    else:
        return jsonify({"message": "User not found"}), 404

# Fetch a specific user by ID (requires authentication)
@user_bp.route('/<int:user_id>', methods=['GET'])
@jwt_required()
def get_user(user_id):
    user = User.query.get(user_id)

    if user:
        return jsonify({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "phone_number": user.phone_number,
            "profile_picture": user.profile_picture,
            "is_admin": user.is_admin,
            "created_at": user.created_at.isoformat() if user.created_at else None
        }), 200
    else:
        return jsonify({"message": "User not found"}), 404

# Update a user (requires authentication)
@user_bp.route('/update', methods=['PUT'])
@jwt_required()
def update_user():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

    if not user:
        return jsonify({"message": "User not found"}), 404

    data = request.get_json()
    username = data.get('username')
    email = data.get('email')
    phone_number = data.get('phone_number')
    password = data.get('password')
    profile_picture = data.get('profile_picture')
    is_admin = data.get('is_admin')

    # Update fields if provided
    if username:
        user.username = username
    if email:
        user.email = email
    if phone_number:
        user.phone_number = phone_number
    if password:
        user.password_hash = generate_password_hash(password)
    if profile_picture:
        user.profile_picture = profile_picture
    if is_admin is not None:  # Only update if explicitly provided
        user.is_admin = is_admin

    db.session.commit()
    return jsonify({"message": "User updated successfully"}), 200

# Delete a user (requires authentication)
@user_bp.route('/<int:user_id>', methods=['DELETE'])
@jwt_required()
def delete_user(user_id):
    user_id = get_jwt_identity()
    user = User.query.get(user_id)

# Only admins or the user themselves can delete the account
    

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted successfully"}), 200