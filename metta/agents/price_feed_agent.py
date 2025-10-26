"""
Price Feed Agent - Handles real-time price data and market analysis
Integrates with frontend /api/get_price route and external price feeds
"""

from uagents import Agent, Context, Model
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)
from typing import Dict, List, Any, Optional
import json
import requests
import asyncio
from datetime import datetime, timedelta
import uuid

from .chat_protocol import (
    ASIChatProtocol, ToolCallRequest, ToolCallResponse
)

class PriceFeedRequest(Model):
    session_id: str
    token_pair: str
    chain: Optional[str] = "ethereum"
    include_history: Optional[bool] = False

class PriceFeedAgent:
    """
    Price Feed Agent for real-time price data and market analysis
    
    Features:
    - Integration with /api/get_price route
    - Multi-source price aggregation (Pyth, CoinGecko, DeFiLlama)
    - Price volatility analysis
    - Market trend detection
    """
    
    def __init__(self, agent_port: int = 8011):
        # Initialize uAgent
        self.agent = Agent(
            name="price_feed_agent",
            seed="price_feed_agent_seed_22222",
            port=agent_port,
            endpoint=[f"http://localhost:{agent_port}/submit"]
        )
        
        self.agent_id = "price_feed_agent"
        self.agent_type = "price_data"
        self.name = "Price Feed Agent"
        
        # Frontend API configuration
        self.frontend_api_base = "http://localhost:3000/api"
        
        # Chat protocol integration
        self.chat_protocol = ASIChatProtocol()
        
        # Price cache
        self.price_cache: Dict[str, Dict[str, Any]] = {}
        self.cache_ttl = 30  # 30 seconds
        
        # Setup agent handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup agent event handlers and message protocols"""
        
        @self.agent.on_event("startup")
        async def startup_handler(ctx: Context):
            ctx.logger.info(f"Price Feed Agent started: {ctx.agent.address}")
            ctx.logger.info("Connected to multi-source price feeds")
            
            # Register with chat protocol coordinator
            self.chat_protocol.register_agent(
                agent_id=self.agent_id,
                agent_address=ctx.agent.address,
                agent_type=self.agent_type,
                capabilities=["price_feeds", "market_analysis", "volatility_tracking", "trend_detection"]
            )
        
        # Tool Call Handler
        @self.agent.on_message(model=ToolCallRequest)
        async def handle_tool_call(ctx: Context, sender: str, msg: ToolCallRequest):
            """Handle price-related tool calls"""
            
            result = {}
            success = True
            
            try:
                if msg.tool_name == "get_price":
                    result = await self._get_price_data(msg.parameters)
                elif msg.tool_name == "analyze_volatility":
                    result = await self._analyze_volatility(msg.parameters)
                elif msg.tool_name == "detect_trends":
                    result = await self._detect_market_trends(msg.parameters)
                elif msg.tool_name == "compare_prices":
                    result = await self._compare_cross_chain_prices(msg.parameters)
                elif msg.tool_name == "get_market_summary":
                    result = await self._get_market_summary(msg.parameters)
                else:
                    result = {"error": f"Unknown tool: {msg.tool_name}"}
                    success = False
            
            except Exception as e:
                result = {"error": str(e)}
                success = False
            
            response = ToolCallResponse(
                session_id=msg.session_id,
                call_id=msg.call_id,
                tool_name=msg.tool_name,
                result=result,
                success=success
            )
            
            await ctx.send(sender, response)
        
        # Chat Message Handler
        @self.agent.on_message(model=ChatMessage)
        async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
            """Handle chat messages about prices"""
            
            for item in msg.content:
                if isinstance(item, TextContent):
                    response_text = await self._process_price_query(item.text)
                    
                    # Send acknowledgment
                    ack = ChatAcknowledgement(
                        timestamp=datetime.utcnow(),
                        acknowledged_msg_id=msg.msg_id
                    )
                    await ctx.send(sender, ack)
                    
                    # Send response
                    if response_text:
                        response = ChatMessage(
                            timestamp=datetime.utcnow(),
                            msg_id=uuid.uuid4(),
                            content=[TextContent(type="text", text=response_text)]
                        )
                        await ctx.send(sender, response)
    
    async def _get_price_data(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get price data via frontend /api/get_price route"""
        
        token_pair = parameters.get("token_pair", "ETH/USDC")
        chain = parameters.get("chain", "ethereum")
        
        # Check cache first
        cache_key = f"{token_pair}_{chain}"
        if cache_key in self.price_cache:
            cached_data = self.price_cache[cache_key]
            cache_time = datetime.fromisoformat(cached_data["timestamp"])
            if datetime.utcnow() - cache_time < timedelta(seconds=self.cache_ttl):
                cached_data["source"] = "cache"
                return cached_data
        
        try:
            # Call frontend API
            response = requests.get(
                f"{self.frontend_api_base}/get_price",
                params={
                    "token_pair": token_pair,
                    "chain": chain,
                    "include_sources": "true"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Cache the result
                enhanced_result = {
                    **result,
                    "timestamp": datetime.utcnow().isoformat(),
                    "cache_key": cache_key,
                    "volatility_analysis": self._calculate_volatility(result),
                    "market_indicators": self._analyze_market_indicators(result)
                }
                
                self.price_cache[cache_key] = enhanced_result
                
                return enhanced_result
            else:
                return {
                    "error": f"Price API call failed with status {response.status_code}",
                    "details": response.text
                }
        
        except Exception as e:
            return {
                "error": f"Failed to fetch price data: {str(e)}",
                "fallback_data": self._get_fallback_price_data(token_pair, chain)
            }
    
    def _calculate_volatility(self, price_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate volatility metrics from price data"""
        
        current_price = price_data.get("price", 0)
        price_24h_ago = price_data.get("price_24h_ago", current_price)
        
        if price_24h_ago > 0:
            price_change_24h = ((current_price - price_24h_ago) / price_24h_ago) * 100
        else:
            price_change_24h = 0
        
        # Volatility classification
        if abs(price_change_24h) > 10:
            volatility_level = "very_high"
        elif abs(price_change_24h) > 5:
            volatility_level = "high"
        elif abs(price_change_24h) > 2:
            volatility_level = "medium"
        else:
            volatility_level = "low"
        
        return {
            "price_change_24h_percent": round(price_change_24h, 2),
            "volatility_level": volatility_level,
            "is_volatile": abs(price_change_24h) > 5,
            "direction": "up" if price_change_24h > 0 else "down" if price_change_24h < 0 else "stable"
        }
    
    def _analyze_market_indicators(self, price_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market indicators from price data"""
        
        volume_24h = price_data.get("volume_24h", 0)
        market_cap = price_data.get("market_cap", 0)
        
        # Volume analysis
        if volume_24h > 1000000000:  # >$1B
            volume_level = "very_high"
        elif volume_24h > 100000000:  # >$100M
            volume_level = "high"
        elif volume_24h > 10000000:   # >$10M
            volume_level = "medium"
        else:
            volume_level = "low"
        
        # Market cap analysis
        if market_cap > 100000000000:  # >$100B
            market_cap_tier = "large_cap"
        elif market_cap > 10000000000:  # >$10B
            market_cap_tier = "mid_cap"
        else:
            market_cap_tier = "small_cap"
        
        return {
            "volume_24h_usd": volume_24h,
            "volume_level": volume_level,
            "market_cap_usd": market_cap,
            "market_cap_tier": market_cap_tier,
            "liquidity_score": min(100, (volume_24h / 1000000) * 10)  # Simplified liquidity score
        }
    
    async def _analyze_volatility(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze volatility for a token pair"""
        
        token_pair = parameters.get("token_pair", "ETH/USDC")
        timeframe = parameters.get("timeframe", "24h")
        
        # Get current price data
        price_data = await self._get_price_data({"token_pair": token_pair})
        
        if "error" in price_data:
            return price_data
        
        volatility_analysis = price_data.get("volatility_analysis", {})
        
        # Enhanced volatility metrics
        enhanced_analysis = {
            **volatility_analysis,
            "timeframe": timeframe,
            "risk_assessment": self._assess_volatility_risk(volatility_analysis),
            "trading_recommendations": self._get_volatility_trading_recommendations(volatility_analysis),
            "optimal_trade_size": self._calculate_optimal_trade_size(volatility_analysis)
        }
        
        return enhanced_analysis
    
    def _assess_volatility_risk(self, volatility_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess risk based on volatility"""
        
        volatility_level = volatility_data.get("volatility_level", "medium")
        price_change = abs(volatility_data.get("price_change_24h_percent", 0))
        
        risk_levels = {
            "very_high": {"risk_score": 90, "recommendation": "avoid_large_trades"},
            "high": {"risk_score": 70, "recommendation": "reduce_position_size"},
            "medium": {"risk_score": 50, "recommendation": "normal_trading"},
            "low": {"risk_score": 20, "recommendation": "favorable_conditions"}
        }
        
        risk_info = risk_levels.get(volatility_level, risk_levels["medium"])
        
        return {
            "risk_score": risk_info["risk_score"],
            "risk_level": volatility_level,
            "recommendation": risk_info["recommendation"],
            "slippage_warning": price_change > 5,
            "timing_sensitivity": "high" if price_change > 10 else "medium" if price_change > 3 else "low"
        }
    
    def _get_volatility_trading_recommendations(self, volatility_data: Dict[str, Any]) -> List[str]:
        """Get trading recommendations based on volatility"""
        
        volatility_level = volatility_data.get("volatility_level", "medium")
        direction = volatility_data.get("direction", "stable")
        
        recommendations = []
        
        if volatility_level in ["very_high", "high"]:
            recommendations.extend([
                "Consider smaller trade sizes",
                "Use limit orders instead of market orders",
                "Monitor price closely during execution"
            ])
        
        if direction == "up" and volatility_level != "very_high":
            recommendations.append("Potential buying opportunity if trend continues")
        elif direction == "down" and volatility_level != "very_high":
            recommendations.append("Consider waiting for price stabilization")
        
        if volatility_level == "low":
            recommendations.extend([
                "Good conditions for larger trades",
                "Lower slippage expected"
            ])
        
        return recommendations
    
    def _calculate_optimal_trade_size(self, volatility_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate optimal trade size based on volatility"""
        
        volatility_level = volatility_data.get("volatility_level", "medium")
        
        size_multipliers = {
            "very_high": 0.3,  # 30% of normal size
            "high": 0.5,       # 50% of normal size
            "medium": 0.8,     # 80% of normal size
            "low": 1.0         # Full size
        }
        
        multiplier = size_multipliers.get(volatility_level, 0.8)
        
        return {
            "size_multiplier": multiplier,
            "recommendation": f"Use {int(multiplier * 100)}% of intended trade size",
            "reasoning": f"Adjusted for {volatility_level} volatility conditions"
        }
    
    async def _detect_market_trends(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Detect market trends for token pairs"""
        
        token_pair = parameters.get("token_pair", "ETH/USDC")
        
        # Get price data
        price_data = await self._get_price_data({"token_pair": token_pair})
        
        if "error" in price_data:
            return price_data
        
        # Analyze trends
        volatility_analysis = price_data.get("volatility_analysis", {})
        market_indicators = price_data.get("market_indicators", {})
        
        trend_analysis = {
            "token_pair": token_pair,
            "current_trend": volatility_analysis.get("direction", "stable"),
            "trend_strength": self._calculate_trend_strength(volatility_analysis, market_indicators),
            "support_resistance": self._identify_support_resistance(price_data),
            "momentum_indicators": self._analyze_momentum(volatility_analysis, market_indicators),
            "prediction": self._predict_short_term_movement(volatility_analysis, market_indicators)
        }
        
        return trend_analysis
    
    def _calculate_trend_strength(self, volatility_data: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate trend strength"""
        
        price_change = abs(volatility_data.get("price_change_24h_percent", 0))
        volume_level = market_data.get("volume_level", "medium")
        
        # Strength based on price change and volume
        if price_change > 5 and volume_level in ["high", "very_high"]:
            strength = "strong"
        elif price_change > 2 and volume_level != "low":
            strength = "moderate"
        elif price_change > 0.5:
            strength = "weak"
        else:
            strength = "sideways"
        
        return {
            "strength": strength,
            "confidence": min(100, price_change * 10 + (["low", "medium", "high", "very_high"].index(volume_level) + 1) * 15),
            "volume_confirmation": volume_level in ["high", "very_high"]
        }
    
    def _identify_support_resistance(self, price_data: Dict[str, Any]) -> Dict[str, Any]:
        """Identify support and resistance levels"""
        
        current_price = price_data.get("price", 0)
        price_24h_ago = price_data.get("price_24h_ago", current_price)
        
        # Simple support/resistance calculation
        if current_price > price_24h_ago:
            support = price_24h_ago * 0.98
            resistance = current_price * 1.02
        else:
            support = current_price * 0.98
            resistance = price_24h_ago * 1.02
        
        return {
            "support_level": round(support, 6),
            "resistance_level": round(resistance, 6),
            "current_price": current_price,
            "distance_to_support": ((current_price - support) / current_price) * 100,
            "distance_to_resistance": ((resistance - current_price) / current_price) * 100
        }
    
    def _analyze_momentum(self, volatility_data: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze price momentum"""
        
        direction = volatility_data.get("direction", "stable")
        price_change = volatility_data.get("price_change_24h_percent", 0)
        volume_level = market_data.get("volume_level", "medium")
        
        # Momentum scoring
        momentum_score = abs(price_change) * 2
        if volume_level in ["high", "very_high"]:
            momentum_score *= 1.5
        
        return {
            "momentum_score": min(100, momentum_score),
            "direction": direction,
            "acceleration": "increasing" if abs(price_change) > 3 else "stable",
            "volume_support": volume_level in ["high", "very_high"]
        }
    
    def _predict_short_term_movement(self, volatility_data: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Predict short-term price movement"""
        
        direction = volatility_data.get("direction", "stable")
        volatility_level = volatility_data.get("volatility_level", "medium")
        volume_level = market_data.get("volume_level", "medium")
        
        # Simple prediction logic
        if direction != "stable" and volume_level in ["high", "very_high"]:
            if volatility_level in ["high", "very_high"]:
                prediction = "continuation_likely"
                confidence = 70
            else:
                prediction = "mild_continuation"
                confidence = 60
        elif volatility_level in ["very_high"]:
            prediction = "reversal_possible"
            confidence = 55
        else:
            prediction = "sideways_movement"
            confidence = 50
        
        return {
            "prediction": prediction,
            "confidence": confidence,
            "timeframe": "1-4 hours",
            "key_factors": [direction, volatility_level, volume_level]
        }
    
    async def _compare_cross_chain_prices(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Compare prices across different chains"""
        
        token_pair = parameters.get("token_pair", "ETH/USDC")
        chains = parameters.get("chains", ["ethereum", "base", "arbitrum", "optimism"])
        
        price_comparison = {}
        
        for chain in chains:
            try:
                price_data = await self._get_price_data({
                    "token_pair": token_pair,
                    "chain": chain
                })
                
                if "error" not in price_data:
                    price_comparison[chain] = {
                        "price": price_data.get("price", 0),
                        "volume_24h": price_data.get("volume_24h", 0),
                        "liquidity_score": price_data.get("market_indicators", {}).get("liquidity_score", 0)
                    }
            except Exception as e:
                price_comparison[chain] = {"error": str(e)}
        
        # Analyze arbitrage opportunities
        arbitrage_analysis = self._analyze_arbitrage_opportunities(price_comparison)
        
        return {
            "token_pair": token_pair,
            "price_comparison": price_comparison,
            "arbitrage_analysis": arbitrage_analysis,
            "best_chain": self._find_best_chain(price_comparison),
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _analyze_arbitrage_opportunities(self, price_comparison: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze arbitrage opportunities across chains"""
        
        valid_prices = {chain: data["price"] for chain, data in price_comparison.items() 
                       if "error" not in data and data.get("price", 0) > 0}
        
        if len(valid_prices) < 2:
            return {"opportunities": [], "max_spread": 0}
        
        min_price = min(valid_prices.values())
        max_price = max(valid_prices.values())
        spread_percent = ((max_price - min_price) / min_price) * 100
        
        opportunities = []
        if spread_percent > 0.5:  # >0.5% spread
            min_chain = min(valid_prices, key=valid_prices.get)
            max_chain = max(valid_prices, key=valid_prices.get)
            
            opportunities.append({
                "type": "cross_chain_arbitrage",
                "buy_chain": min_chain,
                "sell_chain": max_chain,
                "buy_price": valid_prices[min_chain],
                "sell_price": valid_prices[max_chain],
                "spread_percent": round(spread_percent, 3),
                "profit_potential": "high" if spread_percent > 2 else "medium" if spread_percent > 1 else "low"
            })
        
        return {
            "opportunities": opportunities,
            "max_spread": round(spread_percent, 3),
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    def _find_best_chain(self, price_comparison: Dict[str, Any]) -> Dict[str, Any]:
        """Find the best chain for trading"""
        
        valid_chains = {chain: data for chain, data in price_comparison.items() if "error" not in data}
        
        if not valid_chains:
            return {"error": "No valid chain data"}
        
        # Score chains based on price, volume, and liquidity
        chain_scores = {}
        for chain, data in valid_chains.items():
            score = 0
            score += data.get("liquidity_score", 0) * 0.4
            score += min(100, data.get("volume_24h", 0) / 1000000) * 0.4  # Volume score
            score += 20  # Base score
            
            chain_scores[chain] = score
        
        best_chain = max(chain_scores, key=chain_scores.get)
        
        return {
            "best_chain": best_chain,
            "score": chain_scores[best_chain],
            "reasoning": f"Highest combined liquidity and volume score",
            "all_scores": chain_scores
        }
    
    async def _get_market_summary(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get overall market summary"""
        
        major_pairs = ["ETH/USDC", "BTC/USDC", "USDC/USDT"]
        market_data = {}
        
        for pair in major_pairs:
            try:
                price_data = await self._get_price_data({"token_pair": pair})
                if "error" not in price_data:
                    market_data[pair] = {
                        "price": price_data.get("price", 0),
                        "change_24h": price_data.get("volatility_analysis", {}).get("price_change_24h_percent", 0),
                        "volatility": price_data.get("volatility_analysis", {}).get("volatility_level", "medium")
                    }
            except Exception:
                continue
        
        # Overall market sentiment
        if market_data:
            avg_change = sum(data["change_24h"] for data in market_data.values()) / len(market_data)
            high_volatility_count = sum(1 for data in market_data.values() if data["volatility"] in ["high", "very_high"])
            
            if avg_change > 2:
                sentiment = "bullish"
            elif avg_change < -2:
                sentiment = "bearish"
            else:
                sentiment = "neutral"
            
            market_condition = "volatile" if high_volatility_count > len(market_data) / 2 else "stable"
        else:
            sentiment = "unknown"
            market_condition = "unknown"
            avg_change = 0
        
        return {
            "market_pairs": market_data,
            "overall_sentiment": sentiment,
            "market_condition": market_condition,
            "average_change_24h": round(avg_change, 2),
            "summary": f"Market is {sentiment} with {market_condition} conditions",
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def _get_fallback_price_data(self, token_pair: str, chain: str) -> Dict[str, Any]:
        """Provide fallback price data when API fails"""
        
        # Simplified fallback prices
        fallback_prices = {
            "ETH/USDC": 2500.0,
            "BTC/USDC": 45000.0,
            "USDC/USDT": 1.0
        }
        
        price = fallback_prices.get(token_pair, 1.0)
        
        return {
            "price": price,
            "source": "fallback",
            "chain": chain,
            "token_pair": token_pair,
            "timestamp": datetime.utcnow().isoformat(),
            "warning": "Using fallback price data - may not be accurate"
        }
    
    async def _process_price_query(self, query: str) -> Optional[str]:
        """Process chat queries about prices"""
        
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in ['price', 'cost', 'value', 'rate']):
            if 'eth' in query_lower or 'ethereum' in query_lower:
                return "I can get current ETH prices across multiple chains and sources. What specific pair are you interested in?"
            elif 'volatile' in query_lower or 'volatility' in query_lower:
                return "I can analyze price volatility and provide risk assessments. Which token pair should I analyze?"
            elif 'arbitrage' in query_lower:
                return "I can detect arbitrage opportunities across different chains. What token pair interests you?"
            else:
                return "I provide real-time price data, volatility analysis, and market trends. What price information do you need?"
        
        return None
    
    async def start_agent(self):
        """Start the price feed agent"""
        await self.agent.run()

# Global instance for import
price_feed_agent = PriceFeedAgent()
