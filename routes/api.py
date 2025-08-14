import asyncio
from flask import Blueprint, request, jsonify, redirect
from youtube_handler import YouTubeHandler
from telegram_cache import telegram_cache
from auth import require_api_key
from utils import StreamManager, format_duration, validate_youtube_url
from logger_utils import LOGGER
from datetime import datetime

logger = LOGGER(__name__)

api_bp = Blueprint('api', __name__)
youtube_handler = YouTubeHandler()
stream_manager = StreamManager()

@api_bp.route('/', methods=['GET'])
def index():
    """Root endpoint - Professional UI Landing Page"""
    from flask import render_template
    return render_template('index.html')

@api_bp.route('/youtube', methods=['GET'])
@require_api_key
async def youtube_endpoint():
    """Main YouTube API endpoint"""
    try:
        # Get parameters
        query = request.args.get('query')
        is_video = request.args.get('video', 'false').lower() == 'true'
        
        if not query:
            return jsonify({"error": "Query parameter is required"}), 400
        
        # Determine stream type
        stream_type = "video" if is_video else "audio"
        
        # Extract video ID or search
        video_info = await youtube_handler.process_query(query, is_video)
        
        if not video_info:
            return jsonify({"error": "Could not retrieve video information"}), 404
        
        video_id = video_info['id']
        
        # Check cache first
        cached_content = await telegram_cache.get_cached_content(video_id, stream_type)
        logger.info(f"Cache check for {video_id} ({stream_type}): {'Found' if cached_content else 'Not found'}")
        
        if cached_content:
            # Return cached content
            telegram_url = await telegram_cache.get_file_url(cached_content['telegram_file_id'])
            stream_id = stream_manager.create_stream_session(video_id, video_info['direct_url'])
            
            response = {
                "id": video_id,
                "title": cached_content['title'],
                "duration": cached_content['duration'],
                "link": f"https://youtube.com/watch?v={video_id}",
                "channel": cached_content['channel'],
                "views": cached_content['views'],
                "thumbnail": cached_content['thumbnail'],
                "stream_url": f"/stream/{stream_id}",
                "direct_url": video_info['direct_url'],
                "stream_type": stream_type.title(),
                "cached": True,
                "telegram_cached": True,
                "telegram_url": telegram_url
            }
            
            logger.info(f"Served cached content for {video_id} ({stream_type})")
            return jsonify(response)
        
        # Not cached - return direct info and cache in background
        stream_id = stream_manager.create_stream_session(video_id, video_info['direct_url'])
        
        response = {
            "id": video_id,
            "title": video_info['title'],
            "duration": video_info['duration'],
            "link": video_info['link'],
            "channel": video_info['channel'],
            "views": video_info['views'],
            "thumbnail": video_info['thumbnail'],
            "stream_url": f"/stream/{stream_id}",
            "direct_url": video_info['direct_url'],
            "stream_type": stream_type.title(),
            "cached": False,
            "telegram_cached": False
        }
        
        # Start background caching and wait for it to complete
        try:
            cached_file_id = await telegram_cache.cache_content(video_info, stream_type)
            if cached_file_id:
                logger.info(f"Successfully cached {video_id} to Telegram with file_id: {cached_file_id}")
                response["telegram_cached"] = True
                response["telegram_file_id"] = cached_file_id
            else:
                logger.warning(f"Failed to cache {video_id} to Telegram")
        except Exception as e:
            logger.error(f"Error caching to Telegram: {e}")
        
        logger.info(f"Served new content for {video_id} ({stream_type}), caching in background")
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Error in youtube endpoint: {e}")
        return jsonify({"error": "Internal server error"}), 500

@api_bp.route('/stream/<stream_id>')
async def stream_endpoint(stream_id):
    """Stream proxy endpoint"""
    try:
        # Clean up expired streams
        stream_manager.cleanup_expired_streams()
        
        # Get stream URL
        direct_url = stream_manager.get_stream_url(stream_id)
        
        if not direct_url:
            return jsonify({"error": "Stream not found or expired"}), 404
        
        # Redirect to direct URL
        return redirect(direct_url, code=302)
        
    except Exception as e:
        logger.error(f"Error in stream endpoint: {e}")
        return jsonify({"error": "Stream error"}), 500

@api_bp.route('/health')
async def health_check():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "services": {
            "youtube_handler": True,
            "telegram_cache": telegram_cache.bot is not None,
            "database": True  # Add actual DB health check if needed
        }
    })



@api_bp.route('/info')
async def api_info():
    """API information endpoint"""
    return jsonify({
        "name": "YouTube API Service",
        "version": "1.0.0",
        "description": "Production-ready YouTube API with caching and Telegram integration",
        "endpoints": {
            "/youtube": "Main YouTube content retrieval endpoint",
            "/stream/<id>": "Stream proxy endpoint",
            "/admin": "Admin panel for API key management",
            "/health": "Health check endpoint",
            "/test-telegram": "Test Telegram upload functionality",
            "/info": "API information endpoint"
        },
        "parameters": {
            "query": "YouTube URL, video ID, or search term (required)",
            "video": "Boolean for video stream, default: false (audio)",
            "api_key": "Valid API key for authentication (required)"
        }
    })
