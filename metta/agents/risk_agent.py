"""
Risk Assessment Agent - Specialized in comprehensive risk analysis
Uses ASI (Fetch.ai) uAgent framework for autonomous decision making
"""

from uagents import Agent, Context, Model
from typing import Dict, List, Any, Optional
import json
import numpy as np
from dataclasses import dataclass

@dataclass
class RiskMetrics:
    volatility_risk: float
    liquidity_risk: float
    counterparty_risk: float
    smart_contract_risk: float
    market_impact_risk: float
    temporal_risk: float
    overall_risk_score: float

class RiskMessage(Model):
    simulation_data: Dict[str, Any]
    market_conditions: Dict[str, Any]
    user_profile: Dict[str, Any]

class RiskResponse(Model):
    risk_assessment: Dict[str, Any]
    recommended_action: str
    confidence: float
    warnings: List[str]

class RiskAssessmentAgent:
    def __init__(self, agent_address: str = "risk_agent"):
        self.agent = Agent(
            name="risk_assessment_agent",
            seed="risk_seed_12345",
            port=8001,
            endpoint=["http://localhost:8001/submit"]
        )
        
        # Risk thresholds
        self.risk_thresholds = {
            "low": 0.3,
            "medium": 0.6,
            "high": 0.8,
            "critical": 0.95
        }
        
        # Market volatility indicators
        self.volatility_indicators = {
            "vix_equivalent": 0.0,
            "price_deviation": 0.0,
            "volume_spike": 0.0
        }
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        @self.agent.on_message(model=RiskMessage)
        async def handle_risk_analysis(ctx: Context, sender: str, msg: RiskMessage):
            """Handle incoming risk analysis requests"""
            try:
                risk_assessment = await self._analyze_comprehensive_risk(
                    msg.simulation_data,
                    msg.market_conditions,
                    msg.user_profile
                )
                
                response = RiskResponse(
                    risk_assessment=risk_assessment,
                    recommended_action=self._determine_action(risk_assessment),
                    confidence=self._calculate_confidence(risk_assessment),
                    warnings=self._generate_warnings(risk_assessment)
                )
                
                await ctx.send(sender, response)
                
            except Exception as e:
                ctx.logger.error(f"Risk analysis failed: {str(e)}")
    
    async def _analyze_comprehensive_risk(
        self,
        simulation_data: Dict[str, Any],
        market_conditions: Dict[str, Any],
        user_profile: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Comprehensive risk analysis using multiple risk factors"""
        
        # Extract simulation metrics
        simulations = simulation_data.get('simulations', [])
        if not simulations:
            return {"error": "No simulation data provided"}
        
        # Calculate individual risk components
        volatility_risk = self._calculate_volatility_risk(simulations, market_conditions)
        liquidity_risk = self._calculate_liquidity_risk(simulations, market_conditions)
        counterparty_risk = self._calculate_counterparty_risk(simulations)
        smart_contract_risk = self._calculate_smart_contract_risk(simulations)
        market_impact_risk = self._calculate_market_impact_risk(simulations)
        temporal_risk = self._calculate_temporal_risk(simulations, market_conditions)
        
        # Aggregate risk metrics
        risk_metrics = RiskMetrics(
            volatility_risk=volatility_risk,
            liquidity_risk=liquidity_risk,
            counterparty_risk=counterparty_risk,
            smart_contract_risk=smart_contract_risk,
            market_impact_risk=market_impact_risk,
            temporal_risk=temporal_risk,
            overall_risk_score=self._calculate_overall_risk(
                volatility_risk, liquidity_risk, counterparty_risk,
                smart_contract_risk, market_impact_risk, temporal_risk
            )
        )
        
        # Risk-adjusted recommendations
        risk_adjusted_scenarios = self._rank_scenarios_by_risk(simulations, risk_metrics)
        
        return {
            "risk_metrics": {
                "volatility_risk": risk_metrics.volatility_risk,
                "liquidity_risk": risk_metrics.liquidity_risk,
                "counterparty_risk": risk_metrics.counterparty_risk,
                "smart_contract_risk": risk_metrics.smart_contract_risk,
                "market_impact_risk": risk_metrics.market_impact_risk,
                "temporal_risk": risk_metrics.temporal_risk,
                "overall_risk_score": risk_metrics.overall_risk_score
            },
            "risk_level": self._categorize_risk_level(risk_metrics.overall_risk_score),
            "top_scenarios": risk_adjusted_scenarios[:3],
            "risk_factors": self._identify_primary_risk_factors(risk_metrics),
            "mitigation_strategies": self._suggest_mitigation_strategies(risk_metrics),
            "user_risk_alignment": self._assess_user_risk_alignment(risk_metrics, user_profile)
        }
    
    def _calculate_volatility_risk(self, simulations: List[Dict], market_conditions: Dict) -> float:
        """Calculate volatility-based risk"""
        if not simulations:
            return 0.8  # High risk if no data
        
        # Price variance analysis
        outputs = [float(sim.get('estimated_output_usd', 0)) for sim in simulations]
        if len(outputs) < 2:
            return 0.6
        
        price_variance = np.var(outputs) / (np.mean(outputs) ** 2) if np.mean(outputs) > 0 else 1.0
        
        # Market volatility factor
        market_vol = market_conditions.get('volatility_index', 0.5)
        
        # Combined volatility risk
        volatility_risk = min(0.4 * price_variance + 0.6 * market_vol, 1.0)
        return volatility_risk
    
    def _calculate_liquidity_risk(self, simulations: List[Dict], market_conditions: Dict) -> float:
        """Calculate liquidity-based risk"""
        # Analyze price impact across simulations
        price_impacts = []
        for sim in simulations:
            price_impact = float(sim.get('price_impact_percent', '0').replace('%', ''))
            price_impacts.append(price_impact)
        
        if not price_impacts:
            return 0.7
        
        avg_price_impact = np.mean(price_impacts)
        max_price_impact = max(price_impacts)
        
        # Market depth analysis
        market_depth = market_conditions.get('market_depth_score', 0.5)
        
        # Liquidity risk calculation
        liquidity_risk = min(
            0.3 * (avg_price_impact / 10.0) +  # Normalize to 0-1
            0.4 * (max_price_impact / 20.0) +
            0.3 * (1.0 - market_depth),
            1.0
        )
        
        return liquidity_risk
    
    def _calculate_counterparty_risk(self, simulations: List[Dict]) -> float:
        """Calculate counterparty and execution risk"""
        # Analyze execution success probabilities
        success_probs = []
        for sim in simulations:
            success_prob = sim.get('execution_success_probability', 0.5)
            success_probs.append(success_prob)
        
        if not success_probs:
            return 0.8
        
        avg_success = np.mean(success_probs)
        min_success = min(success_probs)
        
        # Counterparty risk is inverse of execution reliability
        counterparty_risk = 1.0 - (0.7 * avg_success + 0.3 * min_success)
        
        return max(0.0, min(counterparty_risk, 1.0))
    
    def _calculate_smart_contract_risk(self, simulations: List[Dict]) -> float:
        """Calculate smart contract and protocol risk"""
        # Analyze MEV risk as proxy for smart contract complexity
        mev_risks = []
        for sim in simulations:
            mev_risk = sim.get('mev_risk_score', 50) / 100.0  # Normalize to 0-1
            mev_risks.append(mev_risk)
        
        if not mev_risks:
            return 0.6
        
        avg_mev_risk = np.mean(mev_risks)
        max_mev_risk = max(mev_risks)
        
        # Smart contract risk correlates with MEV exposure
        smart_contract_risk = 0.6 * avg_mev_risk + 0.4 * max_mev_risk
        
        return smart_contract_risk
    
    def _calculate_market_impact_risk(self, simulations: List[Dict]) -> float:
        """Calculate market impact and slippage risk"""
        # Analyze gas costs and network congestion
        gas_costs = []
        for sim in simulations:
            gas_cost = float(sim.get('gas_cost_usd', '0'))
            gas_costs.append(gas_cost)
        
        if not gas_costs:
            return 0.5
        
        gas_variance = np.var(gas_costs) / (np.mean(gas_costs) ** 2) if np.mean(gas_costs) > 0 else 0.5
        
        # Market impact risk based on gas volatility
        market_impact_risk = min(gas_variance * 2.0, 1.0)
        
        return market_impact_risk
    
    def _calculate_temporal_risk(self, simulations: List[Dict], market_conditions: Dict) -> float:
        """Calculate timing and temporal risk"""
        # Analyze block offset risks
        block_offsets = []
        for sim in simulations:
            block_offset = sim.get('block_offset', 0)
            block_offsets.append(block_offset)
        
        if not block_offsets:
            return 0.4
        
        # Higher block offsets generally mean higher temporal risk
        max_offset = max(block_offsets) if block_offsets else 0
        avg_offset = np.mean(block_offsets) if block_offsets else 0
        
        # Market timing factor
        market_timing = market_conditions.get('market_timing_risk', 0.3)
        
        temporal_risk = min(
            0.4 * (max_offset / 10.0) +  # Normalize assuming max offset ~10
            0.3 * (avg_offset / 5.0) +
            0.3 * market_timing,
            1.0
        )
        
        return temporal_risk
    
    def _calculate_overall_risk(self, *risk_components) -> float:
        """Calculate weighted overall risk score"""
        weights = [0.25, 0.20, 0.15, 0.15, 0.15, 0.10]  # Volatility gets highest weight
        
        if len(risk_components) != len(weights):
            return np.mean(risk_components)
        
        overall_risk = sum(w * r for w, r in zip(weights, risk_components))
        return min(max(overall_risk, 0.0), 1.0)
    
    def _rank_scenarios_by_risk(self, simulations: List[Dict], risk_metrics: RiskMetrics) -> List[Dict]:
        """Rank scenarios by risk-adjusted returns"""
        risk_adjusted_scenarios = []
        
        for sim in simulations:
            # Calculate risk-adjusted score
            output_usd = float(sim.get('estimated_output_usd', 0))
            mev_risk = sim.get('mev_risk_score', 50) / 100.0
            success_prob = sim.get('execution_success_probability', 0.5)
            
            # Risk-adjusted return calculation
            risk_penalty = 1.0 - (0.4 * mev_risk + 0.3 * (1.0 - success_prob) + 0.3 * risk_metrics.overall_risk_score)
            risk_adjusted_return = output_usd * risk_penalty
            
            scenario_with_risk = sim.copy()
            scenario_with_risk['risk_adjusted_return'] = risk_adjusted_return
            scenario_with_risk['risk_penalty'] = 1.0 - risk_penalty
            
            risk_adjusted_scenarios.append(scenario_with_risk)
        
        # Sort by risk-adjusted return (descending)
        return sorted(risk_adjusted_scenarios, key=lambda x: x['risk_adjusted_return'], reverse=True)
    
    def _categorize_risk_level(self, overall_risk: float) -> str:
        """Categorize overall risk level"""
        if overall_risk <= self.risk_thresholds["low"]:
            return "LOW"
        elif overall_risk <= self.risk_thresholds["medium"]:
            return "MEDIUM"
        elif overall_risk <= self.risk_thresholds["high"]:
            return "HIGH"
        else:
            return "CRITICAL"
    
    def _identify_primary_risk_factors(self, risk_metrics: RiskMetrics) -> List[str]:
        """Identify the primary risk factors"""
        risk_factors = []
        
        if risk_metrics.volatility_risk > 0.6:
            risk_factors.append("High market volatility detected")
        if risk_metrics.liquidity_risk > 0.6:
            risk_factors.append("Liquidity constraints identified")
        if risk_metrics.counterparty_risk > 0.6:
            risk_factors.append("Execution reliability concerns")
        if risk_metrics.smart_contract_risk > 0.6:
            risk_factors.append("Smart contract complexity risks")
        if risk_metrics.market_impact_risk > 0.6:
            risk_factors.append("Significant market impact expected")
        if risk_metrics.temporal_risk > 0.6:
            risk_factors.append("Timing-sensitive execution required")
        
        return risk_factors
    
    def _suggest_mitigation_strategies(self, risk_metrics: RiskMetrics) -> List[str]:
        """Suggest risk mitigation strategies"""
        strategies = []
        
        if risk_metrics.volatility_risk > 0.6:
            strategies.append("Consider smaller position sizes or dollar-cost averaging")
        if risk_metrics.liquidity_risk > 0.6:
            strategies.append("Split large orders across multiple venues")
        if risk_metrics.counterparty_risk > 0.6:
            strategies.append("Use reputable DEXs with high TVL")
        if risk_metrics.smart_contract_risk > 0.6:
            strategies.append("Verify contract audits and use established protocols")
        if risk_metrics.market_impact_risk > 0.6:
            strategies.append("Implement gradual execution with time delays")
        if risk_metrics.temporal_risk > 0.6:
            strategies.append("Monitor market conditions closely before execution")
        
        return strategies
    
    def _assess_user_risk_alignment(self, risk_metrics: RiskMetrics, user_profile: Dict) -> Dict[str, Any]:
        """Assess alignment between calculated risk and user risk tolerance"""
        user_tolerance = user_profile.get('risk_tolerance', 'balanced').lower()
        
        tolerance_thresholds = {
            'conservative': 0.4,
            'balanced': 0.6,
            'aggressive': 0.8
        }
        
        max_acceptable_risk = tolerance_thresholds.get(user_tolerance, 0.6)
        risk_alignment = risk_metrics.overall_risk_score <= max_acceptable_risk
        
        return {
            "is_aligned": risk_alignment,
            "user_max_risk": max_acceptable_risk,
            "calculated_risk": risk_metrics.overall_risk_score,
            "risk_gap": risk_metrics.overall_risk_score - max_acceptable_risk,
            "recommendation": "PROCEED" if risk_alignment else "REDUCE_RISK"
        }
    
    def _determine_action(self, risk_assessment: Dict[str, Any]) -> str:
        """Determine recommended action based on risk assessment"""
        risk_level = risk_assessment.get('risk_level', 'HIGH')
        user_alignment = risk_assessment.get('user_risk_alignment', {})
        
        if risk_level == "CRITICAL":
            return "ABORT_TRADE"
        elif risk_level == "HIGH" and not user_alignment.get('is_aligned', False):
            return "REDUCE_POSITION_SIZE"
        elif risk_level in ["MEDIUM", "HIGH"] and user_alignment.get('is_aligned', False):
            return "PROCEED_WITH_CAUTION"
        else:
            return "PROCEED_NORMALLY"
    
    def _calculate_confidence(self, risk_assessment: Dict[str, Any]) -> float:
        """Calculate confidence in risk assessment"""
        # Base confidence on data quality and risk clarity
        risk_metrics = risk_assessment.get('risk_metrics', {})
        
        # Higher confidence when risks are clearly defined
        risk_variance = np.var(list(risk_metrics.values())) if risk_metrics else 0.5
        data_quality = 1.0 - min(risk_variance, 0.5)  # Lower variance = higher confidence
        
        return min(max(data_quality, 0.6), 0.95)  # Confidence between 60-95%
    
    def _generate_warnings(self, risk_assessment: Dict[str, Any]) -> List[str]:
        """Generate specific warnings based on risk assessment"""
        warnings = []
        
        risk_level = risk_assessment.get('risk_level', 'MEDIUM')
        risk_factors = risk_assessment.get('risk_factors', [])
        
        if risk_level in ["HIGH", "CRITICAL"]:
            warnings.append(f"⚠️ {risk_level} risk level detected")
        
        for factor in risk_factors:
            warnings.append(f"🔍 {factor}")
        
        user_alignment = risk_assessment.get('user_risk_alignment', {})
        if not user_alignment.get('is_aligned', True):
            warnings.append("❌ Risk exceeds user tolerance level")
        
        return warnings

    async def analyze_risk(
        self,
        simulation_data: Dict[str, Any],
        market_conditions: Dict[str, Any] = None,
        user_profile: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """Main entry point for risk analysis"""
        if market_conditions is None:
            market_conditions = {}
        if user_profile is None:
            user_profile = {'risk_tolerance': 'balanced'}
        
        return await self._analyze_comprehensive_risk(
            simulation_data, market_conditions, user_profile
        )

    def get_agent(self):
        """Return the uAgent instance"""
        return self.agent
