from flask import Blueprint, request, jsonify
from datetime import datetime, timedelta
from models import db, SearchHistory
from flask_jwt_extended import jwt_required, get_jwt_identity

search_history_bp = Blueprint('search_history', __name__)

# Save search history
@search_history_bp.route('/save-search', methods=['POST'])
def save_search():
    data = request.get_json()
    search_query = data.get('search_query')
    user_id = data.get('user_id')  # Pata user_id kutoka kwenye request body

    # Hakikisha search_query na user_id zipo
    if not search_query or not user_id:
        return jsonify({"error": "Both search_query and user_id are required"}), 400

    # Create new search history entry
    new_search = SearchHistory(
        search_query=search_query,
        user_id=user_id
    )

    try:
        db.session.add(new_search)
        db.session.commit()
        return jsonify({
            "message": "Search history saved successfully",
            "search_query": new_search.search_query,
            "search_date": new_search.search_date.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": new_search.user_id
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Failed to save search history",
            "details": str(e)
        }), 500

# Route ya kuona searches za user fulani (kwa ajili ya kujaribu)
@search_history_bp.route('/searches/<int:user_id>', methods=['GET'])
def get_user_searches(user_id):
    searches = SearchHistory.query.filter_by(user_id=user_id).all()
    search_list = [
        {
            "id": search.id,
            "search_query": search.search_query,
            "search_date": search.search_date.strftime("%Y-%m-%d %H:%M:%S"),
            "user_id": search.user_id
        }
        for search in searches
    ]
    return jsonify(search_list), 200

# Clear search history for a user
@search_history_bp.route('/delete-search/<int:search_id>', methods=['DELETE'])
def delete_search(search_id):
    search = SearchHistory.query.get(search_id)

    if not search:
        return jsonify({"error": "Search history not found"}), 404

    try:
        db.session.delete(search)
        db.session.commit()
        return jsonify({"message": "Search history deleted successfully"}), 200
    except Exception as e:
        db.session.rollback()
        return jsonify({
            "error": "Failed to delete search history",
            "details": str(e)
        }), 500
