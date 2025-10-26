"""
Enhanced Multi-Agent Orchestrator - Coordinates all agents using ASI:One Chat Protocol and MeTTa reasoning
Integrates enhanced agents with MeTTa knowledge graphs for DeFi Payroll Manager
"""

from uagents import Agent, Context, Model, Bureau
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)
from hyperon import MeTTa
from typing import Dict, List, Any, Optional
import asyncio
import json
import uuid
from datetime import datetime
import os

# Import enhanced agents
from .enhanced_mev_agent import EnhancedMEVAgent
from .enhanced_profit_agent import EnhancedProfitAgent
from .enhanced_speed_agent import EnhancedSpeedAgent
from .transaction_agent import TransactionAgent
from .price_feed_agent import PriceFeedAgent
from .mempool_agent import MempoolAgent
from .user_data_agent import UserDataAgent
from .net_status_agent import NetStatusAgent
from .consensus_agent import ConsensusAgent
from .chat_protocol import (
    ASIChatProtocol, AnalysisRequest, AnalysisResponse, 
    ToolCallRequest, ToolCallResponse, ConsensusRequest
)
from .metta_knowledge_base import initialize_defi_knowledge_graph, DeFiMeTTaRAG

class PayrollAnalysisRequest(Model):
    session_id: str
    employee_data: List[Dict[str, Any]]
    payment_schedule: str
    total_amount_usd: float
    preferred_tokens: List[str]
    risk_tolerance: str
    urgency_level: str

class ComprehensiveAnalysisRequest(Model):
    session_id: str
    analysis_type: str  # "payroll", "trading", "comprehensive"
    simulation_data: Dict[str, Any]
    user_preferences: Dict[str, Any]
    context: Dict[str, Any]

