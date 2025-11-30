"""Main predictor module for Dogecoin price analysis."""

import time
import sys
from datetime import datetime, timedelta
from typing import Dict, Tuple

import pandas as pd
from apscheduler.schedulers.blocking import BlockingScheduler
from apscheduler.triggers.interval import IntervalTrigger

from analyzer.db_helper import DatabaseHelper
from analyzer.technical_indicators import TechnicalIndicators
from analyzer.local_model import LocalModelAnalyzer
from config.settings import ANALYSIS_INTERVAL_MINUTES
from utils.logger import setup_logger

logger = setup_logger('analyzer.predictor')


class PricePredictor:
    """Main class for price prediction and analysis."""
    
    def __init__(self):
        """Initialize predictor with database connection."""
        self.db = DatabaseHelper()
        self.indicators = TechnicalIndicators()
        self.local_model = LocalModelAnalyzer()
        
        if self.local_model.enabled:
            if self.local_model.is_available():
                logger.info("PricePredictor initialized with local model support")
            else:
                logger.warning("Local model enabled but not available - will use basic analysis")
        else:
            logger.info("PricePredictor initialized (local model disabled)")
    
    def analyze_timeframe(
        self,
        df: pd.DataFrame,
        timeframe: str
    ) -> Tuple[float, int, str, Dict, str]:
        """
        Analyze a specific timeframe and generate prediction.
        
        Args:
            df: DataFrame with market data
            timeframe: Timeframe string ('1h', '4h', '24h', '7d', '30d')
            
        Returns:
            Tuple of (predicted_price, confidence_score, trend_direction, 
                     technical_indicators, reasoning)
        """
        if df.empty:
            logger.warning(f"No data available for {timeframe} analysis")
            return 0.0, 0, 'neutral', {}, "No data available"
        
        # Filter data based on timeframe
        # Map timeframes to hours for data filtering
        timeframe_hours_map = {
            '1h': 1,
            '4h': 4,
            '24h': 24,
            '7d': 7 * 24,      # 168 hours
            '30d': 30 * 24     # 720 hours
        }
        hours = timeframe_hours_map.get(timeframe, 24)
        # Get 2x timeframe for analysis to have enough historical data
        cutoff = datetime.utcnow() - timedelta(hours=hours * 2)
        
        if 'timestamp' in df.columns:
            timeframe_df = df[df['timestamp'] >= cutoff].copy()
        else:
            # Approximate: assume data points every 5 minutes
            data_points_needed = (hours * 2) * 12  # 12 data points per hour (5 min intervals)
            timeframe_df = df.tail(min(len(df), data_points_needed)).copy()
        
        if timeframe_df.empty:
            timeframe_df = df.tail(min(len(df), 50)).copy()
        
        # Calculate technical indicators
        indicators = self.indicators.calculate_all_indicators(timeframe_df)
        
        if not indicators or indicators.get('current_price') is None:
            return 0.0, 0, 'neutral', {}, "Insufficient data for analysis"
        
        current_price = indicators['current_price']
        
        # Determine trend direction
        trend_direction = self._determine_trend(indicators, timeframe_df)
        
        # Generate price prediction
        predicted_price = self._predict_price(current_price, indicators, trend_direction, timeframe)
        
        # Calculate confidence score
        confidence_score = self._calculate_confidence(indicators, trend_direction, timeframe_df, timeframe)
        
        # Generate reasoning
        basic_reasoning = self._generate_reasoning(indicators, trend_direction, predicted_price, current_price, timeframe)
        
        # Enhance reasoning with local model if available
        reasoning = self.local_model.enhance_reasoning(
            timeframe, current_price, predicted_price,
            trend_direction, indicators, basic_reasoning
        )
        
        return predicted_price, confidence_score, trend_direction, indicators, reasoning
    
    def _determine_trend(self, indicators: Dict, df: pd.DataFrame) -> str:
        """
        Determine trend direction based on indicators.
        
        Args:
            indicators: Dictionary of technical indicators
            df: DataFrame with price data
            
        Returns:
            Trend direction: 'bullish', 'bearish', or 'neutral'
        """
        bullish_signals = 0
        bearish_signals = 0
        
        # RSI signals
        rsi = indicators.get('rsi')
        if rsi is not None:
            if rsi < 30:
                bullish_signals += 1  # Oversold
            elif rsi > 70:
                bearish_signals += 1  # Overbought
            elif 40 < rsi < 60:
                # Neutral zone
                pass
        
        # Moving average signals
        current_price = indicators.get('current_price', 0)
        sma_20 = indicators.get('sma_20')
        sma_50 = indicators.get('sma_50')
        ema_12 = indicators.get('ema_12')
        ema_26 = indicators.get('ema_26')
        
        if sma_20 and current_price > sma_20:
            bullish_signals += 1
        elif sma_20 and current_price < sma_20:
            bearish_signals += 1
        
        if sma_50 and current_price > sma_50:
            bullish_signals += 1
        elif sma_50 and current_price < sma_50:
            bearish_signals += 1
        
        if ema_12 and ema_26 and ema_12 > ema_26:
            bullish_signals += 1
        elif ema_12 and ema_26 and ema_12 < ema_26:
            bearish_signals += 1
        
        # MACD signals
        macd = indicators.get('macd')
        macd_signal = indicators.get('macd_signal')
        macd_histogram = indicators.get('macd_histogram')
        
        if macd and macd_signal:
            if macd > macd_signal:
                bullish_signals += 1
            else:
                bearish_signals += 1
        
        if macd_histogram and macd_histogram > 0:
            bullish_signals += 1
        elif macd_histogram and macd_histogram < 0:
            bearish_signals += 1
        
        # Bollinger Bands signals
        bb_upper = indicators.get('bb_upper')
        bb_lower = indicators.get('bb_lower')
        
        if bb_upper and bb_lower and current_price:
            if current_price < bb_lower:
                bullish_signals += 1  # Price near lower band, potential bounce
            elif current_price > bb_upper:
                bearish_signals += 1  # Price near upper band, potential reversal
        
        # Price momentum
        if len(df) >= 2:
            price_change = ((df['price_usd'].iloc[-1] - df['price_usd'].iloc[-2]) / 
                           df['price_usd'].iloc[-2]) * 100
            if price_change > 1:
                bullish_signals += 1
            elif price_change < -1:
                bearish_signals += 1
        
        # Volume signals
        volume_trend = indicators.get('volume_trend', 'normal')
        if volume_trend == 'high':
            # High volume confirms trend
            if bullish_signals > bearish_signals:
                bullish_signals += 1
            elif bearish_signals > bullish_signals:
                bearish_signals += 1
        
        # Determine final trend
        if bullish_signals > bearish_signals + 1:
            return 'bullish'
        elif bearish_signals > bullish_signals + 1:
            return 'bearish'
        else:
            return 'neutral'
    
    def _predict_price(
        self,
        current_price: float,
        indicators: Dict,
        trend_direction: str,
        timeframe: str
    ) -> float:
        """
        Predict future price based on current price, indicators, and trend.
        
        Args:
            current_price: Current price
            indicators: Technical indicators
            trend_direction: Trend direction
            timeframe: Prediction timeframe
            
        Returns:
            Predicted price
        """
        # Base prediction on current price
        predicted_price = current_price
        
        # Timeframe multipliers (expected percentage change ranges)
        timeframe_multipliers = {
            '1h': 0.02,    # ±2% for 1 hour
            '4h': 0.05,    # ±5% for 4 hours
            '24h': 0.10,   # ±10% for 24 hours
            '7d': 0.20,    # ±20% for 7 days
            '30d': 0.40    # ±40% for 30 days
        }
        
        multiplier = timeframe_multipliers.get(timeframe, 0.05)
        
        # Adjust based on trend
        if trend_direction == 'bullish':
            # Positive price movement expected
            price_change_pct = multiplier * (0.5 + (indicators.get('rsi', 50) - 30) / 80 if indicators.get('rsi') else 0.5)
            predicted_price = current_price * (1 + price_change_pct)
        elif trend_direction == 'bearish':
            # Negative price movement expected
            price_change_pct = multiplier * (0.5 + (70 - indicators.get('rsi', 50)) / 80 if indicators.get('rsi') else 0.5)
            predicted_price = current_price * (1 - price_change_pct)
        else:
            # Neutral - small random variation
            predicted_price = current_price * (1 + (multiplier * 0.1))
        
        # Apply support/resistance levels from Bollinger Bands
        bb_upper = indicators.get('bb_upper')
        bb_lower = indicators.get('bb_lower')
        
        if bb_upper and bb_lower:
            # Cap prediction within reasonable bounds
            predicted_price = max(bb_lower * 0.95, min(bb_upper * 1.05, predicted_price))
        
        return round(predicted_price, 8)
    
    def _calculate_confidence(
        self,
        indicators: Dict,
        trend_direction: str,
        df: pd.DataFrame,
        timeframe: str = '24h'
    ) -> int:
        """
        Calculate confidence score (0-100) for the prediction.
        
        Args:
            indicators: Technical indicators
            trend_direction: Trend direction
            df: DataFrame with price data
            timeframe: Timeframe string for confidence adjustment
            
        Returns:
            Confidence score (0-100)
        """
        confidence = 50  # Base confidence
        
        # Adjust base confidence based on timeframe
        # Longer timeframes have inherently lower confidence
        timeframe_confidence_adjustment = {
            '1h': 0,      # No adjustment for short-term
            '4h': -2,     # Slight reduction
            '24h': -5,    # Moderate reduction
            '7d': -15,    # Significant reduction for weekly
            '30d': -25    # Large reduction for monthly
        }
        confidence += timeframe_confidence_adjustment.get(timeframe, 0)
        
        # Increase confidence if we have more indicators
        indicator_count = sum(1 for v in indicators.values() if v is not None and isinstance(v, (int, float)))
        confidence += min(20, indicator_count * 2)
        
        # Increase confidence if trend signals are strong
        if trend_direction != 'neutral':
            confidence += 10
        
        # Increase confidence if RSI is in extreme zones (strong signal)
        rsi = indicators.get('rsi')
        if rsi is not None:
            if rsi < 25 or rsi > 75:
                confidence += 10
            elif 30 < rsi < 40 or 60 < rsi < 70:
                confidence += 5
        
        # Increase confidence with more data points
        if len(df) > 100:
            confidence += 10
        elif len(df) > 50:
            confidence += 5
        
        # Decrease confidence if indicators conflict
        sma_20 = indicators.get('sma_20')
        sma_50 = indicators.get('sma_50')
        current_price = indicators.get('current_price')
        
        if sma_20 and sma_50 and current_price:
            if (current_price > sma_20 and current_price < sma_50) or \
               (current_price < sma_20 and current_price > sma_50):
                confidence -= 10  # Conflicting signals
        
        # Ensure confidence is within bounds
        confidence = max(0, min(100, confidence))
        
        return int(confidence)
    
    def _generate_reasoning(
        self,
        indicators: Dict,
        trend_direction: str,
        predicted_price: float,
        current_price: float,
        timeframe: str
    ) -> str:
        """
        Generate human-readable reasoning for the prediction.
        
        Args:
            indicators: Technical indicators
            trend_direction: Trend direction
            predicted_price: Predicted price
            current_price: Current price
            timeframe: Prediction timeframe
            
        Returns:
            Reasoning text
        """
        price_change_pct = ((predicted_price - current_price) / current_price) * 100
        direction = "increase" if price_change_pct > 0 else "decrease"
        
        # Format timeframe display
        timeframe_display = {
            '1h': '1 hour',
            '4h': '4 hours',
            '24h': '24 hours',
            '7d': '7 days',
            '30d': '30 days (1 month)'
        }
        timeframe_label = timeframe_display.get(timeframe, timeframe)
        
        reasoning_parts = [
            f"Analysis for {timeframe_label} timeframe:",
            f"Current price: ${current_price:.8f}",
            f"Predicted price: ${predicted_price:.8f} ({abs(price_change_pct):.2f}% {direction})",
            f"Trend: {trend_direction.upper()}"
        ]
        
        # Add note about timeframe reliability for longer periods
        if timeframe in ['7d', '30d']:
            reasoning_parts.append(f"Note: Longer-term predictions ({timeframe_label}) have higher uncertainty")
        
        # Add RSI analysis
        rsi = indicators.get('rsi')
        if rsi is not None:
            if rsi < 30:
                reasoning_parts.append(f"RSI ({rsi:.2f}) indicates oversold conditions")
            elif rsi > 70:
                reasoning_parts.append(f"RSI ({rsi:.2f}) indicates overbought conditions")
            else:
                reasoning_parts.append(f"RSI ({rsi:.2f}) is in neutral range")
        
        # Add moving average analysis
        sma_20 = indicators.get('sma_20')
        sma_50 = indicators.get('sma_50')
        if sma_20 and sma_50:
            if current_price > sma_20 > sma_50:
                reasoning_parts.append("Price is above both SMA 20 and SMA 50 (bullish)")
            elif current_price < sma_20 < sma_50:
                reasoning_parts.append("Price is below both SMA 20 and SMA 50 (bearish)")
        
        # Add MACD analysis
        macd = indicators.get('macd')
        macd_signal = indicators.get('macd_signal')
        if macd is not None and macd_signal is not None:
            if macd > macd_signal:
                reasoning_parts.append("MACD is above signal line (bullish momentum)")
            else:
                reasoning_parts.append("MACD is below signal line (bearish momentum)")
        
        # Add volume analysis
        volume_trend = indicators.get('volume_trend')
        if volume_trend:
            reasoning_parts.append(f"Volume is {volume_trend}")
        
        return " | ".join(reasoning_parts)
    
    def run_analysis(self):
        """Run analysis for all timeframes and save results."""
        try:
            logger.info("Starting analysis run")
            self.db.update_script_status('running', 'Analysis in progress')
            
            # Fetch market data - need more data for longer timeframes (30 days = 720 hours)
            # Add buffer for analysis calculations
            df = self.db.get_market_data(hours=800)
            
            if df.empty:
                error_msg = "No market data available for analysis"
                logger.error(error_msg)
                self.db.update_script_status('error', error_msg)
                return
            
            # Analyze each timeframe
            timeframes = ['1h', '4h', '24h', '7d', '30d']
            
            for timeframe in timeframes:
                try:
                    logger.info(f"Analyzing {timeframe} timeframe")
                    
                    predicted_price, confidence_score, trend_direction, indicators, reasoning = \
                        self.analyze_timeframe(df, timeframe)
                    
                    # Save result to database
                    self.db.save_analysis_result(
                        timeframe=timeframe,
                        predicted_price=predicted_price,
                        confidence_score=confidence_score,
                        trend_direction=trend_direction,
                        technical_indicators=indicators,
                        reasoning=reasoning
                    )
                    
                    logger.info(
                        f"{timeframe} analysis complete: "
                        f"${predicted_price:.8f} ({trend_direction}, {confidence_score}% confidence)"
                    )
                    
                except Exception as e:
                    logger.error(f"Error analyzing {timeframe} timeframe: {e}")
                    continue
            
            # Update status
            next_run = datetime.utcnow() + timedelta(minutes=ANALYSIS_INTERVAL_MINUTES)
            self.db.update_script_status('success', 'Analysis completed successfully', next_run)
            logger.info("Analysis run completed successfully")
            
        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            self.db.update_script_status('error', error_msg)
            raise
    
    def start_scheduler(self):
        """Start the scheduler to run analysis periodically."""
        scheduler = BlockingScheduler()
        
        # Schedule analysis to run at intervals
        trigger = IntervalTrigger(minutes=ANALYSIS_INTERVAL_MINUTES)
        scheduler.add_job(
            self.run_analysis,
            trigger=trigger,
            id='price_analysis',
            name='Dogecoin Price Analysis',
            replace_existing=True
        )
        
        # Run initial analysis
        logger.info("Running initial analysis...")
        self.run_analysis()
        
        # Calculate next run time
        next_run = datetime.utcnow() + timedelta(minutes=ANALYSIS_INTERVAL_MINUTES)
        logger.info(f"Scheduler started. Next analysis at: {next_run}")
        logger.info(f"Analysis will run every {ANALYSIS_INTERVAL_MINUTES} minutes")
        
        try:
            scheduler.start()
        except (KeyboardInterrupt, SystemExit):
            logger.info("Scheduler stopped")
            self.db.close()
            sys.exit(0)


def main():
    """Main entry point for the analyzer."""
    logger.info("Starting DogeAnalyze Price Predictor")
    
    try:
        predictor = PricePredictor()
        predictor.start_scheduler()
    except Exception as e:
        logger.error(f"Failed to start predictor: {e}", exc_info=True)
        sys.exit(1)


if __name__ == '__main__':
    main()

