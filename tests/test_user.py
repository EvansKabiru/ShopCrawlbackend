import pytest
from werkzeug.security import generate_password_hash
from flask import Flask
from models import db, User
from flask_jwt_extended import JWTManager, create_access_token

@pytest.fixture
def app():
    """Fixture to set up the Flask application and database."""
    app = Flask(__name__)
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SECRET_KEY'] = 'test_secret_key'
    app.config['JWT_SECRET_KEY'] = 'test_jwt_secret_key'

    db.init_app(app)
    JWTManager(app)

    # Register the Blueprint
    from views.user import user_bp  # Ensure the Blueprint is correctly imported
    app.register_blueprint(user_bp)

    with app.app_context():
        db.create_all()

    yield app  # Yield the app instance

    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Fixture to create a test client for sending requests."""
    return app.test_client()

@pytest.fixture
def test_user(app):
    """Fixture to create a test user in the database."""
    with app.app_context():
        user = User(
            username='testuser',
            email='test@example.com',
            phone_number='1234567890',
            password_hash=generate_password_hash('testpassword'),
            profile_picture='test.jpg',
            is_admin=False
        )
        db.session.add(user)
        db.session.commit()
        return user

def test_register(client):
    """Test registering a new user."""
    data = {
        "username": "newuser",
        "email": "newuser@example.com",
        "phone_number": "9876543210",
        "password": "newpassword",
        "profile_picture": "new.jpg",
        "is_admin": False
    }
    response = client.post('/register', json=data)
    assert response.status_code == 201
    assert response.json['message'] == 'User registered successfully'

def test_login(client, test_user):
    """Test login with correct credentials."""
    data = {
        "email": "test@example.com",
        "password": "testpassword"
    }
    response = client.post('/login', json=data)
    assert response.status_code == 200
    assert 'access_token' in response.json
    assert response.json['user']['email'] == 'test@example.com'

def test_get_current_user(client, test_user):
    """Test fetching the currently logged-in user."""
    access_token = create_access_token(identity=test_user.id)
    response = client.get('/me', headers={'Authorization': f'Bearer {access_token}'})
    assert response.status_code == 200
    assert response.json['email'] == 'test@example.com'

def test_get_user(client, test_user):
    """Test fetching a specific user by ID."""
    access_token = create_access_token(identity=test_user.id)
    response = client.get(f'/users/{test_user.id}', headers={'Authorization': f'Bearer {access_token}'})
    assert response.status_code == 200
    assert response.json['email'] == 'test@example.com'

def test_update_user(client, test_user):
    """Test updating the logged-in user's details."""
    access_token = create_access_token(identity=test_user.id)
    
    update_data = {
        "username": "updateduser",
        "email": "updated@example.com",
        "phone_number": "1112223333",
        "password": "updatedpassword",
        "profile_picture": "updated.jpg",
        "is_admin": True
    }
    response = client.put(f'/users/{test_user.id}', json=update_data, headers={'Authorization': f'Bearer {access_token}'})
    
    assert response.status_code == 200
    assert response.json['message'] == 'User updated successfully'

def test_delete_user(client, test_user):
    """Test deleting a user."""
    access_token = create_access_token(identity=test_user.id)
    response = client.delete(f'/users/{test_user.id}', headers={'Authorization': f'Bearer {access_token}'})
    
    assert response.status_code == 200
    assert response.json['message'] == 'User deleted successfully'
