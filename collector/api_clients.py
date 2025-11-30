"""API clients for fetching Dogecoin data from various sources."""

import time
import requests
from typing import Dict, Optional
from datetime import datetime
from utils.logger import setup_logger
from config.settings import (
    COINGECKO_BASE_URL,
    CRYPTOCOMPARE_BASE_URL,
    BINANCE_BASE_URL,
    DOGECOIN_SYMBOL,
    DOGECOIN_ID,
    REQUEST_TIMEOUT,
    MAX_RETRIES,
    RETRY_DELAY
)

logger = setup_logger('api_clients')


class RateLimiter:
    """Simple rate limiter to respect API limits."""
    
    def __init__(self, max_calls: int, time_window: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            max_calls: Maximum number of calls allowed
            time_window: Time window in seconds (default: 60)
        """
        self.max_calls = max_calls
        self.time_window = time_window
        self.calls = []
    
    def wait_if_needed(self):
        """Wait if rate limit would be exceeded."""
        now = time.time()
        # Remove calls outside the time window
        self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        if len(self.calls) >= self.max_calls:
            sleep_time = self.time_window - (now - self.calls[0]) + 1
            if sleep_time > 0:
                logger.debug(f"Rate limit reached, waiting {sleep_time:.2f} seconds")
                time.sleep(sleep_time)
                # Clean up again after sleep
                now = time.time()
                self.calls = [call_time for call_time in self.calls if now - call_time < self.time_window]
        
        self.calls.append(now)


class CoinGeckoClient:
    """Client for CoinGecko API."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.base_url = COINGECKO_BASE_URL
        self.api_key = api_key
        self.rate_limiter = RateLimiter(max_calls=50, time_window=60)  # 50 calls per minute
    
    def fetch_dogecoin_data(self) -> Optional[Dict]:
        """
        Fetch Dogecoin data from CoinGecko.
        
        Returns:
            Dictionary with market data or None if failed
        """
        self.rate_limiter.wait_if_needed()
        
        url = f"{self.base_url}/simple/price"
        params = {
            'ids': DOGECOIN_ID,
            'vs_currencies': 'usd',
            'include_24hr_change': 'true',
            'include_24hr_vol': 'true',
            'include_market_cap': 'true',
            'include_last_updated_at': 'true'
        }
        
        if self.api_key:
            params['x_cg_demo_api_key'] = self.api_key
        
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                data = response.json()
                
                if DOGECOIN_ID in data:
                    doge_data = data[DOGECOIN_ID]
                    return {
                        'price_usd': doge_data.get('usd'),
                        'price_change_24h': doge_data.get('usd_24h_change'),
                        'volume_24h': None,  # CoinGecko doesn't provide volume in this endpoint
                        'market_cap': doge_data.get('usd_market_cap'),
                        'high_24h': None,
                        'low_24h': None,
                        'source': 'coingecko',
                        'timestamp': datetime.utcnow()
                    }
                else:
                    logger.warning("CoinGecko response missing dogecoin data")
                    return None
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"CoinGecko API request failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                else:
                    logger.error(f"CoinGecko API failed after {MAX_RETRIES} attempts")
                    return None
        
        return None


class CryptoCompareClient:
    """Client for CryptoCompare API."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.base_url = CRYPTOCOMPARE_BASE_URL
        self.api_key = api_key
        self.rate_limiter = RateLimiter(max_calls=100, time_window=60)  # Conservative limit
    
    def fetch_dogecoin_data(self) -> Optional[Dict]:
        """
        Fetch Dogecoin data from CryptoCompare.
        
        Returns:
            Dictionary with market data or None if failed
        """
        self.rate_limiter.wait_if_needed()
        
        url = f"{self.base_url}/data/pricemultifull"
        params = {
            'fsyms': DOGECOIN_SYMBOL,
            'tsyms': 'USD'
        }
        
        headers = {}
        if self.api_key:
            headers['authorization'] = f'Apikey {self.api_key}'
        
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(url, params=params, headers=headers, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                data = response.json()
                
                if 'RAW' in data and DOGECOIN_SYMBOL in data['RAW']:
                    raw_data = data['RAW'][DOGECOIN_SYMBOL]['USD']
                    return {
                        'price_usd': raw_data.get('PRICE'),
                        'price_change_24h': raw_data.get('CHANGEPCT24HOUR'),
                        'volume_24h': raw_data.get('VOLUME24HOUR'),
                        'market_cap': raw_data.get('MKTCAP'),
                        'high_24h': raw_data.get('HIGH24HOUR'),
                        'low_24h': raw_data.get('LOW24HOUR'),
                        'source': 'cryptocompare',
                        'timestamp': datetime.utcnow()
                    }
                else:
                    logger.warning("CryptoCompare response missing dogecoin data")
                    return None
                    
            except requests.exceptions.RequestException as e:
                logger.warning(f"CryptoCompare API request failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                else:
                    logger.error(f"CryptoCompare API failed after {MAX_RETRIES} attempts")
                    return None
        
        return None


class BinanceClient:
    """Client for Binance Public API."""
    
    def __init__(self):
        self.base_url = BINANCE_BASE_URL
        self.rate_limiter = RateLimiter(max_calls=1200, time_window=60)  # Binance allows 1200/min
    
    def fetch_dogecoin_data(self) -> Optional[Dict]:
        """
        Fetch Dogecoin data from Binance.
        
        Returns:
            Dictionary with market data or None if failed
        """
        self.rate_limiter.wait_if_needed()
        
        url = f"{self.base_url}/api/v3/ticker/24hr"
        params = {'symbol': 'DOGEUSDT'}
        
        for attempt in range(MAX_RETRIES):
            try:
                response = requests.get(url, params=params, timeout=REQUEST_TIMEOUT)
                response.raise_for_status()
                data = response.json()
                
                # Convert price from USDT to USD (assuming 1:1 for now)
                price_usd = float(data.get('lastPrice', 0))
                price_change_24h = float(data.get('priceChangePercent', 0))
                
                return {
                    'price_usd': price_usd,
                    'price_change_24h': price_change_24h,
                    'volume_24h': float(data.get('quoteVolume', 0)),  # Volume in USDT
                    'market_cap': None,  # Binance doesn't provide market cap
                    'high_24h': float(data.get('highPrice', 0)),
                    'low_24h': float(data.get('lowPrice', 0)),
                    'source': 'binance',
                    'timestamp': datetime.utcnow()
                }
                
            except requests.exceptions.RequestException as e:
                logger.warning(f"Binance API request failed (attempt {attempt + 1}/{MAX_RETRIES}): {e}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(RETRY_DELAY * (attempt + 1))
                else:
                    logger.error(f"Binance API failed after {MAX_RETRIES} attempts")
                    return None
            except (ValueError, KeyError) as e:
                logger.error(f"Binance API response parsing error: {e}")
                return None
        
        return None

