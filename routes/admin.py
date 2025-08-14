from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from admin_helper import admin_helper
from config import ADMIN_DAILY_LIMIT
from logger_utils import LOGGER

logger = LOGGER(__name__)

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/admin')
def admin_panel():
    """Admin panel with API key authentication"""
    # Check for admin API key
    admin_key = request.args.get('key')
    if admin_key != 'NOTTY_BOY':
        return render_template('admin_login.html')
    
    try:
        # Get basic stats for initial load using sync approach
        stats = {
            "total_keys": 0,
            "active_keys": 0, 
            "total_requests": 0,
            "today_requests": 0
        }
        
        return render_template('admin.html', stats=stats)
    except Exception as e:
        logger.error(f"Error loading admin panel: {e}")
        return render_template('admin.html', stats={
            "total_keys": 0,
            "active_keys": 0, 
            "total_requests": 0,
            "today_requests": 0
        })

@admin_bp.route('/admin/create-key', methods=['POST'])
def create_api_key():
    """Create a new API key"""
    try:
        data = request.get_json()
        name = data.get('name')
        daily_limit = data.get('daily_limit', 1000)
        expiry_days = data.get('expiry_days', 30)
        
        if not name:
            return jsonify({"error": "Key name is required"}), 400
        
        if not isinstance(daily_limit, int) or daily_limit < 1:
            return jsonify({"error": "Invalid daily limit"}), 400
        
        # Create API key using helper
        api_key = admin_helper.create_api_key_sync(name, daily_limit, expiry_days)
        
        return jsonify({
            "success": True,
            "key_id": api_key,
            "message": f"API key created: {name}"
        })
        
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        return jsonify({"error": f"Failed to create API key: {str(e)}"}), 500

@admin_bp.route('/admin/delete-key/<key_id>', methods=['DELETE'])
def delete_api_key(key_id):
    """Delete an API key"""
    try:        
        # Delete API key using helper
        deleted = admin_helper.delete_api_key_sync(key_id)
        
        if deleted:
            return jsonify({
                "success": True,
                "message": "API key deleted successfully"
            })
        else:
            return jsonify({"error": "API key not found"}), 404
            
    except Exception as e:
        logger.error(f"Error deleting API key: {e}")
        return jsonify({"error": f"Failed to delete API key: {str(e)}"}), 500

@admin_bp.route('/admin/keys', methods=['GET'])
def get_api_keys():
    """Get all API keys"""
    try:
        # Get keys using helper
        keys = admin_helper.get_api_keys_sync()
        return jsonify(keys)
        
    except Exception as e:
        logger.error(f"Error getting API keys: {e}")
        return jsonify({"error": f"Failed to get API keys: {str(e)}"}), 500

@admin_bp.route('/admin/stats')
def get_stats():
    """Get detailed statistics"""
    try:
        async def _get_stats():
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
            
            # Count active keys
            active_keys = await api_keys_collection.count_documents({"is_active": True})
            
            return {
                "total_requests": total_requests_today,
                "total_keys": total_keys,
                "active_keys": active_keys,
                "today_requests": total_requests_today,
                "error_rate": round(error_rate, 2),
                "popular_endpoints": popular_endpoints
            }
        
        # Use thread executor to handle async in sync context
        with ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, _get_stats())
            stats = future.result()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting stats: {e}")
        return jsonify({"error": "Failed to get statistics"}), 500

@admin_bp.route('/admin/enhanced-stats')
def get_enhanced_stats():
    """Get enhanced statistics with weekly/monthly data"""
    try:
        # Get stats using helper
        stats = admin_helper.get_enhanced_stats_sync()
        return jsonify(stats)
        
    except Exception as e:
        logger.error(f"Error getting enhanced stats: {e}")
        return jsonify({
            "today_requests": 0,
            "week_requests": 0,
            "month_requests": 0,
            "active_keys": 0,
            "telegram_responses": 0,
            "api_responses": 0,
            "today_trend": "No data",
            "week_trend": "No data",
            "month_trend": "No data"
        }), 200
