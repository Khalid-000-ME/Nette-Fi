import os
import json
import requests
from typing import Dict, Any, List
from uagents import Agent, Context, Model
import asyncio
from datetime import datetime

class ConsensusAgent:
    """
    MeTTa Consensus Agent - Advanced reasoning system for multi-agent consensus
    Uses ASI (Fetch.ai) uAgent framework with MeTTa reasoning and ASI:One API
    Integrates with Risk, Market Intelligence, Liquidity, Gas, and Arbitrage agents
    """
    
    def __init__(self, agent_address: str = "consensus_agent"):
        self.agent = Agent(
            name="metta_consensus_agent",
            seed="consensus_seed_11111",
            port=8006,
            endpoint=["http://localhost:8006/submit"]
        )
        self.name = "MeTTa Consensus Agent"
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
    
    async def enhanced_consensus_decision(
        self,
        simulation_data: Dict[str, Any],
        user_preferences: Dict[str, Any],
        agent_analyses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Enhanced consensus decision integrating all 5 specialized agents
        
        Args:
            simulation_data: Raw simulation results from chains
            user_preferences: User priority, risk tolerance, etc.
            agent_analyses: Analysis from all 5 agents
            
        Returns:
            Final consensus decision with MeTTa reasoning
        """
        
        # Extract individual agent recommendations
        risk_analysis = agent_analyses.get("risk_agent", {})
        market_analysis = agent_analyses.get("market_intelligence_agent", {})
        liquidity_analysis = agent_analyses.get("liquidity_agent", {})
        gas_analysis = agent_analyses.get("gas_agent", {})
        arbitrage_analysis = agent_analyses.get("arbitrage_agent", {})
        
        # Apply MeTTa reasoning framework
        metta_decision = await self._apply_metta_reasoning(
            simulation_data, user_preferences, {
                "risk": risk_analysis,
                "market": market_analysis,
                "liquidity": liquidity_analysis,
                "gas": gas_analysis,
                "arbitrage": arbitrage_analysis
            }
        )
        
        return metta_decision
    
    async def _apply_metta_reasoning(
        self,
        simulation_data: Dict[str, Any],
        user_preferences: Dict[str, Any],
        agent_analyses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Apply MeTTa-style logical reasoning to reach consensus"""
        
        # Step 1: Extract key facts from each agent
        facts = self._extract_agent_facts(agent_analyses, simulation_data)
        
        # Step 2: Apply logical rules based on user preferences
        rules = self._generate_decision_rules(user_preferences)
        
        # Step 3: Reason through the decision space
        reasoning_chain = self._build_reasoning_chain(facts, rules)
        
        # Step 4: Calculate consensus scores for each option
        consensus_scores = self._calculate_consensus_scores(
            simulation_data, facts, rules, reasoning_chain
        )
        
        # Step 5: Select optimal decision
        optimal_decision = self._select_optimal_decision(
            consensus_scores, reasoning_chain, user_preferences
        )
        
        return optimal_decision
    
    def _extract_agent_facts(
        self, agent_analyses: Dict[str, Any], simulation_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Extract key facts from each agent's analysis"""
        
        facts = {
            "risk_factors": [],
            "market_conditions": {},
            "liquidity_status": {},
            "gas_conditions": {},
            "arbitrage_opportunities": [],
            "simulation_results": simulation_data.get("scenarios", [])
        }
        
        # Risk agent facts
        risk_data = agent_analyses.get("risk", {})
        if risk_data:
            facts["risk_factors"] = risk_data.get("risk_assessment", {}).get("high_risk_factors", [])
            facts["overall_risk_level"] = risk_data.get("risk_assessment", {}).get("overall_risk", "medium")
        
        # Market intelligence facts
        market_data = agent_analyses.get("market", {})
        if market_data:
            facts["market_conditions"] = {
                "sentiment": market_data.get("market_sentiment", {}).get("overall_sentiment", "neutral"),
                "volatility": market_data.get("volatility_analysis", {}).get("current_volatility", "medium"),
                "trend": market_data.get("trend_analysis", {}).get("short_term_trend", "stable")
            }
        
        # Liquidity facts
        liquidity_data = agent_analyses.get("liquidity", {})
        if liquidity_data:
            facts["liquidity_status"] = {
                "quality": liquidity_data.get("liquidity_analysis", {}).get("liquidity_quality", {}).get("quality", "fair"),
                "fragmentation": liquidity_data.get("liquidity_analysis", {}).get("fragmentation_score", 0.5),
                "optimal_routing": liquidity_data.get("optimal_routing", {}).get("cross_chain_required", False)
            }
        
        # Gas optimization facts
        gas_data = agent_analyses.get("gas", {})
        if gas_data:
            facts["gas_conditions"] = {
                "efficiency_ranking": gas_data.get("gas_analysis", {}).get("cost_efficiency_ranking", []),
                "optimal_timing": gas_data.get("timing_recommendations", {}).get("recommendation", "execute_when_convenient"),
                "potential_savings": gas_data.get("optimization_strategy", {}).get("estimated_savings", {}).get("total_potential_savings", 0)
            }
        
        # Arbitrage facts
        arbitrage_data = agent_analyses.get("arbitrage", {})
        if arbitrage_data:
            facts["arbitrage_opportunities"] = arbitrage_data.get("opportunities", [])
            facts["arbitrage_potential"] = arbitrage_data.get("market_analysis", {}).get("arbitrage_potential", {}).get("potential", "low")
        
        return facts
    
    def _generate_decision_rules(self, user_preferences: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate decision rules based on user preferences"""
        
        priority = user_preferences.get("priority", "balanced")
        risk_tolerance = user_preferences.get("risk_tolerance", "balanced")
        
        rules = []
        
        # Priority-based rules
        if priority == "safety":
            rules.extend([
                {"condition": "high_risk_factors", "weight": -0.8, "description": "Heavily penalize high-risk options"},
                {"condition": "low_mev_risk", "weight": 0.6, "description": "Favor low MEV risk scenarios"},
                {"condition": "established_chains", "weight": 0.4, "description": "Prefer established chains"}
            ])
        elif priority == "profit":
            rules.extend([
                {"condition": "high_profit_margin", "weight": 0.7, "description": "Favor high profit scenarios"},
                {"condition": "arbitrage_opportunities", "weight": 0.5, "description": "Leverage arbitrage when available"},
                {"condition": "optimal_liquidity", "weight": 0.3, "description": "Use optimal liquidity routing"}
            ])
        elif priority == "speed":
            rules.extend([
                {"condition": "fast_execution", "weight": 0.8, "description": "Prioritize fast execution chains"},
                {"condition": "low_gas_cost", "weight": 0.4, "description": "Use low-cost chains for speed"},
                {"condition": "simple_routing", "weight": 0.3, "description": "Avoid complex routing"}
            ])
        else:  # balanced
            rules.extend([
                {"condition": "balanced_risk_reward", "weight": 0.5, "description": "Balance risk and reward"},
                {"condition": "reasonable_speed", "weight": 0.3, "description": "Maintain reasonable execution speed"},
                {"condition": "cost_efficiency", "weight": 0.4, "description": "Optimize for cost efficiency"}
            ])
        
        # Risk tolerance rules
        if risk_tolerance == "conservative":
            rules.append({"condition": "conservative_approach", "weight": 0.3, "description": "Apply conservative bias"})
        elif risk_tolerance == "aggressive":
            rules.append({"condition": "aggressive_opportunities", "weight": 0.3, "description": "Pursue aggressive opportunities"})
        
        return rules
    
    def _build_reasoning_chain(
        self, facts: Dict[str, Any], rules: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Build logical reasoning chain"""
        
        reasoning_steps = []
        
        # Step 1: Assess market conditions
        market_conditions = facts.get("market_conditions", {})
        reasoning_steps.append({
            "step": "market_assessment",
            "conclusion": f"Market sentiment is {market_conditions.get('sentiment', 'neutral')} with {market_conditions.get('volatility', 'medium')} volatility",
            "impact": "Affects risk assessment and timing decisions"
        })
        
        # Step 2: Evaluate liquidity landscape
        liquidity_status = facts.get("liquidity_status", {})
        reasoning_steps.append({
            "step": "liquidity_evaluation",
            "conclusion": f"Liquidity quality is {liquidity_status.get('quality', 'fair')}, cross-chain routing {'required' if liquidity_status.get('optimal_routing') else 'not required'}",
            "impact": "Determines execution complexity and slippage risk"
        })
        
        # Step 3: Analyze gas optimization
        gas_conditions = facts.get("gas_conditions", {})
        reasoning_steps.append({
            "step": "gas_optimization",
            "conclusion": f"Gas optimization suggests {gas_conditions.get('optimal_timing', 'flexible timing')} with {gas_conditions.get('potential_savings', 0)*100:.1f}% potential savings",
            "impact": "Influences chain selection and timing strategy"
        })
        
        # Step 4: Consider arbitrage opportunities
        arbitrage_potential = facts.get("arbitrage_potential", "low")
        reasoning_steps.append({
            "step": "arbitrage_analysis",
            "conclusion": f"Arbitrage potential is {arbitrage_potential}",
            "impact": "May provide additional profit opportunities or complexity"
        })
        
        # Step 5: Apply risk assessment
        risk_level = facts.get("overall_risk_level", "medium")
        reasoning_steps.append({
            "step": "risk_synthesis",
            "conclusion": f"Overall risk level assessed as {risk_level}",
            "impact": "Final risk adjustment to recommendations"
        })
        
        return reasoning_steps
    
    def _calculate_consensus_scores(
        self,
        simulation_data: Dict[str, Any],
        facts: Dict[str, Any],
        rules: List[Dict[str, Any]],
        reasoning_chain: List[Dict[str, Any]]
    ) -> Dict[int, Dict[str, Any]]:
        """Calculate consensus scores for each simulation scenario"""
        
        scenarios = simulation_data.get("scenarios", [])
        consensus_scores = {}
        
        for i, scenario in enumerate(scenarios):
            score_components = {
                "base_score": scenario.get("profit_usd", 0) / 1000,  # Normalize profit
                "risk_adjustment": 0,
                "liquidity_adjustment": 0,
                "gas_adjustment": 0,
                "arbitrage_bonus": 0,
                "rule_adjustments": 0
            }
            
            # Apply risk adjustment
            mev_risk = scenario.get("mev_risk", 0.5)
            score_components["risk_adjustment"] = -mev_risk * 20  # Penalize high MEV risk
            
            # Apply liquidity adjustment
            chain = scenario.get("chain", "")
            liquidity_quality = facts.get("liquidity_status", {}).get("quality", "fair")
            liquidity_bonus = {"excellent": 10, "good": 5, "fair": 0, "poor": -10}.get(liquidity_quality, 0)
            score_components["liquidity_adjustment"] = liquidity_bonus
            
            # Apply gas adjustment
            gas_efficiency = self._get_chain_gas_efficiency(chain, facts.get("gas_conditions", {}))
            score_components["gas_adjustment"] = gas_efficiency * 5
            
            # Apply arbitrage bonus
            if facts.get("arbitrage_potential") == "high":
                score_components["arbitrage_bonus"] = 15
            elif facts.get("arbitrage_potential") == "medium":
                score_components["arbitrage_bonus"] = 8
            
            # Apply rule-based adjustments
            for rule in rules:
                rule_score = self._evaluate_rule_for_scenario(rule, scenario, facts)
                score_components["rule_adjustments"] += rule_score * rule["weight"]
            
            # Calculate final score
            final_score = sum(score_components.values())
            
            consensus_scores[i] = {
                "scenario_id": i,
                "final_score": final_score,
                "score_components": score_components,
                "scenario_data": scenario
            }
        
        return consensus_scores
    
    def _get_chain_gas_efficiency(self, chain: str, gas_conditions: Dict[str, Any]) -> float:
        """Get gas efficiency score for a chain"""
        
        efficiency_ranking = gas_conditions.get("efficiency_ranking", [])
        
        for i, chain_data in enumerate(efficiency_ranking):
            if chain_data.get("chain", "").lower() == chain.lower():
                # Higher rank = better efficiency (0-1 scale)
                return 1.0 - (i / len(efficiency_ranking))
        
        return 0.5  # Default neutral score
    
    def _evaluate_rule_for_scenario(
        self, rule: Dict[str, Any], scenario: Dict[str, Any], facts: Dict[str, Any]
    ) -> float:
        """Evaluate how well a scenario matches a decision rule"""
        
        condition = rule["condition"]
        
        if condition == "high_risk_factors":
            return 1.0 if scenario.get("mev_risk", 0) > 0.7 else 0.0
        elif condition == "low_mev_risk":
            return 1.0 if scenario.get("mev_risk", 0) < 0.3 else 0.0
        elif condition == "high_profit_margin":
            return 1.0 if scenario.get("profit_usd", 0) > 1000 else 0.0
        elif condition == "fast_execution":
            return 1.0 if scenario.get("execution_time", 60) < 30 else 0.0
        elif condition == "low_gas_cost":
            return 1.0 if scenario.get("gas_cost", 50) < 20 else 0.0
        elif condition == "balanced_risk_reward":
            risk = scenario.get("mev_risk", 0.5)
            profit = scenario.get("profit_usd", 0)
            return 1.0 if 0.2 < risk < 0.6 and profit > 500 else 0.0
        
        return 0.0  # Default no match
    
    def _select_optimal_decision(
        self,
        consensus_scores: Dict[int, Dict[str, Any]],
        reasoning_chain: List[Dict[str, Any]],
        user_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Select the optimal decision based on consensus scores"""
        
        if not consensus_scores:
            return {"error": "No valid scenarios to evaluate"}
        
        # Find highest scoring scenario
        best_scenario_id = max(consensus_scores.keys(), key=lambda k: consensus_scores[k]["final_score"])
        best_scenario = consensus_scores[best_scenario_id]
        
        # Calculate confidence based on score distribution
        scores = [data["final_score"] for data in consensus_scores.values()]
        max_score = max(scores)
        score_spread = max_score - min(scores) if len(scores) > 1 else max_score
        
        confidence = min(95, max(70, 70 + (score_spread * 2)))
        
        # Generate explanation
        explanation = self._generate_consensus_explanation(
            best_scenario, reasoning_chain, user_preferences
        )
        
        return {
            "recommended_scenario_id": best_scenario_id,
            "confidence": int(confidence),
            "final_score": best_scenario["final_score"],
            "reasoning": explanation,
            "consensus_method": "enhanced_metta_reasoning",
            "score_breakdown": best_scenario["score_components"],
            "alternative_scenarios": self._get_alternative_scenarios(consensus_scores, best_scenario_id),
            "agent_consensus": self._summarize_agent_consensus(reasoning_chain),
            "execution_recommendation": self._generate_execution_recommendation(best_scenario["scenario_data"])
        }
    
    def _generate_consensus_explanation(
        self,
        best_scenario: Dict[str, Any],
        reasoning_chain: List[Dict[str, Any]],
        user_preferences: Dict[str, Any]
    ) -> str:
        """Generate human-readable explanation of the consensus decision"""
        
        scenario_data = best_scenario["scenario_data"]
        score_components = best_scenario["score_components"]
        
        explanation = f"Based on comprehensive multi-agent analysis and MeTTa reasoning, "
        explanation += f"scenario {best_scenario['scenario_id']} on {scenario_data.get('chain', 'unknown')} chain "
        explanation += f"provides optimal balance for your '{user_preferences.get('priority', 'balanced')}' priority. "
        
        # Add key reasoning points
        if score_components.get("risk_adjustment", 0) > -10:
            explanation += "Risk assessment is favorable. "
        elif score_components.get("risk_adjustment", 0) < -15:
            explanation += "Higher risk but justified by other factors. "
        
        if score_components.get("arbitrage_bonus", 0) > 0:
            explanation += "Arbitrage opportunities detected. "
        
        if score_components.get("gas_adjustment", 0) > 3:
            explanation += "Gas optimization is highly favorable. "
        
        explanation += f"Expected profit: ${scenario_data.get('profit_usd', 0):.2f}, "
        explanation += f"MEV risk: {scenario_data.get('mev_risk', 0)*100:.1f}%."
        
        return explanation
    
    def _get_alternative_scenarios(
        self, consensus_scores: Dict[int, Dict[str, Any]], best_id: int
    ) -> List[Dict[str, Any]]:
        """Get alternative scenario recommendations"""
        
        # Sort by score, exclude the best one
        sorted_scenarios = sorted(
            [(k, v) for k, v in consensus_scores.items() if k != best_id],
            key=lambda x: x[1]["final_score"],
            reverse=True
        )
        
        alternatives = []
        for scenario_id, scenario_data in sorted_scenarios[:2]:  # Top 2 alternatives
            alternatives.append({
                "scenario_id": scenario_id,
                "score": scenario_data["final_score"],
                "chain": scenario_data["scenario_data"].get("chain", "unknown"),
                "profit_usd": scenario_data["scenario_data"].get("profit_usd", 0),
                "mev_risk": scenario_data["scenario_data"].get("mev_risk", 0),
                "reason": "Alternative with different risk/reward profile"
            })
        
        return alternatives
    
    def _summarize_agent_consensus(self, reasoning_chain: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Summarize consensus across all agents"""
        
        return {
            "market_intelligence": "Analyzed market conditions and sentiment",
            "risk_assessment": "Evaluated comprehensive risk factors",
            "liquidity_optimization": "Optimized routing and execution strategy",
            "gas_optimization": "Identified cost-efficient execution timing",
            "arbitrage_detection": "Scanned for additional profit opportunities",
            "consensus_strength": "Strong" if len(reasoning_chain) >= 4 else "Moderate"
        }
    
    def _generate_execution_recommendation(self, scenario_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate specific execution recommendations"""
        
        return {
            "execute_immediately": scenario_data.get("mev_risk", 0) < 0.3,
            "monitor_conditions": scenario_data.get("mev_risk", 0) > 0.6,
            "suggested_slippage": min(5.0, max(0.5, scenario_data.get("mev_risk", 0) * 10)),
            "gas_strategy": "fast" if scenario_data.get("execution_time", 60) < 30 else "standard",
            "additional_checks": ["Monitor mempool", "Watch for MEV bots"] if scenario_data.get("mev_risk", 0) > 0.5 else []
        }
    
    def get_agent(self):
        """Return the uAgent instance"""
        return self.agent
