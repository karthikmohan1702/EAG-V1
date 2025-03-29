import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# API Keys and Configuration
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Price Monitoring Settings
PRICE_CHECK_INTERVAL = 300  # 5 minutes in seconds
DEFAULT_PRICE_THRESHOLD = 50000  # Default price threshold in USD

# News Monitoring Settings
NEWS_CHECK_INTERVAL = 900  # 15 minutes in seconds
SIGNIFICANT_PRICE_CHANGE_THRESHOLD = 0.05  # 5% price change threshold

# Logging Settings
LOG_FILE = "bitcoin_bot.log"
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# Gemini Model Settings
GEMINI_MODEL = "gemini-2.0-flash" 