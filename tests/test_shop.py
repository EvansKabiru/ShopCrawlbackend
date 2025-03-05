import pytest
from flask_jwt_extended import create_access_token
from models import db, User, Shop
from app import create_app  # Ensure we import the function, not an instance

class TestConfig:
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    JWT_SECRET_KEY = "test-secret-key"

@pytest.fixture
def app():
    """Create and configure a new app instance for testing."""
    app = create_app(TestConfig)  # Use test configuration
    
    with app.app_context():
        db.create_all()  # Create tables only once
        # Create a test admin user
        admin = User(username="admin", email="admin@example.com", phone_number="0712345678", is_admin=True)
        admin.set_password("adminpass")
        db.session.add(admin)
        db.session.commit()
    
    yield app

    with app.app_context():
        db.session.remove()
        db.drop_all()

@pytest.fixture
def client(app):
    """Set up the test client."""
    return app.test_client()

@pytest.fixture
def admin_user(app):
    """Create an admin user for testing."""
    with app.app_context():
        admin = User(username="admin1", email="admin1@example.com", phone_number="07118745678", is_admin=True)
        admin.set_password("adminpass")
        db.session.add(admin)
        db.session.commit()
        return db.session.get(User, admin.id)  # Ensures instance is bound to the session

@pytest.fixture
def normal_user(app):
    """Create a normal user for testing."""
    with app.app_context():
        user = User(username="user", email="user@example.com", phone_number="0712345609", is_admin=False)
        user.set_password("userpass")
        db.session.add(user)
        db.session.commit()
        return db.session.get(User, user.id)

@pytest.fixture
def admin_token(app, admin_user):
    """Generate a JWT token for the admin user."""
    with app.app_context():
        return create_access_token(identity=admin_user.id)

@pytest.fixture
def user_token(app, normal_user):
    """Generate a JWT token for a normal user."""
    with app.app_context():
        return create_access_token(identity=normal_user.id)

@pytest.fixture
def test_shop(app):
    """Create a test shop."""
    with app.app_context():
        shop = Shop(name="Test Shop", url="https://example.com")
        db.session.add(shop)
        db.session.commit()
        return shop

# Test cases

def test_create_shop_admin(client, admin_token):
    response = client.post(
        "/shops",
        json={"name": "New Shop", "url": "https://newshop.com"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 201
    assert response.json["message"] == "Shop created successfully"

def test_create_shop_non_admin(client, user_token):
    response = client.post(
        "/shops",
        json={"name": "Unauthorized Shop", "url": "https://unauthorized.com"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403
    assert response.json["message"] == "Only admins can create shops"

def test_get_all_shops(client, test_shop):
    response = client.get("/shops")
    assert response.status_code == 200
    assert len(response.json) > 0

def test_get_single_shop(client, test_shop):
    response = client.get(f"/shops/{test_shop.id}")
    assert response.status_code == 200
    assert response.json["name"] == "Test Shop"

def test_get_nonexistent_shop(client):
    response = client.get("/shops/9999")
    assert response.status_code == 404
    assert response.json["message"] == "Shop not found"

def test_update_shop_admin(client, admin_token, test_shop):
    response = client.put(
        f"/shops/{test_shop.id}",
        json={"name": "Updated Shop"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json["message"] == "Shop updated successfully"

def test_update_shop_non_admin(client, user_token, test_shop):
    response = client.put(
        f"/shops/{test_shop.id}",
        json={"name": "Unauthorized Update"},
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403
    assert response.json["message"] == "Only admins can update shops"

def test_delete_shop_admin(client, admin_token, test_shop):
    response = client.delete(
        f"/shops/{test_shop.id}",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 200
    assert response.json["message"] == "Shop deleted successfully"

def test_delete_shop_non_admin(client, user_token, test_shop):
    response = client.delete(
        f"/shops/{test_shop.id}",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert response.status_code == 403
    assert response.json["message"] == "Only admins can delete shops"

def test_delete_nonexistent_shop(client, admin_token):
    response = client.delete(
        "/shops/9999",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert response.status_code == 404
    assert response.json["message"] == "Shop not found"
