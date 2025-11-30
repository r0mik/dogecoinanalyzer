"""Technical indicators for price analysis."""

import numpy as np
import pandas as pd
from typing import Dict, Tuple, Optional

from utils.logger import setup_logger

logger = setup_logger('analyzer.technical_indicators')


class TechnicalIndicators:
    """Calculate technical indicators for price analysis."""
    
    @staticmethod
    def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
        """
        Calculate Relative Strength Index (RSI).
        
        Args:
            prices: Series of closing prices
            period: RSI period (default 14)
            
        Returns:
            Series of RSI values
        """
        if len(prices) < period + 1:
            return pd.Series([np.nan] * len(prices), index=prices.index)
        
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        
        return rsi
    
    @staticmethod
    def calculate_sma(prices: pd.Series, period: int) -> pd.Series:
        """
        Calculate Simple Moving Average (SMA).
        
        Args:
            prices: Series of closing prices
            period: SMA period
            
        Returns:
            Series of SMA values
        """
        return prices.rolling(window=period).mean()
    
    @staticmethod
    def calculate_ema(prices: pd.Series, period: int) -> pd.Series:
        """
        Calculate Exponential Moving Average (EMA).
        
        Args:
            prices: Series of closing prices
            period: EMA period
            
        Returns:
            Series of EMA values
        """
        return prices.ewm(span=period, adjust=False).mean()
    
    @staticmethod
    def calculate_macd(
        prices: pd.Series,
        fast_period: int = 12,
        slow_period: int = 26,
        signal_period: int = 9
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate MACD (Moving Average Convergence Divergence).
        
        Args:
            prices: Series of closing prices
            fast_period: Fast EMA period (default 12)
            slow_period: Slow EMA period (default 26)
            signal_period: Signal line period (default 9)
            
        Returns:
            Tuple of (MACD line, Signal line, Histogram)
        """
        ema_fast = TechnicalIndicators.calculate_ema(prices, fast_period)
        ema_slow = TechnicalIndicators.calculate_ema(prices, slow_period)
        
        macd_line = ema_fast - ema_slow
        signal_line = TechnicalIndicators.calculate_ema(macd_line, signal_period)
        histogram = macd_line - signal_line
        
        return macd_line, signal_line, histogram
    
    @staticmethod
    def calculate_bollinger_bands(
        prices: pd.Series,
        period: int = 20,
        num_std: float = 2.0
    ) -> Tuple[pd.Series, pd.Series, pd.Series]:
        """
        Calculate Bollinger Bands.
        
        Args:
            prices: Series of closing prices
            period: Moving average period (default 20)
            num_std: Number of standard deviations (default 2.0)
            
        Returns:
            Tuple of (Upper band, Middle band (SMA), Lower band)
        """
        sma = TechnicalIndicators.calculate_sma(prices, period)
        std = prices.rolling(window=period).std()
        
        upper_band = sma + (std * num_std)
        lower_band = sma - (std * num_std)
        
        return upper_band, sma, lower_band
    
    @staticmethod
    def calculate_volume_analysis(
        volumes: pd.Series,
        current_volume: Optional[float] = None
    ) -> Dict[str, float]:
        """
        Analyze volume patterns.
        
        Args:
            volumes: Series of volume values
            current_volume: Current volume (if None, uses last value)
            
        Returns:
            Dictionary with volume analysis metrics
        """
        if volumes.empty:
            return {
                'avg_volume': 0.0,
                'volume_ratio': 1.0,
                'volume_trend': 'neutral'
            }
        
        avg_volume = volumes.mean()
        current = current_volume if current_volume is not None else volumes.iloc[-1]
        
        volume_ratio = current / avg_volume if avg_volume > 0 else 1.0
        
        # Determine volume trend
        if volume_ratio > 1.5:
            volume_trend = 'high'
        elif volume_ratio < 0.5:
            volume_trend = 'low'
        else:
            volume_trend = 'normal'
        
        return {
            'avg_volume': float(avg_volume),
            'current_volume': float(current),
            'volume_ratio': float(volume_ratio),
            'volume_trend': volume_trend
        }
    
    @staticmethod
    def calculate_all_indicators(
        df: pd.DataFrame,
        price_col: str = 'price_usd',
        volume_col: str = 'volume_24h'
    ) -> Dict:
        """
        Calculate all technical indicators for a dataframe.
        
        Args:
            df: DataFrame with price and volume data
            price_col: Name of price column
            volume_col: Name of volume column
            
        Returns:
            Dictionary with all calculated indicators
        """
        if df.empty or price_col not in df.columns:
            logger.warning("Empty dataframe or missing price column")
            return {}
        
        prices = df[price_col]
        volumes = df[volume_col] if volume_col in df.columns else pd.Series()
        
        indicators = {}
        
        # RSI (14 period)
        rsi = TechnicalIndicators.calculate_rsi(prices, 14)
        indicators['rsi'] = float(rsi.iloc[-1]) if not pd.isna(rsi.iloc[-1]) else None
        
        # Moving Averages
        sma_20 = TechnicalIndicators.calculate_sma(prices, 20)
        sma_50 = TechnicalIndicators.calculate_sma(prices, 50)
        sma_200 = TechnicalIndicators.calculate_sma(prices, 200)
        
        indicators['sma_20'] = float(sma_20.iloc[-1]) if not pd.isna(sma_20.iloc[-1]) else None
        indicators['sma_50'] = float(sma_50.iloc[-1]) if not pd.isna(sma_50.iloc[-1]) else None
        indicators['sma_200'] = float(sma_200.iloc[-1]) if not pd.isna(sma_200.iloc[-1]) else None
        
        # EMAs
        ema_12 = TechnicalIndicators.calculate_ema(prices, 12)
        ema_26 = TechnicalIndicators.calculate_ema(prices, 26)
        
        indicators['ema_12'] = float(ema_12.iloc[-1]) if not pd.isna(ema_12.iloc[-1]) else None
        indicators['ema_26'] = float(ema_26.iloc[-1]) if not pd.isna(ema_26.iloc[-1]) else None
        
        # MACD
        macd_line, signal_line, histogram = TechnicalIndicators.calculate_macd(prices)
        indicators['macd'] = float(macd_line.iloc[-1]) if not pd.isna(macd_line.iloc[-1]) else None
        indicators['macd_signal'] = float(signal_line.iloc[-1]) if not pd.isna(signal_line.iloc[-1]) else None
        indicators['macd_histogram'] = float(histogram.iloc[-1]) if not pd.isna(histogram.iloc[-1]) else None
        
        # Bollinger Bands
        bb_upper, bb_middle, bb_lower = TechnicalIndicators.calculate_bollinger_bands(prices)
        indicators['bb_upper'] = float(bb_upper.iloc[-1]) if not pd.isna(bb_upper.iloc[-1]) else None
        indicators['bb_middle'] = float(bb_middle.iloc[-1]) if not pd.isna(bb_middle.iloc[-1]) else None
        indicators['bb_lower'] = float(bb_lower.iloc[-1]) if not pd.isna(bb_lower.iloc[-1]) else None
        
        # Current price
        indicators['current_price'] = float(prices.iloc[-1])
        
        # Volume analysis
        if not volumes.empty:
            volume_analysis = TechnicalIndicators.calculate_volume_analysis(volumes)
            indicators.update(volume_analysis)
        
        return indicators

