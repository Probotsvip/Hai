import asyncio
import requests
import json
import re
from typing import Optional, Dict, Any
from youtubesearchpython import VideosSearch
from logger_utils import LOGGER

logger = LOGGER(__name__)

class YouTubeHandler:
    def __init__(self):
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
        ]
    
    def extract_video_id(self, query: str) -> Optional[str]:
        """Extract video ID from YouTube URL or return query if it's already an ID"""
        # If it's already a video ID (11 characters)
        if re.match(r'^[a-zA-Z0-9_-]{11}$', query):
            return query
            
        # Extract from YouTube URLs
        patterns = [
            r'(?:v=|\/)([0-9A-Za-z_-]{11})',
            r'youtu\.be\/([0-9A-Za-z_-]{11})',
            r'embed\/([0-9A-Za-z_-]{11})'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, query)
            if match:
                return match.group(1)
        
        return None
    
    async def search_youtube(self, query: str) -> Optional[str]:
        """Search YouTube and return the first video ID"""
        try:
            search = VideosSearch(query, limit=1)
            result = await search.next()
            
            if result['result']:
                video_url = result['result'][0]['link']
                return self.extract_video_id(video_url)
        except Exception as e:
            logger.error(f"YouTube search failed: {e}")
        
        return None
    
    async def get_video_info(self, video_id: str, is_video: bool = False) -> Optional[Dict[str, Any]]:
        """Get video information and download URLs using Clipto API"""
        try:
            youtube_url = f"https://www.youtube.com/watch?v={video_id}"
            
            # Get CSRF token
            csrf_response = requests.get('https://www.clipto.com/api/csrf', 
                headers={
                    'user-agent': self.user_agents[0],
                    'referer': 'https://www.clipto.com/id/media-downloader/youtube-downloader'
                }, timeout=30)
            
            csrf_data = csrf_response.json()
            csrf_token = csrf_data.get('token')
            
            if not csrf_token:
                logger.error("Failed to get CSRF token")
                return None
            
            # Get video data
            response = requests.post('https://www.clipto.com/api/youtube',
                headers={
                    'x-xsrf-token': csrf_token,
                    'cookie': f'XSRF-TOKEN={csrf_token}',
                    'origin': 'https://www.clipto.com',
                    'referer': 'https://www.clipto.com/id/media-downloader/youtube-downloader',
                    'content-type': 'application/json',
                    'user-agent': self.user_agents[0]
                },
                json={'url': youtube_url},
                timeout=30
            )
            
            if response.status_code != 200:
                logger.error(f"Clipto API error: {response.status_code}")
                return None
            
            data = response.json()
            
            # Extract basic info
            video_info = {
                'id': video_id,
                'title': data.get('title', 'Unknown Title'),
                'duration': data.get('duration', 0),
                'link': youtube_url,
                'channel': 'Unknown Channel',
                'views': 0,
                'thumbnail': data.get('thumbnail', ''),
                'direct_url': None
            }
            
            # Find appropriate stream
            if is_video:
                # Find 720p MP4 with audio
                for media in data.get('medias', []):
                    if (media.get('ext') == 'mp4' and 
                        media.get('quality') in ['720p', 'hd720'] and
                        (media.get('is_audio') or media.get('audioQuality'))):
                        video_info['direct_url'] = media.get('url')
                        break
            else:
                # Find audio stream
                for media in data.get('medias', []):
                    if media.get('is_audio') or 'audio' in media.get('quality', '').lower():
                        video_info['direct_url'] = media.get('url')
                        break
            
            if not video_info['direct_url']:
                logger.error(f"No suitable stream found for video {video_id}")
                return None
            
            return video_info
            
        except Exception as e:
            logger.error(f"Error getting video info for {video_id}: {e}")
            return None
    
    async def process_query(self, query: str, is_video: bool = False) -> Optional[Dict[str, Any]]:
        """Process a query (URL, video ID, or search term) and return video info"""
        video_id = self.extract_video_id(query)
        
        if not video_id:
            # If no video ID found, try searching
            video_id = await self.search_youtube(query)
        
        if not video_id:
            logger.error(f"Could not extract or find video ID for query: {query}")
            return None
        
        return await self.get_video_info(video_id, is_video)
