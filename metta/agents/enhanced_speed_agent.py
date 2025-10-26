"""
Enhanced Speed Optimizer Agent with MeTTa Knowledge Graph and ASI:One Chat Protocol
Focuses on minimizing execution time while maintaining acceptable profit and risk levels
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

class EnhancedSpeedAgent:
    """
    Enhanced Speed Optimizer Agent with MeTTa reasoning and ASI:One communication
    
    Features:
    - MeTTa knowledge graph for speed optimization strategies
    - ASI:One chat protocol for inter-agent communication
    - Real-time execution timing analysis
    - Network congestion and gas price optimization
    """
    
    def __init__(self, agent_port: int = 8003):
        # Initialize uAgent
        self.agent = Agent(
            name="enhanced_speed_agent",
            seed="speed_agent_seed_54321",
            port=agent_port,
            endpoint=[f"http://localhost:{agent_port}/submit"]
        )
        
        self.agent_id = "enhanced_speed_agent"
        self.agent_type = "speed_optimization"
        self.name = "Enhanced Speed Optimizer Agent"
        
        # Initialize MeTTa knowledge graph
        self.metta = MeTTa()
        initialize_defi_knowledge_graph(self.metta)
        self.knowledge_rag = DeFiMeTTaRAG(self.metta)
        
        # ASI:One API configuration
        self.asi_one_api_key = os.getenv("ASI_ONE_API_KEY")
        self.asi_one_url = "https://api.asi1.ai/v1/chat/completions"
        
        # Chat protocol integration
        self.chat_protocol = ASIChatProtocol()
        
        # Network performance cache
        self.network_cache: Dict[str, Dict[str, Any]] = {}
        
        # Setup agent handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup agent event handlers and message protocols"""
        
        @self.agent.on_event("startup")
        async def startup_handler(ctx: Context):
            ctx.logger.info(f"Enhanced Speed Agent started: {ctx.agent.address}")
            ctx.logger.info("Speed optimization strategies loaded")
            
            # Register with chat protocol coordinator
            self.chat_protocol.register_agent(
                agent_id=self.agent_id,
                agent_address=ctx.agent.address,
                agent_type=self.agent_type,
                capabilities=["speed_analysis", "execution_timing", "network_optimization", "gas_timing"]
            )
        
        # Analysis Request Handler
        @self.agent.on_message(model=AnalysisRequest)
        async def handle_analysis_request(ctx: Context, sender: str, msg: AnalysisRequest):
            """Handle speed optimization analysis requests"""
            
            ctx.logger.info(f"Received speed analysis request for session {msg.session_id}")
            
            try:
                # Perform speed analysis using MeTTa reasoning
                analysis_result = await self._perform_speed_analysis(
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
                    confidence=analysis_result.get("confidence", 0.9),
                    timestamp=datetime.utcnow().isoformat()
                )
                
                await ctx.send(sender, response)
                ctx.logger.info(f"Sent speed analysis for session {msg.session_id}")
                
            except Exception as e:
                ctx.logger.error(f"Speed analysis failed: {str(e)}")
        
        # Chat Message Handler
        @self.agent.on_message(model=ChatMessage)
        async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
            """Handle ASI:One chat messages"""
            
            for item in msg.content:
                if isinstance(item, TextContent):
                    ctx.logger.info(f"Received chat: {item.text}")
                    
                    # Process chat content for speed-related queries
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
            
            if msg.tool_name == "execution_timing":
                result = await self._handle_execution_timing_tool_call(msg.parameters)
            elif msg.tool_name == "network_analysis":
                result = await self._handle_network_analysis_tool_call(msg.parameters)
            else:
                result = {"error": f"Unknown tool: {msg.tool_name}"}
            
            response = ToolCallResponse(
                session_id=msg.session_id,
                call_id=msg.call_id,
                tool_name=msg.tool_name,
                result=result,
                success="error" not in result
            )
            
            await ctx.send(sender, response)
    
    async def _perform_speed_analysis(
        self, 
        simulations: List[Dict[str, Any]], 
        user_preferences: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """Perform speed analysis using MeTTa knowledge graph and ASI:One reasoning"""
        
        if not simulations:
            raise ValueError("No simulations provided")
        
        # Extract speed-related factors
        speed_factors = []
        urgency_indicators = []
        
        for sim in simulations:
            # Analyze execution timing
            block_offset = sim.get('block_offset', 0)
            if block_offset == 0:
                speed_factors.append("immediate_execution")
            elif block_offset > 5:
                speed_factors.append("delayed_execution")
            
            # Check urgency indicators
            if sim.get('confidence', 0) > 90:
                urgency_indicators.append("high_confidence")
            
            # Gas price analysis for timing
            gas_price = sim.get('gas_price_gwei', 0)
            if gas_price > 50:
                speed_factors.append("high_gas_price")
            
            # Network congestion indicators
            if sim.get('mempool_snapshot', {}).get('pending_transactions', 0) > 1000:
                speed_factors.append("network_congested")
        
        # Check user urgency preferences
        if user_preferences.get('time_sensitive', False):
            urgency_indicators.append("time_sensitive")
        if user_preferences.get('priority') == 'speed':
            urgency_indicators.append("speed_priority")
        
        # Query MeTTa knowledge graph
        scenario_conditions = {
            "speed_factors": list(set(speed_factors)),
            "agent_states": ["speed_agent_high_confidence"],
            "tool_usage": self._determine_tool_usage_needs(simulations)
        }
        
        metta_results = self.knowledge_rag.query_complex_scenario(scenario_conditions)
        
        # Use ASI:One for advanced timing analysis
        if self.asi_one_api_key:
            asi_analysis = await self._get_asi_one_speed_analysis(simulations, metta_results, user_preferences)
        else:
            asi_analysis = self._fallback_speed_analysis(simulations, metta_results)
        
        # Calculate speed metrics for each simulation
        enriched_simulations = []
        for sim in simulations:
            speed_metrics = self._calculate_speed_metrics(sim, metta_results, asi_analysis)
            enriched_simulations.append({**sim, **speed_metrics})
        
        # Select fastest acceptable simulation
        best_sim = self._select_fastest_simulation(enriched_simulations, user_preferences)
        
        # Generate recommendation
        recommendation = self.knowledge_rag.generate_recommendation(
            metta_results, 
            user_preferences.get("priority", "speed")
        )
        
        return {
            "recommended_id": best_sim["id"],
            "score": recommendation["confidence_score"],
            "reasoning": self._build_speed_reasoning(best_sim, metta_results, asi_analysis),
            "concerns": self._identify_speed_concerns(best_sim, metta_results),
            "agent": "Enhanced_Speed_Optimizer",
            "metta_insights": metta_results,
            "asi_analysis": asi_analysis,
            "confidence": recommendation["confidence_score"] / 100,
            "speed_metrics": {
                "execution_time_seconds": best_sim["execution_time_seconds"],
                "speed_score": best_sim["speed_score"],
                "urgency_level": best_sim["urgency_level"],
                "network_efficiency": best_sim.get("network_efficiency", 0),
                "timing_optimization": best_sim.get("timing_optimization", 0),
                "profit_retention_percent": best_sim.get("profit_retention", 0)
            }
        }
    
    def _determine_tool_usage_needs(self, simulations: List[Dict[str, Any]]) -> List[str]:
        """Determine what tools might be needed based on simulation data"""
        
        tool_needs = []
        
        # Check if we need real-time price data
        avg_volatility = sum(float(sim.get('price_impact_percent', 0)) for sim in simulations) / len(simulations)
        if avg_volatility > 2:
            tool_needs.append("price_volatility_high")
        
        # Check if we need mempool analysis
        has_mempool_data = any(sim.get('mempool_snapshot') for sim in simulations)
        if not has_mempool_data:
            tool_needs.append("mempool_congested")
        
        return tool_needs
    
    async def _get_asi_one_speed_analysis(
        self, 
        simulations: List[Dict[str, Any]], 
        metta_results: Dict[str, List[str]], 
        user_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use ASI:One API for advanced speed analysis"""
        
        prompt = f"""
        Analyze execution speed optimization for DeFi trading:
        
        Simulations: {json.dumps(simulations[:3], indent=2)}
        
        MeTTa Speed Insights: {json.dumps(metta_results, indent=2)}
        
        User Urgency: {user_preferences.get('time_sensitive', False)}
        
        Provide analysis in JSON format with:
        - execution_urgency_assessment: string
        - optimal_timing_strategy: string
        - network_conditions_analysis: object
        - speed_vs_profit_tradeoff: object
        - timing_recommendations: array
        - confidence_level: number (0-1)
        """
        
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
                            "content": "You are an expert DeFi execution timing analyst. Focus on minimizing execution time while maintaining acceptable returns."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.2,
                    "response_format": {"type": "json_object"}
                },
                timeout=10
            )
            
            if response.status_code == 200:
                return json.loads(response.json()["choices"][0]["message"]["content"])
            else:
                return {"error": f"ASI:One API error: {response.status_code}"}
                
        except Exception as e:
            return {"error": f"ASI:One API failed: {str(e)}"}
    
    def _fallback_speed_analysis(
        self, 
        simulations: List[Dict[str, Any]], 
        metta_results: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Fallback speed analysis when ASI:One is not available"""
        
        min_execution_time = min(sim.get('block_offset', 0) * 12 for sim in simulations)
        
        return {
            "execution_urgency_assessment": "high" if min_execution_time == 0 else "medium",
            "optimal_timing_strategy": "immediate_execution" if min_execution_time == 0 else "optimal_timing",
            "network_conditions_analysis": {
                "congestion_level": "moderate",
                "gas_price_trend": "stable"
            },
            "speed_vs_profit_tradeoff": {
                "speed_priority": True,
                "acceptable_profit_loss": 5
            },
            "timing_recommendations": ["execute_immediately", "monitor_gas_prices"],
            "confidence_level": 0.8
        }
    
    def _calculate_speed_metrics(
        self, 
        simulation: Dict[str, Any], 
        metta_results: Dict[str, List[str]], 
        asi_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate speed-related metrics for a simulation"""
        
        # Base execution time
        block_offset = simulation.get('block_offset', 0)
        execution_time_seconds = block_offset * 12  # 12 seconds per block
        
        # Speed score (higher is better, lower execution time)
        speed_score = max(0, 100 - (execution_time_seconds / 6))  # Normalize to 0-100
        
        # Urgency level assessment
        urgency_level = self._assess_urgency_level(simulation, metta_results, asi_analysis)
        
        # Network efficiency score
        network_efficiency = self._calculate_network_efficiency(simulation)
        
        # Timing optimization score
        timing_optimization = self._calculate_timing_optimization(simulation, metta_results)
        
        # Profit retention calculation
        estimated_output = float(simulation.get('estimated_output_usd', 0))
        gas_cost = float(simulation.get('gas_cost_usd', 0))
        profit_retention = ((estimated_output - gas_cost) / estimated_output * 100) if estimated_output > 0 else 0
        
        return {
            "execution_time_seconds": execution_time_seconds,
            "speed_score": speed_score,
            "urgency_level": urgency_level,
            "network_efficiency": network_efficiency,
            "timing_optimization": timing_optimization,
            "profit_retention": profit_retention
        }
    
    def _assess_urgency_level(
        self, 
        simulation: Dict[str, Any], 
        metta_results: Dict[str, List[str]], 
        asi_analysis: Dict[str, Any]
    ) -> str:
        """Assess the urgency level for execution"""
        
        # Check ASI:One assessment first
        if "execution_urgency_assessment" in asi_analysis:
            return asi_analysis["execution_urgency_assessment"]
        
        # Fallback to local assessment
        if simulation.get('block_offset', 0) == 0:
            return "high"
        elif simulation.get('mev_risk_score', 0) > 70:
            return "medium"  # MEV risk might require faster execution
        else:
            return "low"
    
    def _calculate_network_efficiency(self, simulation: Dict[str, Any]) -> float:
        """Calculate network efficiency score"""
        
        score = 50  # Base score
        
        # Gas price efficiency
        gas_price = simulation.get('gas_price_gwei', 0)
        if gas_price < 20:
            score += 30  # Efficient gas price
        elif gas_price > 50:
            score -= 20  # Expensive gas
        
        # Network congestion
        mempool_data = simulation.get('mempool_snapshot', {})
        pending_txs = mempool_data.get('pending_transactions', 0)
        if pending_txs < 500:
            score += 20  # Low congestion
        elif pending_txs > 2000:
            score -= 25  # High congestion
        
        return max(0, min(100, score))
    
    def _calculate_timing_optimization(
        self, 
        simulation: Dict[str, Any], 
        metta_results: Dict[str, List[str]]
    ) -> float:
        """Calculate timing optimization score"""
        
        score = 50  # Base score
        
        # MeTTa insights bonus
        if "immediate_execution" in metta_results.get("speed_methods", []):
            score += 25
        if "optimal_timing" in metta_results.get("speed_methods", []):
            score += 15
        
        # Confidence bonus
        confidence = simulation.get('confidence', 0)
        if confidence > 85:
            score += 15
        elif confidence < 60:
            score -= 10
        
        return max(0, min(100, score))
    
    def _select_fastest_simulation(
        self, 
        simulations: List[Dict[str, Any]], 
        user_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Select the fastest acceptable simulation"""
        
        # Sort by execution time (ascending - faster is better)
        sorted_by_speed = sorted(simulations, key=lambda s: s['execution_time_seconds'])
        
        # Check if user prioritizes pure speed
        if user_preferences.get('priority') == 'speed' or user_preferences.get('time_sensitive', False):
            return sorted_by_speed[0]
        
        # Otherwise, find fastest option that maintains acceptable profit
        max_profit = max(s['profit_retention'] for s in simulations)
        min_acceptable_profit = max_profit * 0.9  # Within 10% of max profit
        
        acceptable_options = [s for s in sorted_by_speed if s['profit_retention'] >= min_acceptable_profit]
        
        if acceptable_options:
            return acceptable_options[0]
        else:
            return sorted_by_speed[0]  # Fallback to fastest
    
    def _build_speed_reasoning(
        self, 
        best_sim: Dict[str, Any], 
        metta_results: Dict[str, List[str]], 
        asi_analysis: Dict[str, Any]
    ) -> str:
        """Build human-readable reasoning for speed recommendation"""
        
        reasoning_parts = []
        
        # Execution timing
        execution_time = best_sim['execution_time_seconds']
        block_offset = best_sim.get('block_offset', 0)
        
        if execution_time == 0:
            reasoning_parts.append(f"Option {best_sim['id']} executes immediately")
        else:
            reasoning_parts.append(f"Option {best_sim['id']} executes in {execution_time}s ({block_offset} blocks)")
        
        # Speed score
        speed_score = best_sim['speed_score']
        reasoning_parts.append(f"Speed score: {speed_score:.0f}/100")
        
        # MeTTa insights
        if "speed_methods" in metta_results and metta_results["speed_methods"]:
            methods = ", ".join(metta_results["speed_methods"])
            reasoning_parts.append(f"MeTTa recommends: {methods}")
        
        # ASI:One insights
        if "optimal_timing_strategy" in asi_analysis:
            reasoning_parts.append(f"ASI:One strategy: {asi_analysis['optimal_timing_strategy']}")
        
        # Profit retention
        profit_retention = best_sim.get('profit_retention', 0)
        reasoning_parts.append(f"Maintains {profit_retention:.1f}% of potential profit")
        
        return ". ".join(reasoning_parts) + "."
    
    def _identify_speed_concerns(
        self, 
        best_sim: Dict[str, Any], 
        metta_results: Dict[str, List[str]]
    ) -> List[str]:
        """Identify concerns with the speed recommendation"""
        
        concerns = []
        
        # Profit sacrifice concerns
        profit_retention = best_sim.get('profit_retention', 0)
        if profit_retention < 90:
            profit_loss = 100 - profit_retention
            concerns.append(f"Sacrifices {profit_loss:.1f}% of potential profit for speed")
        
        # MEV risk from fast execution
        if best_sim.get('execution_time_seconds', 0) == 0 and best_sim.get('mev_risk_score', 0) > 40:
            concerns.append("Immediate execution increases MEV exposure")
        
        # Network efficiency concerns
        if best_sim.get('network_efficiency', 0) < 40:
            concerns.append("Poor network conditions may affect execution speed")
        
        # High gas costs for speed
        gas_cost = float(best_sim.get('gas_cost_usd', 0))
        if gas_cost > 30:
            concerns.append(f"High gas cost (${gas_cost:.2f}) for fast execution")
        
        # Timing optimization concerns
        if best_sim.get('timing_optimization', 0) < 50:
            concerns.append("Suboptimal timing may impact execution efficiency")
        
        return concerns
    
    async def _process_chat_query(self, query: str) -> Optional[str]:
        """Process chat queries related to speed optimization"""
        
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in ['speed', 'fast', 'quick', 'immediate', 'urgent']):
            if 'network congested' in query_lower:
                methods = self.knowledge_rag.get_speed_execution_method('time_sensitive')
                return f"For congested networks, try: {', '.join(methods)}"
            elif 'gas price' in query_lower:
                strategies = self.knowledge_rag.get_gas_optimization_strategy('high_gas_price')
                return f"For high gas prices: {', '.join(strategies)}"
            else:
                return "I can help optimize execution speed. What's your urgency level and current market conditions?"
        
        return None
    
    async def _handle_execution_timing_tool_call(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle execution timing analysis tool calls"""
        
        timing_data = parameters.get('timing_data', {})
        
        # Analyze timing factors
        timing_factors = []
        if timing_data.get('time_sensitive', False):
            timing_factors.append('time_sensitive')
        if timing_data.get('high_volatility', False):
            timing_factors.append('market_moving')
        
        # Query MeTTa for execution methods
        methods = []
        for factor in timing_factors:
            factor_methods = self.knowledge_rag.get_speed_execution_method(factor)
            methods.extend(factor_methods)
        
        return {
            "timing_factors": timing_factors,
            "recommended_methods": list(set(methods)),
            "urgency_score": len(timing_factors) * 25,
            "execution_recommendation": "immediate" if "time_sensitive" in timing_factors else "optimal_timing"
        }
    
    async def _handle_network_analysis_tool_call(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle network analysis tool calls"""
        
        network_data = parameters.get('network_data', {})
        
        # Analyze network conditions
        conditions = []
        gas_price = network_data.get('gas_price_gwei', 0)
        if gas_price > 50:
            conditions.append('high_gas_price')
        
        pending_txs = network_data.get('pending_transactions', 0)
        if pending_txs > 1000:
            conditions.append('congested_network')
        
        # Get optimization strategies
        strategies = []
        for condition in conditions:
            condition_strategies = self.knowledge_rag.get_gas_optimization_strategy(condition)
            strategies.extend(condition_strategies)
        
        return {
            "network_conditions": conditions,
            "optimization_strategies": list(set(strategies)),
            "congestion_level": "high" if pending_txs > 2000 else "medium" if pending_txs > 500 else "low",
            "gas_efficiency_score": max(0, 100 - (gas_price - 10) * 2)
        }
    
    async def start_agent(self):
        """Start the enhanced speed agent"""
        await self.agent.run()

# Global instance for import
enhanced_speed_agent = EnhancedSpeedAgent()
