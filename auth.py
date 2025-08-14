import uuid
import asyncio
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify
from database import api_keys_collection, api_logs_collection
from models import ApiKey, ApiLog
from config import ADMIN_DAILY_LIMIT, REGULAR_DAILY_LIMIT
from logger_utils import LOGGER

logger = LOGGER(__name__)

class AuthManager:
    @staticmethod
    async def create_api_key(owner: str, is_admin: bool = False, daily_limit: int = None, expiry_days: int = 30) -> str:
        """Create a new API key"""
        api_key = str(uuid.uuid4())
        
        if daily_limit is None:
            daily_limit = ADMIN_DAILY_LIMIT if is_admin else REGULAR_DAILY_LIMIT
        
        key_obj = ApiKey(
            key=api_key,
            owner=owner,
            is_admin=is_admin,
            daily_limit=daily_limit,
            expiry_days=expiry_days
        )
        
        try:
            await api_keys_collection.insert_one(key_obj.to_dict())
            logger.info(f"Created new API key for {owner} (admin: {is_admin})")
            return api_key
        except Exception as e:
            logger.error(f"Error creating API key: {e}")
            raise
    
    @staticmethod
    async def validate_api_key(api_key: str) -> tuple[bool, dict, str]:
        """Validate API key and return (is_valid, key_data, error_message)"""
        try:
            key_data = await api_keys_collection.find_one({"key": api_key})
            
            if not key_data:
                return False, {}, "Invalid API key"
            
            # Check expiration
            if datetime.utcnow() > key_data['expires_at']:
                return False, {}, "API key has expired"
            
            # Check and reset daily limit if needed
            now = datetime.utcnow()
            indian_midnight = now.replace(hour=18, minute=30, second=0, microsecond=0)
            
            # If it's past Indian midnight and we haven't reset today
            if now >= indian_midnight and key_data['last_reset'] < indian_midnight:
                await api_keys_collection.update_one(
                    {"key": api_key},
                    {
                        "$set": {
                            "daily_used": 0,
                            "last_reset": indian_midnight
                        }
                    }
                )
                key_data['daily_used'] = 0
            
            # Check daily limit
            if key_data['daily_used'] >= key_data['daily_limit']:
                return False, {}, "Daily limit exceeded"
            
            return True, key_data, ""
            
        except Exception as e:
            logger.error(f"Error validating API key: {e}")
            return False, {}, "Validation error"
    
    @staticmethod
    async def increment_usage(api_key: str):
        """Increment API key usage counters"""
        try:
            await api_keys_collection.update_one(
                {"key": api_key},
                {
                    "$inc": {
                        "daily_used": 1,
                        "total_used": 1
                    },
                    "$set": {
                        "last_used": datetime.utcnow()
                    }
                }
            )
        except Exception as e:
            logger.error(f"Error incrementing usage: {e}")
    
    @staticmethod
    async def log_request(api_key: str, endpoint: str, ip_address: str, 
                         status_code: int, response_time: float = 0.0,
                         query: str = "", error: str = ""):
        """Log API request"""
        try:
            log_entry = ApiLog(
                api_key=api_key,
                endpoint=endpoint,
                ip_address=ip_address,
                status_code=status_code,
                response_time=response_time,
                query=query,
                error=error
            )
            
            await api_logs_collection.insert_one(log_entry.to_dict())
        except Exception as e:
            logger.error(f"Error logging request: {e}")
    
    @staticmethod
    async def get_api_keys() -> list:
        """Get all API keys"""
        try:
            cursor = api_keys_collection.find({})
            keys = []
            async for key in cursor:
                # Remove sensitive key from response
                key_copy = key.copy()
                key_copy['key'] = key_copy['key'][:8] + "..." + key_copy['key'][-4:]
                keys.append(key_copy)
            return keys
        except Exception as e:
            logger.error(f"Error getting API keys: {e}")
            return []
    
    @staticmethod
    async def get_usage_stats() -> dict:
        """Get usage statistics"""
        try:
            pipeline = [
                {
                    "$group": {
                        "_id": "$api_key",
                        "total_requests": {"$sum": 1},
                        "avg_response_time": {"$avg": "$response_time"},
                        "error_count": {
                            "$sum": {"$cond": [{"$gte": ["$status_code", 400]}, 1, 0]}
                        }
                    }
                }
            ]
            
            cursor = api_logs_collection.aggregate(pipeline)
            stats = []
            async for stat in cursor:
                stats.append(stat)
            
            return {"api_stats": stats}
        except Exception as e:
            logger.error(f"Error getting usage stats: {e}")
            return {"api_stats": []}

def require_api_key(f):
    """Decorator to require API key authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        api_key = request.args.get('api_key') or request.headers.get('X-API-Key')
        
        if not api_key:
            return jsonify({"error": "Missing API key"}), 401
            
        # Validate API key synchronously
        async def validate_key():
            return await AuthManager.validate_api_key(api_key)
            
        try:
            is_valid, key_data, error_msg = asyncio.run(validate_key())
            
            if not is_valid:
                return jsonify({"error": error_msg}), 401
                
            # Store key data in request context for the route to use
            request.api_key_data = key_data
            
            # Call the original function
            result = f(*args, **kwargs)
            
            # If it's an async function, run it
            if asyncio.iscoroutine(result):
                result = asyncio.run(result)
                
            # Increment usage after successful call
            asyncio.run(AuthManager.increment_usage(api_key))
            
            return result
            
        except Exception as e:
            logger.error(f"Auth error: {e}")
            return jsonify({"error": "Authentication error"}), 500
    
    return decorated_function

# Global auth manager instance  
auth_manager = AuthManager()
