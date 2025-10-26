"""
Enhanced MEV Protection Agent with MeTTa Knowledge Graph and ASI:One Chat Protocol
Uses Fetch.ai uAgent framework for autonomous communication and MeTTa reasoning for decisions
"""

from uagents import Agent, Context, Model
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)
from hyperon import MeTTa
from typing import List, Dict, Any, Optional
import json
import os
import requests
from datetime import datetime
import uuid

try:
    from .metta_knowledge_base import initialize_defi_knowledge_graph, DeFiMeTTaRAG
    from .chat_protocol import (
        ASIChatProtocol, AnalysisRequest, AnalysisResponse, 
        ToolCallRequest, ToolCallResponse
    )
except ImportError:
    from metta_knowledge_base import initialize_defi_knowledge_graph, DeFiMeTTaRAG
    from chat_protocol import (
        ASIChatProtocol, AnalysisRequest, AnalysisResponse, 
        ToolCallRequest, ToolCallResponse
    )

class EnhancedMEVAgent:
    """
    Enhanced MEV Protection Agent with MeTTa reasoning and ASI:One communication
    
    Features:
    - MeTTa knowledge graph for MEV risk assessment
    - ASI:One chat protocol for inter-agent communication
    - ASI:One API integration for advanced reasoning
    - Tool calling capabilities for real-time data
    """
    
    def __init__(self, agent_port: int = 8001):
        # Initialize uAgent
        self.agent = Agent(
            name="enhanced_mev_agent",
            seed="mev_agent_seed_12345",
            port=agent_port,
            endpoint=[f"http://localhost:{agent_port}/submit"]
        )
        
        self.agent_id = "enhanced_mev_agent"
        self.agent_type = "mev_protection"
        self.name = "Enhanced MEV Protection Agent"
        
        # Initialize MeTTa knowledge graph
        self.metta = MeTTa()
        initialize_defi_knowledge_graph(self.metta)
        self.knowledge_rag = DeFiMeTTaRAG(self.metta)
        
        # ASI:One API configuration
        self.asi_one_api_key = os.getenv("ASI_ONE_API_KEY")
        self.asi_one_url = "https://api.asi1.ai/v1/chat/completions"
        
        # Chat protocol integration
        self.chat_protocol = ASIChatProtocol()
        
        # Analysis results storage
        self.analysis_cache: Dict[str, Dict[str, Any]] = {}
        
        # Setup agent handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup agent event handlers and message protocols"""
        
        @self.agent.on_event("startup")
        async def startup_handler(ctx: Context):
            ctx.logger.info(f"Enhanced MEV Agent started: {ctx.agent.address}")
            ctx.logger.info("MeTTa knowledge graph initialized")
            ctx.logger.info("ASI:One chat protocol ready")
            
            # Register with chat protocol coordinator
            self.chat_protocol.register_agent(
                agent_id=self.agent_id,
                agent_address=ctx.agent.address,
                agent_type=self.agent_type,
                capabilities=["mev_analysis", "risk_assessment", "mempool_monitoring"]
            )
        
        # Analysis Request Handler
        @self.agent.on_message(model=AnalysisRequest)
        async def handle_analysis_request(ctx: Context, sender: str, msg: AnalysisRequest):
            """Handle analysis requests from other agents or orchestrator"""
            
            ctx.logger.info(f"Received analysis request for session {msg.session_id}")
            
            try:
                # Perform MEV analysis using MeTTa reasoning
                analysis_result = await self._perform_mev_analysis(
                    simulations=msg.simulations,
                    user_preferences=msg.user_preferences,
                    session_id=msg.session_id
                )
                
                # Send analysis response
                response = AnalysisResponse(
                    session_id=msg.session_id,
                    agent_id=self.agent_id,
                    agent_type=self.agent_type,
                    analysis=analysis_result,
                    confidence=analysis_result.get("confidence", 0.8),
                    timestamp=datetime.utcnow().isoformat()
                )
                
                await ctx.send(sender, response)
                ctx.logger.info(f"Sent MEV analysis for session {msg.session_id}")
                
            except Exception as e:
                ctx.logger.error(f"MEV analysis failed: {str(e)}")
        
        # Chat Message Handler
        @self.agent.on_message(model=ChatMessage)
        async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
            """Handle ASI:One chat messages"""
            
            for item in msg.content:
                if isinstance(item, TextContent):
                    ctx.logger.info(f"Received chat: {item.text}")
                    
                    # Process chat content for MEV-related queries
                    response_text = await self._process_chat_query(item.text)
                    
                    # Send acknowledgment
                    ack = ChatAcknowledgement(
                        timestamp=datetime.utcnow(),
                        acknowledged_msg_id=msg.msg_id
                    )
                    await ctx.send(sender, ack)
                    
                    # Send response
                    if response_text:
                        response = ChatMessage(
                            timestamp=datetime.utcnow(),
                            msg_id=uuid.uuid4(),
                            content=[TextContent(type="text", text=response_text)]
                        )
                        await ctx.send(sender, response)
        
        # Tool Call Handler
        @self.agent.on_message(model=ToolCallRequest)
        async def handle_tool_call(ctx: Context, sender: str, msg: ToolCallRequest):
            """Handle tool call requests"""
            
            if msg.tool_name == "mev_risk_assessment":
                result = await self._handle_mev_risk_tool_call(msg.parameters)
                
                response = ToolCallResponse(
                    session_id=msg.session_id,
                    call_id=msg.call_id,
                    tool_name=msg.tool_name,
                    result=result,
                    success=True
                )
                
                await ctx.send(sender, response)
    
    async def _perform_mev_analysis(
        self, 
        simulations: List[Dict[str, Any]], 
        user_preferences: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """Perform MEV analysis using MeTTa knowledge graph and ASI:One reasoning"""
        
        if not simulations:
            raise ValueError("No simulations provided")
        
        # Extract MEV-related factors from simulations
        mev_factors = []
        gas_conditions = []
        
        for sim in simulations:
            # Analyze MEV risk factors
            if sim.get('mev_risk_score', 0) > 50:
                mev_factors.append("high_mev_risk")
            if sim.get('block_offset', 0) == 0:
                mev_factors.append("immediate_execution")
            if sim.get('mempool_snapshot', {}).get('sandwich_bots_detected', 0) > 0:
                mev_factors.append("sandwich_bots_detected")
            
            # Analyze gas conditions
            gas_price = sim.get('gas_price_gwei', 0)
            if gas_price > 50:
                gas_conditions.append("high_gas_price")
            elif gas_price < 10:
                gas_conditions.append("low_gas_price")
        
        # Query MeTTa knowledge graph
        scenario_conditions = {
            "mev_factors": list(set(mev_factors)),
            "gas_conditions": list(set(gas_conditions)),
            "agent_states": ["mev_agent_analyzing"]
        }
        
        metta_results = self.knowledge_rag.query_complex_scenario(scenario_conditions)
        
        # Use ASI:One for advanced reasoning if available
        if self.asi_one_api_key:
            asi_analysis = await self._get_asi_one_analysis(simulations, metta_results, user_preferences)
        else:
            asi_analysis = self._fallback_analysis(simulations, metta_results)
        
        # Generate final recommendation
        recommendation = self.knowledge_rag.generate_recommendation(
            metta_results, 
            user_preferences.get("priority", "balanced")
        )
        
        # Find best simulation based on MEV protection
        best_sim = self._select_best_simulation(simulations, metta_results, recommendation)
        
        return {
            "recommended_id": best_sim["id"],
            "score": recommendation["confidence_score"],
            "reasoning": self._build_reasoning(best_sim, metta_results, asi_analysis),
            "concerns": self._identify_concerns(best_sim, metta_results),
            "agent": "Enhanced_MEV_Protection",
            "metta_insights": metta_results,
            "asi_analysis": asi_analysis,
            "confidence": recommendation["confidence_score"] / 100,
            "mev_metrics": {
                "risk_level": self._calculate_risk_level(best_sim),
                "protection_strategy": recommendation["primary_recommendation"],
                "estimated_mev_loss": self._estimate_mev_loss(best_sim),
                "safety_score": self._calculate_safety_score(best_sim, metta_results)
            }
        }
    
    async def _get_asi_one_analysis(
        self, 
        simulations: List[Dict[str, Any]], 
        metta_results: Dict[str, List[str]], 
        user_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use ASI:One API for advanced MEV analysis"""
        
        prompt = self._build_asi_one_prompt(simulations, metta_results, user_preferences)
        
        try:
            response = requests.post(
                self.asi_one_url,
                headers={
                    "Authorization": f"Bearer {self.asi_one_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "asi1-mini",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are an expert MEV protection analyst. Analyze the provided data and return insights in JSON format."
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
                return response.json()["choices"][0]["message"]["content"]
            else:
                return {"error": f"ASI:One API error: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"ASI:One API failed: {str(e)}"}
    
    def _build_asi_one_prompt(
        self, 
        simulations: List[Dict[str, Any]], 
        metta_results: Dict[str, List[str]], 
        user_preferences: Dict[str, Any]
    ) -> str:
        """Build prompt for ASI:One analysis"""
        
        return f"""
        Analyze MEV risks for DeFi trading simulations:
        
        Simulations: {json.dumps(simulations, indent=2)}
        
        MeTTa Knowledge Insights: {json.dumps(metta_results, indent=2)}
        
        User Preferences: {json.dumps(user_preferences, indent=2)}
        
        Provide analysis in JSON format with:
        - mev_threat_assessment: string
        - recommended_protection_strategy: string
        - risk_mitigation_steps: array of strings
        - confidence_level: number (0-1)
        - market_context_analysis: string
        """
    
    def _fallback_analysis(
        self, 
        simulations: List[Dict[str, Any]], 
        metta_results: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Fallback analysis when ASI:One is not available"""
        
        # Analyze MEV risks based on MeTTa results
        high_risk_count = sum(1 for sim in simulations if sim.get('mev_risk_score', 0) > 70)
        
        return {
            "mev_threat_assessment": "high" if high_risk_count > len(simulations) / 2 else "medium",
            "recommended_protection_strategy": "delayed_execution" if high_risk_count > 0 else "standard_protection",
            "risk_mitigation_steps": ["use_private_mempool", "delay_execution", "split_large_orders"],
            "confidence_level": 0.7,
            "market_context_analysis": "Local analysis based on MeTTa knowledge graph"
        }
    
    def _select_best_simulation(
        self, 
        simulations: List[Dict[str, Any]], 
        metta_results: Dict[str, List[str]], 
        recommendation: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Select best simulation based on MEV protection criteria"""
        
        # Sort by MEV risk (ascending - lower is better)
        sorted_sims = sorted(simulations, key=lambda s: s.get('mev_risk_score', 100))
        
        # Apply MeTTa insights
        if "high" in metta_results.get("mev_risks", []):
            # Prefer delayed execution for high MEV risk
            delayed_sims = [s for s in sorted_sims if s.get('block_offset', 0) > 0]
            if delayed_sims:
                return delayed_sims[0]
        
        return sorted_sims[0]
    
    def _build_reasoning(
        self, 
        best_sim: Dict[str, Any], 
        metta_results: Dict[str, List[str]], 
        asi_analysis: Dict[str, Any]
    ) -> str:
        """Build human-readable reasoning for the recommendation"""
        
        reasoning_parts = []
        
        # MEV risk assessment
        mev_risk = best_sim.get('mev_risk_score', 0)
        reasoning_parts.append(f"Selected option {best_sim['id']} with MEV risk score of {mev_risk}/100")
        
        # MeTTa insights
        if "mev_risks" in metta_results and metta_results["mev_risks"]:
            reasoning_parts.append(f"MeTTa analysis identified risks: {', '.join(metta_results['mev_risks'])}")
        
        # ASI:One insights
        if "mev_threat_assessment" in asi_analysis:
            reasoning_parts.append(f"ASI:One assessment: {asi_analysis['mev_threat_assessment']} threat level")
        
        # Execution timing
        block_offset = best_sim.get('block_offset', 0)
        if block_offset > 0:
            reasoning_parts.append(f"Recommends waiting {block_offset} blocks ({block_offset * 12}s) to reduce MEV exposure")
        else:
            reasoning_parts.append("Immediate execution acceptable with current MEV protection measures")
        
        return ". ".join(reasoning_parts) + "."
    
    def _identify_concerns(
        self, 
        best_sim: Dict[str, Any], 
        metta_results: Dict[str, List[str]]
    ) -> List[str]:
        """Identify potential concerns with the recommendation"""
        
        concerns = []
        
        # High MEV risk concerns
        if best_sim.get('mev_risk_score', 0) > 50:
            concerns.append(f"Moderate MEV risk ({best_sim['mev_risk_score']}/100) remains")
        
        # Timing concerns
        block_offset = best_sim.get('block_offset', 0)
        if block_offset > 3:
            concerns.append(f"Long wait time ({block_offset * 12}s) may expose to price volatility")
        
        # Gas cost concerns
        gas_cost = float(best_sim.get('gas_cost_usd', 0))
        if gas_cost > 50:
            concerns.append(f"High gas cost (${gas_cost:.2f}) for MEV protection")
        
        # MeTTa-based concerns
        if "conflicting_recommendations" in metta_results.get("consensus_rules", []):
            concerns.append("Conflicting signals detected in market analysis")
        
        return concerns
    
    def _calculate_risk_level(self, simulation: Dict[str, Any]) -> str:
        """Calculate MEV risk level"""
        risk_score = simulation.get('mev_risk_score', 0)
        
        if risk_score <= 20:
            return "very_low"
        elif risk_score <= 40:
            return "low"
        elif risk_score <= 60:
            return "medium"
        elif risk_score <= 80:
            return "high"
        else:
            return "very_high"
    
    def _estimate_mev_loss(self, simulation: Dict[str, Any]) -> float:
        """Estimate potential MEV loss in USD"""
        output_usd = float(simulation.get('estimated_output_usd', 0))
        mev_risk = simulation.get('mev_risk_score', 0)
        
        # MEV loss estimation based on risk score
        loss_rates = {
            "very_low": 0.001,   # 0.1%
            "low": 0.005,        # 0.5%
            "medium": 0.015,     # 1.5%
            "high": 0.03,        # 3%
            "very_high": 0.05    # 5%
        }
        
        risk_level = self._calculate_risk_level(simulation)
        loss_rate = loss_rates.get(risk_level, 0.02)
        
        return output_usd * loss_rate
    
    def _calculate_safety_score(
        self, 
        simulation: Dict[str, Any], 
        metta_results: Dict[str, List[str]]
    ) -> float:
        """Calculate overall safety score"""
        
        base_score = 100 - simulation.get('mev_risk_score', 0)
        
        # Bonus for protective measures
        if simulation.get('block_offset', 0) > 0:
            base_score += 10
        
        # Bonus for MeTTa-recommended strategies
        if "minimize_mev_risk" in metta_results.get("consensus_rules", []):
            base_score += 5
        
        return min(100, max(0, base_score))
    
    async def _process_chat_query(self, query: str) -> Optional[str]:
        """Process chat queries related to MEV protection"""
        
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in ['mev', 'sandwich', 'frontrun', 'protection']):
            # Query MeTTa knowledge for MEV-related information
            if 'high risk' in query_lower:
                strategies = self.knowledge_rag.get_risk_tolerance_strategy('conservative')
                return f"For high MEV risk scenarios, I recommend: {', '.join(strategies)}"
            elif 'protection' in query_lower:
                methods = self.knowledge_rag.get_speed_execution_method('low_urgency')
                return f"MEV protection methods include: {', '.join(methods)}"
            else:
                return "I can help analyze MEV risks and recommend protection strategies. What specific MEV concern do you have?"
        
        return None
    
    async def _handle_mev_risk_tool_call(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle MEV risk assessment tool calls"""
        
        transaction_data = parameters.get('transaction_data', {})
        
        # Analyze MEV risk factors
        risk_factors = []
        if transaction_data.get('large_amount', False):
            risk_factors.append('high_value_transaction')
        if transaction_data.get('popular_token', False):
            risk_factors.append('high_liquidity_token')
        
        # Query MeTTa knowledge
        mev_risks = []
        for factor in risk_factors:
            risks = self.knowledge_rag.query_mev_risk_factors(factor)
            mev_risks.extend(risks)
        
        return {
            "risk_factors_detected": risk_factors,
            "mev_risk_levels": list(set(mev_risks)),
            "overall_risk_score": len(set(mev_risks)) * 20,  # Simple scoring
            "protection_recommendations": self.knowledge_rag.get_risk_tolerance_strategy('conservative')
        }
    
    async def start_agent(self):
        """Start the enhanced MEV agent"""
        await self.agent.run()

# Global instance for import
enhanced_mev_agent = EnhancedMEVAgent()
