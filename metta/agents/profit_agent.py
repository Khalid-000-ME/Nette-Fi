from typing import List, Dict, Any

class ProfitMaximizerAgent:
    """
    Agent focused on maximizing net profit after accounting for
    gas costs, MEV risks, and execution timing.
    """
    
    def __init__(self):
        self.name = "Profit Maximizer Agent"
        self.priority = "profit"
    
    def analyze(self, simulations: List[Dict[str, Any]], risk_tolerance: str) -> Dict[str, Any]:
        """
        Analyze simulations to find the option with highest net profit
        
        Args:
            simulations: List of simulation results
            risk_tolerance: User's risk tolerance level
            
        Returns:
            Analysis result with recommendation and reasoning
        """
        if not simulations:
            raise ValueError("No simulations provided")
        
        # Calculate net profit for each simulation
        enriched_sims = []
        for sim in simulations:
            net_profit = self.calculate_net_profit(sim, risk_tolerance)
            enriched_sims.append({
                **sim,
                'net_profit': net_profit,
                'profit_score': self.calculate_profit_score(sim, net_profit, risk_tolerance)
            })
        
        # Sort by net profit (descending)
        sorted_sims = sorted(enriched_sims, key=lambda s: s['net_profit'], reverse=True)
        best = sorted_sims[0]
        
        # Find immediate execution option for comparison
        immediate = next((s for s in enriched_sims if s['block_offset'] == 0), sorted_sims[-1])
        profit_diff = best['net_profit'] - immediate['net_profit']
        
        # Build reasoning
        reasoning = (
            f"Option {best['id']} yields ${best['net_profit']:.2f} net profit, "
            f"which is ${profit_diff:.2f} {'more' if profit_diff > 0 else 'less'} than immediate execution. "
            f"This accounts for gas costs (${best['gas_cost_usd']}) and estimated MEV risk."
        )
        
        # Identify concerns
        concerns = []
        if best['block_offset'] > 2:
            concerns.append("Longer wait time increases price movement risk")
        
        if best['mev_risk_score'] > 50:
            concerns.append(f"Moderate MEV risk ({best['mev_risk_score']}/100) for higher profit")
        
        if float(best['price_impact_percent']) > 2.0:
            concerns.append(f"High price impact ({best['price_impact_percent']}%) may affect execution")
        
        # Calculate score
        base_score = min(100, (profit_diff / max(immediate['net_profit'], 1)) * 100 + 70)
        
        # Adjust for risk tolerance
        if risk_tolerance == "aggressive" and best['mev_risk_score'] < 70:
            base_score += 10
        elif risk_tolerance == "conservative" and best['mev_risk_score'] > 30:
            base_score -= 15
        
        return {
            "recommended_id": best['id'],
            "score": max(0, min(100, base_score)),
            "reasoning": reasoning,
            "concerns": concerns,
            "agent": "Profit_Maximizer",
            "profit_improvement": profit_diff,
            "profit_metrics": {
                "net_profit_usd": best['net_profit'],
                "gross_output_usd": float(best['estimated_output_usd']),
                "gas_cost_usd": float(best['gas_cost_usd']),
                "estimated_mev_loss_usd": self.estimate_mev_loss(best),
                "profit_margin_percent": (best['net_profit'] / float(best['estimated_output_usd'])) * 100
            }
        }
    
    def calculate_net_profit(self, simulation: Dict[str, Any], risk_tolerance: str) -> float:
        """Calculate net profit accounting for all costs and risks"""
        gross_output = float(simulation['estimated_output_usd'])
        gas_cost = float(simulation['gas_cost_usd'])
        
        # Estimate MEV loss based on risk score and tolerance
        mev_loss = self.estimate_mev_loss(simulation)
        
        # Apply risk tolerance adjustment
        if risk_tolerance == "conservative":
            # Conservative users want to account for worst-case MEV scenarios
            mev_loss *= 1.5
        elif risk_tolerance == "aggressive":
            # Aggressive users are willing to take MEV risk for profit
            mev_loss *= 0.7
        
        net_profit = gross_output - gas_cost - mev_loss
        return net_profit
    
    def estimate_mev_loss(self, simulation: Dict[str, Any]) -> float:
        """Estimate potential MEV loss in USD"""
        output_usd = float(simulation['estimated_output_usd'])
        mev_risk = simulation['mev_risk_score']
        
        # MEV loss estimation based on risk score
        # Higher risk = higher expected loss
        if mev_risk <= 20:
            loss_rate = 0.005  # 0.5%
        elif mev_risk <= 40:
            loss_rate = 0.015  # 1.5%
        elif mev_risk <= 60:
            loss_rate = 0.025  # 2.5%
        elif mev_risk <= 80:
            loss_rate = 0.035  # 3.5%
        else:
            loss_rate = 0.05   # 5%
        
        return output_usd * loss_rate
    
    def calculate_profit_score(self, simulation: Dict[str, Any], net_profit: float, risk_tolerance: str) -> float:
        """Calculate a composite profit score"""
        base_score = net_profit
        
        # Penalize for high MEV risk
        mev_penalty = simulation['mev_risk_score'] * 0.1
        
        # Penalize for long wait times (opportunity cost)
        time_penalty = simulation['block_offset'] * 5
        
        # Penalize for high gas costs
        gas_penalty = float(simulation['gas_cost_usd']) * 2
        
        total_score = base_score - mev_penalty - time_penalty - gas_penalty
        
        return max(0, total_score)
    
    def analyze_profit_distribution(self, simulations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze profit distribution across all simulations"""
        profits = [float(sim['estimated_output_usd']) - float(sim['gas_cost_usd']) 
                  for sim in simulations]
        
        return {
            "min_profit": min(profits),
            "max_profit": max(profits),
            "avg_profit": sum(profits) / len(profits),
            "profit_range": max(profits) - min(profits),
            "profitable_options": len([p for p in profits if p > 0])
        }
