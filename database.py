from motor.motor_asyncio import AsyncIOMotorClient
from config import MONGO_DB_URI
from logger_utils import LOGGER

logger = LOGGER(__name__)
logger.info("Connecting to your Mongo Database...")
try:
    _mongo_async_ = AsyncIOMotorClient(MONGO_DB_URI)
    mongodb = _mongo_async_.Anon
    logger.info("Connected to your Mongo Database.")
except Exception as e:
    logger.error(f"Failed to connect to your Mongo Database: {e}")
    exit()

# Collections
api_keys_collection = mongodb.api_keys
api_logs_collection = mongodb.api_logs
cache_collection = mongodb.cache_metadata
