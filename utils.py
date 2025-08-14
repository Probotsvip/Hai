import uuid
import re
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

# In-memory stream cache for temporary stream URLs
stream_cache: Dict[str, Dict[str, Any]] = {}

class StreamManager:
    @staticmethod
    def create_stream_session(video_id: str, direct_url: str) -> str:
        """Create a temporary stream session and return stream ID"""
        stream_id = str(uuid.uuid4())
        
        stream_cache[stream_id] = {
            'video_id': video_id,
            'direct_url': direct_url,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + timedelta(hours=24)
        }
        
        return stream_id
    
    @staticmethod
    def get_stream_url(stream_id: str) -> Optional[str]:
        """Get direct URL for a stream session"""
        if stream_id not in stream_cache:
            return None
        
        session = stream_cache[stream_id]
        
        # Check if expired
        if datetime.utcnow() > session['expires_at']:
            del stream_cache[stream_id]
            return None
        
        return session['direct_url']
    
    @staticmethod
    def cleanup_expired_streams():
        """Remove expired stream sessions"""
        now = datetime.utcnow()
        expired_streams = [
            stream_id for stream_id, session in stream_cache.items()
            if now > session['expires_at']
        ]
        
        for stream_id in expired_streams:
            del stream_cache[stream_id]

def format_duration(seconds: int) -> str:
    """Format duration in seconds to human readable format"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes}m {seconds}s"
    else:
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        return f"{hours}h {minutes}m"

def validate_youtube_url(url: str) -> bool:
    """Validate if a string is a valid YouTube URL"""
    youtube_patterns = [
        r'(?:https?://)?(?:www\.)?youtube\.com/watch\?v=([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtu\.be/([a-zA-Z0-9_-]{11})',
        r'(?:https?://)?(?:www\.)?youtube\.com/embed/([a-zA-Z0-9_-]{11})',
        r'^[a-zA-Z0-9_-]{11}$'  # Direct video ID
    ]
    
    return any(re.match(pattern, url) for pattern in youtube_patterns)

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for safe storage"""
    # Remove or replace unsafe characters
    unsafe_chars = '<>:"/\\|?*'
    for char in unsafe_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 200:
        filename = filename[:200]
    
    return filename.strip()
