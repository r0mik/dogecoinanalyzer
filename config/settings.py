"""Configuration settings for DogeAnalyze."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# Database Configuration
DATABASE_URL = os.getenv(
    'DATABASE_URL',
    'sqlite:///dogeanalyze.db'
)

# API Keys
COINGECKO_API_KEY = os.getenv('COINGECKO_API_KEY', '')
CRYPTOCOMPARE_API_KEY = os.getenv('CRYPTOCOMPARE_API_KEY', '')

# Collection Settings
COLLECTION_INTERVAL_MINUTES = int(os.getenv('COLLECTION_INTERVAL_MINUTES', '5'))
ANALYSIS_INTERVAL_MINUTES = int(os.getenv('ANALYSIS_INTERVAL_MINUTES', '15'))

# Dashboard Configuration
FLASK_APP = os.getenv('FLASK_APP', 'dashboard.app')
FLASK_ENV = os.getenv('FLASK_ENV', 'production')
FLASK_PORT = int(os.getenv('FLASK_PORT', '5000'))
SECRET_KEY = os.getenv('SECRET_KEY', 'change-this-in-production')

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'logs/dogeanalyze.log')

# API Configuration
COINGECKO_BASE_URL = 'https://api.coingecko.com/api/v3'
CRYPTOCOMPARE_BASE_URL = 'https://min-api.cryptocompare.com'
BINANCE_BASE_URL = 'https://api.binance.com'

# Rate Limiting (requests per minute)
COINGECKO_RATE_LIMIT = 50  # Free tier: 10-50 calls/minute
CRYPTOCOMPARE_RATE_LIMIT = 100  # Conservative limit
BINANCE_RATE_LIMIT = 1200  # Binance allows 1200 requests/minute

# Request Timeout (seconds)
REQUEST_TIMEOUT = 10

# Retry Configuration
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Dogecoin Symbol
DOGECOIN_SYMBOL = 'DOGE'
DOGECOIN_ID = 'dogecoin'  # CoinGecko ID

# Local LLM Model Configuration (e.g., LM Studio)
LOCAL_MODEL_ENABLED = os.getenv('LOCAL_MODEL_ENABLED', 'false').lower() == 'true'
LOCAL_MODEL_URL = os.getenv('LOCAL_MODEL_URL', 'http://127.0.0.1:1234')
LOCAL_MODEL_TIMEOUT = int(os.getenv('LOCAL_MODEL_TIMEOUT', '30'))  # seconds
LOCAL_MODEL_TEMPERATURE = float(os.getenv('LOCAL_MODEL_TEMPERATURE', '0.7'))
LOCAL_MODEL_MAX_TOKENS = int(os.getenv('LOCAL_MODEL_MAX_TOKENS', '500'))

