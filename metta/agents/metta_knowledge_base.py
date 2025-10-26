# MeTTa Knowledge Base for DeFi Trading Analysis
# Uses MeTTa syntax for representing trading knowledge and relationships

# Try to import real hyperon, fall back to mock
try:
    from hyperon import MeTTa, E, S, ValueAtom
    print("✅ Using real Hyperon/MeTTa (likely running in WSL)")
    USING_REAL_METTA = True
except ImportError:
    print("⚠️ Using mock MeTTa implementation (Windows fallback)")
    from mock_hyperon import MeTTa, E, S, ValueAtom
    USING_REAL_METTA = False
from typing import Dict, List, Any, Optional
import json

def initialize_defi_knowledge_graph(metta: MeTTa):
    """Initialize the MeTTa knowledge graph with DeFi trading relationships."""
    
    # MEV Risk Factors → Risk Levels
    metta.space().add_atom(E(S("mev_risk"), S("sandwich_bots_detected"), S("high")))
    metta.space().add_atom(E(S("mev_risk"), S("frontrunning_activity"), S("high")))
    metta.space().add_atom(E(S("mev_risk"), S("low_liquidity"), S("medium")))
    metta.space().add_atom(E(S("mev_risk"), S("high_slippage"), S("medium")))
    metta.space().add_atom(E(S("mev_risk"), S("immediate_execution"), S("high")))
    metta.space().add_atom(E(S("mev_risk"), S("delayed_execution"), S("low")))
    metta.space().add_atom(E(S("mev_risk"), S("private_mempool"), S("low")))
    
    # Gas Price Conditions → Optimization Strategies
    metta.space().add_atom(E(S("gas_optimization"), S("high_gas_price"), ValueAtom("delay_execution")))
    metta.space().add_atom(E(S("gas_optimization"), S("low_gas_price"), ValueAtom("execute_immediately")))
    metta.space().add_atom(E(S("gas_optimization"), S("volatile_gas"), ValueAtom("wait_for_stability")))
    metta.space().add_atom(E(S("gas_optimization"), S("congested_network"), ValueAtom("use_layer2")))
    
    # Profit Factors → Strategies
    metta.space().add_atom(E(S("profit_strategy"), S("high_volatility"), ValueAtom("fast_execution")))
    metta.space().add_atom(E(S("profit_strategy"), S("arbitrage_opportunity"), ValueAtom("immediate_execution")))
    metta.space().add_atom(E(S("profit_strategy"), S("low_slippage"), ValueAtom("large_trade_size")))
    metta.space().add_atom(E(S("profit_strategy"), S("high_slippage"), ValueAtom("split_orders")))
    metta.space().add_atom(E(S("profit_strategy"), S("trending_market"), ValueAtom("momentum_trading")))
    
    # Speed Requirements → Execution Methods
    metta.space().add_atom(E(S("speed_execution"), S("time_sensitive"), ValueAtom("immediate_execution")))
    metta.space().add_atom(E(S("speed_execution"), S("market_moving"), ValueAtom("priority_gas")))
    metta.space().add_atom(E(S("speed_execution"), S("arbitrage_closing"), ValueAtom("flashloan_execution")))
    metta.space().add_atom(E(S("speed_execution"), S("low_urgency"), ValueAtom("optimal_timing")))
    
    # Risk Tolerance → Decision Rules
    metta.space().add_atom(E(S("risk_tolerance"), S("conservative"), ValueAtom("minimize_mev_risk")))
    metta.space().add_atom(E(S("risk_tolerance"), S("balanced"), ValueAtom("optimize_risk_reward")))
    metta.space().add_atom(E(S("risk_tolerance"), S("aggressive"), ValueAtom("maximize_profit")))
    
    # Market Conditions → Recommendations
    metta.space().add_atom(E(S("market_condition"), S("bull_market"), ValueAtom("hold_longer")))
    metta.space().add_atom(E(S("market_condition"), S("bear_market"), ValueAtom("quick_execution")))
    metta.space().add_atom(E(S("market_condition"), S("sideways"), ValueAtom("range_trading")))
    metta.space().add_atom(E(S("market_condition"), S("high_volatility"), ValueAtom("reduce_position_size")))
    
    # Chain Characteristics → Optimization
    metta.space().add_atom(E(S("chain_optimization"), S("ethereum"), ValueAtom("high_security_high_cost")))
    metta.space().add_atom(E(S("chain_optimization"), S("base"), ValueAtom("low_cost_fast_execution")))
    metta.space().add_atom(E(S("chain_optimization"), S("arbitrum"), ValueAtom("moderate_cost_good_liquidity")))
    metta.space().add_atom(E(S("chain_optimization"), S("optimism"), ValueAtom("low_cost_growing_ecosystem")))
    metta.space().add_atom(E(S("chain_optimization"), S("polygon"), ValueAtom("very_low_cost_high_throughput")))
    
    # Trading Patterns → Success Factors
    metta.space().add_atom(E(S("success_factor"), S("timing"), ValueAtom("market_analysis_required")))
    metta.space().add_atom(E(S("success_factor"), S("liquidity"), ValueAtom("deep_pool_selection")))
    metta.space().add_atom(E(S("success_factor"), S("gas_efficiency"), ValueAtom("batch_transactions")))
    metta.space().add_atom(E(S("success_factor"), S("mev_protection"), ValueAtom("private_mempool_usage")))
    
    # Agent Consensus Rules
    metta.space().add_atom(E(S("consensus_rule"), S("mev_agent_high_confidence"), ValueAtom("prioritize_safety")))
    metta.space().add_atom(E(S("consensus_rule"), S("profit_agent_high_confidence"), ValueAtom("prioritize_returns")))
    metta.space().add_atom(E(S("consensus_rule"), S("speed_agent_high_confidence"), ValueAtom("prioritize_execution")))
    metta.space().add_atom(E(S("consensus_rule"), S("conflicting_recommendations"), ValueAtom("use_user_preference")))
    
    # Tool Integration Rules
    metta.space().add_atom(E(S("tool_usage"), S("price_volatility_high"), ValueAtom("fetch_real_time_prices")))
    metta.space().add_atom(E(S("tool_usage"), S("mempool_congested"), ValueAtom("analyze_mempool_data")))
    metta.space().add_atom(E(S("tool_usage"), S("user_has_pending_tx"), ValueAtom("check_user_transactions")))
    metta.space().add_atom(E(S("tool_usage"), S("network_issues"), ValueAtom("check_net_status")))

