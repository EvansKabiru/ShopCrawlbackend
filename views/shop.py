from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import Shop, User, db

# Define the Blueprint
shop_bp = Blueprint('shop', __name__)

# Helper function to check if the current user is an admin
def is_admin():
    user_id = get_jwt_identity()
    user = User.query.get(user_id)
    return user and user.is_admin

# Create a new shop (Admin only)
@shop_bp.route('/shops', methods=['POST'])
@jwt_required()
def create_shop():
    if not is_admin():
        return jsonify({"message": "Only admins can create shops"}), 403

    data = request.get_json()
    name = data.get('name')
    url = data.get('url')

    # Validate required fields
    if not name or not url:
        return jsonify({"message": "Name and URL are required"}), 400

    # Check if the shop already exists
    if Shop.query.filter_by(name=name).first():
        return jsonify({"message": "Shop with this name already exists"}), 400

    # Create a new shop
    new_shop = Shop(name=name, url=url)
    db.session.add(new_shop)
    db.session.commit()

    return jsonify({
        "message": "Shop created successfully",
        "shop": {
            "id": new_shop.id,
            "name": new_shop.name,
            "url": new_shop.url
        }
    }), 201

# Fetch all shops (Public access)
# Fetch all shops (Public access)
@shop_bp.route('/shops', methods=['GET'])
def get_all_shops():
    shops = Shop.query.all()
    shops_list = []
    for shop in shops:
        # Use 'shop_products' relationship to get the products count
        shops_list.append({
            "id": shop.id,
            "name": shop.name,
            "url": shop.url,
            "products_count": len(shop.shop_products)  # Correct attribute to access related products
        })
    return jsonify(shops_list), 200



# Fetch a single shop by ID (Public access)
@shop_bp.route('/shops/<int:shop_id>', methods=['GET'])
def get_shop(shop_id):
    shop = Shop.query.get(shop_id)
    if shop:
        return jsonify({
            "id": shop.id,
            "name": shop.name,
            "url": shop.url,
            "products": [{
                "id": product.id,
                "name": product.name,
                "price": product.price
            } for product in shop.products]  # Include related products
        }), 200
    else:
        return jsonify({"message": "Shop not found"}), 404

# Update a shop (Admin only)
@shop_bp.route('/shops/<int:shop_id>', methods=['PUT'])
@jwt_required()
def update_shop(shop_id):
    if not is_admin():
        return jsonify({"message": "Only admins can update shops"}), 403

    shop = Shop.query.get(shop_id)
    if not shop:
        return jsonify({"message": "Shop not found"}), 404

    data = request.get_json()
    name = data.get('name')
    url = data.get('url')

    # Update fields if provided
    if name:
        shop.name = name
    if url:
        shop.url = url

    db.session.commit()
    return jsonify({
        "message": "Shop updated successfully",
        "shop": {
            "id": shop.id,
            "name": shop.name,
            "url": shop.url
        }
    }), 200

# Delete a shop (Admin only)
@shop_bp.route('/shops/<int:shop_id>', methods=['DELETE'])
@jwt_required()
def delete_shop(shop_id):
    if not is_admin():
        return jsonify({"message": "Only admins can delete shops"}), 403

    shop = Shop.query.get(shop_id)
    if not shop:
        return jsonify({"message": "Shop not found"}), 404

    db.session.delete(shop)
    db.session.commit()
    return jsonify({"message": "Shop deleted successfully"}), 200