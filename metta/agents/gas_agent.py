"""
Gas Optimization Agent - Specialized in gas cost analysis and optimization
Uses ASI (Fetch.ai) uAgent framework for autonomous gas monitoring
"""

from uagents import Agent, Context, Model
from typing import Dict, List, Any, Optional
import json
import numpy as np
import asyncio
from datetime import datetime, timedelta

class GasRequest(Model):
    chains: List[str]
    transaction_types: List[str]
    urgency_level: str

class GasResponse(Model):
    gas_analysis: Dict[str, Any]
    optimization_strategy: Dict[str, Any]
    timing_recommendations: Dict[str, Any]

class GasOptimizationAgent:
    def __init__(self, agent_address: str = "gas_agent"):
        self.agent = Agent(
            name="gas_optimization_agent",
            seed="gas_seed_98765",
            port=8004,
            endpoint=["http://localhost:8004/submit"]
        )
        
        # Gas price history cache
        self.gas_history = {}
        self.last_update = {}
        
        # Chain-specific gas configurations
        self.chain_configs = {
            "ethereum": {"base_fee": 20, "priority_multiplier": 1.5, "block_time": 12},
            "base": {"base_fee": 0.1, "priority_multiplier": 1.2, "block_time": 2},
            "optimism": {"base_fee": 0.5, "priority_multiplier": 1.1, "block_time": 2},
            "arbitrum": {"base_fee": 1.0, "priority_multiplier": 1.3, "block_time": 1},
            "polygon": {"base_fee": 30, "priority_multiplier": 1.4, "block_time": 2}
        }
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        @self.agent.on_message(model=GasRequest)
        async def handle_gas_analysis(ctx: Context, sender: str, msg: GasRequest):
            try:
                analysis = await self._analyze_gas_landscape(
                    msg.chains, msg.transaction_types, msg.urgency_level
                )
                
                response = GasResponse(
                    gas_analysis=analysis['analysis'],
                    optimization_strategy=analysis['optimization'],
                    timing_recommendations=analysis['timing']
                )
                
                await ctx.send(sender, response)
                
            except Exception as e:
                ctx.logger.error(f"Gas analysis failed: {str(e)}")
    
    async def _analyze_gas_landscape(
        self, chains: List[str], transaction_types: List[str], urgency_level: str
    ) -> Dict[str, Any]:
        """Comprehensive gas analysis across chains"""
        
        # Fetch current gas prices
        current_gas_prices = await self._fetch_gas_prices(chains)
        
        # Analyze gas trends
        gas_trends = await self._analyze_gas_trends(chains)
        
        # Calculate optimization strategies
        optimization_strategy = self._calculate_optimization_strategy(
            current_gas_prices, transaction_types, urgency_level
        )
        
        # Generate timing recommendations
        timing_recommendations = self._generate_timing_recommendations(
            gas_trends, urgency_level
        )
        
        return {
            "analysis": {
                "current_prices": current_gas_prices,
                "trends": gas_trends,
                "cross_chain_comparison": self._compare_cross_chain_costs(current_gas_prices),
                "cost_efficiency_ranking": self._rank_chains_by_efficiency(current_gas_prices)
            },
            "optimization": optimization_strategy,
            "timing": timing_recommendations
        }
    
    async def _fetch_gas_prices(self, chains: List[str]) -> Dict[str, Any]:
        """Fetch current gas prices for specified chains"""
        
        gas_prices = {}
        
        for chain in chains:
            # Simulate real-time gas price fetching
            config = self.chain_configs.get(chain, self.chain_configs["ethereum"])
            
            # Generate realistic gas prices with some volatility
            base_fee = config["base_fee"]
            current_multiplier = np.random.uniform(0.7, 2.0)  # Market volatility
            
            current_gas = base_fee * current_multiplier
            
            # Calculate different priority levels
            gas_prices[chain] = {
                "chain": chain,
                "base_fee": base_fee,
                "current_gas": current_gas,
                "slow": current_gas * 0.8,
                "standard": current_gas,
                "fast": current_gas * config["priority_multiplier"],
                "instant": current_gas * config["priority_multiplier"] * 1.5,
                "block_time": config["block_time"],
                "network_congestion": self._assess_network_congestion(current_multiplier),
                "price_trend": self._determine_price_trend(chain, current_gas),
                "last_updated": datetime.now().isoformat()
            }
        
        return gas_prices
    
    def _assess_network_congestion(self, multiplier: float) -> str:
        """Assess network congestion based on gas multiplier"""
        if multiplier > 1.8:
            return "high"
        elif multiplier > 1.3:
            return "medium"
        else:
            return "low"
    
    def _determine_price_trend(self, chain: str, current_gas: float) -> Dict[str, Any]:
        """Determine gas price trend for a chain"""
        
        # Get or initialize history
        if chain not in self.gas_history:
            self.gas_history[chain] = []
        
        # Add current price to history
        self.gas_history[chain].append({
            "price": current_gas,
            "timestamp": datetime.now()
        })
        
        # Keep only last 24 hours of data
        cutoff_time = datetime.now() - timedelta(hours=24)
        self.gas_history[chain] = [
            entry for entry in self.gas_history[chain]
            if entry["timestamp"] > cutoff_time
        ]
        
        # Analyze trend
        if len(self.gas_history[chain]) < 2:
            return {"direction": "stable", "strength": 0.0, "confidence": 0.5}
        
        recent_prices = [entry["price"] for entry in self.gas_history[chain][-10:]]
        
        if len(recent_prices) >= 2:
            trend_slope = (recent_prices[-1] - recent_prices[0]) / len(recent_prices)
            trend_strength = abs(trend_slope) / recent_prices[0] if recent_prices[0] > 0 else 0
            
            direction = "increasing" if trend_slope > 0.01 else "decreasing" if trend_slope < -0.01 else "stable"
            
            return {
                "direction": direction,
                "strength": trend_strength,
                "confidence": min(len(recent_prices) / 10, 1.0)
            }
        
        return {"direction": "stable", "strength": 0.0, "confidence": 0.5}
    
    async def _analyze_gas_trends(self, chains: List[str]) -> Dict[str, Any]:
        """Analyze gas price trends and patterns"""
        
        trends_analysis = {}
        
        for chain in chains:
            history = self.gas_history.get(chain, [])
            
            if len(history) < 5:
                trends_analysis[chain] = {
                    "trend": "insufficient_data",
                    "volatility": 0.5,
                    "prediction": "stable"
                }
                continue
            
            prices = [entry["price"] for entry in history]
            
            # Calculate volatility
            volatility = np.std(prices) / np.mean(prices) if np.mean(prices) > 0 else 0
            
            # Predict next period
            recent_trend = np.polyfit(range(len(prices[-5:])), prices[-5:], 1)[0]
            prediction = "increasing" if recent_trend > 0.1 else "decreasing" if recent_trend < -0.1 else "stable"
            
            # Identify patterns
            patterns = self._identify_gas_patterns(prices)
            
            trends_analysis[chain] = {
                "volatility": volatility,
                "prediction": prediction,
                "patterns": patterns,
                "optimal_windows": self._identify_optimal_windows(history),
                "risk_assessment": self._assess_gas_risk(volatility, recent_trend)
            }
        
        return trends_analysis
    
    def _identify_gas_patterns(self, prices: List[float]) -> List[str]:
        """Identify patterns in gas price history"""
        
        patterns = []
        
        if len(prices) < 10:
            return patterns
        
        # Check for cyclical patterns
        hourly_avg = {}
        for i, price in enumerate(prices):
            hour = i % 24  # Simulate hourly data
            if hour not in hourly_avg:
                hourly_avg[hour] = []
            hourly_avg[hour].append(price)
        
        # Identify peak hours
        hour_averages = {h: np.mean(prices) for h, prices in hourly_avg.items()}
        max_hour = max(hour_averages, key=hour_averages.get)
        min_hour = min(hour_averages, key=hour_averages.get)
        
        if hour_averages[max_hour] > hour_averages[min_hour] * 1.2:
            patterns.append(f"peak_hours_{max_hour}h")
            patterns.append(f"low_hours_{min_hour}h")
        
        # Check for trending patterns
        recent_prices = prices[-5:]
        if all(recent_prices[i] > recent_prices[i-1] for i in range(1, len(recent_prices))):
            patterns.append("consistent_increase")
        elif all(recent_prices[i] < recent_prices[i-1] for i in range(1, len(recent_prices))):
            patterns.append("consistent_decrease")
        
        return patterns
    
    def _identify_optimal_windows(self, history: List[Dict]) -> List[Dict[str, Any]]:
        """Identify optimal execution windows based on historical data"""
        
        if len(history) < 12:
            return [{"window": "insufficient_data", "confidence": 0.3}]
        
        # Group by hour of day
        hourly_prices = {}
        for entry in history:
            hour = entry["timestamp"].hour
            if hour not in hourly_prices:
                hourly_prices[hour] = []
            hourly_prices[hour].append(entry["price"])
        
        # Calculate average prices by hour
        hourly_averages = {
            hour: np.mean(prices) for hour, prices in hourly_prices.items()
            if len(prices) >= 2
        }
        
        if not hourly_averages:
            return [{"window": "any_time", "confidence": 0.5}]
        
        # Find optimal windows (lowest average prices)
        sorted_hours = sorted(hourly_averages.items(), key=lambda x: x[1])
        
        optimal_windows = []
        for i, (hour, avg_price) in enumerate(sorted_hours[:3]):
            confidence = 1.0 - (i * 0.2)  # Decreasing confidence
            optimal_windows.append({
                "window": f"{hour:02d}:00-{(hour+1)%24:02d}:00",
                "average_price": avg_price,
                "confidence": confidence,
                "savings_potential": (max(hourly_averages.values()) - avg_price) / max(hourly_averages.values())
            })
        
        return optimal_windows
    
    def _assess_gas_risk(self, volatility: float, trend: float) -> Dict[str, Any]:
        """Assess gas price risk"""
        
        # Risk factors
        volatility_risk = min(volatility * 2, 1.0)  # Normalize volatility
        trend_risk = min(abs(trend) / 10, 1.0)  # Normalize trend impact
        
        overall_risk = (volatility_risk * 0.6 + trend_risk * 0.4)
        
        risk_level = "low" if overall_risk < 0.3 else "medium" if overall_risk < 0.6 else "high"
        
        return {
            "risk_level": risk_level,
            "risk_score": overall_risk,
            "volatility_component": volatility_risk,
            "trend_component": trend_risk,
            "recommendation": self._get_risk_recommendation(risk_level, trend)
        }
    
    def _get_risk_recommendation(self, risk_level: str, trend: float) -> str:
        """Get recommendation based on risk assessment"""
        
        if risk_level == "high":
            if trend > 0:
                return "Execute immediately before further increases"
            else:
                return "Wait for prices to stabilize"
        elif risk_level == "medium":
            return "Monitor closely and execute during optimal windows"
        else:
            return "Flexible timing - execute when convenient"
    
    def _compare_cross_chain_costs(self, gas_prices: Dict[str, Any]) -> Dict[str, Any]:
        """Compare gas costs across chains"""
        
        # Standard transaction costs in USD
        tx_costs = {}
        for chain, data in gas_prices.items():
            # Estimate cost for standard swap transaction
            gas_limit = 150000  # Typical swap gas limit
            gas_price_gwei = data["standard"]
            
            # Convert to USD (simplified)
            if chain == "ethereum":
                cost_usd = (gas_limit * gas_price_gwei * 1e-9) * 3000  # ETH price
            elif chain == "polygon":
                cost_usd = (gas_limit * gas_price_gwei * 1e-9) * 1  # MATIC price
            else:
                cost_usd = (gas_limit * gas_price_gwei * 1e-9) * 3000 * 0.1  # L2 scaling
            
            tx_costs[chain] = {
                "cost_usd": cost_usd,
                "gas_price_gwei": gas_price_gwei,
                "relative_cost": 1.0  # Will be updated below
            }
        
        # Calculate relative costs
        min_cost = min(data["cost_usd"] for data in tx_costs.values())
        for chain_data in tx_costs.values():
            chain_data["relative_cost"] = chain_data["cost_usd"] / min_cost
        
        # Find most cost-effective chain
        cheapest_chain = min(tx_costs.items(), key=lambda x: x[1]["cost_usd"])
        
        return {
            "transaction_costs": tx_costs,
            "cheapest_chain": cheapest_chain[0],
            "cost_spread": max(tx_costs.values(), key=lambda x: x["cost_usd"])["cost_usd"] / min_cost,
            "savings_opportunity": self._calculate_savings_opportunity(tx_costs)
        }
    
    def _calculate_savings_opportunity(self, tx_costs: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate potential savings from optimal chain selection"""
        
        costs = [data["cost_usd"] for data in tx_costs.values()]
        min_cost = min(costs)
        max_cost = max(costs)
        avg_cost = np.mean(costs)
        
        return {
            "max_savings_usd": max_cost - min_cost,
            "max_savings_percent": ((max_cost - min_cost) / max_cost) * 100,
            "avg_savings_usd": avg_cost - min_cost,
            "avg_savings_percent": ((avg_cost - min_cost) / avg_cost) * 100
        }
    
    def _rank_chains_by_efficiency(self, gas_prices: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rank chains by gas efficiency"""
        
        efficiency_scores = []
        
        for chain, data in gas_prices.items():
            # Calculate efficiency score (lower gas cost + faster confirmation = higher efficiency)
            gas_cost = data["standard"]
            block_time = data["block_time"]
            congestion = data["network_congestion"]
            
            # Normalize factors
            cost_score = 1 / (1 + gas_cost / 10)  # Lower cost = higher score
            speed_score = 1 / (1 + block_time / 5)  # Faster = higher score
            congestion_penalty = {"low": 1.0, "medium": 0.8, "high": 0.6}[congestion]
            
            efficiency = (cost_score * 0.5 + speed_score * 0.3) * congestion_penalty
            
            efficiency_scores.append({
                "chain": chain,
                "efficiency_score": efficiency,
                "cost_score": cost_score,
                "speed_score": speed_score,
                "congestion_penalty": congestion_penalty,
                "recommendation": self._get_chain_recommendation(efficiency)
            })
        
        # Sort by efficiency (descending)
        return sorted(efficiency_scores, key=lambda x: x["efficiency_score"], reverse=True)
    
    def _get_chain_recommendation(self, efficiency: float) -> str:
        """Get recommendation based on chain efficiency"""
        
        if efficiency > 0.8:
            return "Highly recommended"
        elif efficiency > 0.6:
            return "Good option"
        elif efficiency > 0.4:
            return "Consider alternatives"
        else:
            return "Avoid if possible"
    
    def _calculate_optimization_strategy(
        self, gas_prices: Dict[str, Any], transaction_types: List[str], urgency_level: str
    ) -> Dict[str, Any]:
        """Calculate comprehensive gas optimization strategy"""
        
        # Analyze transaction requirements
        tx_requirements = self._analyze_transaction_requirements(transaction_types)
        
        # Select optimal chains based on urgency
        optimal_chains = self._select_optimal_chains(gas_prices, urgency_level)
        
        # Calculate batch optimization opportunities
        batch_optimization = self._analyze_batch_opportunities(transaction_types, gas_prices)
        
        # Generate cost reduction strategies
        cost_reduction = self._generate_cost_reduction_strategies(gas_prices, urgency_level)
        
        return {
            "transaction_requirements": tx_requirements,
            "optimal_chains": optimal_chains,
            "batch_optimization": batch_optimization,
            "cost_reduction_strategies": cost_reduction,
            "estimated_savings": self._estimate_total_savings(optimal_chains, cost_reduction)
        }
    
    def _analyze_transaction_requirements(self, transaction_types: List[str]) -> Dict[str, Any]:
        """Analyze gas requirements for different transaction types"""
        
        # Gas estimates for different transaction types
        gas_estimates = {
            "simple_transfer": 21000,
            "token_swap": 150000,
            "liquidity_add": 200000,
            "liquidity_remove": 180000,
            "multi_hop_swap": 300000,
            "cross_chain_bridge": 250000
        }
        
        total_gas = sum(gas_estimates.get(tx_type, 150000) for tx_type in transaction_types)
        
        return {
            "transaction_types": transaction_types,
            "individual_estimates": {tx: gas_estimates.get(tx, 150000) for tx in transaction_types},
            "total_gas_estimate": total_gas,
            "complexity_score": len(transaction_types) + (total_gas / 100000),
            "optimization_potential": self._assess_optimization_potential(transaction_types)
        }
    
    def _assess_optimization_potential(self, transaction_types: List[str]) -> str:
        """Assess potential for gas optimization"""
        
        if len(transaction_types) > 3:
            return "high"  # Many transactions can be batched
        elif any("multi" in tx or "cross" in tx for tx in transaction_types):
            return "medium"  # Complex transactions have optimization opportunities
        else:
            return "low"  # Simple transactions have limited optimization
    
    def _select_optimal_chains(self, gas_prices: Dict[str, Any], urgency_level: str) -> List[Dict[str, Any]]:
        """Select optimal chains based on urgency and costs"""
        
        chain_scores = []
        
        for chain, data in gas_prices.items():
            if urgency_level == "immediate":
                # Prioritize speed over cost
                score = (1 / data["block_time"]) * 0.7 + (1 / data["fast"]) * 0.3
                recommended_gas = data["instant"]
            elif urgency_level == "fast":
                # Balance speed and cost
                score = (1 / data["block_time"]) * 0.5 + (1 / data["fast"]) * 0.5
                recommended_gas = data["fast"]
            else:  # normal or low urgency
                # Prioritize cost over speed
                score = (1 / data["slow"]) * 0.7 + (1 / data["block_time"]) * 0.3
                recommended_gas = data["slow"]
            
            chain_scores.append({
                "chain": chain,
                "score": score,
                "recommended_gas_price": recommended_gas,
                "estimated_confirmation_time": self._estimate_confirmation_time(
                    data["block_time"], urgency_level
                ),
                "cost_efficiency": 1 / recommended_gas if recommended_gas > 0 else 0
            })
        
        # Sort by score (descending)
        return sorted(chain_scores, key=lambda x: x["score"], reverse=True)
    
    def _estimate_confirmation_time(self, block_time: int, urgency_level: str) -> str:
        """Estimate transaction confirmation time"""
        
        multipliers = {
            "immediate": 1,
            "fast": 2,
            "normal": 3,
            "low": 5
        }
        
        estimated_blocks = multipliers.get(urgency_level, 3)
        estimated_seconds = block_time * estimated_blocks
        
        if estimated_seconds < 60:
            return f"{estimated_seconds} seconds"
        else:
            return f"{estimated_seconds // 60} minutes"
    
    def _analyze_batch_opportunities(self, transaction_types: List[str], gas_prices: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze opportunities for transaction batching"""
        
        if len(transaction_types) <= 1:
            return {"batching_possible": False, "savings": 0}
        
        # Calculate potential savings from batching
        individual_overhead = len(transaction_types) * 21000  # Base transaction cost
        batch_overhead = 21000 + (len(transaction_types) * 5000)  # Batch overhead
        
        gas_savings = individual_overhead - batch_overhead
        
        # Calculate cost savings across chains
        cost_savings = {}
        for chain, data in gas_prices.items():
            savings_usd = (gas_savings * data["standard"] * 1e-9) * 3000  # Rough USD conversion
            cost_savings[chain] = savings_usd
        
        return {
            "batching_possible": len(transaction_types) > 1,
            "gas_savings": gas_savings,
            "cost_savings_by_chain": cost_savings,
            "batch_efficiency": gas_savings / individual_overhead if individual_overhead > 0 else 0,
            "recommendation": "Highly recommended" if gas_savings > 50000 else "Consider batching"
        }
    
    def _generate_cost_reduction_strategies(self, gas_prices: Dict[str, Any], urgency_level: str) -> List[Dict[str, Any]]:
        """Generate specific cost reduction strategies"""
        
        strategies = []
        
        # Strategy 1: Optimal timing
        strategies.append({
            "strategy": "optimal_timing",
            "description": "Execute during low gas price periods",
            "potential_savings": "10-30%",
            "implementation": "Monitor gas prices and execute during identified optimal windows"
        })
        
        # Strategy 2: Chain selection
        cheapest_chains = sorted(gas_prices.items(), key=lambda x: x[1]["standard"])[:2]
        strategies.append({
            "strategy": "chain_optimization",
            "description": f"Use {cheapest_chains[0][0]} or {cheapest_chains[1][0]} for lower costs",
            "potential_savings": "50-90%",
            "implementation": "Route transactions through most cost-effective chains"
        })
        
        # Strategy 3: Gas price optimization
        if urgency_level != "immediate":
            strategies.append({
                "strategy": "gas_price_tuning",
                "description": "Use lower gas prices for non-urgent transactions",
                "potential_savings": "20-40%",
                "implementation": "Set gas prices based on actual urgency requirements"
            })
        
        return strategies
    
    def _estimate_total_savings(self, optimal_chains: List[Dict], cost_reduction: List[Dict]) -> Dict[str, Any]:
        """Estimate total potential savings"""
        
        # Calculate savings from optimal chain selection
        if len(optimal_chains) >= 2:
            best_chain = optimal_chains[0]
            worst_chain = optimal_chains[-1]
            
            chain_savings = (worst_chain["recommended_gas_price"] - best_chain["recommended_gas_price"]) / worst_chain["recommended_gas_price"]
        else:
            chain_savings = 0
        
        # Estimate savings from strategies
        strategy_savings = 0.2  # Conservative 20% from optimization strategies
        
        total_savings = min(chain_savings + strategy_savings, 0.8)  # Cap at 80%
        
        return {
            "chain_selection_savings": chain_savings,
            "strategy_savings": strategy_savings,
            "total_potential_savings": total_savings,
            "confidence": 0.8 if len(optimal_chains) > 2 else 0.6
        }
    
    def _generate_timing_recommendations(self, gas_trends: Dict[str, Any], urgency_level: str) -> Dict[str, Any]:
        """Generate timing recommendations based on trends and urgency"""
        
        if urgency_level == "immediate":
            return {
                "recommendation": "execute_now",
                "reasoning": "Immediate execution required",
                "optimal_window": "now",
                "delay_risk": "high"
            }
        
        # Analyze trends to find best timing
        best_windows = []
        for chain, trend_data in gas_trends.items():
            if trend_data.get("prediction") == "decreasing":
                best_windows.append({
                    "chain": chain,
                    "window": "next_2_hours",
                    "expected_savings": "10-20%",
                    "confidence": trend_data.get("risk_assessment", {}).get("risk_score", 0.5)
                })
            elif trend_data.get("prediction") == "stable":
                optimal_windows = trend_data.get("optimal_windows", [])
                if optimal_windows:
                    best_window = optimal_windows[0]
                    best_windows.append({
                        "chain": chain,
                        "window": best_window.get("window", "flexible"),
                        "expected_savings": f"{best_window.get('savings_potential', 0)*100:.1f}%",
                        "confidence": best_window.get("confidence", 0.5)
                    })
        
        # Generate overall recommendation
        if not best_windows:
            recommendation = "execute_when_convenient"
            reasoning = "No clear timing advantages identified"
        elif urgency_level == "low":
            recommendation = "wait_for_optimal_window"
            reasoning = "Low urgency allows waiting for better gas prices"
        else:
            recommendation = "monitor_and_execute"
            reasoning = "Balance timing optimization with execution needs"
        
        return {
            "recommendation": recommendation,
            "reasoning": reasoning,
            "best_windows": best_windows,
            "monitoring_required": len(best_windows) > 0,
            "fallback_plan": "Execute within 24 hours regardless of gas prices"
        }

    async def analyze_gas_optimization(
        self, chains: List[str] = None, transaction_types: List[str] = None, urgency_level: str = "normal"
    ) -> Dict[str, Any]:
        """Main entry point for gas optimization analysis"""
        if chains is None:
            chains = ["ethereum", "base", "optimism", "arbitrum", "polygon"]
        if transaction_types is None:
            transaction_types = ["token_swap"]
        
        return await self._analyze_gas_landscape(chains, transaction_types, urgency_level)

    def get_agent(self):
        """Return the uAgent instance"""
        return self.agent