class DeFiMeTTaRAG:
    """RAG system for DeFi trading knowledge using MeTTa reasoning"""
    
    def __init__(self, metta_instance: MeTTa):
        self.metta = metta_instance

    def query_mev_risk_factors(self, condition: str) -> List[str]:
        """Find MEV risk levels for given conditions."""
        condition = condition.strip('"')
        query_str = f'!(match &self (mev_risk {condition} $risk) $risk)'
        results = self.metta.run(query_str)
        return list(set(str(r[0]) for r in results if r and len(r) > 0)) if results else []

    def get_gas_optimization_strategy(self, gas_condition: str) -> List[str]:
        """Find gas optimization strategies for given conditions."""
        gas_condition = gas_condition.strip('"')
        query_str = f'!(match &self (gas_optimization {gas_condition} $strategy) $strategy)'
        results = self.metta.run(query_str)
        return [r[0].get_object().value for r in results if r and len(r) > 0] if results else []

    def get_profit_strategy(self, market_factor: str) -> List[str]:
        """Find profit strategies for given market factors."""
        market_factor = market_factor.strip('"')
        query_str = f'!(match &self (profit_strategy {market_factor} $strategy) $strategy)'
        results = self.metta.run(query_str)
        return [r[0].get_object().value for r in results if r and len(r) > 0] if results else []

    def get_speed_execution_method(self, urgency: str) -> List[str]:
        """Find execution methods for given urgency levels."""
        urgency = urgency.strip('"')
        query_str = f'!(match &self (speed_execution {urgency} $method) $method)'
        results = self.metta.run(query_str)
        return [r[0].get_object().value for r in results if r and len(r) > 0] if results else []

    def get_risk_tolerance_strategy(self, tolerance: str) -> List[str]:
        """Find strategies based on risk tolerance."""
        tolerance = tolerance.strip('"')
        query_str = f'!(match &self (risk_tolerance {tolerance} $strategy) $strategy)'
        results = self.metta.run(query_str)
        return [r[0].get_object().value for r in results if r and len(r) > 0] if results else []

    def get_consensus_rule(self, agent_state: str) -> List[str]:
        """Find consensus rules for agent states."""
        agent_state = agent_state.strip('"')
        query_str = f'!(match &self (consensus_rule {agent_state} $rule) $rule)'
        results = self.metta.run(query_str)
        return [r[0].get_object().value for r in results if r and len(r) > 0] if results else []

    def get_tool_usage_recommendation(self, condition: str) -> List[str]:
        """Find tool usage recommendations for given conditions."""
        condition = condition.strip('"')
        query_str = f'!(match &self (tool_usage {condition} $tool) $tool)'
        results = self.metta.run(query_str)
        return [r[0].get_object().value for r in results if r and len(r) > 0] if results else []

    def add_dynamic_knowledge(self, relation_type: str, subject: str, object_value: str):
        """Add new knowledge dynamically based on market observations."""
        if isinstance(object_value, str):
            object_value = ValueAtom(object_value)
        self.metta.space().add_atom(E(S(relation_type), S(subject), object_value))
        return f"Added {relation_type}: {subject} → {object_value}"

    def query_complex_scenario(self, conditions: Dict[str, Any]) -> Dict[str, List[str]]:
        """Query multiple conditions for complex scenario analysis."""
        results = {}
        
        # Query MEV risks
        if 'mev_factors' in conditions:
            results['mev_risks'] = []
            for factor in conditions['mev_factors']:
                risks = self.query_mev_risk_factors(factor)
                results['mev_risks'].extend(risks)
        
        # Query profit strategies
        if 'profit_factors' in conditions:
            results['profit_strategies'] = []
            for factor in conditions['profit_factors']:
                strategies = self.get_profit_strategy(factor)
                results['profit_strategies'].extend(strategies)
        
        # Query speed requirements
        if 'speed_factors' in conditions:
            results['speed_methods'] = []
            for factor in conditions['speed_factors']:
                methods = self.get_speed_execution_method(factor)
                results['speed_methods'].extend(methods)
        
        # Query gas optimization
        if 'gas_conditions' in conditions:
            results['gas_strategies'] = []
            for condition in conditions['gas_conditions']:
                strategies = self.get_gas_optimization_strategy(condition)
                results['gas_strategies'].extend(strategies)
        
        # Query consensus rules
        if 'agent_states' in conditions:
            results['consensus_rules'] = []
            for state in conditions['agent_states']:
                rules = self.get_consensus_rule(state)
                results['consensus_rules'].extend(rules)
        
        return results

    def generate_recommendation(self, scenario_results: Dict[str, List[str]], user_priority: str) -> Dict[str, Any]:
        """Generate final recommendation based on MeTTa query results."""
        
        # Analyze conflicting recommendations
        conflicts = []
        if 'mev_risks' in scenario_results and 'high' in scenario_results['mev_risks']:
            if 'profit_strategies' in scenario_results and 'immediate_execution' in scenario_results['profit_strategies']:
                conflicts.append("MEV risk vs profit optimization conflict")
        
        # Priority-based decision making
        if user_priority == "safety":
            primary_factor = "mev_protection"
        elif user_priority == "profit":
            primary_factor = "profit_maximization"
        elif user_priority == "speed":
            primary_factor = "fast_execution"
        else:
            primary_factor = "balanced_approach"
        
        return {
            "primary_recommendation": primary_factor,
            "supporting_evidence": scenario_results,
            "conflicts_detected": conflicts,
            "confidence_score": self._calculate_confidence(scenario_results, conflicts)
        }

    def _calculate_confidence(self, results: Dict[str, List[str]], conflicts: List[str]) -> float:
        """Calculate confidence score based on result consistency."""
        total_recommendations = sum(len(recommendations) for recommendations in results.values())
        conflict_penalty = len(conflicts) * 0.1
        
        if total_recommendations == 0:
            return 0.0
        
        base_confidence = min(1.0, total_recommendations / 10.0)  # Normalize to 0-1
        final_confidence = max(0.0, base_confidence - conflict_penalty)
        
        return round(final_confidence * 100, 1)  # Convert to percentage
