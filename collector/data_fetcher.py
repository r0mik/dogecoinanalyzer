"""Data fetcher module for collecting Dogecoin market data."""

from typing import Optional, Dict
from datetime import datetime
from database.models import MarketData, ScriptStatus, get_db_session
from collector.api_clients import CoinGeckoClient, CryptoCompareClient, BinanceClient
from config.settings import COINGECKO_API_KEY, CRYPTOCOMPARE_API_KEY
from utils.logger import setup_logger

logger = setup_logger('data_fetcher')


class DataFetcher:
    """Fetches Dogecoin data from multiple sources and stores in database."""
    
    def __init__(self):
        """Initialize data fetcher with API clients."""
        self.coingecko = CoinGeckoClient(api_key=COINGECKO_API_KEY if COINGECKO_API_KEY else None)
        self.cryptocompare = CryptoCompareClient(api_key=CRYPTOCOMPARE_API_KEY if CRYPTOCOMPARE_API_KEY else None)
        self.binance = BinanceClient()
        self.api_clients = [
            ('CoinGecko', self.coingecko),
            ('CryptoCompare', self.cryptocompare),
            ('Binance', self.binance)
        ]
    
    def fetch_and_store(self) -> bool:
        """
        Fetch data from all available APIs and store in database.
        
        Returns:
            True if at least one source succeeded, False otherwise
        """
        logger.info("Starting data collection...")
        success_count = 0
        error_messages = []
        
        for source_name, client in self.api_clients:
            try:
                logger.debug(f"Fetching data from {source_name}...")
                data = client.fetch_dogecoin_data()
                
                if data and self._validate_data(data):
                    if self._store_data(data):
                        logger.info(f"Successfully collected and stored data from {source_name}")
                        success_count += 1
                    else:
                        error_msg = f"Failed to store data from {source_name}"
                        logger.error(error_msg)
                        error_messages.append(error_msg)
                else:
                    error_msg = f"Invalid or missing data from {source_name}"
                    logger.warning(error_msg)
                    error_messages.append(error_msg)
                    
            except Exception as e:
                error_msg = f"Error fetching from {source_name}: {str(e)}"
                logger.error(error_msg, exc_info=True)
                error_messages.append(error_msg)
        
        # Update script status
        status = 'success' if success_count > 0 else 'error'
        message = f"Collected from {success_count}/{len(self.api_clients)} sources"
        if error_messages:
            message += f". Errors: {'; '.join(error_messages[:3])}"  # Limit message length
        
        self._update_script_status(status, message)
        
        if success_count > 0:
            logger.info(f"Data collection completed. Successfully collected from {success_count} source(s)")
            return True
        else:
            logger.error("Data collection failed from all sources")
            return False
    
    def _validate_data(self, data: Dict) -> bool:
        """
        Validate fetched data.
        
        Args:
            data: Dictionary with market data
            
        Returns:
            True if data is valid, False otherwise
        """
        required_fields = ['price_usd', 'timestamp']
        
        for field in required_fields:
            if field not in data or data[field] is None:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # Validate price is positive
        try:
            price = float(data['price_usd'])
            if price <= 0:
                logger.warning(f"Invalid price: {price}")
                return False
        except (ValueError, TypeError):
            logger.warning(f"Price is not a valid number: {data['price_usd']}")
            return False
        
        return True
    
    def _store_data(self, data: Dict) -> bool:
        """
        Store market data in database.
        
        Args:
            data: Dictionary with market data
            
        Returns:
            True if stored successfully, False otherwise
        """
        db = get_db_session()
        try:
            market_data = MarketData(
                timestamp=data['timestamp'],
                price_usd=data['price_usd'],
                volume_24h=data.get('volume_24h'),
                market_cap=data.get('market_cap'),
                price_change_24h=data.get('price_change_24h'),
                high_24h=data.get('high_24h'),
                low_24h=data.get('low_24h'),
                source=data.get('source', 'unknown')
            )
            
            db.add(market_data)
            db.commit()
            logger.debug(f"Stored market data: price={data['price_usd']}, source={data.get('source')}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store data in database: {e}", exc_info=True)
            db.rollback()
            return False
        finally:
            db.close()
    
    def _update_script_status(self, status: str, message: str = None):
        """
        Update script status in database.
        
        Args:
            status: Status string ('running', 'success', 'error')
            message: Optional status message
        """
        db = get_db_session()
        try:
            script_status = db.query(ScriptStatus).filter(
                ScriptStatus.script_name == 'collector'
            ).first()
            
            if not script_status:
                script_status = ScriptStatus(script_name='collector')
                db.add(script_status)
            
            script_status.last_run = datetime.utcnow()
            script_status.status = status
            script_status.message = message
            
            db.commit()
            logger.debug(f"Updated script status: {status}")
            
        except Exception as e:
            logger.error(f"Failed to update script status: {e}", exc_info=True)
            db.rollback()
        finally:
            db.close()

