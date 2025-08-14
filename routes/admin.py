import asyncio
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from auth import AuthManager
from config import ADMIN_DAILY_LIMIT
from logger_utils import LOGGER

logger = LOGGER(__name__)

admin_bp = Blueprint('admin', __name__)
auth_manager = AuthManager()

@admin_bp.route('/admin')
async def admin_panel():
    """Admin panel for API key management"""
    try:
        # Get API keys and usage stats
        api_keys = await auth_manager.get_api_keys()
        usage_stats = await auth_manager.get_usage_stats()
        
        return render_template('admin.html', 
                             api_keys=api_keys, 
                             usage_stats=usage_stats)
    except Exception as e:
        logger.error(f"Error loading admin panel: {e}")
        return render_template('admin.html', 
                             api_keys=[], 
                             usage_stats={"api_stats": []},
                             error="Failed to load data")

@admin_bp.route('/admin/create_key', methods=['POST'])
async def create_api_key():
    """Create a new API key"""
    try:
        data = request.get_json()
        owner = data.get('owner')
        is_admin = data.get('is_admin', False)
        daily_limit = data.get('daily_limit', ADMIN_DAILY_LIMIT if is_admin else 1000)
        expiry_days = data.get('expiry_days', 30)
        
        if not owner:
            return jsonify({"error": "Owner name is required"}), 400
        
        # Create API key
        api_key = await auth_manager.create_api_key(
            owner=owner,
            is_admin=is_admin,
            daily_limit=daily_limit,
            expiry_days=expiry_days
        )
        
        return jsonify({
            "success": True,
            "api_key": api_key,
            "message": f"API key created for {owner}"
        })
        
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        return jsonify({"error": "Failed to create API key"}), 500

@admin_bp.route('/admin/revoke_key', methods=['POST'])
async def revoke_api_key():
    """Revoke an API key"""
    try:
        data = request.get_json()
        api_key = data.get('api_key')
        
        if not api_key:
            return jsonify({"error": "API key is required"}), 400
        
        # Delete API key from database
        from database import api_keys_collection
        result = await api_keys_collection.delete_one({"key": api_key})
        
        if result.deleted_count > 0:
            return jsonify({
                "success": True,
                "message": "API key revoked successfully"
            })
        else:
            return jsonify({"error": "API key not found"}), 404
            
    except Exception as e:
        logger.error(f"Error revoking API key: {e}")
        return jsonify({"error": "Failed to revoke API key"}), 500

@admin_bp.route('/admin/stats')
async def get_stats():
    """Get detailed statistics"""
    try:
        # Get comprehensive stats
        from database import api_logs_collection, api_keys_collection
        
        # Total requests today
        from datetime import datetime
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        total_requests_today = await api_logs_collection.count_documents({
            "timestamp": {"$gte": today}
        })
        
        # Total API keys
        total_keys = await api_keys_collection.count_documents({})
        
        # Error rate
        total_requests = await api_logs_collection.count_documents({})
        error_requests = await api_logs_collection.count_documents({
            "status_code": {"$gte": 400}
        })
        error_rate = (error_requests / total_requests * 100) if total_requests > 0 else 0
        
        # Most used endpoints
        pipeline = [
            {"$group": {
                "_id": "$endpoint",
                "count": {"$sum": 1}
            }},
            {"$sort": {"count": -1}},
            {"$limit": 5}
        ]
        
        cursor = api_logs_collection.aggregate(pipeline)
        popular_endpoints = []
        async for endpoint in cursor:
            popular_endpoints.append(endpoint)
        
        return jsonify({
            "total_requests_today": total_requests_today,
            "total_api_keys": total_keys,
            "error_rate": round(error_rate, 2),
            "popular_endpoints": popular_endpoints
        })
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({"error": "Failed to get statistics"}), 500
