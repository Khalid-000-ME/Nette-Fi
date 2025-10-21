from typing import List, Dict, Any

class MEVProtectionAgent:
    """
    Agent focused on minimizing MEV risk and protecting user trades
    from sandwich attacks and frontrunning.
    """
    
    def __init__(self):
        self.name = "MEV Protection Agent"
        self.priority = "safety"
    
    def analyze(self, simulations: List[Dict[str, Any]], user_priority: str) -> Dict[str, Any]:
        """
        Analyze simulations to find the option with lowest MEV risk
        
        Args:
            simulations: List of simulation results
            user_priority: User's stated priority
            
        Returns:
            Analysis result with recommendation and reasoning
        """
        if not simulations:
            raise ValueError("No simulations provided")
        
        # Sort by MEV risk (ascending - lower is better)
        sorted_sims = sorted(simulations, key=lambda s: s['mev_risk_score'])
        best = sorted_sims[0]
        
        # Calculate risk reduction compared to immediate execution
        immediate_sim = next((s for s in simulations if s['block_offset'] == 0), sorted_sims[-1])
        risk_reduction = max(0, immediate_sim['mev_risk_score'] - best['mev_risk_score'])
        
        # Build reasoning
        reasoning = (
            f"Option {best['id']} has lowest MEV risk ({best['mev_risk_score']}/100). "
            f"Detected {best.get('mempool_snapshot', {}).get('sandwich_bots_detected', 0)} sandwich bots "
            f"in current block. Waiting {best['block_offset']} blocks reduces exposure by {risk_reduction}%."
        )
        
        # Identify concerns
        concerns = []
        if best['block_offset'] > 3:
            concerns.append(f"Wait time of {best['block_offset'] * 12}s may expose to price movement")
        
        if float(best['estimated_output_usd']) < float(sorted_sims[-1]['estimated_output_usd']) * 0.95:
            profit_loss = float(sorted_sims[-1]['estimated_output_usd']) - float(best['estimated_output_usd'])
            concerns.append(f"May sacrifice ${profit_loss:.2f} in potential profit for safety")
        
        # Calculate score (higher = better)
        base_score = 100 - best['mev_risk_score']
        
        # Bonus for user priority alignment
        if user_priority == "mev_protection":
            base_score += 10
        elif user_priority == "balanced":
            base_score += 5
        
        return {
            "recommended_id": best['id'],
            "score": min(100, base_score),
            "reasoning": reasoning,
            "concerns": concerns,
            "agent": "MEV_Protection",
            "risk_reduction_percent": risk_reduction,
            "safety_metrics": {
                "mev_risk": best['mev_risk_score'],
                "blocks_to_wait": best['block_offset'],
                "sandwich_bots_detected": best.get('mempool_snapshot', {}).get('sandwich_bots_detected', 0)
            }
        }
    
    def calculate_mev_severity(self, mev_risk_score: int) -> str:
        """Categorize MEV risk severity"""
        if mev_risk_score <= 20:
            return "Very Low"
        elif mev_risk_score <= 40:
            return "Low"
        elif mev_risk_score <= 60:
            return "Medium"
        elif mev_risk_score <= 80:
            return "High"
        else:
            return "Very High"
    
    def estimate_mev_loss(self, simulation: Dict[str, Any]) -> float:
        """Estimate potential MEV loss in USD"""
        output_usd = float(simulation['estimated_output_usd'])
        mev_risk = simulation['mev_risk_score']
        
        # Typical MEV attack extracts 1-5% of trade value
        # Risk score represents probability, not guaranteed loss
        estimated_loss = (mev_risk / 100) * output_usd * 0.03  # 3% average extraction
        
        return estimated_loss
