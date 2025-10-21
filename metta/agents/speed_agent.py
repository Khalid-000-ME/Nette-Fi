from typing import List, Dict, Any

class SpeedOptimizerAgent:
    """
    Agent focused on minimizing execution time while maintaining
    acceptable profit levels and reasonable risk.
    """
    
    def __init__(self):
        self.name = "Speed Optimizer Agent"
        self.priority = "speed"
    
    def analyze(self, simulations: List[Dict[str, Any]], user_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze simulations to find the fastest acceptable execution
        
        Args:
            simulations: List of simulation results
            user_context: Additional context about user preferences
            
        Returns:
            Analysis result with recommendation and reasoning
        """
        if not simulations:
            raise ValueError("No simulations provided")
        
        # Sort by execution speed (block offset ascending)
        sorted_by_speed = sorted(simulations, key=lambda s: s['block_offset'])
        
        # Calculate profit benchmarks
        max_profit = max(float(s['estimated_output_usd']) for s in simulations)
        min_acceptable_profit = max_profit * 0.90  # Within 10% of max profit
        
        # Find fastest option that meets profit threshold
        acceptable_options = []
        for sim in sorted_by_speed:
            profit = float(sim['estimated_output_usd']) - float(sim['gas_cost_usd'])
            
            # Check if option meets minimum criteria
            if (profit >= min_acceptable_profit * 0.95 and  # 95% of acceptable profit
                sim['mev_risk_score'] <= 70 and  # Reasonable MEV risk
                sim['confidence'] >= 70):  # Good confidence
                
                acceptable_options.append({
                    **sim,
                    'execution_time_seconds': sim['block_offset'] * 12,
                    'profit_ratio': profit / max_profit,
                    'speed_score': self.calculate_speed_score(sim, user_context)
                })
        
        # If no acceptable options, fall back to fastest overall
        if not acceptable_options:
            acceptable_options = [{
                **sorted_by_speed[0],
                'execution_time_seconds': sorted_by_speed[0]['block_offset'] * 12,
                'profit_ratio': float(sorted_by_speed[0]['estimated_output_usd']) / max_profit,
                'speed_score': self.calculate_speed_score(sorted_by_speed[0], user_context)
            }]
        
        best = acceptable_options[0]
        
        # Build reasoning
        execution_time = best['execution_time_seconds']
        profit_percentage = best['profit_ratio'] * 100
        
        reasoning = (
            f"Option {best['id']} executes in {execution_time}s ({best['block_offset']} blocks). "
            f"Minimizes exposure to price volatility while maintaining "
            f"{profit_percentage:.1f}% of maximum profit. "
        )
        
        # Add context-specific reasoning
        if user_context.get('is_time_sensitive', False):
            reasoning += "Prioritized for time-sensitive execution. "
        
        volatility = user_context.get('volatility', '1.2%')
        reasoning += f"Reduces market risk exposure given {volatility} hourly volatility."
        
        # Identify concerns
        concerns = []
        if best['profit_ratio'] < 0.95:
            profit_loss = (1 - best['profit_ratio']) * 100
            concerns.append(f"Sacrifices {profit_loss:.1f}% profit for speed")
        
        if best['mev_risk_score'] > 40:
            concerns.append(f"Moderate MEV risk ({best['mev_risk_score']}/100) due to faster execution")
        
        if execution_time == 0:
            concerns.append("Immediate execution has highest MEV exposure")
        
        # Calculate score (higher = better, penalize waiting time)
        base_score = 100 - (best['block_offset'] * 15)  # Heavy penalty for waiting
        
        # Bonus for maintaining profit
        if best['profit_ratio'] > 0.95:
            base_score += 15
        elif best['profit_ratio'] > 0.90:
            base_score += 10
        
        # Bonus for time sensitivity
        if user_context.get('is_time_sensitive', False):
            base_score += 10
        
        return {
            "recommended_id": best['id'],
            "score": max(0, min(100, base_score)),
            "reasoning": reasoning,
            "concerns": concerns,
            "agent": "Speed_Optimizer",
            "execution_time_seconds": execution_time,
            "speed_metrics": {
                "blocks_to_wait": best['block_offset'],
                "execution_time_seconds": execution_time,
                "profit_retention_percent": profit_percentage,
                "mev_risk_score": best['mev_risk_score'],
                "time_vs_profit_tradeoff": self.calculate_time_profit_tradeoff(best, simulations)
            }
        }
    
    def calculate_speed_score(self, simulation: Dict[str, Any], user_context: Dict[str, Any]) -> float:
        """Calculate composite speed optimization score"""
        # Base score inversely related to wait time
        base_score = 100 - (simulation['block_offset'] * 20)
        
        # Adjust for profit retention
        profit = float(simulation['estimated_output_usd']) - float(simulation['gas_cost_usd'])
        if profit > 0:
            base_score += 10
        
        # Penalty for high MEV risk
        mev_penalty = simulation['mev_risk_score'] * 0.2
        base_score -= mev_penalty
        
        # Bonus for time sensitivity
        if user_context.get('is_time_sensitive', False):
            base_score += 20
        
        return max(0, base_score)
    
    def calculate_time_profit_tradeoff(self, selected_sim: Dict[str, Any], all_simulations: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze the time vs profit tradeoff for the selected option"""
        max_profit_sim = max(all_simulations, key=lambda s: float(s['estimated_output_usd']))
        
        selected_profit = float(selected_sim['estimated_output_usd'])
        max_profit = float(max_profit_sim['estimated_output_usd'])
        
        profit_sacrifice = max_profit - selected_profit
        time_saved = (max_profit_sim['block_offset'] - selected_sim['block_offset']) * 12
        
        return {
            "profit_sacrificed_usd": profit_sacrifice,
            "time_saved_seconds": time_saved,
            "profit_per_second_saved": profit_sacrifice / max(time_saved, 1),
            "is_good_tradeoff": profit_sacrifice < max_profit * 0.05  # Less than 5% sacrifice
        }
    
    def analyze_execution_urgency(self, user_context: Dict[str, Any]) -> str:
        """Determine execution urgency level"""
        if user_context.get('is_time_sensitive', False):
            return "high"
        
        trade_size = user_context.get('trade_size_usd', 0)
        if trade_size > 50000:  # Large trades may need faster execution
            return "medium"
        
        volatility = float(user_context.get('volatility', '1.2').rstrip('%'))
        if volatility > 3.0:  # High volatility markets
            return "medium"
        
        return "low"
    
    def estimate_slippage_risk(self, simulation: Dict[str, Any], wait_time_seconds: int) -> float:
        """Estimate additional slippage risk from waiting"""
        base_slippage = float(simulation.get('price_impact_percent', '0.5'))
        
        # Additional slippage risk increases with wait time
        # Assume 0.1% additional slippage per minute of waiting
        additional_risk = (wait_time_seconds / 60) * 0.1
        
        return base_slippage + additional_risk
