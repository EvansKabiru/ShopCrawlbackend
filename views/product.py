from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Product, User, db
from datetime import datetime

# Define the Blueprint
product_bp = Blueprint('product', __name__)

# Helper function to check if the current user is an admin
def is_admin():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return user and user.is_admin

# Create a new product (Admin only)
@product_bp.route('/products', methods=['POST'])
def add_product():
    # Get JSON data from the request
    data = request.get_json()

    # Validate required fields
    if not data or not all(key in data for key in ['product_name', 'product_price', 'shop_id']):
        return jsonify({"error": "Missing required fields"}), 400

    try:
        # Create a new product instance
        new_product = Product(
            product_name=data['product_name'],
            product_price=data['product_price'],
            product_rating=data.get('product_rating'),
            product_url=data.get('product_url'),
            delivery_cost=data.get('delivery_cost'),
            shop_name=data.get('shop_name'),
            payment_mode=data.get('payment_mode'),
            navigate_link=data.get('navigate_link'),
            shop_id=data['shop_id'],
            created_at=datetime.utcnow()
        )

        # Add the product to the database
        db.session.add(new_product)
        db.session.commit()

        # Return the created product as JSON
        return jsonify({
            "id": new_product.id,
            "product_name": new_product.product_name,
            "product_price": new_product.product_price,
            "product_rating": new_product.product_rating,
            "product_url": new_product.product_url,
            "delivery_cost": new_product.delivery_cost,
            "shop_name": new_product.shop_name,
            "payment_mode": new_product.payment_mode,
            "navigate_link": new_product.navigate_link,
            "shop_id": new_product.shop_id,
            "created_at": new_product.created_at.isoformat()
        }), 201

    except Exception as e:
        db.session.rollback()
        return jsonify({"error": str(e)}), 500

@product_bp.route('/products/search', methods=['GET'])
def search_products():
    query = request.args.get('query', '').strip().lower()
    if not query:
        return jsonify({"message": "No search query provided"}), 400

    products = Product.query.filter(Product.product_name.ilike(f"%{query}%")).order_by(Product.product_price.asc()).all()

    products_list = [{
        "id": product.id,
        "product_name": product.product_name,
        "product_price": product.product_price,
        "product_rating": product.product_rating,
        "product_url": product.product_url,
        "delivery_cost": product.delivery_cost,
        "shop_name": product.shop_name,
        "payment_mode": product.payment_mode,
        "created_at": product.created_at.isoformat() if product.created_at else None
    } for product in products]

    return jsonify(products_list), 200

# Fetch all products (Public access)
@product_bp.route('/products', methods=['GET'])
def get_all_products():
    products = Product.query.all()
    products_list = []
    for product in products:
        products_list.append({
            "id": product.id,
            "product_name": product.product_name,
            "product_price": product.product_price,
            "product_rating": product.product_rating,
            "product_url": product.product_url,
            "delivery_cost": product.delivery_cost,
            "shop_name": product.shop_name,
            "payment_mode": product.payment_mode,
            "navigate_link": product.navigate_link,  # Include navigate_link
            "created_at": product.created_at.isoformat() if product.created_at else None
        })
    return jsonify(products_list), 200

# Fetch a single product by ID (Public access)
@product_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get(product_id)
    if product:
        return jsonify({
            "id": product.id,
            "product_name": product.product_name,
            "product_price": product.product_price,
            "product_rating": product.product_rating,
            "product_url": product.product_url,
            "delivery_cost": product.delivery_cost,
            "shop_name": product.shop_name,
            "payment_mode": product.payment_mode,
            "created_at": product.created_at.isoformat() if product.created_at else None
        }), 200
    else:
        return jsonify({"message": "Product not found"}), 404

# Update a product (Admin only)
@product_bp.route('/products/<int:product_id>', methods=['PUT'])
@jwt_required()
def update_product(product_id):
    if not is_admin():
        return jsonify({"message": "Only admins can update products"}), 403

    product = Product.query.get(product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404

    data = request.get_json()
    product_name = data.get('product_name')
    product_price = data.get('product_price')
    product_rating = data.get('product_rating')
    product_url = data.get('product_url')
    delivery_cost = data.get('delivery_cost')
    shop_name = data.get('shop_name')
    payment_mode = data.get('payment_mode')

    # Update fields if provided
    if product_name:
        product.product_name = product_name
    if product_price:
        product.product_price = product_price
    if product_rating:
        product.product_rating = product_rating
    if product_url:
        product.product_url = product_url
    if delivery_cost:
        product.delivery_cost = delivery_cost
    if shop_name:
        product.shop_name = shop_name
    if payment_mode:
        product.payment_mode = payment_mode

    db.session.commit()
    return jsonify({
        "message": "Product updated successfully",
        "product": {
            "id": product.id,
            "product_name": product.product_name,
            "product_price": product.product_price,
            "product_rating": product.product_rating,
            "product_url": product.product_url,
            "delivery_cost": product.delivery_cost,
            "shop_name": product.shop_name,
            "payment_mode": product.payment_mode,
            "created_at": product.created_at.isoformat() if product.created_at else None
        }
    }), 200

# Delete a product (Admin only)
@product_bp.route('/products/<int:product_id>', methods=['DELETE'])
@jwt_required()
def delete_product(product_id):
    if not is_admin():
        return jsonify({"message": "Only admins can delete products"}), 403

    product = Product.query.get(product_id)
    if not product:
        return jsonify({"message": "Product not found"}), 404

    db.session.delete(product)
    db.session.commit()
    return jsonify({"message": "Product deleted successfully"}), 200