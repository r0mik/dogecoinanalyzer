"""Local LLM model integration for enhanced analysis (e.g., LM Studio)."""

import json
import time
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
            logger.debug("Local model check skipped (disabled)")
            return False
        
        try:
            logger.debug(f"Checking local model availability at {self.base_url}/v1/models")
            start_time = time.time()
            
            # Try to reach the health endpoint or base URL
            response = requests.get(
                f"{self.base_url}/v1/models",
                timeout=5
            )
            
            elapsed = time.time() - start_time
            is_available = response.status_code == 200
            
            if is_available:
                logger.info(f"Local model is available (response time: {elapsed:.2f}s, status: {response.status_code})")
                try:
                    models_data = response.json()
                    if 'data' in models_data and len(models_data['data']) > 0:
                        model_name = models_data['data'][0].get('id', 'unknown')
                        logger.info(f"Available model: {model_name}")
                except (KeyError, ValueError, json.JSONDecodeError):
                    logger.debug("Could not parse model information from response")
            else:
                logger.warning(f"Local model check failed (status: {response.status_code}, time: {elapsed:.2f}s)")
            
            return is_available
            
        except Timeout:
            logger.warning(f"Local model availability check timed out after 5s")
            return False
        except RequestException as e:
            logger.warning(f"Local model availability check failed: {e}")
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
            logger.debug(f"LLM analysis skipped for {timeframe} (local model disabled)")
            return None
        
        logger.info(f"[AI Request] Starting LLM analysis generation for {timeframe} timeframe")
        logger.debug(f"[AI Request] Parameters: price=${current_price:.8f}, predicted=${predicted_price:.8f}, trend={trend_direction}")
        
        try:
            prompt_start = time.time()
            prompt = self._build_prompt(
                timeframe, current_price, predicted_price,
                trend_direction, indicators, basic_reasoning
            )
            prompt_time = time.time() - prompt_start
            prompt_size = len(prompt.encode('utf-8'))
            
            logger.debug(f"[AI Request] Prompt built in {prompt_time:.3f}s (size: {prompt_size} bytes, ~{prompt_size//4} tokens)")
            logger.debug(f"[AI Request] Prompt preview: {prompt[:200]}...")
            
            request_start = time.time()
            response = self._call_model(prompt)
            request_time = time.time() - request_start
            
            if response:
                response_size = len(response.encode('utf-8'))
                logger.info(
                    f"[AI Request] Successfully generated analysis for {timeframe} "
                    f"(response time: {request_time:.2f}s, size: {response_size} bytes)"
                )
                logger.debug(f"[AI Request] Response preview: {response[:200]}...")
                return response
            else:
                logger.warning(
                    f"[AI Request] Failed to generate analysis for {timeframe} "
                    f"(request time: {request_time:.2f}s)"
                )
                return None
                
        except Exception as e:
            logger.error(f"[AI Request] Error generating LLM analysis for {timeframe}: {e}", exc_info=True)
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
        
        # Log request details
        payload_size = len(json.dumps(payload).encode('utf-8'))
        logger.info(
            f"[AI Request] Sending request to {url} "
            f"(timeout: {self.timeout}s, temp: {self.temperature}, max_tokens: {self.max_tokens})"
        )
        logger.debug(f"[AI Request] Payload size: {payload_size} bytes")
        logger.debug(f"[AI Request] Request payload: {json.dumps(payload, indent=2)[:500]}...")
        
        request_start = time.time()
        
        try:
            response = requests.post(
                url,
                json=payload,
                timeout=self.timeout,
                headers={"Content-Type": "application/json"}
            )
            
            request_time = time.time() - request_start
            response_size = len(response.content) if response.content else 0
            
            logger.info(
                f"[AI Request] Response received (status: {response.status_code}, "
                f"time: {request_time:.2f}s, size: {response_size} bytes)"
            )
            
            # Log response details
            if response.status_code != 200:
                logger.error(
                    f"[AI Request] Non-200 status code: {response.status_code}. "
                    f"Response: {response.text[:500]}"
                )
            
            response.raise_for_status()
            data = response.json()
            
            # Log token usage if available
            if 'usage' in data:
                usage = data['usage']
                prompt_tokens = usage.get('prompt_tokens', 0)
                completion_tokens = usage.get('completion_tokens', 0)
                total_tokens = usage.get('total_tokens', 0)
                logger.info(
                    f"[AI Request] Token usage - Prompt: {prompt_tokens}, "
                    f"Completion: {completion_tokens}, Total: {total_tokens}"
                )
            
            # Extract response text
            if 'choices' in data and len(data['choices']) > 0:
                choice = data['choices'][0]
                finish_reason = choice.get('finish_reason', 'unknown')
                message = choice.get('message', {})
                content = message.get('content', '').strip()
                
                logger.debug(f"[AI Request] Finish reason: {finish_reason}")
                
                if content:
                    logger.debug(f"[AI Request] Response content length: {len(content)} characters")
                    return content
                else:
                    logger.warning("[AI Request] Empty content in response")
                    return None
            else:
                logger.warning(f"[AI Request] Unexpected response format: {json.dumps(data, indent=2)[:500]}")
                return None
            
        except Timeout:
            request_time = time.time() - request_start
            logger.error(
                f"[AI Request] Request timed out after {request_time:.2f}s "
                f"(configured timeout: {self.timeout}s)"
            )
            return None
            
        except RequestException as e:
            request_time = time.time() - request_start
            logger.error(
                f"[AI Request] Request failed after {request_time:.2f}s: {type(e).__name__}: {e}"
            )
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"[AI Request] Response status: {e.response.status_code}")
                logger.error(f"[AI Request] Response body: {e.response.text[:500]}")
            return None
            
        except (KeyError, ValueError, json.JSONDecodeError) as e:
            request_time = time.time() - request_start
            logger.error(
                f"[AI Request] Response parsing failed after {request_time:.2f}s: "
                f"{type(e).__name__}: {e}"
            )
            logger.debug(f"[AI Request] Response content: {response.text[:1000] if 'response' in locals() else 'N/A'}")
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
            logger.debug(f"[AI Request] Enhancement skipped for {timeframe} (local model disabled)")
            return basic_reasoning
        
        logger.info(f"[AI Request] Attempting to enhance reasoning for {timeframe} timeframe")
        enhance_start = time.time()
        
        enhanced_analysis = self.generate_analysis(
            timeframe, current_price, predicted_price,
            trend_direction, indicators, basic_reasoning
        )
        
        enhance_time = time.time() - enhance_start
        
        if enhanced_analysis:
            # Combine basic reasoning with enhanced analysis
            logger.info(
                f"[AI Request] Successfully enhanced reasoning for {timeframe} "
                f"(total time: {enhance_time:.2f}s)"
            )
            return f"{basic_reasoning}\n\n--- Enhanced Analysis ---\n{enhanced_analysis}"
        else:
            # Fall back to basic reasoning if LLM fails
            logger.warning(
                f"[AI Request] Falling back to basic reasoning for {timeframe} "
                f"(LLM unavailable or failed, time: {enhance_time:.2f}s)"
            )
            return basic_reasoning

