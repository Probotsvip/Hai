import asyncio
import threading
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, List, Any
from database import api_keys_collection, api_logs_collection
from auth import AuthManager

class AdminHelper:
    """Helper class to handle async operations for admin panel"""
    
    def __init__(self):
        self.auth_manager = AuthManager()
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    def run_async_safely(self, coro):
        """Run async coroutine safely in a new thread"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                result = loop.run_until_complete(coro)
                return result
            finally:
                loop.close()
        except Exception as e:
            print(f"Error in async operation: {e}")
            raise
    
    def create_api_key_sync(self, name: str, daily_limit: int, expiry_days: int) -> str:
        """Create API key synchronously"""
        async def _create():
            return await self.auth_manager.create_api_key(
                owner=name,
                is_admin=(daily_limit >= 10000000),
                daily_limit=daily_limit,
                expiry_days=expiry_days
            )
        
        return self.run_async_safely(_create())
    
    def get_api_keys_sync(self) -> List[Dict]:
        """Get all API keys synchronously"""
        async def _get_keys():
            try:
                cursor = api_keys_collection.find({})
                keys = []
                
                async for key_doc in cursor:
                    # Format expires_at as ISO string if it exists
                    expires_at = key_doc.get("expires_at")
                    if expires_at:
                        expires_at = expires_at.isoformat() if hasattr(expires_at, 'isoformat') else str(expires_at)
                    
                    keys.append({
                        "key_id": key_doc.get("key"),
                        "name": key_doc.get("owner", "Unknown"),
                        "daily_limit": key_doc.get("daily_limit", 1000),
                        "daily_usage": key_doc.get("daily_used", 0),
                        "is_active": key_doc.get("is_active", True),
                        "expires_at": expires_at,
                        "created_at": key_doc.get("created_at").isoformat() if key_doc.get("created_at") else None
                    })
                return keys
            except Exception as e:
                print(f"Error in _get_keys: {e}")
                return []
        
        return self.run_async_safely(_get_keys())
    
    def delete_api_key_sync(self, key_id: str) -> bool:
        """Delete API key synchronously"""
        async def _delete():
            result = await api_keys_collection.delete_one({"key": key_id})
            return result.deleted_count > 0
        
        return self.run_async_safely(_delete())
    
    def get_enhanced_stats_sync(self) -> Dict:
        """Get enhanced statistics synchronously"""
        async def _get_stats():
            now = datetime.utcnow()
            today = now.replace(hour=0, minute=0, second=0, microsecond=0)
            week_start = today - timedelta(days=7)
            month_start = today - timedelta(days=30)
            
            # Get various time period stats
            today_requests = await api_logs_collection.count_documents({
                "timestamp": {"$gte": today}
            })
            
            week_requests = await api_logs_collection.count_documents({
                "timestamp": {"$gte": week_start}
            })
            
            month_requests = await api_logs_collection.count_documents({
                "timestamp": {"$gte": month_start}
            })
            
            # Active keys
            active_keys = await api_keys_collection.count_documents({"is_active": True})
            
            # Simulate responses for demo
            telegram_responses = today_requests // 2 if today_requests > 0 else 0
            api_responses = today_requests // 2 if today_requests > 0 else 0
            
            return {
                "today_requests": today_requests,
                "week_requests": week_requests,
                "month_requests": month_requests,
                "active_keys": active_keys,
                "telegram_responses": telegram_responses,
                "api_responses": api_responses,
                "today_trend": "+12% from yesterday",
                "week_trend": "+8% from last week", 
                "month_trend": "+25% from last month"
            }
        
        return self.run_async_safely(_get_stats())

# Global instance
admin_helper = AdminHelper()