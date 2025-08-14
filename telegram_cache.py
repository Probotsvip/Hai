import asyncio
import os
import tempfile
import requests
from typing import Optional, Dict, Any
from pyrogram.client import Client
from pyrogram.types import Message
import uuid
from config import TELEGRAM_BOT_TOKEN, TELEGRAM_CHANNEL_ID, TELEGRAM_API_ID, TELEGRAM_API_HASH
from database import cache_collection
from models import CacheMetadata
from logger_utils import LOGGER

logger = LOGGER(__name__)

class TelegramCache:
    def __init__(self):
        self.bot = None
        self.channel_id = TELEGRAM_CHANNEL_ID
        
    async def init_bot(self):
        """Initialize Telegram bot"""
        if not self.bot:
            try:
                self.bot = Client(
                    "youtube_cache_bot",
                    api_id=TELEGRAM_API_ID,
                    api_hash=TELEGRAM_API_HASH,
                    bot_token=TELEGRAM_BOT_TOKEN
                )
                await self.bot.start()
                logger.info("Telegram bot initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Telegram bot: {e}")
                self.bot = None
    
    async def get_cached_content(self, video_id: str, stream_type: str) -> Optional[Dict[str, Any]]:
        """Check if content is cached and return metadata"""
        try:
            cache_entry = await cache_collection.find_one({
                "video_id": video_id,
                "stream_type": stream_type
            })
            
            if cache_entry:
                logger.info(f"Found cached content for {video_id} ({stream_type})")
                return cache_entry
            
        except Exception as e:
            logger.error(f"Error checking cache for {video_id}: {e}")
        
        return None
    
    async def cache_content(self, video_info: Dict[str, Any], stream_type: str) -> Optional[str]:
        """Download and cache content to Telegram channel"""
        if not self.bot:
            await self.init_bot()
        
        if not self.bot:
            logger.error("Cannot cache content: Telegram bot not available")
            return None
        
        try:
            # Download file to temporary location
            response = requests.get(video_info['direct_url'], stream=True, timeout=300)
            response.raise_for_status()
            
            # Create temporary file
            file_extension = 'mp4' if stream_type == 'video' else 'm4a'
            with tempfile.NamedTemporaryFile(suffix=f'.{file_extension}', delete=False) as temp_file:
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            try:
                # Upload to Telegram
                caption = f"🎵 {video_info['title']}\n📹 Video ID: {video_info['id']}\n🎯 Type: {stream_type}"
                
                if stream_type == 'video':
                    message = await self.bot.send_video(
                        chat_id=self.channel_id,
                        video=temp_file_path,
                        caption=caption,
                        supports_streaming=True
                    )
                    file_id = message.video.file_id if message and message.video else None
                else:
                    message = await self.bot.send_audio(
                        chat_id=self.channel_id,
                        audio=temp_file_path,
                        caption=caption,
                        title=video_info['title']
                    )
                    file_id = message.audio.file_id if message and message.audio else None
                
                if not file_id:
                    logger.error("Failed to get file ID from Telegram message")
                    return None
                
                # Save cache metadata
                cache_metadata = CacheMetadata(
                    video_id=video_info['id'],
                    stream_type=stream_type,
                    telegram_file_id=file_id,
                    title=video_info['title'],
                    duration=video_info['duration'],
                    channel=video_info['channel'],
                    views=video_info['views'],
                    thumbnail=video_info['thumbnail'],
                    direct_url=video_info['direct_url']
                )
                
                await cache_collection.insert_one(cache_metadata.to_dict())
                logger.info(f"Successfully cached {video_info['id']} ({stream_type}) to Telegram")
                
                return file_id
                
            finally:
                # Clean up temporary file
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Error caching content to Telegram: {e}")
            return None
    
    async def get_file_url(self, file_id: str) -> Optional[str]:
        """Get direct download URL for a Telegram file"""
        if not self.bot:
            await self.init_bot()
        
        if not self.bot:
            return None
        
        try:
            # Get file information from Telegram
            file_info = await self.bot.download_media(file_id, in_memory=True)
            if file_info:
                # For Telegram bot files, construct direct URL
                return f"https://api.telegram.org/file/bot{TELEGRAM_BOT_TOKEN}/{file_id}"
            return None
        except Exception as e:
            logger.error(f"Error getting file URL for {file_id}: {e}")
            return None

# Global instance
telegram_cache = TelegramCache()
