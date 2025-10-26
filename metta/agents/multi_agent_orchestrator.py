"""
Multi-Agent Orchestrator - Coordinates all specialized agents for consensus decision-making
Uses ASI (Fetch.ai) uAgent framework to manage agent communication and MeTTa reasoning
"""

from uagents import Agent, Context, Model, Bureau
from typing import Dict, List, Any, Optional
import asyncio
import json
import uuid
from datetime import datetime

# Import all specialized agents
from .risk_agent import RiskAssessmentAgent
from .market_intelligence_agent import MarketIntelligenceAgent
from .liquidity_agent import LiquidityOptimizationAgent
from .gas_agent import GasOptimizationAgent
from .arbitrage_agent import ArbitrageDetectionAgent
from .consensus_agent import ConsensusAgent
from .communication_protocol import AgentCommunicationProtocol

class AnalysisRequest(Model):
    session_id: str
    simulation_data: Dict[str, Any]
    user_preferences: Dict[str, Any]
    token_pair: str
    trade_size: float
    chains: List[str]

class AnalysisResponse(Model):
    session_id: str
    consensus_decision: Dict[str, Any]
    agent_analyses: Dict[str, Any]
    execution_plan: Dict[str, Any]

class MultiAgentOrchestrator:
    def __init__(self, orchestrator_port: int = 8100):
        """Initialize the multi-agent orchestrator"""
        
        self.orchestrator = Agent(
            name="multi_agent_orchestrator",
            seed="orchestrator_seed_99999",
            port=orchestrator_port,
            endpoint=[f"http://localhost:{orchestrator_port}/submit"]
        )
        
        # Initialize all specialized agents
        self.risk_agent = RiskAssessmentAgent()
        self.market_agent = MarketIntelligenceAgent()
        self.liquidity_agent = LiquidityOptimizationAgent()
        self.gas_agent = GasOptimizationAgent()
        self.arbitrage_agent = ArbitrageDetectionAgent()
        self.consensus_agent = ConsensusAgent()
        
        # Initialize communication protocol
        self.communication_protocol = AgentCommunicationProtocol()
        
        # Active analysis sessions
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Agent registry
        self.agent_registry = {
            "risk_agent": self.risk_agent,
            "market_intelligence_agent": self.market_agent,
            "liquidity_agent": self.liquidity_agent,
            "gas_agent": self.gas_agent,
            "arbitrage_agent": self.arbitrage_agent,
            "consensus_agent": self.consensus_agent
        }
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup message handlers for the orchestrator"""
        
        @self.orchestrator.on_message(model=AnalysisRequest)
        async def handle_analysis_request(ctx: Context, sender: str, msg: AnalysisRequest):
            """Handle incoming analysis requests"""
            
            try:
                ctx.logger.info(f"Starting multi-agent analysis for session {msg.session_id}")
                
                # Initialize session
                await self._initialize_session(msg.session_id, msg)
                
                # Coordinate multi-agent analysis
                result = await self._coordinate_multi_agent_analysis(ctx, msg)
                
                # Send response
                response = AnalysisResponse(
                    session_id=msg.session_id,
                    consensus_decision=result["consensus_decision"],
                    agent_analyses=result["agent_analyses"],
                    execution_plan=result["execution_plan"]
                )
                
                await ctx.send(sender, response)
                
                ctx.logger.info(f"Completed analysis for session {msg.session_id}")
                
            except Exception as e:
                ctx.logger.error(f"Analysis failed for session {msg.session_id}: {str(e)}")
        
        @self.orchestrator.on_event("startup")
        async def startup_handler(ctx: Context):
            ctx.logger.info("Multi-Agent Orchestrator started")
            
            # Register all agents with communication protocol
            for agent_id, agent in self.agent_registry.items():
                self.communication_protocol.register_agent(
                    agent_id, 
                    agent.__class__.__name__,
                    f"http://localhost:{agent.get_agent().port}/submit"
                )
        
        @self.orchestrator.on_interval(period=60.0)  # Every minute
        async def session_cleanup(ctx: Context):
            """Clean up expired sessions"""
            await self._cleanup_expired_sessions(ctx)
    
    async def _initialize_session(self, session_id: str, request: AnalysisRequest):
        """Initialize a new analysis session"""
        
        self.active_sessions[session_id] = {
            "session_id": session_id,
            "start_time": datetime.now(),
            "request": request,
            "agent_results": {},
            "status": "initialized",
            "current_phase": "agent_analysis"
        }
        
        # Start debate session in communication protocol
        await self.communication_protocol.start_debate_session(
            session_id, request.simulation_data
        )
    
    async def _coordinate_multi_agent_analysis(
        self, ctx: Context, request: AnalysisRequest
    ) -> Dict[str, Any]:
        """Coordinate analysis across all specialized agents"""
        
        session = self.active_sessions[request.session_id]
        session["status"] = "analyzing"
        
        # Phase 1: Parallel agent analysis
        ctx.logger.info("Phase 1: Running parallel agent analyses")
        agent_analyses = await self._run_parallel_agent_analyses(ctx, request)
        
        session["agent_results"] = agent_analyses
        session["current_phase"] = "debate"
        
        # Phase 2: Agent debate and discussion
        ctx.logger.info("Phase 2: Facilitating agent debate")
        debate_results = await self._facilitate_agent_debate(ctx, request, agent_analyses)
        
        session["current_phase"] = "consensus"
        
        # Phase 3: MeTTa consensus decision
        ctx.logger.info("Phase 3: Generating MeTTa consensus")
        consensus_decision = await self._generate_consensus_decision(
            ctx, request, agent_analyses, debate_results
        )
        
        session["current_phase"] = "execution_planning"
        
        # Phase 4: Execution planning
        ctx.logger.info("Phase 4: Creating execution plan")
        execution_plan = await self._create_execution_plan(
            ctx, request, consensus_decision, agent_analyses
        )
        
        session["status"] = "completed"
        session["completion_time"] = datetime.now()
        
        return {
            "consensus_decision": consensus_decision,
            "agent_analyses": agent_analyses,
            "execution_plan": execution_plan,
            "debate_summary": debate_results,
            "session_metadata": {
                "session_id": request.session_id,
                "duration": (session["completion_time"] - session["start_time"]).total_seconds(),
                "agents_participated": len(agent_analyses),
                "consensus_method": consensus_decision.get("consensus_method", "enhanced_metta_reasoning")
            }
        }
    
    async def _run_parallel_agent_analyses(
        self, ctx: Context, request: AnalysisRequest
    ) -> Dict[str, Any]:
        """Run all agent analyses in parallel"""
        
        # Prepare analysis tasks
        analysis_tasks = []
        
        # Risk Assessment Agent
        analysis_tasks.append(
            self._run_risk_analysis(request)
        )
        
        # Market Intelligence Agent
        analysis_tasks.append(
            self._run_market_analysis(request)
        )
        
        # Liquidity Optimization Agent
        analysis_tasks.append(
            self._run_liquidity_analysis(request)
        )
        
        # Gas Optimization Agent
        analysis_tasks.append(
            self._run_gas_analysis(request)
        )
        
        # Arbitrage Detection Agent
        analysis_tasks.append(
            self._run_arbitrage_analysis(request)
        )
        
        # Execute all analyses in parallel
        results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
        
        # Compile results
        agent_analyses = {}
        agent_names = ["risk_agent", "market_intelligence_agent", "liquidity_agent", "gas_agent", "arbitrage_agent"]
        
        for i, result in enumerate(results):
            agent_name = agent_names[i]
            
            if isinstance(result, Exception):
                ctx.logger.error(f"{agent_name} analysis failed: {str(result)}")
                agent_analyses[agent_name] = {"error": str(result), "status": "failed"}
            else:
                agent_analyses[agent_name] = result
                ctx.logger.info(f"{agent_name} analysis completed successfully")
        
        return agent_analyses
    
    async def _run_risk_analysis(self, request: AnalysisRequest) -> Dict[str, Any]:
        """Run risk assessment analysis"""
        
        return await self.risk_agent.analyze_comprehensive_risk(
            simulation_data=request.simulation_data,
            market_conditions={},  # Will be populated by market agent
            user_profile=request.user_preferences
        )
    
    async def _run_market_analysis(self, request: AnalysisRequest) -> Dict[str, Any]:
        """Run market intelligence analysis"""
        
        return await self.market_agent.analyze_market_intelligence(
            token_pair=request.token_pair,
            chains=request.chains,
            analysis_depth="comprehensive"
        )
    
    async def _run_liquidity_analysis(self, request: AnalysisRequest) -> Dict[str, Any]:
        """Run liquidity optimization analysis"""
        
        return await self.liquidity_agent.analyze_liquidity(
            token_pair=request.token_pair,
            trade_size=request.trade_size,
            chains=request.chains
        )
    
    async def _run_gas_analysis(self, request: AnalysisRequest) -> Dict[str, Any]:
        """Run gas optimization analysis"""
        
        transaction_types = ["token_swap"]  # Default, could be extracted from request
        urgency_level = request.user_preferences.get("urgency", "normal")
        
        return await self.gas_agent.analyze_gas_optimization(
            chains=request.chains,
            transaction_types=transaction_types,
            urgency_level=urgency_level
        )
    
    async def _run_arbitrage_analysis(self, request: AnalysisRequest) -> Dict[str, Any]:
        """Run arbitrage detection analysis"""
        
        token_pairs = [request.token_pair]
        min_profit_threshold = request.user_preferences.get("min_profit_threshold", 0.005)
        
        return await self.arbitrage_agent.detect_arbitrage(
            token_pairs=token_pairs,
            chains=request.chains,
            min_profit_threshold=min_profit_threshold
        )
    
    async def _facilitate_agent_debate(
        self, ctx: Context, request: AnalysisRequest, agent_analyses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Facilitate debate between agents"""
        
        session_id = request.session_id
        
        # Simulate agent debate (in a full implementation, this would involve actual message passing)
        debate_summary = {
            "debate_rounds": 3,
            "key_disagreements": self._identify_agent_disagreements(agent_analyses),
            "consensus_points": self._identify_consensus_points(agent_analyses),
            "debate_outcome": "agents_reached_understanding"
        }
        
        # Update communication protocol with debate results
        session_status = self.communication_protocol.get_session_status(session_id)
        if session_status:
            ctx.logger.info(f"Debate session status: {session_status['phase']}")
        
        return debate_summary
    
    def _identify_agent_disagreements(self, agent_analyses: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify key disagreements between agents"""
        
        disagreements = []
        
        # Compare risk vs profit priorities
        risk_assessment = agent_analyses.get("risk_agent", {})
        arbitrage_assessment = agent_analyses.get("arbitrage_agent", {})
        
        if (risk_assessment.get("risk_assessment", {}).get("overall_risk") == "high" and
            len(arbitrage_assessment.get("opportunities", [])) > 0):
            disagreements.append({
                "topic": "risk_vs_opportunity",
                "agents": ["risk_agent", "arbitrage_agent"],
                "description": "Risk agent identifies high risk while arbitrage agent sees opportunities"
            })
        
        # Compare gas optimization vs speed requirements
        gas_analysis = agent_analyses.get("gas_agent", {})
        liquidity_analysis = agent_analyses.get("liquidity_agent", {})
        
        gas_timing = gas_analysis.get("timing_recommendations", {}).get("recommendation", "")
        liquidity_complexity = liquidity_analysis.get("optimal_routing", {}).get("routing_complexity", {}).get("complexity_level", "")
        
        if "wait" in gas_timing.lower() and liquidity_complexity == "high":
            disagreements.append({
                "topic": "timing_vs_complexity",
                "agents": ["gas_agent", "liquidity_agent"],
                "description": "Gas agent suggests waiting while liquidity agent indicates complex routing needed"
            })
        
        return disagreements
    
    def _identify_consensus_points(self, agent_analyses: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify points where agents agree"""
        
        consensus_points = []
        
        # Check if multiple agents favor similar chains
        preferred_chains = {}
        
        for agent_name, analysis in agent_analyses.items():
            if "error" not in analysis:
                # Extract chain preferences (implementation would vary by agent)
                if "optimal_chains" in analysis:
                    for chain in analysis["optimal_chains"]:
                        chain_name = chain.get("chain", "")
                        if chain_name:
                            preferred_chains[chain_name] = preferred_chains.get(chain_name, 0) + 1
        
        # Find chains preferred by multiple agents
        for chain, count in preferred_chains.items():
            if count >= 2:
                consensus_points.append({
                    "topic": "chain_preference",
                    "agreement": f"Multiple agents favor {chain}",
                    "supporting_agents": count
                })
        
        return consensus_points
    
    async def _generate_consensus_decision(
        self, ctx: Context, request: AnalysisRequest, 
        agent_analyses: Dict[str, Any], debate_results: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate final consensus decision using MeTTa reasoning"""
        
        # Use enhanced consensus method
        consensus_decision = await self.consensus_agent.enhanced_consensus_decision(
            simulation_data=request.simulation_data,
            user_preferences=request.user_preferences,
            agent_analyses=agent_analyses
        )
        
        # Add debate context
        consensus_decision["debate_context"] = {
            "disagreements_resolved": len(debate_results.get("key_disagreements", [])),
            "consensus_points": len(debate_results.get("consensus_points", [])),
            "debate_rounds": debate_results.get("debate_rounds", 0)
        }
        
        return consensus_decision
    
    async def _create_execution_plan(
        self, ctx: Context, request: AnalysisRequest,
        consensus_decision: Dict[str, Any], agent_analyses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create detailed execution plan based on consensus decision"""
        
        recommended_scenario_id = consensus_decision.get("recommended_scenario_id", 0)
        scenarios = request.simulation_data.get("scenarios", [])
        
        if recommended_scenario_id < len(scenarios):
            recommended_scenario = scenarios[recommended_scenario_id]
        else:
            recommended_scenario = {}
        
        # Extract execution details from agent analyses
        liquidity_analysis = agent_analyses.get("liquidity_agent", {})
        gas_analysis = agent_analyses.get("gas_agent", {})
        
        execution_plan = {
            "execution_strategy": {
                "primary_chain": recommended_scenario.get("chain", "ethereum"),
                "execution_method": "single_chain",  # or "cross_chain" based on liquidity analysis
                "timing_strategy": gas_analysis.get("timing_recommendations", {}).get("recommendation", "execute_when_convenient"),
                "slippage_tolerance": consensus_decision.get("execution_recommendation", {}).get("suggested_slippage", 2.0)
            },
            "risk_management": {
                "mev_protection": recommended_scenario.get("mev_risk", 0) < 0.3,
                "monitoring_required": consensus_decision.get("execution_recommendation", {}).get("monitor_conditions", False),
                "fallback_options": self._generate_fallback_options(agent_analyses),
                "risk_limits": {
                    "max_slippage": 5.0,
                    "max_execution_time": 300,  # 5 minutes
                    "min_profit_threshold": request.user_preferences.get("min_profit_threshold", 0)
                }
            },
            "optimization_opportunities": {
                "gas_savings": gas_analysis.get("optimization_strategy", {}).get("estimated_savings", {}),
                "arbitrage_potential": agent_analyses.get("arbitrage_agent", {}).get("market_analysis", {}).get("arbitrage_potential", {}),
                "liquidity_routing": liquidity_analysis.get("optimal_routing", {})
            },
            "execution_timeline": self._create_execution_timeline(consensus_decision, agent_analyses),
            "success_metrics": {
                "target_profit": recommended_scenario.get("profit_usd", 0),
                "acceptable_loss": recommended_scenario.get("profit_usd", 0) * 0.1,  # 10% tolerance
                "execution_confidence": consensus_decision.get("confidence", 70)
            }
        }
        
        return execution_plan
    
    def _generate_fallback_options(self, agent_analyses: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate fallback execution options"""
        
        fallback_options = []
        
        # Gas-based fallback
        gas_analysis = agent_analyses.get("gas_agent", {})
        if gas_analysis.get("optimization_strategy", {}).get("cost_reduction_strategies"):
            fallback_options.append({
                "trigger": "high_gas_prices",
                "action": "switch_to_cheaper_chain",
                "details": "Use gas agent's alternative chain recommendations"
            })
        
        # Liquidity-based fallback
        liquidity_analysis = agent_analyses.get("liquidity_agent", {})
        if liquidity_analysis.get("execution_strategy", {}).get("fallback_options"):
            fallback_options.append({
                "trigger": "insufficient_liquidity",
                "action": "reduce_trade_size",
                "details": "Split trade according to liquidity agent recommendations"
            })
        
        # Risk-based fallback
        fallback_options.append({
            "trigger": "mev_risk_spike",
            "action": "delay_execution",
            "details": "Wait for better market conditions"
        })
        
        return fallback_options
    
    def _create_execution_timeline(
        self, consensus_decision: Dict[str, Any], agent_analyses: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Create execution timeline"""
        
        gas_analysis = agent_analyses.get("gas_agent", {})
        timing_rec = gas_analysis.get("timing_recommendations", {})
        
        timeline = {
            "immediate_actions": [],
            "pre_execution_checks": [],
            "execution_window": "flexible",
            "post_execution_monitoring": []
        }
        
        # Immediate actions
        if consensus_decision.get("execution_recommendation", {}).get("execute_immediately"):
            timeline["immediate_actions"].append("Execute trade immediately")
            timeline["execution_window"] = "immediate"
        else:
            timeline["immediate_actions"].append("Monitor market conditions")
        
        # Pre-execution checks
        timeline["pre_execution_checks"] = [
            "Verify gas prices are within acceptable range",
            "Confirm liquidity availability",
            "Check for MEV bot activity",
            "Validate slippage tolerance"
        ]
        
        # Execution window
        if timing_rec.get("recommendation") == "wait_for_optimal_window":
            timeline["execution_window"] = "next_optimal_window"
        elif timing_rec.get("recommendation") == "execute_now":
            timeline["execution_window"] = "immediate"
        
        # Post-execution monitoring
        timeline["post_execution_monitoring"] = [
            "Monitor transaction confirmation",
            "Verify execution price",
            "Check for any MEV attacks",
            "Validate final profit/loss"
        ]
        
        return timeline
    
    async def _cleanup_expired_sessions(self, ctx: Context):
        """Clean up expired analysis sessions"""
        
        current_time = datetime.now()
        expired_sessions = []
        
        for session_id, session in self.active_sessions.items():
            # Sessions expire after 1 hour
            if (current_time - session["start_time"]).total_seconds() > 3600:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del self.active_sessions[session_id]
            ctx.logger.info(f"Cleaned up expired session: {session_id}")
    
    # Public API methods
    
    async def analyze_trade_execution(
        self,
        simulation_data: Dict[str, Any],
        user_preferences: Dict[str, Any],
        token_pair: str = "ETH/USDC",
        trade_size: float = 1.0,
        chains: List[str] = None
    ) -> Dict[str, Any]:
        """
        Main entry point for multi-agent trade execution analysis
        
        Args:
            simulation_data: Results from simulation system
            user_preferences: User priority, risk tolerance, etc.
            token_pair: Trading pair
            trade_size: Size of trade
            chains: List of chains to consider
            
        Returns:
            Comprehensive analysis with consensus decision
        """
        
        if chains is None:
            chains = ["ethereum", "base", "optimism", "arbitrum", "polygon"]
        
        session_id = str(uuid.uuid4())
        
        request = AnalysisRequest(
            session_id=session_id,
            simulation_data=simulation_data,
            user_preferences=user_preferences,
            token_pair=token_pair,
            trade_size=trade_size,
            chains=chains
        )
        
        # Initialize session
        await self._initialize_session(session_id, request)
        
        # Run analysis
        result = await self._coordinate_multi_agent_analysis(None, request)
        
        return result
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an analysis session"""
        
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        return {
            "session_id": session_id,
            "status": session["status"],
            "current_phase": session["current_phase"],
            "start_time": session["start_time"].isoformat(),
            "agents_completed": len(session.get("agent_results", {}))
        }
    
    def create_bureau(self) -> Bureau:
        """Create a uAgents Bureau with all agents"""
        
        bureau = Bureau(port=8200, endpoint="http://localhost:8200/submit")
        
        # Add all agents to the bureau
        bureau.add(self.orchestrator)
        bureau.add(self.risk_agent.get_agent())
        bureau.add(self.market_agent.get_agent())
        bureau.add(self.liquidity_agent.get_agent())
        bureau.add(self.gas_agent.get_agent())
        bureau.add(self.arbitrage_agent.get_agent())
        bureau.add(self.consensus_agent.get_agent())
        bureau.add(self.communication_protocol.get_agent())
        
        return bureau
    
    def get_agent(self):
        """Return the orchestrator agent instance"""
        return self.orchestrator
