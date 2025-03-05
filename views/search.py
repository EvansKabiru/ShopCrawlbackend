from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Product, Shop, ProductSearch, User

search_bp = Blueprint('search', __name__)

@search_bp.route('/search', methods=['GET'])
@jwt_required(optional=True)  # Allows both authenticated and non-authenticated users
def search_products():
    query = request.args.get('q', '').strip()
    current_user_id = get_jwt_identity()  # Get logged-in user ID

    if not query:
        return jsonify({"error": "Please provide a search query."}), 400

    # Fetch all products that match the search query
    products = Product.query.filter(Product.product_name.ilike(f"%{query}%")).all()

    if not products:
        return jsonify({"message": "No products found."}), 404

    search_results = []

    for product in products:
        # Fetch all shops selling this product
        shops_selling_product = Shop.query.join(Product).filter(Product.id == product.id).all()

        for shop in shops_selling_product:
            shop_product = Product.query.filter_by(id=product.id, shop_id=shop.id).first()

            if not shop_product:
                continue  # Skip if shop-specific product details are missing

            # Structuring the search result
            product_data = {
                "product_name": product.product_name,
                "product_price": shop_product.product_price,
                "product_rating": shop_product.product_rating,
                "product_url": shop_product.product_url,
                "delivery_cost": shop_product.delivery_cost,
                "shop_name": shop.name,
                "payment_mode": shop_product.payment_mode,
                "shop_id": shop.id
            }

            search_results.append(product_data)

            # **Save search result only for registered users**
            if current_user_id:
                search_entry = ProductSearch(
                    user_id=current_user_id,  # Associate search history with the logged-in user
                    product_name=product.product_name,
                    product_price=shop_product.product_price,
                    product_rating=shop_product.product_rating,
                    product_url=shop_product.product_url,
                    delivery_cost=shop_product.delivery_cost,
                    shop_name=shop.name,
                    payment_mode=shop_product.payment_mode,
                    shop_id=shop.id
                )
                db.session.add(search_entry)

    db.session.commit()

    return jsonify({"results": search_results}), 200
