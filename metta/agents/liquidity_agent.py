"""
Liquidity Optimization Agent - Specialized in liquidity analysis and optimization
Uses ASI (Fetch.ai) uAgent framework for autonomous liquidity monitoring
"""

from uagents import Agent, Context, Model
from typing import Dict, List, Any, Optional
import json
import numpy as np
import asyncio
from dataclasses import dataclass

@dataclass
class LiquidityMetrics:
    total_liquidity: float
    depth_score: float
    spread_impact: float
    slippage_estimate: float
    fragmentation_risk: float

class LiquidityRequest(Model):
    token_pair: str
    trade_size: float
    chains: List[str]

class LiquidityResponse(Model):
    liquidity_analysis: Dict[str, Any]
    optimal_routing: Dict[str, Any]
    execution_strategy: Dict[str, Any]

class LiquidityOptimizationAgent:
    def __init__(self, agent_address: str = "liquidity_agent"):
        self.agent = Agent(
            name="liquidity_optimization_agent",
            seed="liquidity_seed_54321",
            port=8003,
            endpoint=["http://localhost:8003/submit"]
        )
        
        # DEX liquidity sources
        self.dex_sources = {
            "uniswap_v3": {"weight": 0.3, "fee_tier": 0.003},
            "curve": {"weight": 0.25, "fee_tier": 0.0004},
            "balancer": {"weight": 0.2, "fee_tier": 0.0025},
            "sushiswap": {"weight": 0.15, "fee_tier": 0.003},
            "1inch": {"weight": 0.1, "fee_tier": 0.002}
        }
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        @self.agent.on_message(model=LiquidityRequest)
        async def handle_liquidity_analysis(ctx: Context, sender: str, msg: LiquidityRequest):
            try:
                analysis = await self._analyze_liquidity_landscape(
                    msg.token_pair, msg.trade_size, msg.chains
                )
                
                response = LiquidityResponse(
                    liquidity_analysis=analysis['analysis'],
                    optimal_routing=analysis['routing'],
                    execution_strategy=analysis['strategy']
                )
                
                await ctx.send(sender, response)
                
            except Exception as e:
                ctx.logger.error(f"Liquidity analysis failed: {str(e)}")
    
    async def _analyze_liquidity_landscape(
        self, token_pair: str, trade_size: float, chains: List[str]
    ) -> Dict[str, Any]:
        """Comprehensive liquidity analysis across chains and DEXs"""
        
        # Fetch liquidity data for each chain
        chain_liquidity = {}
        for chain in chains:
            chain_liquidity[chain] = await self._fetch_chain_liquidity(token_pair, chain)
        
        # Analyze cross-chain liquidity distribution
        distribution_analysis = self._analyze_liquidity_distribution(chain_liquidity)
        
        # Calculate optimal routing strategy
        routing_strategy = await self._calculate_optimal_routing(
            token_pair, trade_size, chain_liquidity
        )
        
        # Generate execution recommendations
        execution_strategy = self._generate_execution_strategy(
            trade_size, routing_strategy, distribution_analysis
        )
        
        return {
            "analysis": {
                "chain_liquidity": chain_liquidity,
                "distribution": distribution_analysis,
                "total_available": sum(cl.get('total_liquidity', 0) for cl in chain_liquidity.values()),
                "fragmentation_score": distribution_analysis['fragmentation_score'],
                "liquidity_quality": self._assess_liquidity_quality(chain_liquidity)
            },
            "routing": routing_strategy,
            "strategy": execution_strategy
        }
    
    async def _fetch_chain_liquidity(self, token_pair: str, chain: str) -> Dict[str, Any]:
        """Fetch liquidity data for a specific chain"""
        
        # Simulate liquidity data (replace with real DEX API calls)
        base_liquidity = {
            "ethereum": 50000000,
            "base": 25000000,
            "optimism": 15000000,
            "arbitrum": 20000000,
            "polygon": 10000000
        }.get(chain.lower(), 5000000)
        
        # Add some randomness to simulate real conditions
        liquidity_variance = np.random.uniform(0.8, 1.2)
        total_liquidity = base_liquidity * liquidity_variance
        
        # Calculate depth metrics
        depth_2_percent = total_liquidity * 0.15  # 2% depth
        depth_5_percent = total_liquidity * 0.35  # 5% depth
        
        # DEX distribution on this chain
        dex_distribution = {}
        remaining_liquidity = total_liquidity
        
        for dex, config in self.dex_sources.items():
            if remaining_liquidity > 0:
                dex_liquidity = min(
                    remaining_liquidity * config["weight"] * np.random.uniform(0.7, 1.3),
                    remaining_liquidity
                )
                dex_distribution[dex] = {
                    "liquidity": dex_liquidity,
                    "fee_tier": config["fee_tier"],
                    "spread": config["fee_tier"] * np.random.uniform(0.8, 1.5)
                }
                remaining_liquidity -= dex_liquidity
        
        return {
            "chain": chain,
            "total_liquidity": total_liquidity,
            "depth_2_percent": depth_2_percent,
            "depth_5_percent": depth_5_percent,
            "dex_distribution": dex_distribution,
            "average_spread": np.mean([d["spread"] for d in dex_distribution.values()]),
            "liquidity_concentration": self._calculate_concentration(dex_distribution),
            "estimated_slippage": self._estimate_slippage(total_liquidity, depth_2_percent)
        }
    
    def _calculate_concentration(self, dex_distribution: Dict[str, Any]) -> float:
        """Calculate liquidity concentration (Herfindahl index)"""
        total_liquidity = sum(d["liquidity"] for d in dex_distribution.values())
        if total_liquidity == 0:
            return 1.0
        
        shares = [d["liquidity"] / total_liquidity for d in dex_distribution.values()]
        herfindahl_index = sum(share ** 2 for share in shares)
        
        return herfindahl_index
    
    def _estimate_slippage(self, total_liquidity: float, depth_2_percent: float) -> float:
        """Estimate slippage based on liquidity depth"""
        if total_liquidity == 0:
            return 0.1  # 10% slippage for no liquidity
        
        # Simple slippage model
        liquidity_ratio = depth_2_percent / total_liquidity
        base_slippage = 0.002  # 0.2% base slippage
        
        return base_slippage / max(liquidity_ratio, 0.01)
    
    def _analyze_liquidity_distribution(self, chain_liquidity: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze liquidity distribution across chains"""
        
        total_liquidity = sum(cl.get('total_liquidity', 0) for cl in chain_liquidity.values())
        
        if total_liquidity == 0:
            return {"fragmentation_score": 1.0, "dominant_chain": None}
        
        # Calculate chain shares
        chain_shares = {}
        for chain, data in chain_liquidity.items():
            chain_shares[chain] = data.get('total_liquidity', 0) / total_liquidity
        
        # Calculate fragmentation score (1 - Herfindahl index)
        herfindahl = sum(share ** 2 for share in chain_shares.values())
        fragmentation_score = 1 - herfindahl
        
        # Identify dominant chain
        dominant_chain = max(chain_shares.items(), key=lambda x: x[1])[0] if chain_shares else None
        
        return {
            "fragmentation_score": fragmentation_score,
            "dominant_chain": dominant_chain,
            "chain_shares": chain_shares,
            "liquidity_balance": "balanced" if fragmentation_score > 0.6 else "concentrated"
        }
    
    async def _calculate_optimal_routing(
        self, token_pair: str, trade_size: float, chain_liquidity: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate optimal routing strategy across chains and DEXs"""
        
        # Sort chains by liquidity efficiency
        chain_efficiency = {}
        for chain, data in chain_liquidity.items():
            liquidity = data.get('total_liquidity', 0)
            slippage = data.get('estimated_slippage', 0.1)
            spread = data.get('average_spread', 0.01)
            
            # Efficiency score (higher is better)
            efficiency = liquidity / (1 + slippage + spread) if liquidity > 0 else 0
            chain_efficiency[chain] = {
                "efficiency": efficiency,
                "liquidity": liquidity,
                "slippage": slippage,
                "spread": spread
            }
        
        # Sort by efficiency
        sorted_chains = sorted(
            chain_efficiency.items(),
            key=lambda x: x[1]["efficiency"],
            reverse=True
        )
        
        # Calculate optimal allocation
        optimal_allocation = self._calculate_trade_allocation(trade_size, sorted_chains)
        
        # Generate routing paths
        routing_paths = []
        for chain, allocation in optimal_allocation.items():
            if allocation["amount"] > 0:
                chain_data = chain_liquidity[chain]
                best_dexs = self._select_best_dexs(chain_data["dex_distribution"], allocation["amount"])
                
                routing_paths.append({
                    "chain": chain,
                    "allocation_percent": allocation["percent"],
                    "amount": allocation["amount"],
                    "dex_routing": best_dexs,
                    "estimated_output": allocation["amount"] * (1 - chain_efficiency[chain]["slippage"]),
                    "gas_estimate": self._estimate_gas_cost(chain, best_dexs)
                })
        
        return {
            "total_paths": len(routing_paths),
            "routing_paths": routing_paths,
            "efficiency_ranking": sorted_chains,
            "cross_chain_required": len(routing_paths) > 1,
            "estimated_total_output": sum(path["estimated_output"] for path in routing_paths),
            "routing_complexity": self._assess_routing_complexity(routing_paths)
        }
    
    def _calculate_trade_allocation(
        self, trade_size: float, sorted_chains: List[tuple]
    ) -> Dict[str, Dict[str, float]]:
        """Calculate optimal trade allocation across chains"""
        
        allocation = {}
        remaining_size = trade_size
        
        for chain, metrics in sorted_chains:
            if remaining_size <= 0:
                break
            
            # Calculate maximum efficient size for this chain
            max_efficient = metrics["liquidity"] * 0.05  # 5% of liquidity
            
            # Allocate based on efficiency and available liquidity
            allocated_amount = min(remaining_size, max_efficient)
            
            if allocated_amount > 0:
                allocation[chain] = {
                    "amount": allocated_amount,
                    "percent": (allocated_amount / trade_size) * 100
                }
                remaining_size -= allocated_amount
        
        # If there's remaining size, distribute proportionally
        if remaining_size > 0 and allocation:
            total_allocated = sum(a["amount"] for a in allocation.values())
            for chain in allocation:
                additional = remaining_size * (allocation[chain]["amount"] / total_allocated)
                allocation[chain]["amount"] += additional
                allocation[chain]["percent"] = (allocation[chain]["amount"] / trade_size) * 100
        
        return allocation
    
    def _select_best_dexs(self, dex_distribution: Dict[str, Any], amount: float) -> List[Dict[str, Any]]:
        """Select best DEXs for execution on a specific chain"""
        
        # Sort DEXs by cost efficiency (liquidity/spread ratio)
        dex_efficiency = []
        for dex, data in dex_distribution.items():
            efficiency = data["liquidity"] / (1 + data["spread"]) if data["liquidity"] > 0 else 0
            dex_efficiency.append({
                "dex": dex,
                "efficiency": efficiency,
                "liquidity": data["liquidity"],
                "spread": data["spread"],
                "fee_tier": data["fee_tier"]
            })
        
        # Sort by efficiency
        dex_efficiency.sort(key=lambda x: x["efficiency"], reverse=True)
        
        # Allocate amount across top DEXs
        selected_dexs = []
        remaining_amount = amount
        
        for dex_data in dex_efficiency[:3]:  # Use top 3 DEXs max
            if remaining_amount <= 0:
                break
            
            # Calculate allocation for this DEX
            max_allocation = min(remaining_amount, dex_data["liquidity"] * 0.1)  # 10% of DEX liquidity
            
            if max_allocation > 0:
                selected_dexs.append({
                    "dex": dex_data["dex"],
                    "amount": max_allocation,
                    "percent": (max_allocation / amount) * 100,
                    "expected_spread": dex_data["spread"],
                    "fee_tier": dex_data["fee_tier"]
                })
                remaining_amount -= max_allocation
        
        return selected_dexs
    
    def _estimate_gas_cost(self, chain: str, dex_routing: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Estimate gas costs for execution on a chain"""
        
        # Base gas costs by chain (in USD)
        base_gas_costs = {
            "ethereum": 15.0,
            "base": 0.5,
            "optimism": 1.0,
            "arbitrum": 2.0,
            "polygon": 0.1
        }
        
        base_cost = base_gas_costs.get(chain.lower(), 5.0)
        
        # Additional cost per DEX interaction
        dex_complexity_cost = len(dex_routing) * base_cost * 0.3
        
        total_gas_cost = base_cost + dex_complexity_cost
        
        return {
            "base_cost": base_cost,
            "complexity_cost": dex_complexity_cost,
            "total_cost_usd": total_gas_cost,
            "gas_efficiency": "high" if total_gas_cost < 5 else "medium" if total_gas_cost < 15 else "low"
        }
    
    def _assess_routing_complexity(self, routing_paths: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess the complexity of the routing strategy"""
        
        total_paths = len(routing_paths)
        total_dex_interactions = sum(len(path["dex_routing"]) for path in routing_paths)
        
        complexity_score = (total_paths - 1) * 0.3 + (total_dex_interactions - 1) * 0.2
        
        complexity_level = "simple" if complexity_score < 0.5 else "moderate" if complexity_score < 1.5 else "complex"
        
        return {
            "complexity_score": complexity_score,
            "complexity_level": complexity_level,
            "total_paths": total_paths,
            "total_dex_interactions": total_dex_interactions,
            "execution_time_estimate": self._estimate_execution_time(complexity_score)
        }
    
    def _estimate_execution_time(self, complexity_score: float) -> str:
        """Estimate execution time based on complexity"""
        
        base_time = 30  # 30 seconds base
        additional_time = complexity_score * 45  # 45 seconds per complexity unit
        
        total_seconds = base_time + additional_time
        
        if total_seconds < 60:
            return f"{int(total_seconds)} seconds"
        else:
            minutes = int(total_seconds / 60)
            seconds = int(total_seconds % 60)
            return f"{minutes}m {seconds}s"
    
    def _assess_liquidity_quality(self, chain_liquidity: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall liquidity quality"""
        
        if not chain_liquidity:
            return {"quality": "poor", "score": 0.0}
        
        # Calculate quality metrics
        total_liquidity = sum(cl.get('total_liquidity', 0) for cl in chain_liquidity.values())
        avg_spread = np.mean([cl.get('average_spread', 0.1) for cl in chain_liquidity.values()])
        avg_concentration = np.mean([cl.get('liquidity_concentration', 1.0) for cl in chain_liquidity.values()])
        
        # Quality score calculation
        liquidity_score = min(total_liquidity / 100000000, 1.0)  # Normalize to 100M
        spread_score = max(0, 1 - avg_spread * 100)  # Lower spread = higher score
        concentration_score = 1 - avg_concentration  # Lower concentration = higher score
        
        overall_score = (liquidity_score * 0.5 + spread_score * 0.3 + concentration_score * 0.2)
        
        quality_level = "excellent" if overall_score > 0.8 else "good" if overall_score > 0.6 else "fair" if overall_score > 0.4 else "poor"
        
        return {
            "quality": quality_level,
            "score": overall_score,
            "liquidity_score": liquidity_score,
            "spread_score": spread_score,
            "concentration_score": concentration_score,
            "recommendations": self._generate_quality_recommendations(overall_score, avg_spread, avg_concentration)
        }
    
    def _generate_quality_recommendations(self, score: float, avg_spread: float, avg_concentration: float) -> List[str]:
        """Generate recommendations based on liquidity quality"""
        
        recommendations = []
        
        if score < 0.5:
            recommendations.append("Consider splitting trade into smaller chunks")
        
        if avg_spread > 0.01:
            recommendations.append("High spreads detected - consider alternative routing")
        
        if avg_concentration > 0.8:
            recommendations.append("Liquidity highly concentrated - diversify across more DEXs")
        
        if score > 0.8:
            recommendations.append("Excellent liquidity conditions - optimal for large trades")
        
        return recommendations
    
    def _generate_execution_strategy(
        self, trade_size: float, routing_strategy: Dict[str, Any], distribution_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate comprehensive execution strategy"""
        
        routing_paths = routing_strategy.get("routing_paths", [])
        complexity = routing_strategy.get("routing_complexity", {})
        
        # Determine execution approach
        if len(routing_paths) == 1:
            approach = "single_chain"
        elif complexity.get("complexity_level") == "simple":
            approach = "parallel_execution"
        else:
            approach = "sequential_execution"
        
        # Calculate timing strategy
        timing_strategy = self._calculate_timing_strategy(routing_paths, complexity)
        
        # Risk mitigation measures
        risk_measures = self._identify_risk_measures(routing_paths, distribution_analysis)
        
        return {
            "execution_approach": approach,
            "timing_strategy": timing_strategy,
            "risk_mitigation": risk_measures,
            "monitoring_requirements": self._define_monitoring_requirements(routing_paths),
            "fallback_options": self._generate_fallback_options(routing_paths),
            "success_criteria": self._define_success_criteria(trade_size, routing_strategy)
        }
    
    def _calculate_timing_strategy(self, routing_paths: List[Dict], complexity: Dict) -> Dict[str, Any]:
        """Calculate optimal timing strategy"""
        
        if len(routing_paths) <= 1:
            return {"strategy": "immediate", "delay": 0}
        
        complexity_level = complexity.get("complexity_level", "simple")
        
        if complexity_level == "simple":
            return {
                "strategy": "parallel",
                "delay": 0,
                "coordination": "simultaneous_execution"
            }
        else:
            return {
                "strategy": "sequential",
                "delay": 15,  # 15 seconds between executions
                "coordination": "staged_execution"
            }
    
    def _identify_risk_measures(self, routing_paths: List[Dict], distribution: Dict) -> List[str]:
        """Identify necessary risk mitigation measures"""
        
        measures = []
        
        if len(routing_paths) > 2:
            measures.append("Implement partial execution monitoring")
        
        if distribution.get("fragmentation_score", 0) > 0.7:
            measures.append("Monitor cross-chain bridge risks")
        
        measures.append("Set maximum slippage tolerance")
        measures.append("Implement execution timeout controls")
        
        return measures
    
    def _define_monitoring_requirements(self, routing_paths: List[Dict]) -> Dict[str, Any]:
        """Define monitoring requirements for execution"""
        
        return {
            "real_time_tracking": len(routing_paths) > 1,
            "slippage_monitoring": True,
            "gas_price_tracking": True,
            "liquidity_depth_monitoring": len(routing_paths) > 2,
            "cross_chain_status": any("bridge" in str(path) for path in routing_paths)
        }
    
    def _generate_fallback_options(self, routing_paths: List[Dict]) -> List[Dict[str, Any]]:
        """Generate fallback execution options"""
        
        fallbacks = [
            {
                "option": "reduce_trade_size",
                "description": "Reduce trade size by 50% if slippage exceeds threshold",
                "trigger": "slippage > 5%"
            },
            {
                "option": "alternative_routing",
                "description": "Switch to single-chain execution on most liquid chain",
                "trigger": "cross_chain_failure"
            }
        ]
        
        if len(routing_paths) > 1:
            fallbacks.append({
                "option": "sequential_fallback",
                "description": "Execute remaining portions sequentially if parallel execution fails",
                "trigger": "partial_execution_failure"
            })
        
        return fallbacks
    
    def _define_success_criteria(self, trade_size: float, routing_strategy: Dict) -> Dict[str, Any]:
        """Define success criteria for execution"""
        
        expected_output = routing_strategy.get("estimated_total_output", trade_size * 0.95)
        
        return {
            "minimum_output": expected_output * 0.98,  # 2% tolerance
            "maximum_slippage": 0.05,  # 5%
            "execution_time_limit": "5 minutes",
            "partial_success_threshold": 0.8,  # 80% of trade executed
            "quality_metrics": {
                "price_improvement": expected_output > trade_size * 0.99,
                "execution_efficiency": True,
                "cost_effectiveness": True
            }
        }

    async def analyze_liquidity(
        self, token_pair: str = "ETH/USDC", trade_size: float = 1.0, chains: List[str] = None
    ) -> Dict[str, Any]:
        """Main entry point for liquidity analysis"""
        if chains is None:
            chains = ["ethereum", "base", "optimism", "arbitrum", "polygon"]
        
        return await self._analyze_liquidity_landscape(token_pair, trade_size, chains)

    def get_agent(self):
        """Return the uAgent instance"""
        return self.agent
