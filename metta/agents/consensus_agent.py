import os
import json
import requests
from typing import Dict, Any, List

class ConsensusAgent:
    """
    Agent that combines recommendations from other agents using MeTTa reasoning
    and ASI:One API to reach optimal consensus decisions.
    """
    
    def __init__(self):
        self.name = "Consensus Agent"
        self.asi_one_api_key = os.getenv("ASI_ONE_API_KEY")
        self.asi_one_url = "https://api.asi1.ai/v1/chat/completions"
        
    def decide(
        self, 
        mev_analysis: Dict[str, Any],
        profit_analysis: Dict[str, Any],
        speed_analysis: Dict[str, Any],
        user_priority: str,
        risk_tolerance: str
    ) -> Dict[str, Any]:
        """
        Use MeTTa reasoning and ASI:One to combine agent recommendations
        
        Args:
            mev_analysis: MEV protection agent analysis
            profit_analysis: Profit maximizer agent analysis  
            speed_analysis: Speed optimizer agent analysis
            user_priority: User's stated priority
            risk_tolerance: User's risk tolerance
            
        Returns:
            Consensus recommendation with reasoning
        """
        
        # If ASI:One API is available, use it for advanced reasoning
        if self.asi_one_api_key:
            try:
                return self._asi_one_consensus(
                    mev_analysis, profit_analysis, speed_analysis,
                    user_priority, risk_tolerance
                )
            except Exception as e:
                print(f"ASI:One API failed, falling back to local reasoning: {e}")
        
        # Fallback to local MeTTa-style reasoning
        return self._local_metta_consensus(
            mev_analysis, profit_analysis, speed_analysis,
            user_priority, risk_tolerance
        )
    
    def _asi_one_consensus(
        self,
        mev_analysis: Dict[str, Any],
        profit_analysis: Dict[str, Any], 
        speed_analysis: Dict[str, Any],
        user_priority: str,
        risk_tolerance: str
    ) -> Dict[str, Any]:
        """Use ASI:One API for consensus reasoning"""
        
        prompt = self._build_consensus_prompt(
            mev_analysis, profit_analysis, speed_analysis,
            user_priority, risk_tolerance
        )
        
        response = requests.post(
            self.asi_one_url,
            headers={
                "Authorization": f"Bearer {self.asi_one_api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "asi1",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a DeFi trading optimizer that combines multiple agent analyses to make optimal decisions. Respond only in valid JSON format."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "temperature": 0.3,
                "response_format": {"type": "json_object"}
            },
            timeout=10
        )
        
        if response.status_code == 200:
            decision_text = response.json()['choices'][0]['message']['content']
            decision = json.loads(decision_text)
            
            return {
                "recommended_id": decision["recommended_id"],
                "confidence": decision["confidence"],
                "reasoning": decision["reasoning"],
                "agent_agreement": decision["agent_agreement"],
                "key_tradeoff": decision["key_tradeoff"],
                "user_should_know": decision.get("user_should_know", ""),
                "consensus_method": "asi_one"
            }
        else:
            raise Exception(f"ASI:One API error: {response.status_code}")
    
    def _local_metta_consensus(
        self,
        mev_analysis: Dict[str, Any],
        profit_analysis: Dict[str, Any],
        speed_analysis: Dict[str, Any], 
        user_priority: str,
        risk_tolerance: str
    ) -> Dict[str, Any]:
        """Local MeTTa-style reasoning for consensus"""
        
        # Define priority weights based on user preference
        weights = {
            "mev_protection": {"mev": 0.6, "profit": 0.3, "speed": 0.1},
            "profit": {"mev": 0.2, "profit": 0.6, "speed": 0.2},
            "speed": {"mev": 0.2, "profit": 0.2, "speed": 0.6},
            "balanced": {"mev": 0.4, "profit": 0.4, "speed": 0.2}
        }
        
        weight = weights.get(user_priority, weights["balanced"])
        
        # Calculate weighted scores for each recommendation
        candidates = [
            {
                "id": mev_analysis["recommended_id"],
                "score": mev_analysis["score"] * weight["mev"],
                "source": "mev",
                "original_score": mev_analysis["score"]
            },
            {
                "id": profit_analysis["recommended_id"], 
                "score": profit_analysis["score"] * weight["profit"],
                "source": "profit",
                "original_score": profit_analysis["score"]
            },
            {
                "id": speed_analysis["recommended_id"],
                "score": speed_analysis["score"] * weight["speed"], 
                "source": "speed",
                "original_score": speed_analysis["score"]
            }
        ]
        
        # Group by ID and sum weighted scores
        score_map = {}
        for candidate in candidates:
            sim_id = candidate["id"]
            if sim_id not in score_map:
                score_map[sim_id] = {
                    "total_score": 0,
                    "sources": [],
                    "individual_scores": {}
                }
            
            score_map[sim_id]["total_score"] += candidate["score"]
            score_map[sim_id]["sources"].append(candidate["source"])
            score_map[sim_id]["individual_scores"][candidate["source"]] = candidate["original_score"]
        
        # Find highest scoring option
        best_id = max(score_map.keys(), key=lambda k: score_map[k]["total_score"])
        best_data = score_map[best_id]
        
        # Calculate confidence based on score and agreement
        base_confidence = min(95, max(70, best_data["total_score"]))
        
        # Boost confidence if multiple agents agree
        if len(best_data["sources"]) > 1:
            base_confidence += 5
        
        # Adjust for risk tolerance
        if risk_tolerance == "conservative":
            base_confidence -= 5
        elif risk_tolerance == "aggressive":
            base_confidence += 5
        
        confidence = max(70, min(95, int(base_confidence)))
        
        # Build agent agreement description
        if len(best_data["sources"]) > 1:
            agent_agreement = f"{len(best_data['sources'])}/3 agents agree ({' + '.join(best_data['sources'])})"
        else:
            agent_agreement = f"Primary recommendation from {best_data['sources'][0]} agent"
        
        # Generate reasoning
        reasoning = self._generate_local_reasoning(
            best_id, best_data, user_priority, risk_tolerance,
            mev_analysis, profit_analysis, speed_analysis
        )
        
        # Determine key tradeoff
        key_tradeoff = self._identify_key_tradeoff(
            best_id, mev_analysis, profit_analysis, speed_analysis
        )
        
        return {
            "recommended_id": best_id,
            "confidence": confidence,
            "reasoning": reasoning,
            "agent_agreement": agent_agreement, 
            "key_tradeoff": key_tradeoff,
            "consensus_method": "local_metta"
        }
    
    def _build_consensus_prompt(
        self,
        mev_analysis: Dict[str, Any],
        profit_analysis: Dict[str, Any],
        speed_analysis: Dict[str, Any],
        user_priority: str,
        risk_tolerance: str
    ) -> str:
        """Build prompt for ASI:One API"""
        
        return f"""
Three specialist agents have analyzed trade execution options. Find consensus.

**MEV Protection Agent says:**
- Recommends: Option {mev_analysis['recommended_id']}
- Score: {mev_analysis['score']}/100
- Reasoning: {mev_analysis['reasoning']}
- Concerns: {', '.join(mev_analysis['concerns']) if mev_analysis['concerns'] else 'None'}

**Profit Maximizer Agent says:**
- Recommends: Option {profit_analysis['recommended_id']}
- Score: {profit_analysis['score']}/100
- Reasoning: {profit_analysis['reasoning']}
- Concerns: {', '.join(profit_analysis['concerns']) if profit_analysis['concerns'] else 'None'}

**Speed Optimizer Agent says:**
- Recommends: Option {speed_analysis['recommended_id']}
- Score: {speed_analysis['score']}/100
- Reasoning: {speed_analysis['reasoning']}
- Concerns: {', '.join(speed_analysis['concerns']) if speed_analysis['concerns'] else 'None'}

**User Context:**
- Priority: {user_priority} (mev_protection | profit | speed | balanced)
- Risk Tolerance: {risk_tolerance} (conservative | balanced | aggressive)

**Your Task:**
1. Analyze the recommendations considering user priority and risk tolerance
2. If user_priority is "mev_protection", heavily weight the MEV agent's recommendation
3. If user_priority is "profit", heavily weight the Profit agent's recommendation  
4. If user_priority is "speed", heavily weight the Speed agent's recommendation
5. If user_priority is "balanced", weight all three equally
6. Consider if agents disagree - explain the tradeoff clearly
7. Pick the option that best serves the user's stated goals

**Respond in JSON format:**
{{
  "recommended_id": <option_id>,
  "confidence": <70-95>,
  "reasoning": "<Why this option best serves user's priority and balances agent concerns>",
  "agent_agreement": "<Which agents agreed with this choice>", 
  "key_tradeoff": "<What user gains and what they sacrifice>",
  "user_should_know": "<Any critical risk or consideration>"
}}
"""
    
    def _generate_local_reasoning(
        self,
        best_id: int,
        best_data: Dict[str, Any],
        user_priority: str,
        risk_tolerance: str,
        mev_analysis: Dict[str, Any],
        profit_analysis: Dict[str, Any],
        speed_analysis: Dict[str, Any]
    ) -> str:
        """Generate reasoning for local consensus"""
        
        reasoning = f"Given user priority '{user_priority}' and '{risk_tolerance}' risk tolerance, "
        reasoning += f"option {best_id} provides optimal balance. "
        
        # Add priority-specific reasoning
        if user_priority == "mev_protection" and "mev" in best_data["sources"]:
            reasoning += "Prioritizes safety as requested, minimizing MEV exposure. "
        elif user_priority == "profit" and "profit" in best_data["sources"]:
            reasoning += "Maximizes net profit as requested, accounting for all costs. "
        elif user_priority == "speed" and "speed" in best_data["sources"]:
            reasoning += "Optimizes for fast execution as requested. "
        elif user_priority == "balanced":
            reasoning += "Balances all factors according to balanced priority. "
        
        # Add agent agreement context
        if len(best_data["sources"]) > 1:
            reasoning += f"Multiple agents ({', '.join(best_data['sources'])}) converged on this choice. "
        else:
            reasoning += f"Clear recommendation from {best_data['sources'][0]} specialist. "
        
        return reasoning
    
    def _identify_key_tradeoff(
        self,
        best_id: int,
        mev_analysis: Dict[str, Any],
        profit_analysis: Dict[str, Any], 
        speed_analysis: Dict[str, Any]
    ) -> str:
        """Identify the key tradeoff for the recommended option"""
        
        # Check if this is the MEV agent's choice
        if best_id == mev_analysis["recommended_id"]:
            return "Prioritizing safety over potential profit and speed"
        
        # Check if this is the profit agent's choice  
        elif best_id == profit_analysis["recommended_id"]:
            return "Maximizing profit with acceptable MEV risk and timing"
        
        # Check if this is the speed agent's choice
        elif best_id == speed_analysis["recommended_id"]:
            return "Optimizing execution speed while maintaining reasonable profit"
        
        else:
            return "Balancing MEV safety, profit optimization, and execution speed"
    
    def _find_alternatives(
        self,
        chosen_id: int,
        mev_analysis: Dict[str, Any],
        profit_analysis: Dict[str, Any],
        speed_analysis: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Find alternative options for different priorities"""
        
        alternatives = []
        
        # If chosen isn't the MEV agent's pick, offer it as alternative
        if mev_analysis["recommended_id"] != chosen_id:
            alternatives.append({
                "id": mev_analysis["recommended_id"],
                "reason": "Safest option if MEV protection is top priority",
                "tradeoff": "May sacrifice some profit for safety"
            })
        
        # If chosen isn't the Profit agent's pick, offer it
        if profit_analysis["recommended_id"] != chosen_id:
            alternatives.append({
                "id": profit_analysis["recommended_id"],
                "reason": "Highest profit if willing to take more risk", 
                "tradeoff": "Higher potential returns with elevated MEV exposure"
            })
        
        # If chosen isn't the Speed agent's pick, offer it
        if speed_analysis["recommended_id"] != chosen_id:
            alternatives.append({
                "id": speed_analysis["recommended_id"],
                "reason": "Fastest execution if time is critical",
                "tradeoff": "Executes quickly but may miss better pricing"
            })
        
        return alternatives[:2]  # Max 2 alternatives
