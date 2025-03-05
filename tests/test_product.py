import sys
import os
import pytest
from flask import Flask
from flask_jwt_extended import JWTManager, create_access_token
from models import db, Product, Shop

# Fix sys.path for module resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

@pytest.fixture
def app():
    """Fixture to create a Flask test app."""
    app = Flask(__name__)

    # Configure the app for testing
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['JWT_SECRET_KEY'] = 'test_secret_key'
    app.config['TESTING'] = True

    # Add JWT configuration
    app.config['JWT_TOKEN_LOCATION'] = ['headers']
    app.config['JWT_HEADER_NAME'] = 'Authorization'
    app.config['JWT_HEADER_TYPE'] = 'Bearer'

    # Initialize Flask-JWT-Extended
    JWTManager(app)

    # Register the product blueprint
    from views.product import product_bp
    app.register_blueprint(product_bp, url_prefix='/api')

    # Initialize the database
    db.init_app(app)

    with app.app_context():
        db.create_all()  # Ensure tables are created

    yield app  # Yield app for testing

    # Cleanup after each test
    with app.app_context():
        db.drop_all()
        db.session.remove()

@pytest.fixture
def client(app):
    """Fixture to create a test client."""
    return app.test_client()

@pytest.fixture
def auth_headers(app):
    """Generate a JWT token for authentication."""
    with app.app_context():
        access_token = create_access_token(identity='test_user')
        return {'Authorization': f'Bearer {access_token}'}

@pytest.fixture
def init_db(app):
    """Fixture to initialize the database and add test data."""
    with app.app_context():
        db.create_all()

        # Add a test shop
        shop = Shop(name='Test Shop', url='http://example.com')  
        db.session.add(shop)
        db.session.commit()

        # Add a test product
        product = Product(
            product_name='Test Product',
            product_price=10.0,
            shop_id=shop.id
        )
        db.session.add(product)
        db.session.commit()

        yield db  # Allow tests to use this database

        # Cleanup after tests
        db.session.remove()
        db.drop_all()

# ✅ Test Cases

def test_create_product(client, init_db, auth_headers):
    """Test creating a new product."""
    response = client.post('/api/products', json={
        'product_name': 'New Product',
        'product_price': 20.0,
        'shop_id': 1
    }, headers=auth_headers)
    assert response.status_code == 201
    assert b"Product created successfully" in response.data

def test_get_product(client, init_db, auth_headers):
    """Test retrieving a product."""
    response = client.get('/api/products/1', headers=auth_headers)
    assert response.status_code == 200
    assert b"Test Product" in response.data

def test_update_product(client, init_db, auth_headers):
    """Test updating a product."""
    response = client.put('/api/products/1', json={
        'product_name': 'Updated Product',
        'product_price': 25.0
    }, headers=auth_headers)
    assert response.status_code == 200
    assert b"Updated Product" in response.data

def test_delete_product(client, init_db, auth_headers):
    """Test deleting a product."""
    response = client.delete('/api/products/1', headers=auth_headers)
    assert response.status_code == 200
    assert b"Product deleted successfully" in response.data
