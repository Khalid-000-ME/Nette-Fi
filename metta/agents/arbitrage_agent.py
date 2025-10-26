"""
Arbitrage Detection Agent - Specialized in cross-chain arbitrage opportunities
Uses ASI (Fetch.ai) uAgent framework for autonomous arbitrage monitoring
"""

from uagents import Agent, Context, Model
from typing import Dict, List, Any, Optional, Tuple
import json
import numpy as np
import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta

@dataclass
class ArbitrageOpportunity:
    token_pair: str
    buy_chain: str
    sell_chain: str
    buy_price: float
    sell_price: float
    profit_margin: float
    volume_available: float
    execution_complexity: str

class ArbitrageRequest(Model):
    token_pairs: List[str]
    chains: List[str]
    min_profit_threshold: float

class ArbitrageResponse(Model):
    opportunities: List[Dict[str, Any]]
    market_analysis: Dict[str, Any]
    execution_strategies: List[Dict[str, Any]]

class ArbitrageDetectionAgent:
    def __init__(self, agent_address: str = "arbitrage_agent"):
        self.agent = Agent(
            name="arbitrage_detection_agent",
            seed="arbitrage_seed_13579",
            port=8005,
            endpoint=["http://localhost:8005/submit"]
        )
        
        # Price feeds cache
        self.price_cache = {}
        self.last_price_update = {}
        
        # Bridge costs and times
        self.bridge_configs = {
            ("ethereum", "base"): {"cost": 15, "time_minutes": 7, "reliability": 0.98},
            ("ethereum", "optimism"): {"cost": 12, "time_minutes": 7, "reliability": 0.97},
            ("ethereum", "arbitrum"): {"cost": 10, "time_minutes": 10, "reliability": 0.96},
            ("ethereum", "polygon"): {"cost": 8, "time_minutes": 30, "reliability": 0.95},
            ("base", "optimism"): {"cost": 5, "time_minutes": 15, "reliability": 0.94},
            ("base", "arbitrum"): {"cost": 6, "time_minutes": 20, "reliability": 0.93},
            ("optimism", "arbitrum"): {"cost": 4, "time_minutes": 25, "reliability": 0.92}
        }
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        @self.agent.on_message(model=ArbitrageRequest)
        async def handle_arbitrage_detection(ctx: Context, sender: str, msg: ArbitrageRequest):
            try:
                analysis = await self._detect_arbitrage_opportunities(
                    msg.token_pairs, msg.chains, msg.min_profit_threshold
                )
                
                response = ArbitrageResponse(
                    opportunities=analysis['opportunities'],
                    market_analysis=analysis['market_analysis'],
                    execution_strategies=analysis['execution_strategies']
                )
                
                await ctx.send(sender, response)
                
            except Exception as e:
                ctx.logger.error(f"Arbitrage detection failed: {str(e)}")
    
    async def _detect_arbitrage_opportunities(
        self, token_pairs: List[str], chains: List[str], min_profit_threshold: float
    ) -> Dict[str, Any]:
        """Detect arbitrage opportunities across chains"""
        
        # Fetch current prices across all chains
        price_matrix = await self._fetch_cross_chain_prices(token_pairs, chains)
        
        # Detect arbitrage opportunities
        opportunities = await self._identify_arbitrage_opportunities(
            price_matrix, min_profit_threshold
        )
        
        # Analyze market conditions
        market_analysis = self._analyze_market_conditions(price_matrix, opportunities)
        
        # Generate execution strategies
        execution_strategies = self._generate_execution_strategies(opportunities)
        
        return {
            "opportunities": [self._format_opportunity(opp) for opp in opportunities],
            "market_analysis": market_analysis,
            "execution_strategies": execution_strategies
        }
    
    async def _fetch_cross_chain_prices(self, token_pairs: List[str], chains: List[str]) -> Dict[str, Dict[str, Dict[str, float]]]:
        """Fetch prices for token pairs across all chains"""
        
        price_matrix = {}
        
        for pair in token_pairs:
            price_matrix[pair] = {}
            
            # Base prices with some realistic variation
            base_prices = {
                "ETH/USDC": 3000,
                "WBTC/USDC": 45000,
                "USDC/USDT": 1.0,
                "DAI/USDC": 1.0
            }
            
            base_price = base_prices.get(pair, 100)
            
            for chain in chains:
                # Simulate price differences across chains
                chain_multipliers = {
                    "ethereum": 1.0,  # Reference price
                    "base": np.random.uniform(0.998, 1.002),
                    "optimism": np.random.uniform(0.996, 1.004),
                    "arbitrum": np.random.uniform(0.997, 1.003),
                    "polygon": np.random.uniform(0.995, 1.005)
                }
                
                multiplier = chain_multipliers.get(chain, 1.0)
                chain_price = base_price * multiplier
                
                # Add liquidity and volume data
                price_matrix[pair][chain] = {
                    "price": chain_price,
                    "liquidity": np.random.uniform(1000000, 10000000),
                    "volume_24h": np.random.uniform(500000, 5000000),
                    "spread": np.random.uniform(0.001, 0.01),
                    "last_updated": datetime.now().isoformat()
                }
        
        return price_matrix
    
    async def _identify_arbitrage_opportunities(
        self, price_matrix: Dict[str, Dict[str, Dict[str, float]]], min_profit_threshold: float
    ) -> List[ArbitrageOpportunity]:
        """Identify profitable arbitrage opportunities"""
        
        opportunities = []
        
        for pair, chain_data in price_matrix.items():
            chains = list(chain_data.keys())
            
            # Compare all chain pairs
            for i, buy_chain in enumerate(chains):
                for sell_chain in chains[i+1:]:
                    
                    buy_data = chain_data[buy_chain]
                    sell_data = chain_data[sell_chain]
                    
                    buy_price = buy_data["price"]
                    sell_price = sell_data["price"]
                    
                    # Calculate potential profit in both directions
                    profit_1 = (sell_price - buy_price) / buy_price  # Buy on buy_chain, sell on sell_chain
                    profit_2 = (buy_price - sell_price) / sell_price  # Buy on sell_chain, sell on buy_chain
                    
                    # Check if either direction is profitable
                    if profit_1 > min_profit_threshold:
                        opportunity = await self._create_arbitrage_opportunity(
                            pair, buy_chain, sell_chain, buy_data, sell_data, profit_1
                        )
                        if opportunity:
                            opportunities.append(opportunity)
                    
                    elif profit_2 > min_profit_threshold:
                        opportunity = await self._create_arbitrage_opportunity(
                            pair, sell_chain, buy_chain, sell_data, buy_data, profit_2
                        )
                        if opportunity:
                            opportunities.append(opportunity)
        
        # Sort by profit margin (descending)
        opportunities.sort(key=lambda x: x.profit_margin, reverse=True)
        
        return opportunities
    
    async def _create_arbitrage_opportunity(
        self, pair: str, buy_chain: str, sell_chain: str, 
        buy_data: Dict[str, Any], sell_data: Dict[str, Any], raw_profit: float
    ) -> Optional[ArbitrageOpportunity]:
        """Create and validate an arbitrage opportunity"""
        
        # Calculate bridge costs and time
        bridge_key = (buy_chain, sell_chain)
        reverse_bridge_key = (sell_chain, buy_chain)
        
        bridge_config = self.bridge_configs.get(bridge_key) or self.bridge_configs.get(reverse_bridge_key)
        
        if not bridge_config:
            # Estimate bridge config for unknown pairs
            bridge_config = {"cost": 20, "time_minutes": 30, "reliability": 0.9}
        
        # Calculate net profit after bridge costs
        bridge_cost_percent = bridge_config["cost"] / (buy_data["price"] * 1000)  # Assume $1000 trade
        net_profit = raw_profit - bridge_cost_percent - (buy_data["spread"] + sell_data["spread"])
        
        # Only create opportunity if still profitable after costs
        if net_profit <= 0:
            return None
        
        # Calculate available volume
        available_volume = min(
            buy_data["liquidity"] * 0.1,  # Max 10% of liquidity
            sell_data["liquidity"] * 0.1,
            1000000  # Cap at $1M
        )
        
        # Assess execution complexity
        complexity = self._assess_execution_complexity(
            buy_chain, sell_chain, bridge_config, net_profit
        )
        
        return ArbitrageOpportunity(
            token_pair=pair,
            buy_chain=buy_chain,
            sell_chain=sell_chain,
            buy_price=buy_data["price"],
            sell_price=sell_data["price"],
            profit_margin=net_profit,
            volume_available=available_volume,
            execution_complexity=complexity
        )
    
    def _assess_execution_complexity(
        self, buy_chain: str, sell_chain: str, bridge_config: Dict[str, Any], profit_margin: float
    ) -> str:
        """Assess the complexity of executing an arbitrage opportunity"""
        
        # Factors affecting complexity
        bridge_time = bridge_config["time_minutes"]
        bridge_reliability = bridge_config["reliability"]
        
        complexity_score = 0
        
        # Time factor
        if bridge_time > 20:
            complexity_score += 2
        elif bridge_time > 10:
            complexity_score += 1
        
        # Reliability factor
        if bridge_reliability < 0.95:
            complexity_score += 2
        elif bridge_reliability < 0.97:
            complexity_score += 1
        
        # Profit margin factor (lower profit = higher risk)
        if profit_margin < 0.01:  # Less than 1%
            complexity_score += 2
        elif profit_margin < 0.02:  # Less than 2%
            complexity_score += 1
        
        # Chain factor (some chains are more complex)
        complex_chains = ["polygon"]  # Longer bridge times
        if buy_chain in complex_chains or sell_chain in complex_chains:
            complexity_score += 1
        
        if complexity_score >= 4:
            return "high"
        elif complexity_score >= 2:
            return "medium"
        else:
            return "low"
    
    def _format_opportunity(self, opportunity: ArbitrageOpportunity) -> Dict[str, Any]:
        """Format arbitrage opportunity for response"""
        
        return {
            "token_pair": opportunity.token_pair,
            "strategy": f"Buy on {opportunity.buy_chain}, sell on {opportunity.sell_chain}",
            "buy_chain": opportunity.buy_chain,
            "sell_chain": opportunity.sell_chain,
            "buy_price": opportunity.buy_price,
            "sell_price": opportunity.sell_price,
            "gross_profit_margin": (opportunity.sell_price - opportunity.buy_price) / opportunity.buy_price,
            "net_profit_margin": opportunity.profit_margin,
            "volume_available": opportunity.volume_available,
            "execution_complexity": opportunity.execution_complexity,
            "estimated_profit_usd": opportunity.volume_available * opportunity.profit_margin,
            "risk_assessment": self._assess_opportunity_risk(opportunity),
            "execution_time_estimate": self._estimate_execution_time(opportunity),
            "confidence_score": self._calculate_confidence_score(opportunity)
        }
    
    def _assess_opportunity_risk(self, opportunity: ArbitrageOpportunity) -> Dict[str, Any]:
        """Assess risk factors for an arbitrage opportunity"""
        
        risk_factors = []
        risk_score = 0
        
        # Bridge risk
        bridge_key = (opportunity.buy_chain, opportunity.sell_chain)
        bridge_config = self.bridge_configs.get(bridge_key)
        
        if bridge_config:
            if bridge_config["reliability"] < 0.95:
                risk_factors.append("Bridge reliability concerns")
                risk_score += 0.2
            
            if bridge_config["time_minutes"] > 20:
                risk_factors.append("Long bridge execution time")
                risk_score += 0.15
        
        # Profit margin risk
        if opportunity.profit_margin < 0.02:
            risk_factors.append("Thin profit margins")
            risk_score += 0.25
        
        # Volume risk
        if opportunity.volume_available < 100000:
            risk_factors.append("Limited volume available")
            risk_score += 0.1
        
        # Complexity risk
        if opportunity.execution_complexity == "high":
            risk_factors.append("High execution complexity")
            risk_score += 0.3
        
        risk_level = "low" if risk_score < 0.3 else "medium" if risk_score < 0.6 else "high"
        
        return {
            "risk_level": risk_level,
            "risk_score": min(risk_score, 1.0),
            "risk_factors": risk_factors,
            "mitigation_strategies": self._suggest_risk_mitigation(risk_factors)
        }
    
    def _suggest_risk_mitigation(self, risk_factors: List[str]) -> List[str]:
        """Suggest risk mitigation strategies"""
        
        strategies = []
        
        if "Bridge reliability concerns" in risk_factors:
            strategies.append("Use multiple bridge providers for redundancy")
        
        if "Long bridge execution time" in risk_factors:
            strategies.append("Monitor price movements during bridge execution")
        
        if "Thin profit margins" in risk_factors:
            strategies.append("Use smaller position sizes to reduce impact")
        
        if "Limited volume available" in risk_factors:
            strategies.append("Split execution across multiple opportunities")
        
        if "High execution complexity" in risk_factors:
            strategies.append("Implement comprehensive monitoring and fallback plans")
        
        return strategies
    
    def _estimate_execution_time(self, opportunity: ArbitrageOpportunity) -> Dict[str, Any]:
        """Estimate total execution time for arbitrage"""
        
        bridge_key = (opportunity.buy_chain, opportunity.sell_chain)
        bridge_config = self.bridge_configs.get(bridge_key, {"time_minutes": 30})
        
        # Execution steps timing
        buy_execution = 2  # 2 minutes for buy transaction
        bridge_time = bridge_config["time_minutes"]
        sell_execution = 2  # 2 minutes for sell transaction
        
        total_time = buy_execution + bridge_time + sell_execution
        
        return {
            "total_minutes": total_time,
            "buy_execution": buy_execution,
            "bridge_time": bridge_time,
            "sell_execution": sell_execution,
            "time_risk": "high" if total_time > 30 else "medium" if total_time > 15 else "low"
        }
    
    def _calculate_confidence_score(self, opportunity: ArbitrageOpportunity) -> float:
        """Calculate confidence score for opportunity"""
        
        # Base confidence
        confidence = 0.7
        
        # Adjust based on profit margin
        if opportunity.profit_margin > 0.05:  # >5%
            confidence += 0.2
        elif opportunity.profit_margin > 0.02:  # >2%
            confidence += 0.1
        elif opportunity.profit_margin < 0.01:  # <1%
            confidence -= 0.2
        
        # Adjust based on complexity
        complexity_adjustments = {"low": 0.1, "medium": 0, "high": -0.15}
        confidence += complexity_adjustments.get(opportunity.execution_complexity, 0)
        
        # Adjust based on volume
        if opportunity.volume_available > 500000:
            confidence += 0.1
        elif opportunity.volume_available < 100000:
            confidence -= 0.1
        
        return max(0.1, min(confidence, 0.95))
    
    def _analyze_market_conditions(
        self, price_matrix: Dict[str, Dict[str, Dict[str, float]]], 
        opportunities: List[ArbitrageOpportunity]
    ) -> Dict[str, Any]:
        """Analyze overall market conditions for arbitrage"""
        
        # Calculate market fragmentation
        fragmentation_scores = {}
        for pair, chain_data in price_matrix.items():
            prices = [data["price"] for data in chain_data.values()]
            if len(prices) > 1:
                price_variance = np.var(prices) / np.mean(prices) ** 2
                fragmentation_scores[pair] = price_variance
        
        avg_fragmentation = np.mean(list(fragmentation_scores.values())) if fragmentation_scores else 0
        
        # Analyze opportunity distribution
        opportunity_count_by_pair = {}
        for opp in opportunities:
            pair = opp.token_pair
            opportunity_count_by_pair[pair] = opportunity_count_by_pair.get(pair, 0) + 1
        
        # Market efficiency assessment
        efficiency_score = 1 - min(avg_fragmentation * 10, 1.0)  # Higher fragmentation = lower efficiency
        
        return {
            "market_fragmentation": avg_fragmentation,
            "efficiency_score": efficiency_score,
            "total_opportunities": len(opportunities),
            "opportunities_by_pair": opportunity_count_by_pair,
            "market_condition": self._assess_market_condition(efficiency_score, len(opportunities)),
            "fragmentation_by_pair": fragmentation_scores,
            "arbitrage_potential": self._assess_arbitrage_potential(opportunities)
        }
    
    def _assess_market_condition(self, efficiency_score: float, opportunity_count: int) -> str:
        """Assess overall market condition for arbitrage"""
        
        if efficiency_score < 0.7 and opportunity_count > 5:
            return "highly_fragmented"  # Many opportunities, low efficiency
        elif efficiency_score < 0.8 and opportunity_count > 2:
            return "moderately_fragmented"
        elif opportunity_count > 0:
            return "some_opportunities"
        else:
            return "efficient_market"
    
    def _assess_arbitrage_potential(self, opportunities: List[ArbitrageOpportunity]) -> Dict[str, Any]:
        """Assess overall arbitrage potential"""
        
        if not opportunities:
            return {"potential": "low", "total_profit": 0, "avg_margin": 0}
        
        total_profit = sum(opp.volume_available * opp.profit_margin for opp in opportunities)
        avg_margin = np.mean([opp.profit_margin for opp in opportunities])
        
        potential_level = "high" if total_profit > 50000 else "medium" if total_profit > 10000 else "low"
        
        return {
            "potential": potential_level,
            "total_profit_usd": total_profit,
            "average_margin": avg_margin,
            "executable_opportunities": len([opp for opp in opportunities if opp.execution_complexity != "high"]),
            "high_confidence_opportunities": len([opp for opp in opportunities if self._calculate_confidence_score(opp) > 0.8])
        }
    
    def _generate_execution_strategies(self, opportunities: List[ArbitrageOpportunity]) -> List[Dict[str, Any]]:
        """Generate execution strategies for arbitrage opportunities"""
        
        if not opportunities:
            return []
        
        strategies = []
        
        # Strategy 1: High-confidence, low-complexity opportunities first
        high_confidence_opps = [
            opp for opp in opportunities 
            if self._calculate_confidence_score(opp) > 0.8 and opp.execution_complexity == "low"
        ]
        
        if high_confidence_opps:
            strategies.append({
                "strategy": "priority_execution",
                "description": "Execute high-confidence, low-complexity opportunities immediately",
                "opportunities": len(high_confidence_opps),
                "estimated_profit": sum(opp.volume_available * opp.profit_margin for opp in high_confidence_opps),
                "execution_order": [self._format_opportunity(opp) for opp in high_confidence_opps[:3]],
                "risk_level": "low"
            })
        
        # Strategy 2: Portfolio approach for medium opportunities
        medium_opps = [
            opp for opp in opportunities 
            if opp.execution_complexity in ["low", "medium"] and opp.profit_margin > 0.015
        ]
        
        if len(medium_opps) > 1:
            strategies.append({
                "strategy": "diversified_portfolio",
                "description": "Execute multiple medium-profit opportunities to diversify risk",
                "opportunities": len(medium_opps),
                "estimated_profit": sum(opp.volume_available * opp.profit_margin * 0.7 for opp in medium_opps),  # Conservative estimate
                "execution_approach": "parallel_where_possible",
                "risk_level": "medium"
            })
        
        # Strategy 3: Conservative approach for high-risk, high-reward
        high_reward_opps = [
            opp for opp in opportunities 
            if opp.profit_margin > 0.03  # >3% profit
        ]
        
        if high_reward_opps:
            strategies.append({
                "strategy": "selective_high_reward",
                "description": "Carefully execute high-reward opportunities with enhanced monitoring",
                "opportunities": len(high_reward_opps),
                "estimated_profit": sum(opp.volume_available * opp.profit_margin * 0.5 for opp in high_reward_opps),  # Very conservative
                "execution_approach": "sequential_with_monitoring",
                "risk_level": "high",
                "additional_requirements": ["Enhanced monitoring", "Smaller position sizes", "Quick exit strategies"]
            })
        
        return strategies

    async def detect_arbitrage(
        self, token_pairs: List[str] = None, chains: List[str] = None, min_profit_threshold: float = 0.005
    ) -> Dict[str, Any]:
        """Main entry point for arbitrage detection"""
        if token_pairs is None:
            token_pairs = ["ETH/USDC", "WBTC/USDC"]
        if chains is None:
            chains = ["ethereum", "base", "optimism", "arbitrum", "polygon"]
        
        return await self._detect_arbitrage_opportunities(token_pairs, chains, min_profit_threshold)

    def get_agent(self):
        """Return the uAgent instance"""
        return self.agent
