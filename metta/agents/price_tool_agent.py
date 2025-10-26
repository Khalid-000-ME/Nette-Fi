"""
Price Tool Agent - Gets real-time prices using /api/get_price
This agent makes real API calls to get token prices and market data
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

class PriceToolAgent:
    """Agent that makes real API calls to get token prices"""
    
    def __init__(self, api_base_url: str = "http://localhost:3000"):
        self.api_base_url = api_base_url
        self.agent_id = f"price_agent_{uuid.uuid4().hex[:8]}"
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def get_token_prices(
        self,
        token_pairs: List[str] = None,
        include_volatility: bool = True
    ) -> Dict[str, Any]:
        """
        Get current token prices using /api/get_price
        
        Args:
            token_pairs: List of token pairs to get prices for
            include_volatility: Whether to include volatility analysis
            
        Returns:
            Price data with market analysis
        """
        
        if token_pairs is None:
            token_pairs = ["ETH/USDC", "ETH/DAI", "USDC/DAI"]
        
        print(f"📈 {self.agent_id}: Getting prices for {token_pairs}")
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            # Prepare API request
            params = {
                "pairs": ",".join(token_pairs),
                "include_volatility": str(include_volatility).lower()
            }
            
            print(f"   📡 Calling /api/get_price with params: {params}")
            
            # Make API call to get prices
            async with self.session.get(
                f"{self.api_base_url}/api/get_price",
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    
                    print(f"   ✅ Price data retrieved successfully!")
                    
                    # Process and enhance the price data
                    enhanced_result = {
                        "success": True,
                        "agent_id": self.agent_id,
                        "price_data": result,
                        "market_analysis": self._analyze_market_conditions(result),
                        "timestamp": datetime.now().isoformat(),
                        "data_freshness": "real_time"
                    }
                    
                    # Log key prices
                    if "prices" in result:
                        for pair, price_info in result["prices"].items():
                            if isinstance(price_info, dict) and "price" in price_info:
                                print(f"   💰 {pair}: ${price_info['price']}")
                    
                    return enhanced_result
                    
                else:
                    error_text = await response.text()
                    print(f"   ❌ Price API call failed with status {response.status}: {error_text}")
                    
                    return {
                        "success": False,
                        "agent_id": self.agent_id,
                        "error": f"Price API failed: {response.status} - {error_text}",
                        "fallback_prices": self._get_fallback_prices(token_pairs)
                    }
                    
        except asyncio.TimeoutError:
            print(f"   ⏰ Price API call timed out")
            return {
                "success": False,
                "agent_id": self.agent_id,
                "error": "Price API timed out",
                "fallback_prices": self._get_fallback_prices(token_pairs)
            }
            
        except Exception as e:
            print(f"   💥 Price API call failed: {str(e)}")
            return {
                "success": False,
                "agent_id": self.agent_id,
                "error": f"Price fetch failed: {str(e)}",
                "fallback_prices": self._get_fallback_prices(token_pairs)
            }
    
    def _analyze_market_conditions(self, price_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze market conditions from price data"""
        
        analysis = {
            "market_sentiment": "neutral",
            "volatility_level": "medium",
            "trading_recommendation": "proceed_with_caution",
            "risk_factors": []
        }
        
        # Analyze volatility if available
        if "volatility" in price_data:
            volatility = price_data["volatility"]
            if isinstance(volatility, dict):
                avg_volatility = sum(v for v in volatility.values() if isinstance(v, (int, float))) / len(volatility)
                
                if avg_volatility > 5:
                    analysis["volatility_level"] = "high"
                    analysis["risk_factors"].append("high_volatility")
                    analysis["trading_recommendation"] = "delay_execution"
                elif avg_volatility < 2:
                    analysis["volatility_level"] = "low"
                    analysis["trading_recommendation"] = "optimal_conditions"
        
        # Analyze price trends
        if "prices" in price_data:
            prices = price_data["prices"]
            eth_price = None
            
            # Look for ETH price
            for pair, price_info in prices.items():
                if "ETH" in pair and isinstance(price_info, dict):
                    eth_price = price_info.get("price")
                    break
            
            if eth_price:
                if eth_price > 3000:
                    analysis["market_sentiment"] = "bullish"
                elif eth_price < 2000:
                    analysis["market_sentiment"] = "bearish"
                    analysis["risk_factors"].append("low_eth_price")
        
        return analysis
    
    def _get_fallback_prices(self, token_pairs: List[str]) -> Dict[str, Any]:
        """Get fallback prices when API fails"""
        
        fallback_prices = {}
        
        for pair in token_pairs:
            if "ETH/USDC" in pair:
                fallback_prices[pair] = {"price": 2500.00, "source": "fallback"}
            elif "ETH/DAI" in pair:
                fallback_prices[pair] = {"price": 2498.50, "source": "fallback"}
            elif "USDC/DAI" in pair:
                fallback_prices[pair] = {"price": 0.9995, "source": "fallback"}
            else:
                fallback_prices[pair] = {"price": 1.0, "source": "fallback"}
        
        return {
            "prices": fallback_prices,
            "note": "Using fallback prices due to API failure",
            "timestamp": datetime.now().isoformat()
        }
    
    async def get_price_history(
        self,
        token_pair: str,
        timeframe: str = "24h"
    ) -> Dict[str, Any]:
        """Get price history for a token pair"""
        
        print(f"📊 {self.agent_id}: Getting {timeframe} price history for {token_pair}")
        
        # Mock implementation - in production would call actual API
        return {
            "agent_id": self.agent_id,
            "token_pair": token_pair,
            "timeframe": timeframe,
            "price_history": {
                "high_24h": 2650.00,
                "low_24h": 2450.00,
                "change_24h_percent": 2.1,
                "volume_24h": 1250000000
            },
            "trend_analysis": {
                "direction": "upward",
                "strength": "moderate",
                "support_level": 2400.00,
                "resistance_level": 2700.00
            }
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "agent_id": self.agent_id,
            "agent_type": "price_tool_agent",
            "capabilities": [
                "real_time_prices",
                "market_analysis",
                "volatility_assessment",
                "price_history"
            ],
            "api_endpoints": [
                "/api/get_price"
            ],
            "supported_pairs": ["ETH/USDC", "ETH/DAI", "USDC/DAI"]
        }

# Example usage and testing
async def test_price_agent():
    """Test the price tool agent"""
    print("🧪 Testing Price Tool Agent")
    print("=" * 50)
    
    async with PriceToolAgent() as agent:
        
        # Test 1: Get current prices
        print("\n1️⃣ Testing Price Retrieval...")
        price_result = await agent.get_token_prices(
            token_pairs=["ETH/USDC", "ETH/DAI"],
            include_volatility=True
        )
        
        print(f"Price Result: {json.dumps(price_result, indent=2)}")
        
        # Test 2: Get price history
        print("\n2️⃣ Testing Price History...")
        history_result = await agent.get_price_history("ETH/USDC", "24h")
        
        print(f"History Result: {json.dumps(history_result, indent=2)}")
        
        # Test 3: Agent info
        print("\n3️⃣ Agent Information...")
        agent_info = agent.get_agent_info()
        print(f"Agent Info: {json.dumps(agent_info, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_price_agent())
