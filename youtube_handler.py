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
        self.user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    
    def extract_video_id(self, url: str) -> Optional[str]:
        """Extract video ID from YouTube URL"""
        match = re.search(r'(?:v=|\/)([0-9A-Za-z_-]{11})', url)
        return match.group(1) if match else None
    
    async def search_youtube(self, query: str) -> Optional[str]:
        """Search YouTube and return the first video ID"""
        try:
            search = VideosSearch(query, limit=1)
            result = search.result()
            
            if result['result']:
                video_url = result['result'][0]['link']
                return self.extract_video_id(video_url)
        except Exception as e:
            logger.error(f"YouTube search failed: {e}")
        
        return None
    
    async def get_video_info_clipto(self, url: str) -> Optional[Dict[str, Any]]:
        """Get video information using Clipto API - Python version of JerryCoder's implementation"""
        try:
            # Validate YouTube URL
            if not url or ('youtube.com' not in url and 'youtu.be' not in url):
                logger.error("Missing or invalid YouTube URL")
                return None

            video_id = self.extract_video_id(url)
            if not video_id:
                logger.error("Could not extract video ID")
                return None

            # Get CSRF token from Clipto API
            def get_csrf_token():
                csrf_response = requests.get(
                    'https://www.clipto.com/api/csrf',
                    headers={
                        'user-agent': self.user_agent,
                        'referer': 'https://www.clipto.com/id/media-downloader/youtube-downloader'
                    },
                    timeout=10
                )
                return csrf_response.json()['token']

            def get_video_data(csrf_token, cookie):
                clipto_response = requests.post(
                    'https://www.clipto.com/api/youtube',
                    headers={
                        'x-xsrf-token': csrf_token,
                        'cookie': cookie,
                        'origin': 'https://www.clipto.com',
                        'referer': 'https://www.clipto.com/id/media-downloader/youtube-downloader',
                        'content-type': 'application/json',
                        'user-agent': self.user_agent
                    },
                    json={'url': url},
                    timeout=15
                )
                return clipto_response.json()

            # Run requests in executor to avoid blocking
            loop = asyncio.get_event_loop()
            csrf_token = await loop.run_in_executor(None, get_csrf_token)
            cookie = f'XSRF-TOKEN={csrf_token}'
            
            data = await loop.run_in_executor(None, get_video_data, csrf_token, cookie)
            
            title = data.get('title')
            thumbnail = data.get('thumbnail')
            duration = data.get('duration')
            
            # Find MP4 with 720p quality
            mp4_url = None
            if 'medias' in data:
                mp4_with_audio = None
                for media in data['medias']:
                    if (media.get('ext') == 'mp4' and 
                        media.get('quality') in ['720p', 'hd720'] and 
                        (media.get('is_audio') == True or media.get('audioQuality'))):
                        mp4_with_audio = media
                        break
                
                if mp4_with_audio:
                    mp4_url = mp4_with_audio.get('url')
            
            if not mp4_url:
                logger.error("Failed to extract 720p MP4 link")
                return None
            
            # Build result
            result = {
                'id': video_id,
                'title': title,
                'thumbnail': thumbnail,
                'direct_url': mp4_url,
                'duration': round(duration) if duration else None,
                'link': url,
                'channel': 'Unknown Channel',
                'views': 0
            }
            
            logger.info(f"Successfully extracted 720p MP4 for {video_id}: {title}")
            return result
            
        except Exception as e:
            logger.error(f"Clipto API failed for {url}: {e}")
            return None
    
    async def process_query(self, query: str, is_video: bool = False) -> Optional[Dict[str, Any]]:
        """Process a query (URL, video ID, or search term) and return video info"""
        # If query is already a YouTube URL, use it directly with Clipto API
        if 'youtube.com' in query or 'youtu.be' in query:
            return await self.get_video_info_clipto(query)
        
        # If query is a video ID, convert to URL
        video_id = self.extract_video_id(query)
        if video_id and len(video_id) == 11:
            youtube_url = f"https://www.youtube.com/watch?v={video_id}"
            return await self.get_video_info_clipto(youtube_url)
        
        # If no video ID found, try searching
        video_id = await self.search_youtube(query)
        if video_id:
            youtube_url = f"https://www.youtube.com/watch?v={video_id}"
            return await self.get_video_info_clipto(youtube_url)
        
        logger.error(f"Could not extract or find video ID for query: {query}")
        return None
