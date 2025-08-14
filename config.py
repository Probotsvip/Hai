import os

# MongoDB Configuration
MONGO_DB_URI = os.getenv("MONGO_DB_URI", "mongodb+srv://jaydipmore74:xCpTm5OPAfRKYnif@cluster0.5jo18.mongodb.net/?retryWrites=true&w=majority")

# Telegram Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "-1002611582825")
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID", "")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH", "")

# App Configuration
DEBUG = os.getenv("DEBUG", "false").lower() == "true"
SECRET_KEY = os.getenv("SECRET_KEY", "komalmusic")

# Rate Limiting
DEFAULT_RATE_LIMIT = 100  # requests per minute
ADMIN_DAILY_LIMIT = 10000000
REGULAR_DAILY_LIMIT = 1000

# Cache Settings
STREAM_EXPIRY_HOURS = 24
