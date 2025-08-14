import asyncio
from concurrent.futures import ThreadPoolExecutor
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from auth import AuthManager
from config import ADMIN_DAILY_LIMIT
from logger_utils import LOGGER

logger = LOGGER(__name__)

admin_bp = Blueprint('admin', __name__)
auth_manager = AuthManager()

@admin_bp.route('/admin')
def admin_panel():
    """Admin panel for API key management"""
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
        
        # Create API key using asyncio
        async def _create_key():
            return await auth_manager.create_api_key(
                owner=name,
                is_admin=(daily_limit >= 10000000),
                daily_limit=daily_limit,
                expiry_days=expiry_days
            )
        
        # Use thread executor to handle async in sync context  
        with ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, _create_key())
            api_key = future.result()
        
        return jsonify({
            "success": True,
            "key_id": api_key,
            "message": f"API key created: {name}"
        })
        
    except Exception as e:
        logger.error(f"Error creating API key: {e}")
        return jsonify({"error": "Failed to create API key"}), 500

@admin_bp.route('/admin/delete-key/<key_id>', methods=['DELETE'])
def delete_api_key(key_id):
    """Delete an API key"""
    try:        
        # Delete API key from database using asyncio
        async def _delete_key():
            from database import api_keys_collection
            return await api_keys_collection.delete_one({"key": key_id})
        
        # Use thread executor to handle async in sync context
        with ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, _delete_key())
            result = future.result()
        
        if result.deleted_count > 0:
            return jsonify({
                "success": True,
                "message": "API key deleted successfully"
            })
        else:
            return jsonify({"error": "API key not found"}), 404
            
    except Exception as e:
        logger.error(f"Error deleting API key: {e}")
        return jsonify({"error": "Failed to delete API key"}), 500

@admin_bp.route('/admin/keys', methods=['GET'])
def get_api_keys():
    """Get all API keys"""
    try:
        async def _get_keys():
            from database import api_keys_collection
            cursor = api_keys_collection.find({})
            keys = []
            
            async for key_doc in cursor:
                keys.append({
                    "key_id": key_doc.get("key"),
                    "name": key_doc.get("owner", key_doc.get("name", "Unknown")),
                    "daily_limit": key_doc.get("daily_limit", 1000),
                    "daily_usage": key_doc.get("daily_used", 0),
                    "is_active": key_doc.get("is_active", True),
                    "expires_at": key_doc.get("expires_at"),
                    "created_at": key_doc.get("created_at")
                })
            return keys
        
        # Use thread executor to handle async in sync context
        with ThreadPoolExecutor() as executor:
            future = executor.submit(asyncio.run, _get_keys())
            keys = future.result()
        return jsonify(keys)
        
    except Exception as e:
        logger.error(f"Error getting API keys: {e}")
        return jsonify({"error": "Failed to get API keys"}), 500

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
