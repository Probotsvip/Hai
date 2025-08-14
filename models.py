from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import uuid

class ApiKey:
    def __init__(self, key: str, owner: str, is_admin: bool = False, 
                 daily_limit: int = 1000, expiry_days: int = 30):
        self.key = key
        self.owner = owner
        self.is_admin = is_admin
        self.daily_limit = daily_limit
        self.daily_used = 0
        self.total_used = 0
        self.created_at = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(days=expiry_days)
        self.last_used = None
        self.last_reset = datetime.utcnow().replace(hour=18, minute=30, second=0, microsecond=0)  # Indian midnight
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "key": self.key,
            "owner": self.owner,
            "is_admin": self.is_admin,
            "daily_limit": self.daily_limit,
            "daily_used": self.daily_used,
            "total_used": self.total_used,
            "created_at": self.created_at,
            "expires_at": self.expires_at,
            "last_used": self.last_used,
            "last_reset": self.last_reset
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ApiKey':
        obj = cls.__new__(cls)
        for key, value in data.items():
            setattr(obj, key, value)
        return obj

class ApiLog:
    def __init__(self, api_key: str, endpoint: str, ip_address: str, 
                 status_code: int, response_time: float = 0.0, 
                 query: str = "", error: str = ""):
        self.id = str(uuid.uuid4())
        self.api_key = api_key
        self.endpoint = endpoint
        self.ip_address = ip_address
        self.status_code = status_code
        self.response_time = response_time
        self.query = query
        self.error = error
        self.timestamp = datetime.utcnow()
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "api_key": self.api_key,
            "endpoint": self.endpoint,
            "ip_address": self.ip_address,
            "status_code": self.status_code,
            "response_time": self.response_time,
            "query": self.query,
            "error": self.error,
            "timestamp": self.timestamp
        }

class CacheMetadata:
    def __init__(self, video_id: str, stream_type: str, telegram_file_id: str,
                 title: str, duration: int, channel: str, views: int, 
                 thumbnail: str, direct_url: str):
        self.video_id = video_id
        self.stream_type = stream_type  # "audio" or "video"
        self.telegram_file_id = telegram_file_id
        self.title = title
        self.duration = duration
        self.channel = channel
        self.views = views
        self.thumbnail = thumbnail
        self.direct_url = direct_url
        self.cached_at = datetime.utcnow()
        
    def to_dict(self) -> Dict[str, Any]:
        return {
            "video_id": self.video_id,
            "stream_type": self.stream_type,
            "telegram_file_id": self.telegram_file_id,
            "title": self.title,
            "duration": self.duration,
            "channel": self.channel,
            "views": self.views,
            "thumbnail": self.thumbnail,
            "direct_url": self.direct_url,
            "cached_at": self.cached_at
        }

class StreamSession:
    def __init__(self, stream_id: str, direct_url: str, video_id: str):
        self.stream_id = stream_id
        self.direct_url = direct_url
        self.video_id = video_id
        self.created_at = datetime.utcnow()
        self.expires_at = datetime.utcnow() + timedelta(hours=24)
        
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expires_at
