from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Product, User, db,Shop
from datetime import datetime

# Define the Blueprint
product_bp = Blueprint('product', __name__)

# Helper function to check if the current user is an admin
def is_admin():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return user and user.is_admin

@product_bp.route('/products', methods=['POST'])
@jwt_required()
def create_product():
    if not is_admin():
        return jsonify({"message": "Only admins can create products"}), 403

    data = request.get_json()
    product_name = data.get('product_name')
    product_price = data.get('product_price')
    product_rating = data.get('product_rating')
    product_url = data.get('product_url')
    delivery_cost = data.get('delivery_cost')
    shop_name = data.get('shop_name')
    payment_mode = data.get('payment_mode')

    # Validate required fields
    if not product_name or not product_price or not product_url or not shop_name:
        return jsonify({"message": "Product name, price, URL, and shop name are required"}), 400

    # Find the shop by name (this is assuming shop_name exists)
    shop = Shop.query.filter_by(name=shop_name).first()

    # If the shop doesn't exist, return an error
    if not shop:
        return jsonify({"message": "Shop not found"}), 404

    # Create a new product and associate the shop by its shop_id
    new_product = Product(
        product_name=product_name,
        product_price=product_price,
        product_rating=product_rating,
        product_url=product_url,
        delivery_cost=delivery_cost,
        shop_name=shop_name,  # You may still keep this field if you want to store it as well
        payment_mode=payment_mode,
        shop_id=shop.id  # Here you associate the product with the shop using shop_id
    )

    db.session.add(new_product)
    db.session.commit()

    return jsonify({
        "message": "Product created successfully",
        "product": {
            "id": new_product.id,
            "product_name": new_product.product_name,
            "product_price": new_product.product_price,
            "product_rating": new_product.product_rating,
            "product_url": new_product.product_url,
            "delivery_cost": new_product.delivery_cost,
            "shop_name": new_product.shop_name,
            "payment_mode": new_product.payment_mode,
            "created_at": new_product.created_at.isoformat() if new_product.created_at else None
        }
    }), 201


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