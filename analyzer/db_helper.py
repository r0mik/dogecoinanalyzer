"""Database helper for analyzer to read market data and write analysis results."""

import json
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from decimal import Decimal

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from config.settings import DATABASE_URL
from utils.logger import setup_logger

logger = setup_logger('analyzer.db_helper')


class DatabaseHelper:
    """Helper class for database operations in analyzer."""
    
    def __init__(self):
        """Initialize database connection."""
        self.engine: Optional[Engine] = None
        self._connect()
    
    def _connect(self):
        """Create database connection."""
        try:
            self.engine = create_engine(DATABASE_URL, pool_pre_ping=True)
            logger.info(f"Connected to database: {DATABASE_URL.split('@')[-1] if '@' in DATABASE_URL else DATABASE_URL}")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise
    
    def get_market_data(self, hours: int = 48) -> pd.DataFrame:
        """
        Fetch market data from database for analysis.
        
        Args:
            hours: Number of hours of historical data to fetch
            
        Returns:
            DataFrame with market data sorted by timestamp
        """
        try:
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            
            query = text("""
                SELECT 
                    timestamp,
                    price_usd,
                    volume_24h,
                    market_cap,
                    price_change_24h,
                    high_24h,
                    low_24h,
                    source
                FROM market_data
                WHERE timestamp >= :cutoff_time
                ORDER BY timestamp ASC
            """)
            
            with self.engine.connect() as conn:
                df = pd.read_sql(query, conn, params={'cutoff_time': cutoff_time})
            
            if df.empty:
                logger.warning(f"No market data found for the last {hours} hours")
                return df
            
            # Convert timestamp to datetime if it's not already
            if 'timestamp' in df.columns:
                df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            logger.info(f"Fetched {len(df)} market data records")
            return df
            
        except Exception as e:
            logger.error(f"Error fetching market data: {e}")
            raise
    
    def save_analysis_result(
        self,
        timeframe: str,
        predicted_price: float,
        confidence_score: int,
        trend_direction: str,
        technical_indicators: Dict,
        reasoning: str
    ):
        """
        Save analysis result to database.
        
        Args:
            timeframe: Timeframe ('1h', '4h', '24h', '7d', '30d')
            predicted_price: Predicted price
            confidence_score: Confidence score (0-100)
            trend_direction: Trend direction ('bullish', 'bearish', 'neutral')
            technical_indicators: Dictionary of technical indicator values
            reasoning: Text explanation of the analysis
        """
        try:
            # Check if reasoning was enhanced by AI
            is_ai_enhanced = "--- Enhanced Analysis ---" in reasoning if reasoning else False
            
            query = text("""
                INSERT INTO analysis_results 
                (timestamp, timeframe, predicted_price, confidence_score, 
                 trend_direction, technical_indicators, reasoning)
                VALUES 
                (:timestamp, :timeframe, :predicted_price, :confidence_score,
                 :trend_direction, :technical_indicators, :reasoning)
            """)
            
            params = {
                'timestamp': datetime.utcnow(),
                'timeframe': timeframe,
                'predicted_price': Decimal(str(predicted_price)),
                'confidence_score': confidence_score,
                'trend_direction': trend_direction,
                'technical_indicators': json.dumps(technical_indicators),
                'reasoning': reasoning
            }
            
            reasoning_size = len(reasoning.encode('utf-8')) if reasoning else 0
            
            with self.engine.connect() as conn:
                conn.execute(query, params)
                conn.commit()
            
            ai_status = " (AI-enhanced)" if is_ai_enhanced else ""
            logger.info(
                f"Saved analysis result for {timeframe} timeframe{ai_status} "
                f"(reasoning size: {reasoning_size} bytes, confidence: {confidence_score}%)"
            )
            
        except Exception as e:
            logger.error(f"Error saving analysis result for {timeframe}: {e}", exc_info=True)
            raise
    
    def update_script_status(
        self,
        status: str,
        message: str = '',
        next_run: Optional[datetime] = None
    ):
        """
        Update script status in database.
        
        Args:
            status: Status ('running', 'success', 'error')
            message: Status message
            next_run: Next scheduled run time
        """
        try:
            query = text("""
                UPDATE script_status
                SET last_run = :last_run,
                    status = :status,
                    message = :message,
                    next_run = :next_run,
                    updated_at = CURRENT_TIMESTAMP
                WHERE script_name = 'analyzer'
            """)
            
            params = {
                'last_run': datetime.utcnow(),
                'status': status,
                'message': message,
                'next_run': next_run
            }
            
            with self.engine.connect() as conn:
                conn.execute(query, params)
                conn.commit()
            
            logger.debug(f"Updated script status: {status}")
            
        except Exception as e:
            logger.error(f"Error updating script status: {e}")
            raise
    
    def close(self):
        """Close database connection."""
        if self.engine:
            self.engine.dispose()
            logger.info("Database connection closed")

