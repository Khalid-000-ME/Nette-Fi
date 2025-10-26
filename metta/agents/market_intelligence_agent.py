"""
Market Intelligence Agent - Real-time market analysis and prediction
Uses ASI (Fetch.ai) uAgent framework for autonomous market monitoring
"""

from uagents import Agent, Context, Model
from typing import Dict, List, Any, Optional
import json
import numpy as np
import asyncio
import aiohttp
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class MarketSignal:
    signal_type: str
    strength: float
    confidence: float
    timeframe: str
    description: str

class MarketDataRequest(Model):
    token_pair: str
    timeframe: str
    analysis_depth: str

class MarketIntelligenceResponse(Model):
    market_sentiment: Dict[str, Any]
    price_predictions: Dict[str, Any]
    volume_analysis: Dict[str, Any]
    trend_signals: List[Dict[str, Any]]
    risk_indicators: Dict[str, Any]
    optimal_timing: Dict[str, Any]

class MarketIntelligenceAgent:
    def __init__(self, agent_address: str = "market_intel_agent"):
        self.agent = Agent(
            name="market_intelligence_agent",
            seed="market_intel_seed_67890",
            port=8002,
            endpoint=["http://localhost:8002/submit"]
        )
        
        # Market data sources
        self.data_sources = {
            "coingecko": "https://api.coingecko.com/api/v3",
            "dexscreener": "https://api.dexscreener.com/latest",
            "defipulse": "https://data-api.defipulse.com/api/v1"
        }
        
        # Technical indicators cache
        self.indicators_cache = {}
        self.last_update = None
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        @self.agent.on_message(model=MarketDataRequest)
        async def handle_market_analysis(ctx: Context, sender: str, msg: MarketDataRequest):
            """Handle market intelligence requests"""
            try:
                intelligence = await self._analyze_market_conditions(
                    msg.token_pair,
                    msg.timeframe,
                    msg.analysis_depth
                )
                
                response = MarketIntelligenceResponse(
                    market_sentiment=intelligence['sentiment'],
                    price_predictions=intelligence['predictions'],
                    volume_analysis=intelligence['volume'],
                    trend_signals=intelligence['signals'],
                    risk_indicators=intelligence['risk_indicators'],
                    optimal_timing=intelligence['timing']
                )
                
                await ctx.send(sender, response)
                
            except Exception as e:
                ctx.logger.error(f"Market analysis failed: {str(e)}")
    
    async def _analyze_market_conditions(
        self,
        token_pair: str,
        timeframe: str = "1h",
        analysis_depth: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Comprehensive market analysis"""
        
        # Fetch real-time market data
        market_data = await self._fetch_market_data(token_pair, timeframe)
        
        # Analyze market sentiment
        sentiment_analysis = await self._analyze_sentiment(market_data)
        
        # Generate price predictions
        price_predictions = await self._predict_price_movements(market_data)
        
        # Analyze volume patterns
        volume_analysis = await self._analyze_volume_patterns(market_data)
        
        # Detect trend signals
        trend_signals = await self._detect_trend_signals(market_data)
        
        # Assess risk indicators
        risk_indicators = await self._assess_market_risks(market_data)
        
        # Determine optimal timing
        optimal_timing = await self._calculate_optimal_timing(market_data, trend_signals)
        
        return {
            "sentiment": sentiment_analysis,
            "predictions": price_predictions,
            "volume": volume_analysis,
            "signals": trend_signals,
            "risk_indicators": risk_indicators,
            "timing": optimal_timing,
            "data_quality": self._assess_data_quality(market_data),
            "last_updated": datetime.now().isoformat()
        }
    
    async def _fetch_market_data(self, token_pair: str, timeframe: str) -> Dict[str, Any]:
        """Fetch market data from multiple sources"""
        market_data = {
            "price_data": [],
            "volume_data": [],
            "liquidity_data": {},
            "social_metrics": {},
            "on_chain_metrics": {}
        }
        
        try:
            # Simulate market data fetching (replace with real API calls)
            base_price = 3000  # ETH price
            
            # Generate realistic price data
            price_points = []
            current_price = base_price
            
            for i in range(24):  # 24 hours of data
                # Add some realistic price movement
                change = np.random.normal(0, 0.02) * current_price
                current_price += change
                
                price_points.append({
                    "timestamp": (datetime.now() - timedelta(hours=23-i)).isoformat(),
                    "price": current_price,
                    "volume": np.random.uniform(1000000, 5000000),
                    "high": current_price * 1.01,
                    "low": current_price * 0.99
                })
            
            market_data["price_data"] = price_points
            
            # Add liquidity metrics
            market_data["liquidity_data"] = {
                "total_liquidity": np.random.uniform(50000000, 200000000),
                "liquidity_depth": np.random.uniform(0.7, 0.95),
                "spread": np.random.uniform(0.001, 0.005)
            }
            
            # Add social metrics
            market_data["social_metrics"] = {
                "sentiment_score": np.random.uniform(-1, 1),
                "social_volume": np.random.uniform(1000, 10000),
                "trending_score": np.random.uniform(0, 100)
            }
            
        except Exception as e:
            print(f"Error fetching market data: {e}")
        
        return market_data
    
    async def _analyze_sentiment(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market sentiment from multiple indicators"""
        
        price_data = market_data.get("price_data", [])
        social_metrics = market_data.get("social_metrics", {})
        
        if not price_data:
            return {"sentiment": "neutral", "confidence": 0.5}
        
        # Price momentum sentiment
        recent_prices = [p["price"] for p in price_data[-6:]]  # Last 6 hours
        price_trend = (recent_prices[-1] - recent_prices[0]) / recent_prices[0]
        
        # Volume sentiment
        recent_volumes = [p["volume"] for p in price_data[-6:]]
        volume_trend = np.mean(recent_volumes[-3:]) / np.mean(recent_volumes[:3])
        
        # Social sentiment
        social_sentiment = social_metrics.get("sentiment_score", 0)
        
        # Combine sentiments
        combined_sentiment = (
            0.4 * np.tanh(price_trend * 10) +  # Price weight
            0.3 * np.tanh((volume_trend - 1) * 5) +  # Volume weight
            0.3 * social_sentiment  # Social weight
        )
        
        sentiment_label = "bullish" if combined_sentiment > 0.2 else "bearish" if combined_sentiment < -0.2 else "neutral"
        
        return {
            "sentiment": sentiment_label,
            "score": combined_sentiment,
            "confidence": min(abs(combined_sentiment) + 0.5, 0.95),
            "components": {
                "price_sentiment": price_trend,
                "volume_sentiment": volume_trend - 1,
                "social_sentiment": social_sentiment
            }
        }
    
    async def _predict_price_movements(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict short-term price movements"""
        
        price_data = market_data.get("price_data", [])
        if len(price_data) < 10:
            return {"predictions": [], "confidence": 0.3}
        
        prices = [p["price"] for p in price_data]
        
        # Simple trend analysis
        short_ma = np.mean(prices[-5:])  # 5-period moving average
        long_ma = np.mean(prices[-10:])  # 10-period moving average
        
        # Price momentum
        momentum = (prices[-1] - prices[-5]) / prices[-5]
        
        # Volatility
        volatility = np.std(prices[-10:]) / np.mean(prices[-10:])
        
        # Predict next few periods
        predictions = []
        current_price = prices[-1]
        
        for i in range(1, 4):  # Predict next 3 periods
            # Simple momentum-based prediction
            predicted_change = momentum * (0.8 ** i)  # Decay momentum
            predicted_price = current_price * (1 + predicted_change)
            
            predictions.append({
                "period": i,
                "predicted_price": predicted_price,
                "confidence": max(0.4, 0.8 - volatility * 2),
                "direction": "up" if predicted_change > 0 else "down",
                "magnitude": abs(predicted_change)
            })
        
        return {
            "predictions": predictions,
            "trend_strength": abs(short_ma - long_ma) / long_ma,
            "momentum": momentum,
            "volatility": volatility,
            "support_level": min(prices[-10:]),
            "resistance_level": max(prices[-10:])
        }
    
    async def _analyze_volume_patterns(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze volume patterns and anomalies"""
        
        price_data = market_data.get("price_data", [])
        if not price_data:
            return {"volume_trend": "unknown"}
        
        volumes = [p["volume"] for p in price_data]
        prices = [p["price"] for p in price_data]
        
        # Volume trend analysis
        recent_volume = np.mean(volumes[-6:])
        historical_volume = np.mean(volumes[:-6]) if len(volumes) > 6 else recent_volume
        
        volume_ratio = recent_volume / historical_volume if historical_volume > 0 else 1
        
        # Price-volume correlation
        price_changes = np.diff(prices)
        volume_changes = np.diff(volumes)
        
        correlation = np.corrcoef(price_changes, volume_changes[:-1])[0, 1] if len(price_changes) > 1 else 0
        
        # Volume anomaly detection
        volume_zscore = (recent_volume - np.mean(volumes)) / np.std(volumes) if np.std(volumes) > 0 else 0
        
        return {
            "volume_trend": "increasing" if volume_ratio > 1.2 else "decreasing" if volume_ratio < 0.8 else "stable",
            "volume_ratio": volume_ratio,
            "price_volume_correlation": correlation,
            "volume_anomaly": abs(volume_zscore) > 2,
            "volume_zscore": volume_zscore,
            "average_volume": np.mean(volumes),
            "volume_volatility": np.std(volumes) / np.mean(volumes) if np.mean(volumes) > 0 else 0
        }
    
    async def _detect_trend_signals(self, market_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect various trend and trading signals"""
        
        price_data = market_data.get("price_data", [])
        if len(price_data) < 15:
            return []
        
        prices = [p["price"] for p in price_data]
        volumes = [p["volume"] for p in price_data]
        
        signals = []
        
        # Moving average crossover
        if len(prices) >= 20:
            short_ma = np.mean(prices[-5:])
            long_ma = np.mean(prices[-20:])
            prev_short_ma = np.mean(prices[-6:-1])
            prev_long_ma = np.mean(prices[-21:-1])
            
            if short_ma > long_ma and prev_short_ma <= prev_long_ma:
                signals.append({
                    "type": "MA_CROSSOVER_BULLISH",
                    "strength": 0.7,
                    "confidence": 0.8,
                    "description": "Short MA crossed above Long MA"
                })
            elif short_ma < long_ma and prev_short_ma >= prev_long_ma:
                signals.append({
                    "type": "MA_CROSSOVER_BEARISH",
                    "strength": 0.7,
                    "confidence": 0.8,
                    "description": "Short MA crossed below Long MA"
                })
        
        # Volume breakout
        avg_volume = np.mean(volumes[-10:])
        recent_volume = volumes[-1]
        
        if recent_volume > avg_volume * 2:
            price_change = (prices[-1] - prices[-2]) / prices[-2]
            signals.append({
                "type": "VOLUME_BREAKOUT",
                "strength": min(recent_volume / avg_volume / 2, 1.0),
                "confidence": 0.75,
                "description": f"High volume {'surge' if price_change > 0 else 'dump'} detected"
            })
        
        # Price momentum
        momentum = (prices[-1] - prices[-5]) / prices[-5]
        if abs(momentum) > 0.05:  # 5% move
            signals.append({
                "type": "MOMENTUM_SIGNAL",
                "strength": min(abs(momentum) * 10, 1.0),
                "confidence": 0.6,
                "description": f"Strong {'bullish' if momentum > 0 else 'bearish'} momentum"
            })
        
        return signals
    
    async def _assess_market_risks(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess various market risk factors"""
        
        price_data = market_data.get("price_data", [])
        liquidity_data = market_data.get("liquidity_data", {})
        
        if not price_data:
            return {"overall_risk": "high"}
        
        prices = [p["price"] for p in price_data]
        
        # Volatility risk
        volatility = np.std(prices[-10:]) / np.mean(prices[-10:]) if len(prices) >= 10 else 0.1
        
        # Liquidity risk
        liquidity_score = liquidity_data.get("liquidity_depth", 0.5)
        spread = liquidity_data.get("spread", 0.01)
        
        # Market depth risk
        market_depth_risk = 1 - liquidity_score
        
        # Spread risk
        spread_risk = min(spread * 200, 1.0)  # Normalize spread to 0-1
        
        # Overall risk assessment
        overall_risk = (
            0.4 * volatility * 10 +  # Volatility component
            0.3 * market_depth_risk +  # Liquidity component
            0.3 * spread_risk  # Spread component
        )
        
        risk_level = "low" if overall_risk < 0.3 else "medium" if overall_risk < 0.6 else "high"
        
        return {
            "overall_risk": risk_level,
            "risk_score": min(overall_risk, 1.0),
            "volatility_risk": volatility,
            "liquidity_risk": market_depth_risk,
            "spread_risk": spread_risk,
            "risk_factors": self._identify_risk_factors(volatility, market_depth_risk, spread_risk)
        }
    
    def _identify_risk_factors(self, volatility: float, liquidity_risk: float, spread_risk: float) -> List[str]:
        """Identify specific risk factors"""
        factors = []
        
        if volatility > 0.05:
            factors.append("High price volatility")
        if liquidity_risk > 0.4:
            factors.append("Limited market liquidity")
        if spread_risk > 0.3:
            factors.append("Wide bid-ask spreads")
        
        return factors
    
    async def _calculate_optimal_timing(
        self,
        market_data: Dict[str, Any],
        trend_signals: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Calculate optimal timing for trade execution"""
        
        # Analyze signal strength
        signal_strength = sum(s.get("strength", 0) for s in trend_signals) / len(trend_signals) if trend_signals else 0.5
        
        # Market condition assessment
        liquidity_data = market_data.get("liquidity_data", {})
        spread = liquidity_data.get("spread", 0.01)
        
        # Time-based factors (simplified)
        current_hour = datetime.now().hour
        
        # Trading activity is typically higher during certain hours
        activity_multiplier = 1.0
        if 8 <= current_hour <= 16:  # Business hours
            activity_multiplier = 1.2
        elif 0 <= current_hour <= 6:  # Low activity
            activity_multiplier = 0.8
        
        # Calculate timing score
        timing_score = (
            0.4 * signal_strength +
            0.3 * (1 - spread * 100) +  # Lower spread = better timing
            0.3 * activity_multiplier
        )
        
        timing_recommendation = "immediate" if timing_score > 0.7 else "wait" if timing_score < 0.4 else "monitor"
        
        return {
            "recommendation": timing_recommendation,
            "timing_score": timing_score,
            "signal_strength": signal_strength,
            "market_activity": activity_multiplier,
            "optimal_window": self._suggest_optimal_window(timing_score),
            "factors": {
                "signal_alignment": signal_strength > 0.6,
                "liquidity_adequate": spread < 0.005,
                "market_active": activity_multiplier > 1.0
            }
        }
    
    def _suggest_optimal_window(self, timing_score: float) -> str:
        """Suggest optimal execution window"""
        if timing_score > 0.8:
            return "Next 15 minutes"
        elif timing_score > 0.6:
            return "Next 1 hour"
        elif timing_score > 0.4:
            return "Next 4 hours"
        else:
            return "Wait for better conditions"
    
    def _assess_data_quality(self, market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess the quality of market data"""
        
        price_data = market_data.get("price_data", [])
        
        data_completeness = len(price_data) / 24  # Assuming 24 data points expected
        data_freshness = 1.0  # Assume fresh data for now
        
        quality_score = (data_completeness + data_freshness) / 2
        
        return {
            "quality_score": quality_score,
            "completeness": data_completeness,
            "freshness": data_freshness,
            "reliability": "high" if quality_score > 0.8 else "medium" if quality_score > 0.6 else "low"
        }

    async def get_market_intelligence(
        self,
        token_pair: str = "ETH/USDC",
        timeframe: str = "1h",
        analysis_depth: str = "comprehensive"
    ) -> Dict[str, Any]:
        """Main entry point for market intelligence"""
        return await self._analyze_market_conditions(token_pair, timeframe, analysis_depth)

    def get_agent(self):
        """Return the uAgent instance"""
        return self.agent
