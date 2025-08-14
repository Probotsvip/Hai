#!/usr/bin/env python3
import asyncio
import sys
from youtube_handler import YouTubeHandler
from logger_utils import LOGGER

logger = LOGGER(__name__)

async def test_youtube_handler():
    """Test the YouTube handler with the provided URL"""
    handler = YouTubeHandler()
    test_url = "https://youtu.be/6orD8SFHLzI?si=Ve5EdsX0738V3EGl"
    
    print(f"\n=== Testing YouTube Handler ===")
    print(f"URL: {test_url}")
    print("=" * 50)
    
    for attempt in range(1, 3):
        print(f"\n--- Test Attempt {attempt} ---")
        try:
            result = await handler.process_query(test_url, is_video=True)
            
            if result:
                print("✅ SUCCESS!")
                print(f"Title: {result.get('title', 'N/A')}")
                print(f"Duration: {result.get('duration', 'N/A')}")
                print(f"Video ID: {result.get('id', 'N/A')}")
                print(f"Thumbnail: {result.get('thumbnail', 'N/A')}")
                print(f"Direct URL: {result.get('direct_url', 'N/A')[:100]}..." if result.get('direct_url') else "Direct URL: N/A")
                print(f"Channel: {result.get('channel', 'N/A')}")
            else:
                print("❌ FAILED - No result returned")
                
        except Exception as e:
            print(f"❌ ERROR: {e}")
            logger.error(f"Test attempt {attempt} failed: {e}")
    
    print("\n" + "=" * 50)
    print("Test completed")

if __name__ == "__main__":
    asyncio.run(test_youtube_handler())