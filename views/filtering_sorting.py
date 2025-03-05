from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, Product, Shop, ComparisonResult, ProductSearch

filter_bp = Blueprint('filter', __name__)

@filter_bp.route('/filter_sort', methods=['GET'])
@jwt_required(optional=True)  # Allows both authenticated and non-authenticated users
def filter_and_sort():
    query = request.args.get('q', '').strip()
    sort_by = request.args.get('sort_by', 'cost_benefit')  # Default sorting by cost-benefit ie.price
    current_user_id = get_jwt_identity()  # Get logged-in user ID

    if not query:
        return jsonify({"error": "Please provide a search query."}), 400

    # Fetch products from search history if user is logged in
    if current_user_id:
        products = ProductSearch.query.filter(
            ProductSearch.user_id == current_user_id,
            ProductSearch.product_name.ilike(f"%{query}%")
        ).all()
    else:
        # If user isn't logged in, fetch directly from the products table
        products = Product.query.filter(Product.product_name.ilike(f"%{query}%")).all()

    if not products:
        return jsonify({"message": "No products found."}), 404

    comparison_results = []

    for product in products:
        # Fetch all shops that sell this product
        shops_selling_product = Shop.query.filter(Shop.id == product.shop_id).all()

        if len(shops_selling_product) < 2:
            continue  # Skip if there aren't at least two shops for comparison

        # Generate pairwise comparisons between shops
        for i in range(len(shops_selling_product) - 1):
            for j in range(i + 1, len(shops_selling_product)):
                shop_x = shops_selling_product[i]
                shop_y = shops_selling_product[j]

                shop_x_product = Product.query.filter_by(product_name=product.product_name, shop_id=shop_x.id).first()
                shop_y_product = Product.query.filter_by(product_name=product.product_name, shop_id=shop_y.id).first()

                if not shop_x_product or not shop_y_product:
                    continue  # Skip if product details are missing for either shop

                # Extract shop-specific product details
                shop_x_cost = shop_x_product.product_price
                shop_x_rating = shop_x_product.product_rating
                shop_x_delivery_cost = shop_x_product.delivery_cost
                shop_x_payment_mode = shop_x_product.payment_mode

                shop_y_cost = shop_y_product.product_price
                shop_y_rating = shop_y_product.product_rating
                shop_y_delivery_cost = shop_y_product.delivery_cost
                shop_y_payment_mode = shop_y_product.payment_mode

                # Compute Marginal Benefit (MB) and Cost-Benefit (CB)
                marginal_benefit = shop_x_rating - shop_y_rating
                cost_benefit = (shop_x_cost + shop_x_delivery_cost) - (shop_y_cost + shop_y_delivery_cost)

                # Save comparison results to the database
                comparison_entry = ComparisonResult(
                    product_id=product.id,
                    shop_x_id=shop_x.id,
                    shop_y_id=shop_y.id,
                    product_name=product.product_name,
                    shop_x_cost=shop_x_cost,
                    shop_x_rating=shop_x_rating,
                    shop_x_delivery_cost=shop_x_delivery_cost,
                    shop_x_payment_mode=shop_x_payment_mode,
                    shop_y_cost=shop_y_cost,
                    shop_y_rating=shop_y_rating,
                    shop_y_delivery_cost=shop_y_delivery_cost,
                    shop_y_payment_mode=shop_y_payment_mode,
                    marginal_benefit=marginal_benefit,
                    cost_benefit=cost_benefit
                )
                db.session.add(comparison_entry)
                comparison_results.append(comparison_entry)

    db.session.commit()

    # Sorting options
    if sort_by == "mb":  # Sort by Marginal Benefit (descending)
        comparison_results.sort(key=lambda x: x.marginal_benefit, reverse=True)
    elif sort_by == "cb":  # Sort by Cost-Benefit (ascending)
        comparison_results.sort(key=lambda x: x.cost_benefit)
    else:  # Default sorting by total cost (ascending)
        comparison_results.sort(key=lambda x: (x.shop_x_cost + x.shop_x_delivery_cost))

    # Format response
    results = [
        {
            "product_name": comparison.product_name,
            "shop_x_name": comparison.shop_x.name,
            "shop_x_cost": comparison.shop_x_cost,
            "shop_x_rating": comparison.shop_x_rating,
            "shop_x_delivery_cost": comparison.shop_x_delivery_cost,
            "shop_x_payment_mode": comparison.shop_x_payment_mode,
            "shop_y_name": comparison.shop_y.name,
            "shop_y_cost": comparison.shop_y_cost,
            "shop_y_rating": comparison.shop_y_rating,
            "shop_y_delivery_cost": comparison.shop_y_delivery_cost,
            "shop_y_payment_mode": comparison.shop_y_payment_mode,
            "marginal_benefit": comparison.marginal_benefit,
            "cost_benefit": comparison.cost_benefit,
        }
        for comparison in comparison_results
    ]

    return jsonify({"results": results}), 200
