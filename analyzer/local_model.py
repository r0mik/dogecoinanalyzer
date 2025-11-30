"""Local LLM model integration for enhanced analysis (e.g., LM Studio)."""

import json
from typing import Dict, Optional
import requests
from requests.exceptions import RequestException, Timeout

from config.settings import (
    LOCAL_MODEL_ENABLED,
    LOCAL_MODEL_URL,
    LOCAL_MODEL_TIMEOUT,
    LOCAL_MODEL_TEMPERATURE,
    LOCAL_MODEL_MAX_TOKENS
)
from utils.logger import setup_logger

logger = setup_logger('analyzer.local_model')


class LocalModelAnalyzer:
    """Interface to local LLM model for enhanced market analysis."""
    
    def __init__(self):
        """Initialize local model analyzer."""
        self.enabled = LOCAL_MODEL_ENABLED
        self.base_url = LOCAL_MODEL_URL.rstrip('/')
        self.timeout = LOCAL_MODEL_TIMEOUT
        self.temperature = LOCAL_MODEL_TEMPERATURE
        self.max_tokens = LOCAL_MODEL_MAX_TOKENS
        
        if self.enabled:
            logger.info(f"Local model analyzer enabled: {self.base_url}")
        else:
            logger.debug("Local model analyzer disabled")
    
    def is_available(self) -> bool:
        """
        Check if local model is enabled and available.
        
        Returns:
            True if model is enabled and reachable, False otherwise
        """
        if not self.enabled:
            return False
        
        try:
            # Try to reach the health endpoint or base URL
            response = requests.get(
                f"{self.base_url}/v1/models",
                timeout=5
            )
            return response.status_code == 200
        except (RequestException, Timeout):
            return False
    
    def generate_analysis(
        self,
        timeframe: str,
        current_price: float,
        predicted_price: float,
        trend_direction: str,
        indicators: Dict,
        basic_reasoning: str
    ) -> Optional[str]:
        """
        Generate enhanced analysis using local LLM model.
        
        Args:
            timeframe: Analysis timeframe (e.g., '1h', '7d', '30d')
            current_price: Current Dogecoin price
            predicted_price: Predicted price
            trend_direction: Trend direction ('bullish', 'bearish', 'neutral')
            indicators: Dictionary of technical indicators
            basic_reasoning: Basic reasoning from technical analysis
            
        Returns:
            Enhanced analysis text or None if generation fails
        """
        if not self.enabled:
            return None
        
        try:
            prompt = self._build_prompt(
                timeframe, current_price, predicted_price,
                trend_direction, indicators, basic_reasoning
            )
            
            response = self._call_model(prompt)
            
            if response:
                logger.debug(f"Generated enhanced analysis for {timeframe}")
                return response
            else:
                logger.warning(f"Failed to generate analysis for {timeframe}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating LLM analysis: {e}", exc_info=True)
            return None
    
    def _build_prompt(
        self,
        timeframe: str,
        current_price: float,
        predicted_price: float,
        trend_direction: str,
        indicators: Dict,
        basic_reasoning: str
    ) -> str:
        """
        Build prompt for LLM analysis.
        
        Args:
            timeframe: Analysis timeframe
            current_price: Current price
            predicted_price: Predicted price
            trend_direction: Trend direction
            indicators: Technical indicators
            basic_reasoning: Basic reasoning
            
        Returns:
            Formatted prompt string
        """
        price_change_pct = ((predicted_price - current_price) / current_price) * 100
        
        # Format indicators for prompt
        indicators_text = self._format_indicators(indicators)
        
        prompt = f"""You are a cryptocurrency market analyst specializing in Dogecoin (DOGE) analysis.

Current Market Analysis:
- Timeframe: {timeframe}
- Current Price: ${current_price:.8f}
- Predicted Price: ${predicted_price:.8f} ({price_change_pct:+.2f}%)
- Trend Direction: {trend_direction.upper()}

Technical Indicators:
{indicators_text}

Basic Technical Analysis:
{basic_reasoning}

Please provide a deeper analysis that:
1. Interprets the technical indicators in the context of Dogecoin's market behavior
2. Considers market sentiment and potential catalysts
3. Explains the reasoning behind the {trend_direction} trend
4. Discusses potential risks and opportunities
5. Provides context for the {timeframe} timeframe prediction

Keep the analysis concise, professional, and focused on actionable insights. 
Do not provide financial advice, only market analysis.

Enhanced Analysis:"""
        
        return prompt
    
    def _format_indicators(self, indicators: Dict) -> str:
        """
        Format technical indicators for prompt.
        
        Args:
            indicators: Dictionary of technical indicators
            
        Returns:
            Formatted string of indicators
        """
        lines = []
        
        # RSI
        rsi = indicators.get('rsi')
        if rsi is not None:
            rsi_status = "Oversold" if rsi < 30 else "Overbought" if rsi > 70 else "Neutral"
            lines.append(f"- RSI: {rsi:.2f} ({rsi_status})")
        
        # Moving Averages
        sma_20 = indicators.get('sma_20')
        sma_50 = indicators.get('sma_50')
        sma_200 = indicators.get('sma_200')
        if sma_20:
            lines.append(f"- SMA 20: ${sma_20:.8f}")
        if sma_50:
            lines.append(f"- SMA 50: ${sma_50:.8f}")
        if sma_200:
            lines.append(f"- SMA 200: ${sma_200:.8f}")
        
        # EMAs
        ema_12 = indicators.get('ema_12')
        ema_26 = indicators.get('ema_26')
        if ema_12:
            lines.append(f"- EMA 12: ${ema_12:.8f}")
        if ema_26:
            lines.append(f"- EMA 26: ${ema_26:.8f}")
        
        # MACD
        macd = indicators.get('macd')
        macd_signal = indicators.get('macd_signal')
        macd_histogram = indicators.get('macd_histogram')
        if macd is not None:
            macd_trend = "Bullish" if macd > macd_signal else "Bearish" if macd_signal else "Neutral"
            lines.append(f"- MACD: {macd:.8f} (Signal: {macd_signal:.8f}, {macd_trend})")
        
        # Bollinger Bands
        bb_upper = indicators.get('bb_upper')
        bb_lower = indicators.get('bb_lower')
        bb_middle = indicators.get('bb_middle')
        if bb_upper and bb_lower:
            lines.append(f"- Bollinger Bands: Upper ${bb_upper:.8f}, Middle ${bb_middle:.8f}, Lower ${bb_lower:.8f}")
        
        # Volume
        volume_trend = indicators.get('volume_trend')
        volume_ratio = indicators.get('volume_ratio')
        if volume_trend:
            lines.append(f"- Volume: {volume_trend.upper()} (Ratio: {volume_ratio:.2f}x)")
        
        return "\n".join(lines) if lines else "No indicators available"
    
    def _call_model(self, prompt: str) -> Optional[str]:
        """
        Call local LLM model API.
        
        Args:
            prompt: Prompt text
            
        Returns:
            Generated text or None if call fails
        """
        try:
            # LM Studio and OpenAI-compatible APIs use /v1/chat/completions
            url = f"{self.base_url}/v1/chat/completions"
            
            payload = {
                "model": "local-model",  # LM Studio uses this or the model name
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a professional cryptocurrency market analyst."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": self.temperature,
                "max_tokens": self.max_tokens,
                "stream": False
            }
            
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            response.raise_for_status()
            data = response.json()
            
            # Extract response text
            if 'choices' in data and len(data['choices']) > 0:
                message = data['choices'][0].get('message', {})
                content = message.get('content', '').strip()
                return content if content else None
            
            logger.warning("Unexpected response format from local model")
            return None
            
        except Timeout:
            logger.error(f"Local model request timed out after {self.timeout}s")
            return None
        except RequestException as e:
            logger.error(f"Error calling local model: {e}")
            return None
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            logger.error(f"Error parsing local model response: {e}")
            return None
    
    def enhance_reasoning(
        self,
        timeframe: str,
        current_price: float,
        predicted_price: float,
        trend_direction: str,
        indicators: Dict,
        basic_reasoning: str
    ) -> str:
        """
        Enhance basic reasoning with LLM analysis if available.
        
        Args:
            timeframe: Analysis timeframe
            current_price: Current price
            predicted_price: Predicted price
            trend_direction: Trend direction
            indicators: Technical indicators
            basic_reasoning: Basic reasoning text
            
        Returns:
            Enhanced reasoning (with LLM analysis if available, otherwise basic)
        """
        if not self.enabled:
            return basic_reasoning
        
        enhanced_analysis = self.generate_analysis(
            timeframe, current_price, predicted_price,
            trend_direction, indicators, basic_reasoning
        )
        
        if enhanced_analysis:
            # Combine basic reasoning with enhanced analysis
            return f"{basic_reasoning}\n\n--- Enhanced Analysis ---\n{enhanced_analysis}"
        else:
            # Fall back to basic reasoning if LLM fails
            logger.debug("Falling back to basic reasoning (LLM unavailable)")
            return basic_reasoning

