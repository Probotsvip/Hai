#!/usr/bin/env python3

import asyncio
import sys
from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_DB_URI

async def check_telegram_cache():
    """Check MongoDB cache for Telegram uploads"""
    try:
        # Connect to MongoDB
        client = AsyncIOMotorClient(MONGO_DB_URI)
        db = client["Anon"]
        cache_collection = db["cache_metadata"]
        
        # Count total cached files
        total_count = await cache_collection.count_documents({})
        print(f"📊 Total cached files in database: {total_count}")
        
        if total_count > 0:
            # Get recent cached files
            recent_files = await cache_collection.find().sort("_id", -1).limit(5).to_list(None)
            
            print("\n🔍 Recent cached files:")
            for i, file_data in enumerate(recent_files, 1):
                print(f"\n{i}. Video ID: {file_data.get('video_id', 'N/A')}")
                print(f"   Title: {file_data.get('title', 'N/A')}")
                print(f"   Stream Type: {file_data.get('stream_type', 'N/A')}")
                print(f"   Telegram File ID: {file_data.get('telegram_file_id', 'N/A')}")
                print(f"   Duration: {file_data.get('duration', 'N/A')} seconds")
                
                if file_data.get('telegram_file_id'):
                    print(f"   ✅ SUCCESSFULLY UPLOADED TO TELEGRAM CHANNEL!")
                else:
                    print(f"   ❌ Upload pending or failed")
        else:
            print("\n📭 No cached files found yet. Upload in progress...")
            
        client.close()
        
    except Exception as e:
        print(f"❌ Error checking cache: {e}")

if __name__ == "__main__":
    asyncio.run(check_telegram_cache())