class EnhancedMultiAgentOrchestrator:
    """
    Enhanced Multi-Agent Orchestrator with ASI:One Chat Protocol and MeTTa reasoning
    
    Features:
    - Coordinates enhanced MEV, Profit, and Speed agents
    - Manages tool agents for frontend API integration
    - Uses MeTTa knowledge graphs for consensus decisions
    - Implements ASI:One chat protocol for communication
    - Specialized for DeFi Payroll Manager use case
    """
    
    def __init__(self, orchestrator_port: int = 8000):
        # Initialize main orchestrator agent
        self.orchestrator = Agent(
            name="enhanced_orchestrator",
            seed="enhanced_orchestrator_seed_12345",
            port=orchestrator_port,
            endpoint=[f"http://localhost:{orchestrator_port}/submit"]
        )
        
        self.orchestrator_id = "enhanced_orchestrator"
        self.name = "Enhanced Multi-Agent Orchestrator"
        
        # Initialize MeTTa knowledge graph
        self.metta = MeTTa()
        initialize_defi_knowledge_graph(self.metta)
        self.knowledge_rag = DeFiMeTTaRAG(self.metta)
        
        # Initialize ASI:One chat protocol
        self.chat_protocol = ASIChatProtocol(coordinator_port=orchestrator_port)
        
        # Initialize all enhanced agents
        self.core_agents = {
            "mev_agent": EnhancedMEVAgent(agent_port=8001),
            "profit_agent": EnhancedProfitAgent(agent_port=8002),
            "speed_agent": EnhancedSpeedAgent(agent_port=8003),
            "consensus_agent": ConsensusAgent()
        }
        
        # Initialize tool agents
        self.tool_agents = {
            "transaction_agent": TransactionAgent(agent_port=8010),
            "price_feed_agent": PriceFeedAgent(agent_port=8011),
            "mempool_agent": MempoolAgent(agent_port=8012),
            "user_data_agent": UserDataAgent(agent_port=8013),
            "net_status_agent": NetStatusAgent(agent_port=8014)
        }
        
        # Session management
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.analysis_results: Dict[str, Dict[str, Any]] = {}
        
        # Setup orchestrator handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup orchestrator event handlers and message protocols"""
        
        @self.orchestrator.on_event("startup")
        async def startup_handler(ctx: Context):
            ctx.logger.info(f"Enhanced Multi-Agent Orchestrator started: {ctx.agent.address}")
            ctx.logger.info("Initializing enhanced agent ecosystem...")
            
            # Register orchestrator with chat protocol
            self.chat_protocol.register_agent(
                agent_id=self.orchestrator_id,
                agent_address=ctx.agent.address,
                agent_type="orchestrator",
                capabilities=["coordination", "consensus", "payroll_analysis", "trading_analysis"]
            )
            
            ctx.logger.info("Enhanced orchestrator ready for multi-agent coordination")
        
        # Comprehensive Analysis Request Handler
        @self.orchestrator.on_message(model=ComprehensiveAnalysisRequest)
        async def handle_comprehensive_analysis(ctx: Context, sender: str, msg: ComprehensiveAnalysisRequest):
            """Handle comprehensive analysis requests"""
            
            ctx.logger.info(f"Received comprehensive analysis request: {msg.analysis_type} for session {msg.session_id}")
            
            try:
                if msg.analysis_type == "payroll":
                    result = await self._orchestrate_payroll_analysis(msg, ctx)
                elif msg.analysis_type == "trading":
                    result = await self._orchestrate_trading_analysis(msg, ctx)
                else:
                    result = await self._orchestrate_comprehensive_analysis(msg, ctx)
                
                # Send result back to requester
                response = AnalysisResponse(
                    session_id=msg.session_id,
                    agent_id=self.orchestrator_id,
                    agent_type="orchestrator",
                    analysis=result,
                    confidence=result.get("confidence", 0.8),
                    timestamp=datetime.utcnow().isoformat()
                )
                
                await ctx.send(sender, response)
                
            except Exception as e:
                ctx.logger.error(f"Comprehensive analysis failed: {str(e)}")
        
        # Payroll Analysis Request Handler
        @self.orchestrator.on_message(model=PayrollAnalysisRequest)
        async def handle_payroll_analysis(ctx: Context, sender: str, msg: PayrollAnalysisRequest):
            """Handle specialized payroll analysis requests"""
            
            ctx.logger.info(f"Received payroll analysis request for session {msg.session_id}")
            
            try:
                result = await self._orchestrate_payroll_optimization(msg, ctx)
                
                response = AnalysisResponse(
                    session_id=msg.session_id,
                    agent_id=self.orchestrator_id,
                    agent_type="payroll_orchestrator",
                    analysis=result,
                    confidence=result.get("confidence", 0.85),
                    timestamp=datetime.utcnow().isoformat()
                )
                
                await ctx.send(sender, response)
                
            except Exception as e:
                ctx.logger.error(f"Payroll analysis failed: {str(e)}")
        
        # Chat Message Handler
        @self.orchestrator.on_message(model=ChatMessage)
        async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
            """Handle ASI:One chat messages"""
            
            for item in msg.content:
                if isinstance(item, TextContent):
                    ctx.logger.info(f"Received chat message: {item.text}")
                    
                    # Process chat content and coordinate agents
                    response_text = await self._process_orchestrator_chat(item.text, msg.session_id if hasattr(msg, 'session_id') else 'default')
                    
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
        
        # Tool Call Request Handler
        @self.orchestrator.on_message(model=ToolCallRequest)
        async def handle_tool_call_request(ctx: Context, sender: str, msg: ToolCallRequest):
            """Handle tool call requests and route to appropriate agents"""
            
            ctx.logger.info(f"Routing tool call: {msg.tool_name}")
            
            try:
                result = await self._route_tool_call(msg)
                
                response = ToolCallResponse(
                    session_id=msg.session_id,
                    call_id=msg.call_id,
                    tool_name=msg.tool_name,
                    result=result,
                    success="error" not in result
                )
                
                await ctx.send(sender, response)
                
            except Exception as e:
                error_response = ToolCallResponse(
                    session_id=msg.session_id,
                    call_id=msg.call_id,
                    tool_name=msg.tool_name,
                    result={"error": str(e)},
                    success=False
                )
                
                await ctx.send(sender, error_response)
    
    async def _orchestrate_payroll_analysis(self, request: ComprehensiveAnalysisRequest, ctx: Context) -> Dict[str, Any]:
        """Orchestrate payroll-specific analysis using enhanced agents"""
        
        session_id = request.session_id
        simulation_data = request.simulation_data
        user_preferences = request.user_preferences
        
        # Initialize session
        self.active_sessions[session_id] = {
            "type": "payroll_analysis",
            "start_time": datetime.utcnow(),
            "status": "analyzing",
            "agents_involved": ["mev_agent", "profit_agent", "speed_agent", "transaction_agent"]
        }
        
        # Step 1: Get payroll-specific insights from MeTTa
        payroll_context = {
            "mev_factors": ["batch_transactions", "delayed_execution"],
            "profit_factors": ["low_slippage", "gas_optimization"],
            "speed_factors": ["scheduled_execution"],
            "tool_usage": ["batch_transactions", "gas_optimization"]
        }
        
        metta_insights = self.knowledge_rag.query_complex_scenario(payroll_context)
        
        # Step 2: Request analysis from core agents
        analysis_requests = []
        
        # MEV analysis for batch payroll security
        mev_request = AnalysisRequest(
            session_id=session_id,
            simulations=simulation_data.get("simulations", []),
            user_preferences={**user_preferences, "priority": "safety"},
            analysis_type="mev",
            requester_id=self.orchestrator_id
        )
        analysis_requests.append(("mev_agent", mev_request))
        
        # Profit analysis for cost optimization
        profit_request = AnalysisRequest(
            session_id=session_id,
            simulations=simulation_data.get("simulations", []),
            user_preferences={**user_preferences, "priority": "cost_efficiency"},
            analysis_type="profit",
            requester_id=self.orchestrator_id
        )
        analysis_requests.append(("profit_agent", profit_request))
        
        # Speed analysis for payroll timing
        speed_request = AnalysisRequest(
            session_id=session_id,
            simulations=simulation_data.get("simulations", []),
            user_preferences={**user_preferences, "priority": "reliability"},
            analysis_type="speed",
            requester_id=self.orchestrator_id
        )
        analysis_requests.append(("speed_agent", speed_request))
        
        # Collect agent analyses
        agent_analyses = {}
        for agent_name, analysis_request in analysis_requests:
            try:
                # In a real implementation, this would send messages to agents
                # For now, we'll simulate the analysis
                agent_analyses[agent_name] = await self._simulate_agent_analysis(agent_name, analysis_request)
            except Exception as e:
                ctx.logger.error(f"Analysis failed for {agent_name}: {str(e)}")
                agent_analyses[agent_name] = {"error": str(e)}
        
        # Step 3: Generate consensus using MeTTa reasoning
        consensus_result = await self._generate_payroll_consensus(agent_analyses, metta_insights, user_preferences)
        
        # Step 4: Create execution plan
        execution_plan = await self._create_payroll_execution_plan(consensus_result, simulation_data)
        
        # Update session status
        self.active_sessions[session_id]["status"] = "completed"
        self.active_sessions[session_id]["end_time"] = datetime.utcnow()
        
        return {
            "analysis_type": "payroll_optimization",
            "session_id": session_id,
            "metta_insights": metta_insights,
            "agent_analyses": agent_analyses,
            "consensus_decision": consensus_result,
            "execution_plan": execution_plan,
            "payroll_recommendations": self._generate_payroll_recommendations(consensus_result),
            "confidence": consensus_result.get("confidence_score", 80) / 100,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _orchestrate_trading_analysis(self, request: ComprehensiveAnalysisRequest, ctx: Context) -> Dict[str, Any]:
        """Orchestrate general trading analysis"""
        
        session_id = request.session_id
        
        # Standard multi-agent trading analysis
        trading_context = {
            "mev_factors": ["immediate_execution", "sandwich_bots_detected"],
            "profit_factors": ["arbitrage_opportunity", "high_volatility"],
            "speed_factors": ["time_sensitive"],
            "tool_usage": ["price_volatility_high", "mempool_congested"]
        }
        
        metta_insights = self.knowledge_rag.query_complex_scenario(trading_context)
        
        # Get real-time market data
        market_data = await self._gather_market_intelligence(request.context)
        
        # Coordinate agent analyses
        agent_analyses = await self._coordinate_trading_agents(session_id, request.simulation_data, request.user_preferences)
        
        # Generate trading consensus
        consensus_result = await self._generate_trading_consensus(agent_analyses, metta_insights, market_data)
        
        return {
            "analysis_type": "trading_optimization",
            "session_id": session_id,
            "market_intelligence": market_data,
            "agent_analyses": agent_analyses,
            "consensus_decision": consensus_result,
            "trading_recommendations": self._generate_trading_recommendations(consensus_result),
            "confidence": consensus_result.get("confidence_score", 75) / 100,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _orchestrate_comprehensive_analysis(self, request: ComprehensiveAnalysisRequest, ctx: Context) -> Dict[str, Any]:
        """Orchestrate comprehensive analysis combining all capabilities"""
        
        # Combine payroll and trading analysis
        payroll_analysis = await self._orchestrate_payroll_analysis(request, ctx)
        trading_analysis = await self._orchestrate_trading_analysis(request, ctx)
        
        # Meta-analysis using MeTTa
        comprehensive_insights = self.knowledge_rag.query_complex_scenario({
            "mev_factors": ["comprehensive_protection"],
            "profit_factors": ["balanced_optimization"],
            "speed_factors": ["optimal_timing"],
            "consensus_rules": ["conflicting_recommendations"]
        })
        
        return {
            "analysis_type": "comprehensive",
            "session_id": request.session_id,
            "payroll_analysis": payroll_analysis,
            "trading_analysis": trading_analysis,
            "comprehensive_insights": comprehensive_insights,
            "unified_recommendations": self._generate_unified_recommendations(payroll_analysis, trading_analysis),
            "confidence": (payroll_analysis.get("confidence", 0.8) + trading_analysis.get("confidence", 0.75)) / 2,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def _simulate_agent_analysis(self, agent_name: str, request: AnalysisRequest) -> Dict[str, Any]:
        """Simulate agent analysis (would be replaced with actual agent communication)"""
        
        # This is a simplified simulation - in production, this would send actual messages to agents
        simulations = request.simulations
        
        if agent_name == "mev_agent":
            return {
                "recommended_id": 1,
                "score": 85,
                "reasoning": "Enhanced MEV protection through delayed execution and private mempool usage",
                "concerns": ["Moderate wait time for safety"],
                "agent": "Enhanced_MEV_Protection",
                "mev_metrics": {
                    "risk_level": "low",
                    "protection_strategy": "delayed_execution",
                    "safety_score": 85
                }
            }
        elif agent_name == "profit_agent":
            return {
                "recommended_id": 2,
                "score": 78,
                "reasoning": "Optimized for cost efficiency with batch processing benefits",
                "concerns": ["Slightly lower immediate returns"],
                "agent": "Enhanced_Profit_Maximizer",
                "profit_metrics": {
                    "net_profit_usd": 1250.50,
                    "profit_margin_percent": 2.8,
                    "gas_efficiency_ratio": 15.2
                }
            }
        elif agent_name == "speed_agent":
            return {
                "recommended_id": 1,
                "score": 72,
                "reasoning": "Balanced execution timing for payroll reliability",
                "concerns": ["Not immediate execution"],
                "agent": "Enhanced_Speed_Optimizer",
                "speed_metrics": {
                    "execution_time_seconds": 180,
                    "urgency_level": "medium",
                    "timing_optimization": 72
                }
            }
        
        return {"error": f"Unknown agent: {agent_name}"}
    
    async def _generate_payroll_consensus(self, agent_analyses: Dict[str, Any], metta_insights: Dict[str, Any], user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Generate consensus decision for payroll operations"""
        
        # Analyze agent recommendations
        recommendations = {}
        confidence_scores = []
        
        for agent_name, analysis in agent_analyses.items():
            if "error" not in analysis:
                recommendations[agent_name] = analysis.get("recommended_id", 0)
                confidence_scores.append(analysis.get("score", 0))
        
        # Apply MeTTa reasoning for payroll-specific consensus
        payroll_priority = user_preferences.get("payroll_priority", "safety")
        
        if payroll_priority == "safety":
            # Prioritize MEV agent recommendation
            final_recommendation = recommendations.get("mev_agent", 1)
            reasoning = "Prioritized safety for payroll operations"
        elif payroll_priority == "cost":
            # Prioritize profit agent recommendation
            final_recommendation = recommendations.get("profit_agent", 1)
            reasoning = "Prioritized cost efficiency for payroll operations"
        else:
            # Balanced approach
            final_recommendation = max(set(recommendations.values()), key=list(recommendations.values()).count)
            reasoning = "Balanced consensus for reliable payroll execution"
        
        avg_confidence = sum(confidence_scores) / len(confidence_scores) if confidence_scores else 70
        
        return {
            "final_recommendation": final_recommendation,
            "consensus_reasoning": reasoning,
            "confidence_score": avg_confidence,
            "agent_votes": recommendations,
            "metta_factors": metta_insights,
            "payroll_optimizations": {
                "batch_processing": True,
                "mev_protection": True,
                "cost_optimization": True,
                "timing_reliability": True
            }
        }
    
    async def _create_payroll_execution_plan(self, consensus: Dict[str, Any], simulation_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create detailed execution plan for payroll operations"""
        
        recommended_sim = None
        simulations = simulation_data.get("simulations", [])
        
        for sim in simulations:
            if sim.get("id") == consensus.get("final_recommendation"):
                recommended_sim = sim
                break
        
        if not recommended_sim:
            recommended_sim = simulations[0] if simulations else {}
        
        return {
            "execution_strategy": "batch_payroll_processing",
            "recommended_simulation": recommended_sim,
            "batch_configuration": {
                "max_batch_size": 5,  # Based on container stability analysis
                "batch_delay_seconds": 2,
                "fallback_to_individual": True
            },
            "safety_measures": {
                "avoid_deployer_address": True,  # Based on container crash analysis
                "gas_limit": 25000,  # Fixed gas limit for stability
                "transaction_type": 0,  # Legacy type for compatibility
                "timeout_seconds": 3
            },
            "monitoring": {
                "track_execution": True,
                "health_checks": True,
                "rollback_capability": True
            },
            "estimated_completion_time": recommended_sim.get("block_offset", 1) * 12,
            "total_cost_estimate": recommended_sim.get("gas_cost_usd", 0)
        }
    
    def _generate_payroll_recommendations(self, consensus: Dict[str, Any]) -> List[str]:
        """Generate specific recommendations for payroll operations"""
        
        recommendations = []
        
        # Based on DeFi Payroll Manager use case
        recommendations.extend([
            "Use netted transaction layer for zero MEV risk",
            "Batch employee payments for gas optimization",
            "Schedule payments during off-peak hours",
            "Implement CSV upload for bulk employee data",
            "Generate invoices automatically post-execution"
        ])
        
        # Based on consensus decision
        if consensus.get("payroll_optimizations", {}).get("mev_protection"):
            recommendations.append("Enhanced MEV protection enabled for payroll security")
        
        if consensus.get("payroll_optimizations", {}).get("cost_optimization"):
            recommendations.append("Cost optimization strategies applied for budget efficiency")
        
        return recommendations
    
    async def _coordinate_trading_agents(self, session_id: str, simulation_data: Dict[str, Any], user_preferences: Dict[str, Any]) -> Dict[str, Any]:
        """Coordinate agents for trading analysis"""
        
        # Simplified coordination - would use actual agent communication in production
        return {
            "mev_agent": await self._simulate_agent_analysis("mev_agent", AnalysisRequest(
                session_id=session_id,
                simulations=simulation_data.get("simulations", []),
                user_preferences=user_preferences,
                analysis_type="mev",
                requester_id=self.orchestrator_id
            )),
            "profit_agent": await self._simulate_agent_analysis("profit_agent", AnalysisRequest(
                session_id=session_id,
                simulations=simulation_data.get("simulations", []),
                user_preferences=user_preferences,
                analysis_type="profit",
                requester_id=self.orchestrator_id
            )),
            "speed_agent": await self._simulate_agent_analysis("speed_agent", AnalysisRequest(
                session_id=session_id,
                simulations=simulation_data.get("simulations", []),
                user_preferences=user_preferences,
                analysis_type="speed",
                requester_id=self.orchestrator_id
            ))
        }
    
    async def _gather_market_intelligence(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Gather market intelligence using tool agents"""
        
        # Simulate market data gathering
        return {
            "price_data": {
                "ETH/USDC": {"price": 2500, "volatility": "medium", "trend": "stable"},
                "BTC/USDC": {"price": 45000, "volatility": "low", "trend": "up"}
            },
            "mempool_status": {
                "congestion": "moderate",
                "gas_price_gwei": 25,
                "mev_activity": "low"
            },
            "network_health": {
                "status": "operational",
                "netting_efficiency": 65,
                "processing_capacity": "good"
            }
        }
    
    async def _generate_trading_consensus(self, agent_analyses: Dict[str, Any], metta_insights: Dict[str, Any], market_data: Dict[str, Any]) -> Dict[str, Any]:
        """Generate consensus for trading operations"""
        
        # Simplified consensus generation
        return {
            "final_recommendation": 1,
            "consensus_reasoning": "Balanced approach considering market conditions",
            "confidence_score": 78,
            "market_factors": market_data,
            "metta_factors": metta_insights
        }
    
    def _generate_trading_recommendations(self, consensus: Dict[str, Any]) -> List[str]:
        """Generate trading-specific recommendations"""
        
        return [
            "Monitor market volatility before execution",
            "Use limit orders for better price control",
            "Consider cross-chain arbitrage opportunities",
            "Implement slippage protection"
        ]
    
    def _generate_unified_recommendations(self, payroll_analysis: Dict[str, Any], trading_analysis: Dict[str, Any]) -> List[str]:
        """Generate unified recommendations combining payroll and trading insights"""
        
        unified = []
        
        # Combine recommendations from both analyses
        payroll_recs = payroll_analysis.get("payroll_recommendations", [])
        trading_recs = trading_analysis.get("trading_recommendations", [])
        
        unified.extend(payroll_recs[:3])  # Top 3 payroll recommendations
        unified.extend(trading_recs[:2])  # Top 2 trading recommendations
        
        # Add unified insights
        unified.extend([
            "Integrate payroll scheduling with market timing",
            "Use comprehensive risk management across all operations",
            "Leverage netted layer for both payroll and trading efficiency"
        ])
        
        return unified
    
    async def _route_tool_call(self, request: ToolCallRequest) -> Dict[str, Any]:
        """Route tool calls to appropriate agents"""
        
        tool_name = request.tool_name
        
        # Route based on tool name
        if tool_name in ["execute_transaction", "check_transaction_status", "batch_transactions"]:
            return await self.tool_agents["transaction_agent"]._execute_transaction(request.parameters)
        elif tool_name in ["get_price", "analyze_volatility", "detect_trends"]:
            return await self.tool_agents["price_feed_agent"]._get_price_data(request.parameters)
        elif tool_name in ["analyze_mempool", "detect_mev_bots"]:
            return await self.tool_agents["mempool_agent"]._analyze_mempool(request.parameters)
        elif tool_name in ["get_user_data", "get_transaction_history"]:
            return await self.tool_agents["user_data_agent"]._get_user_data(request.parameters)
        elif tool_name in ["get_net_status", "analyze_netting_performance"]:
            return await self.tool_agents["net_status_agent"]._get_net_status(request.parameters)
        else:
            return {"error": f"Unknown tool: {tool_name}"}
    
    async def _process_orchestrator_chat(self, message: str, session_id: str) -> str:
        """Process chat messages and coordinate appropriate responses"""
        
        message_lower = message.lower()
        
        if any(keyword in message_lower for keyword in ['payroll', 'employee', 'salary', 'batch payment']):
            return "I can orchestrate payroll analysis using enhanced MEV protection, cost optimization, and reliable timing. What payroll operation do you need help with?"
        
        elif any(keyword in message_lower for keyword in ['trade', 'swap', 'exchange']):
            return "I coordinate multi-agent trading analysis with real-time market intelligence. What trading decision needs analysis?"
        
        elif any(keyword in message_lower for keyword in ['analyze', 'recommend', 'suggest']):
            return "I orchestrate comprehensive analysis using MEV, Profit, and Speed agents with MeTTa reasoning. What type of analysis do you need?"
        
        else:
            return "I'm the Enhanced Multi-Agent Orchestrator. I coordinate specialized agents for DeFi operations including payroll management, trading optimization, and comprehensive analysis. How can I help?"
    
    def get_orchestrator_status(self) -> Dict[str, Any]:
        """Get current orchestrator status"""
        
        return {
            "orchestrator_id": self.orchestrator_id,
            "active_sessions": len(self.active_sessions),
            "core_agents": list(self.core_agents.keys()),
            "tool_agents": list(self.tool_agents.keys()),
            "metta_knowledge_loaded": True,
            "chat_protocol_active": True,
            "capabilities": [
                "payroll_analysis",
                "trading_optimization", 
                "comprehensive_coordination",
                "metta_reasoning",
                "asi_one_communication"
            ]
        }
    
    async def start_orchestrator(self):
        """Start the enhanced orchestrator and all agents"""
        
        # Start orchestrator
        await self.orchestrator.run()

# Global instance for import
enhanced_orchestrator = EnhancedMultiAgentOrchestrator()
