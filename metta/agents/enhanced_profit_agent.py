"""
Enhanced Profit Maximizer Agent with MeTTa Knowledge Graph and ASI:One Chat Protocol
Focuses on maximizing net profit while considering MEV risks and market conditions
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

class EnhancedProfitAgent:
    """
    Enhanced Profit Maximizer Agent with MeTTa reasoning and ASI:One communication
    
    Features:
    - MeTTa knowledge graph for profit optimization strategies
    - ASI:One chat protocol for inter-agent communication
    - Market analysis and arbitrage detection
    - Dynamic profit calculation with risk adjustment
    """
    
    def __init__(self, agent_port: int = 8002):
        # Initialize uAgent
        self.agent = Agent(
            name="enhanced_profit_agent",
            seed="profit_agent_seed_67890",
            port=agent_port,
            endpoint=[f"http://localhost:{agent_port}/submit"]
        )
        
        self.agent_id = "enhanced_profit_agent"
        self.agent_type = "profit_maximization"
        self.name = "Enhanced Profit Maximizer Agent"
        
        # Initialize MeTTa knowledge graph
        self.metta = MeTTa()
        initialize_defi_knowledge_graph(self.metta)
        self.knowledge_rag = DeFiMeTTaRAG(self.metta)
        
        # ASI:One API configuration
        self.asi_one_api_key = os.getenv("ASI_ONE_API_KEY")
        self.asi_one_url = "https://api.asi1.ai/v1/chat/completions"
        
        # Chat protocol integration
        self.chat_protocol = ASIChatProtocol()
        
        # Market data cache
        self.market_cache: Dict[str, Dict[str, Any]] = {}
        
        # Setup agent handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup agent event handlers and message protocols"""
        
        @self.agent.on_event("startup")
        async def startup_handler(ctx: Context):
            ctx.logger.info(f"Enhanced Profit Agent started: {ctx.agent.address}")
            ctx.logger.info("Profit optimization strategies loaded")
            
            # Register with chat protocol coordinator
            self.chat_protocol.register_agent(
                agent_id=self.agent_id,
                agent_address=ctx.agent.address,
                agent_type=self.agent_type,
                capabilities=["profit_analysis", "arbitrage_detection", "market_analysis", "yield_optimization"]
            )
        
        # Analysis Request Handler
        @self.agent.on_message(model=AnalysisRequest)
        async def handle_analysis_request(ctx: Context, sender: str, msg: AnalysisRequest):
            """Handle profit analysis requests"""
            
            ctx.logger.info(f"Received profit analysis request for session {msg.session_id}")
            
            try:
                # Perform profit analysis using MeTTa reasoning
                analysis_result = await self._perform_profit_analysis(
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
                    confidence=analysis_result.get("confidence", 0.85),
                    timestamp=datetime.utcnow().isoformat()
                )
                
                await ctx.send(sender, response)
                ctx.logger.info(f"Sent profit analysis for session {msg.session_id}")
                
            except Exception as e:
                ctx.logger.error(f"Profit analysis failed: {str(e)}")
        
        # Chat Message Handler
        @self.agent.on_message(model=ChatMessage)
        async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
            """Handle ASI:One chat messages"""
            
            for item in msg.content:
                if isinstance(item, TextContent):
                    ctx.logger.info(f"Received chat: {item.text}")
                    
                    # Process chat content for profit-related queries
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
            
            if msg.tool_name == "profit_optimization":
                result = await self._handle_profit_optimization_tool_call(msg.parameters)
            elif msg.tool_name == "arbitrage_detection":
                result = await self._handle_arbitrage_detection_tool_call(msg.parameters)
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
    
    async def _perform_profit_analysis(
        self, 
        simulations: List[Dict[str, Any]], 
        user_preferences: Dict[str, Any],
        session_id: str
    ) -> Dict[str, Any]:
        """Perform profit analysis using MeTTa knowledge graph and ASI:One reasoning"""
        
        if not simulations:
            raise ValueError("No simulations provided")
        
        # Extract profit-related factors
        profit_factors = []
        market_conditions = []
        
        for sim in simulations:
            # Analyze profit opportunities
            estimated_output = float(sim.get('estimated_output_usd', 0))
            gas_cost = float(sim.get('gas_cost_usd', 0))
            net_profit = estimated_output - gas_cost
            
            if net_profit > estimated_output * 0.05:  # >5% profit margin
                profit_factors.append("high_profit_margin")
            
            # Check for arbitrage opportunities
            price_impact = float(sim.get('price_impact_percent', 0))
            if price_impact < 0.5:
                profit_factors.append("low_slippage")
            elif price_impact > 2.0:
                profit_factors.append("high_slippage")
            
            # Market volatility analysis
            if sim.get('confidence', 0) < 70:
                market_conditions.append("high_volatility")
            else:
                market_conditions.append("stable_market")
        
        # Query MeTTa knowledge graph
        scenario_conditions = {
            "profit_factors": list(set(profit_factors)),
            "gas_conditions": self._analyze_gas_conditions(simulations),
            "agent_states": ["profit_agent_high_confidence"]
        }
        
        metta_results = self.knowledge_rag.query_complex_scenario(scenario_conditions)
        
        # Use ASI:One for advanced market analysis
        if self.asi_one_api_key:
            asi_analysis = await self._get_asi_one_profit_analysis(simulations, metta_results, user_preferences)
        else:
            asi_analysis = self._fallback_profit_analysis(simulations, metta_results)
        
        # Calculate enhanced profit metrics for each simulation
        enriched_simulations = []
        for sim in simulations:
            enhanced_metrics = self._calculate_enhanced_profit_metrics(sim, metta_results, asi_analysis)
            enriched_simulations.append({**sim, **enhanced_metrics})
        
        # Select best simulation for profit maximization
        best_sim = self._select_most_profitable_simulation(enriched_simulations, user_preferences)
        
        # Generate recommendation
        recommendation = self.knowledge_rag.generate_recommendation(
            metta_results, 
            user_preferences.get("priority", "profit")
        )
        
        return {
            "recommended_id": best_sim["id"],
            "score": recommendation["confidence_score"],
            "reasoning": self._build_profit_reasoning(best_sim, metta_results, asi_analysis),
            "concerns": self._identify_profit_concerns(best_sim, metta_results),
            "agent": "Enhanced_Profit_Maximizer",
            "metta_insights": metta_results,
            "asi_analysis": asi_analysis,
            "confidence": recommendation["confidence_score"] / 100,
            "profit_metrics": {
                "net_profit_usd": best_sim["enhanced_net_profit"],
                "profit_margin_percent": best_sim["profit_margin_percent"],
                "risk_adjusted_profit": best_sim["risk_adjusted_profit"],
                "arbitrage_potential": best_sim.get("arbitrage_score", 0),
                "market_timing_score": best_sim.get("timing_score", 0),
                "gas_efficiency_ratio": best_sim.get("gas_efficiency", 0)
            }
        }
    
    def _analyze_gas_conditions(self, simulations: List[Dict[str, Any]]) -> List[str]:
        """Analyze gas conditions across simulations"""
        conditions = []
        
        avg_gas_price = sum(sim.get('gas_price_gwei', 0) for sim in simulations) / len(simulations)
        
        if avg_gas_price > 50:
            conditions.append("high_gas_price")
        elif avg_gas_price < 10:
            conditions.append("low_gas_price")
        else:
            conditions.append("moderate_gas_price")
        
        # Check for gas price volatility
        gas_prices = [sim.get('gas_price_gwei', 0) for sim in simulations]
        if max(gas_prices) - min(gas_prices) > 20:
            conditions.append("volatile_gas")
        
        return conditions
    
    async def _get_asi_one_profit_analysis(
        self, 
        simulations: List[Dict[str, Any]], 
        metta_results: Dict[str, List[str]], 
        user_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Use ASI:One API for advanced profit analysis"""
        
        prompt = f"""
        Analyze profit optimization opportunities for DeFi trading:
        
        Simulations: {json.dumps(simulations[:3], indent=2)}  # Limit for token efficiency
        
        MeTTa Knowledge Insights: {json.dumps(metta_results, indent=2)}
        
        User Risk Tolerance: {user_preferences.get('risk_tolerance', 'balanced')}
        
        Provide analysis in JSON format with:
        - market_opportunity_assessment: string
        - optimal_profit_strategy: string
        - risk_reward_analysis: object
        - arbitrage_opportunities: array
        - timing_recommendations: string
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
                            "content": "You are an expert DeFi profit optimization analyst. Focus on maximizing returns while managing risks."
                        },
                        {
                            "role": "user",
                            "content": prompt
                        }
                    ],
                    "temperature": 0.4,
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
    
    def _fallback_profit_analysis(
        self, 
        simulations: List[Dict[str, Any]], 
        metta_results: Dict[str, List[str]]
    ) -> Dict[str, Any]:
        """Fallback profit analysis when ASI:One is not available"""
        
        max_profit = max(float(sim.get('estimated_output_usd', 0)) - float(sim.get('gas_cost_usd', 0)) 
                        for sim in simulations)
        
        return {
            "market_opportunity_assessment": "moderate" if max_profit > 100 else "limited",
            "optimal_profit_strategy": "maximize_net_returns",
            "risk_reward_analysis": {
                "expected_return": max_profit,
                "risk_level": "medium"
            },
            "arbitrage_opportunities": [],
            "timing_recommendations": "execute_when_profitable",
            "confidence_level": 0.75
        }
    
    def _calculate_enhanced_profit_metrics(
        self, 
        simulation: Dict[str, Any], 
        metta_results: Dict[str, List[str]], 
        asi_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate enhanced profit metrics using MeTTa insights"""
        
        # Base profit calculation
        estimated_output = float(simulation.get('estimated_output_usd', 0))
        gas_cost = float(simulation.get('gas_cost_usd', 0))
        base_profit = estimated_output - gas_cost
        
        # Risk adjustment based on MEV risk
        mev_risk = simulation.get('mev_risk_score', 0)
        risk_multiplier = 1.0 - (mev_risk / 200)  # Reduce profit by MEV risk
        
        # Market timing adjustment
        timing_score = self._calculate_timing_score(simulation, metta_results)
        timing_multiplier = 1.0 + (timing_score / 100)
        
        # Gas efficiency calculation
        gas_efficiency = estimated_output / max(gas_cost, 1)  # Output per dollar of gas
        
        # Arbitrage potential
        arbitrage_score = self._calculate_arbitrage_potential(simulation, asi_analysis)
        
        return {
            "enhanced_net_profit": base_profit * risk_multiplier * timing_multiplier,
            "profit_margin_percent": (base_profit / estimated_output) * 100 if estimated_output > 0 else 0,
            "risk_adjusted_profit": base_profit * risk_multiplier,
            "timing_score": timing_score,
            "gas_efficiency": gas_efficiency,
            "arbitrage_score": arbitrage_score
        }
    
    def _calculate_timing_score(
        self, 
        simulation: Dict[str, Any], 
        metta_results: Dict[str, List[str]]
    ) -> float:
        """Calculate market timing score"""
        
        score = 50  # Base score
        
        # Adjust based on block offset (timing)
        block_offset = simulation.get('block_offset', 0)
        if block_offset == 0:
            score += 20  # Bonus for immediate execution
        elif block_offset > 5:
            score -= 10  # Penalty for long delays
        
        # Adjust based on MeTTa insights
        if "fast_execution" in metta_results.get("profit_strategies", []):
            score += 15
        if "optimal_timing" in metta_results.get("speed_methods", []):
            score += 10
        
        return max(0, min(100, score))
    
    def _calculate_arbitrage_potential(
        self, 
        simulation: Dict[str, Any], 
        asi_analysis: Dict[str, Any]
    ) -> float:
        """Calculate arbitrage opportunity score"""
        
        # Check for arbitrage opportunities in ASI analysis
        arbitrage_ops = asi_analysis.get("arbitrage_opportunities", [])
        if arbitrage_ops:
            return 80  # High arbitrage potential
        
        # Check price impact for arbitrage potential
        price_impact = float(simulation.get('price_impact_percent', 0))
        if price_impact < 0.1:
            return 60  # Low slippage suggests arbitrage potential
        elif price_impact < 0.5:
            return 40  # Moderate potential
        else:
            return 20  # Limited potential
    
    def _select_most_profitable_simulation(
        self, 
        simulations: List[Dict[str, Any]], 
        user_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Select the most profitable simulation based on enhanced metrics"""
        
        risk_tolerance = user_preferences.get('risk_tolerance', 'balanced')
        
        if risk_tolerance == 'aggressive':
            # Prioritize raw profit potential
            return max(simulations, key=lambda s: s['enhanced_net_profit'])
        elif risk_tolerance == 'conservative':
            # Prioritize risk-adjusted profit
            return max(simulations, key=lambda s: s['risk_adjusted_profit'])
        else:
            # Balanced approach - consider multiple factors
            def balanced_score(sim):
                return (
                    sim['enhanced_net_profit'] * 0.4 +
                    sim['risk_adjusted_profit'] * 0.3 +
                    sim['timing_score'] * 0.2 +
                    sim['arbitrage_score'] * 0.1
                )
            
            return max(simulations, key=balanced_score)
    
    def _build_profit_reasoning(
        self, 
        best_sim: Dict[str, Any], 
        metta_results: Dict[str, List[str]], 
        asi_analysis: Dict[str, Any]
    ) -> str:
        """Build human-readable reasoning for profit recommendation"""
        
        reasoning_parts = []
        
        # Profit metrics
        net_profit = best_sim['enhanced_net_profit']
        profit_margin = best_sim['profit_margin_percent']
        
        reasoning_parts.append(f"Selected option {best_sim['id']} with net profit of ${net_profit:.2f} ({profit_margin:.1f}% margin)")
        
        # MeTTa insights
        if "profit_strategies" in metta_results and metta_results["profit_strategies"]:
            strategies = ", ".join(metta_results["profit_strategies"])
            reasoning_parts.append(f"MeTTa recommends strategies: {strategies}")
        
        # ASI:One insights
        if "optimal_profit_strategy" in asi_analysis:
            reasoning_parts.append(f"ASI:One suggests: {asi_analysis['optimal_profit_strategy']}")
        
        # Timing considerations
        if best_sim.get('timing_score', 0) > 70:
            reasoning_parts.append("Excellent market timing for execution")
        elif best_sim.get('timing_score', 0) < 40:
            reasoning_parts.append("Suboptimal timing but best available option")
        
        # Arbitrage potential
        if best_sim.get('arbitrage_score', 0) > 60:
            reasoning_parts.append("High arbitrage potential detected")
        
        return ". ".join(reasoning_parts) + "."
    
    def _identify_profit_concerns(
        self, 
        best_sim: Dict[str, Any], 
        metta_results: Dict[str, List[str]]
    ) -> List[str]:
        """Identify concerns with the profit recommendation"""
        
        concerns = []
        
        # Low profit margin concerns
        if best_sim['profit_margin_percent'] < 2:
            concerns.append("Low profit margin may not justify execution costs")
        
        # High MEV risk affecting profits
        if best_sim.get('mev_risk_score', 0) > 60:
            concerns.append("High MEV risk may reduce actual profits")
        
        # Gas efficiency concerns
        if best_sim.get('gas_efficiency', 0) < 10:
            concerns.append("Poor gas efficiency reduces net returns")
        
        # Market timing concerns
        if best_sim.get('timing_score', 0) < 30:
            concerns.append("Poor market timing may impact profitability")
        
        # Slippage concerns
        price_impact = float(best_sim.get('price_impact_percent', 0))
        if price_impact > 2:
            concerns.append(f"High slippage ({price_impact}%) may erode profits")
        
        return concerns
    
    async def _process_chat_query(self, query: str) -> Optional[str]:
        """Process chat queries related to profit optimization"""
        
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in ['profit', 'maximize', 'returns', 'yield']):
            if 'arbitrage' in query_lower:
                strategies = self.knowledge_rag.get_profit_strategy('arbitrage_opportunity')
                return f"For arbitrage opportunities, I recommend: {', '.join(strategies)}"
            elif 'high volatility' in query_lower:
                strategies = self.knowledge_rag.get_profit_strategy('high_volatility')
                return f"In high volatility markets: {', '.join(strategies)}"
            else:
                return "I can help optimize your profit potential. What specific market conditions are you facing?"
        
        return None
    
    async def _handle_profit_optimization_tool_call(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle profit optimization tool calls"""
        
        trade_data = parameters.get('trade_data', {})
        
        # Analyze profit factors
        profit_factors = []
        if trade_data.get('high_liquidity', False):
            profit_factors.append('low_slippage')
        if trade_data.get('volatile_market', False):
            profit_factors.append('high_volatility')
        
        # Query MeTTa for profit strategies
        strategies = []
        for factor in profit_factors:
            factor_strategies = self.knowledge_rag.get_profit_strategy(factor)
            strategies.extend(factor_strategies)
        
        return {
            "profit_factors": profit_factors,
            "recommended_strategies": list(set(strategies)),
            "optimization_score": len(set(strategies)) * 15,
            "market_analysis": "Analyzed using MeTTa knowledge graph"
        }
    
    async def _handle_arbitrage_detection_tool_call(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle arbitrage detection tool calls"""
        
        price_data = parameters.get('price_data', {})
        
        # Simple arbitrage detection logic
        opportunities = []
        if 'prices' in price_data:
            prices = price_data['prices']
            if len(prices) > 1:
                min_price = min(prices)
                max_price = max(prices)
                spread = ((max_price - min_price) / min_price) * 100
                
                if spread > 1:  # >1% spread
                    opportunities.append({
                        "type": "price_arbitrage",
                        "spread_percent": spread,
                        "profit_potential": "high" if spread > 3 else "medium"
                    })
        
        return {
            "arbitrage_opportunities": opportunities,
            "total_opportunities": len(opportunities),
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
    
    async def start_agent(self):
        """Start the enhanced profit agent"""
        await self.agent.run()

# Global instance for import
enhanced_profit_agent = EnhancedProfitAgent()
