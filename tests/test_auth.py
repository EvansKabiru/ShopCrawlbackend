import pytest
import time
from flask import Flask
from werkzeug.security import generate_password_hash
from models import User, db
from flask_mail import Mail
from itsdangerous import URLSafeTimedSerializer, SignatureExpired
from flask_jwt_extended import JWTManager
from views.auth import auth_bp, serializer  # Ensure serializer is correctly initialized

@pytest.fixture
def app():
    """Fixture to initialize the Flask app."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SECRET_KEY'] = 'test_secret_key'
    app.config['JWT_SECRET_KEY'] = 'test_jwt_secret_key'
    app.config['MAIL_SUPPRESS_SEND'] = True  # Disable actual emails during testing

    db.init_app(app)
    JWTManager(app)
    mail = Mail(app)

    app.register_blueprint(auth_bp)

    with app.app_context():
        db.create_all()

    yield app  # Yield app for testing

    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Fixture to create a test client."""
    return app.test_client()

@pytest.fixture
def test_user(app):
    """Fixture to create a test user."""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            phone_number='1234567890',
            password_hash=generate_password_hash('testpassword')
        )
        db.session.add(user)
        db.session.commit()
        return user

def test_reset_password_expired_token(client, test_user):
    """Test case for expired password reset token."""

    # Generate token with a short expiration time (1 second)
    token = serializer.dumps('test@example.com', salt="password-reset-salt")

    # Wait for expiration
    time.sleep(2)

    # Post expired token to the reset-password endpoint
    response = client.post(f'/reset-password/{token}', json={'new_password': 'newpassword'})

    # Assert that the response code is 400 and message is 'Token expired'
    assert response.status_code == 400
    assert response.json['message'] == 'Token expired'

def test_reset_password_invalid_token(client):
    """Test case for invalid password reset token."""
    response = client.post('/reset-password/invalidtoken', json={'new_password': 'newpassword'})
    assert response.status_code == 400
    assert response.json['message'] == 'Invalid token'

def test_reset_password_success(client, test_user):
    """Test case for successful password reset."""

    # Generate a valid token
    token = serializer.dumps('test@example.com', salt="password-reset-salt")

    # Post valid token to the reset-password endpoint
    response = client.post(f'/reset-password/{token}', json={'new_password': 'newpassword'})

    # Assert success response
    assert response.status_code == 200
    assert response.json['message'] == 'Password reset successfully'
