"""
ASI:One Chat Protocol - Enhanced inter-agent communication using Fetch.ai uAgent framework
Implements the official ASI:One chat protocol for autonomous agent coordination and debate
"""

from uagents import Agent, Context, Model, Protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)
from typing import Dict, List, Any, Optional, Callable
import json
import asyncio
import uuid
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from enum import Enum

class MessageType(Enum):
    ANALYSIS_REQUEST = "analysis_request"
    ANALYSIS_RESPONSE = "analysis_response"
    PROPOSAL = "proposal"
    COUNTER_PROPOSAL = "counter_proposal"
    SUPPORT = "support"
    OBJECTION = "objection"
    QUESTION = "question"
    ANSWER = "answer"
    CONSENSUS_REQUEST = "consensus_request"
    FINAL_DECISION = "final_decision"
    TOOL_CALL = "tool_call"
    TOOL_RESPONSE = "tool_response"

class DebatePhase(Enum):
    INITIALIZATION = "initialization"
    ANALYSIS_PHASE = "analysis_phase"
    PROPOSAL_PHASE = "proposal_phase"
    DEBATE_PHASE = "debate_phase"
    CONSENSUS_PHASE = "consensus_phase"
    DECISION_PHASE = "decision_phase"
    COMPLETED = "completed"

@dataclass
class AgentAnalysis:
    agent_id: str
    agent_type: str
    recommended_id: int
    score: float
    reasoning: str
    concerns: List[str]
    metrics: Dict[str, Any]
    timestamp: datetime

class AnalysisRequest(Model):
    session_id: str
    simulations: List[Dict[str, Any]]
    user_preferences: Dict[str, Any]
    analysis_type: str  # "mev", "profit", "speed", "comprehensive"
    requester_id: str

class AnalysisResponse(Model):
    session_id: str
    agent_id: str
    agent_type: str
    analysis: Dict[str, Any]
    confidence: float
    timestamp: str

class DebateMessage(Model):
    sender_id: str
    sender_type: str
    message_type: str
    content: Dict[str, Any]
    timestamp: str
    session_id: str
    message_id: str
    references: List[str] = []

class ConsensusRequest(Model):
    session_id: str
    debate_summary: Dict[str, Any]
    agent_positions: Dict[str, Any]
    simulation_data: Dict[str, Any]

class ToolCallRequest(Model):
    session_id: str
    tool_name: str
    parameters: Dict[str, Any]
    requester_id: str
    call_id: str

class ToolCallResponse(Model):
    session_id: str
    call_id: str
    tool_name: str
    result: Dict[str, Any]
    success: bool
    error: Optional[str] = None

class ASIChatProtocol:
    def __init__(self, coordinator_port: int = 8000):
        """Initialize ASI:One Chat Protocol for agent communication"""
        
        self.coordinator = Agent(
            name="asi_chat_coordinator",
            seed="asi_chat_coord_seed_24680",
            port=coordinator_port,
            endpoint=[f"http://localhost:{coordinator_port}/submit"]
        )
        
        # Initialize official ASI:One chat protocol
        self.chat_protocol = Protocol(spec=chat_protocol_spec)
        
        # Active debate sessions
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        
        # Registered agents with their addresses
        self.registered_agents: Dict[str, Dict[str, Any]] = {}
        
        # Message history for each session
        self.message_history: Dict[str, List[ChatMessage]] = {}
        
        # Analysis results storage
        self.analysis_results: Dict[str, Dict[str, Any]] = {}
        
        # Tool call tracking
        self.pending_tool_calls: Dict[str, ToolCallRequest] = {}
        
        self._setup_protocols()
        self._setup_handlers()
    
    def _setup_protocols(self):
        """Setup ASI:One chat protocols and custom debate protocols"""
        
        # ASI:One Chat Message Handler
        @self.chat_protocol.on_message(ChatMessage)
        async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
            """Handle official ASI:One chat messages"""
            
            for item in msg.content:
                if isinstance(item, TextContent):
                    ctx.logger.info(f"Received chat message from {sender}: {item.text}")
                    
                    # Store message in history
                    session_id = getattr(msg, 'session_id', 'default')
                    if session_id not in self.message_history:
                        self.message_history[session_id] = []
                    self.message_history[session_id].append(msg)
                    
                    # Send acknowledgment
                    ack = ChatAcknowledgement(
                        timestamp=datetime.utcnow(),
                        acknowledged_msg_id=msg.msg_id
                    )
                    await ctx.send(sender, ack)
                    
                    # Process message content for analysis requests
                    await self._process_chat_content(ctx, sender, item.text, session_id)
        
        # Chat Acknowledgment Handler
        @self.chat_protocol.on_message(ChatAcknowledgement)
        async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
            """Handle message acknowledgments"""
            ctx.logger.info(f"Received acknowledgement from {sender} for message: {msg.acknowledged_msg_id}")
        
        # Analysis Request Handler
        @self.chat_protocol.on_message(AnalysisRequest)
        async def handle_analysis_request(ctx: Context, sender: str, msg: AnalysisRequest):
            """Handle analysis requests from agents"""
            
            ctx.logger.info(f"Received analysis request from {sender} for session {msg.session_id}")
            
            # Initialize session if not exists
            if msg.session_id not in self.active_sessions:
                self.active_sessions[msg.session_id] = {
                    "phase": DebatePhase.ANALYSIS_PHASE,
                    "participants": [],
                    "analyses": {},
                    "start_time": datetime.utcnow(),
                    "simulation_data": msg.simulations
                }
            
            # Add requester to participants
            if sender not in self.active_sessions[msg.session_id]["participants"]:
                self.active_sessions[msg.session_id]["participants"].append(sender)
            
            # Broadcast analysis request to relevant agents
            await self._broadcast_analysis_request(ctx, msg)
        
        # Analysis Response Handler
        @self.chat_protocol.on_message(AnalysisResponse)
        async def handle_analysis_response(ctx: Context, sender: str, msg: AnalysisResponse):
            """Handle analysis responses from agents"""
            
            ctx.logger.info(f"Received analysis from {msg.agent_type} for session {msg.session_id}")
            
            # Store analysis result
            if msg.session_id not in self.analysis_results:
                self.analysis_results[msg.session_id] = {}
            
            self.analysis_results[msg.session_id][msg.agent_type] = {
                "analysis": msg.analysis,
                "confidence": msg.confidence,
                "timestamp": msg.timestamp,
                "agent_id": msg.agent_id
            }
            
            # Check if we have enough analyses to proceed to debate
            await self._check_analysis_completion(ctx, msg.session_id)
        
        # Tool Call Handlers
        @self.chat_protocol.on_message(ToolCallRequest)
        async def handle_tool_call_request(ctx: Context, sender: str, msg: ToolCallRequest):
            """Handle tool call requests"""
            
            ctx.logger.info(f"Tool call request: {msg.tool_name} from {sender}")
            
            # Store pending tool call
            self.pending_tool_calls[msg.call_id] = msg
            
            # Route to appropriate tool agent
            await self._route_tool_call(ctx, msg)
        
        @self.chat_protocol.on_message(ToolCallResponse)
        async def handle_tool_call_response(ctx: Context, sender: str, msg: ToolCallResponse):
            """Handle tool call responses"""
            
            ctx.logger.info(f"Tool call response: {msg.tool_name} - {'Success' if msg.success else 'Failed'}")
            
            # Remove from pending calls
            if msg.call_id in self.pending_tool_calls:
                original_request = self.pending_tool_calls.pop(msg.call_id)
                
                # Send response back to original requester
                await self._send_tool_response_to_requester(ctx, original_request, msg)
    
    def _setup_handlers(self):
        """Setup coordinator event handlers"""
        
        @self.coordinator.on_event("startup")
        async def startup_handler(ctx: Context):
            ctx.logger.info(f"ASI Chat Protocol Coordinator started: {ctx.agent.address}")
            ctx.logger.info("Ready to coordinate multi-agent analysis and debate")
        
        # Include the chat protocol in coordinator
        self.coordinator.include(self.chat_protocol, publish_manifest=True)
    
    async def _process_chat_content(self, ctx: Context, sender: str, content: str, session_id: str):
        """Process chat message content for commands and analysis requests"""
        
        content_lower = content.lower()
        
        # Check for analysis requests
        if any(keyword in content_lower for keyword in ['analyze', 'recommend', 'suggest']):
            # Extract analysis type
            analysis_type = "comprehensive"
            if "mev" in content_lower:
                analysis_type = "mev"
            elif "profit" in content_lower:
                analysis_type = "profit"
            elif "speed" in content_lower:
                analysis_type = "speed"
            
            # Send analysis request
            analysis_req = AnalysisRequest(
                session_id=session_id,
                simulations=[],  # Would be populated from context
                user_preferences={"priority": analysis_type},
                analysis_type=analysis_type,
                requester_id=sender
            )
            
            await self._broadcast_analysis_request(ctx, analysis_req)
        
        # Check for tool calls
        elif any(keyword in content_lower for keyword in ['price', 'transaction', 'mempool', 'status']):
            await self._handle_tool_request_from_chat(ctx, sender, content, session_id)
    
    async def _broadcast_analysis_request(self, ctx: Context, request: AnalysisRequest):
        """Broadcast analysis request to relevant agents"""
        
        # Define agent addresses (would be populated from registry)
        target_agents = []
        
        if request.analysis_type in ["mev", "comprehensive"]:
            target_agents.append("mev_agent_address")
        if request.analysis_type in ["profit", "comprehensive"]:
            target_agents.append("profit_agent_address")
        if request.analysis_type in ["speed", "comprehensive"]:
            target_agents.append("speed_agent_address")
        
        # Broadcast to all target agents
        for agent_address in target_agents:
            if agent_address in self.registered_agents:
                await ctx.send(agent_address, request)
    
    async def _check_analysis_completion(self, ctx: Context, session_id: str):
        """Check if enough analyses are received to proceed to consensus"""
        
        if session_id not in self.analysis_results:
            return
        
        analyses = self.analysis_results[session_id]
        required_agents = ["mev_agent", "profit_agent", "speed_agent"]
        
        # Check if we have all required analyses
        if all(agent in analyses for agent in required_agents):
            # Move to consensus phase
            if session_id in self.active_sessions:
                self.active_sessions[session_id]["phase"] = DebatePhase.CONSENSUS_PHASE
            
            # Trigger consensus process
            await self._initiate_consensus(ctx, session_id)
    
    async def _initiate_consensus(self, ctx: Context, session_id: str):
        """Initiate consensus process using MeTTa reasoning"""
        
        analyses = self.analysis_results.get(session_id, {})
        
        # Create consensus request
        consensus_req = ConsensusRequest(
            session_id=session_id,
            debate_summary={"phase": "consensus_initiated"},
            agent_positions=analyses,
            simulation_data=self.active_sessions[session_id]["simulation_data"]
        )
        
        # Send to consensus agent (MeTTa reasoning agent)
        consensus_agent_address = "consensus_agent_address"
        if consensus_agent_address in self.registered_agents:
            await ctx.send(consensus_agent_address, consensus_req)
    
    async def _handle_tool_request_from_chat(self, ctx: Context, sender: str, content: str, session_id: str):
        """Handle tool requests extracted from chat messages"""
        
        content_lower = content.lower()
        call_id = str(uuid.uuid4())
        
        # Determine tool type and parameters
        if "price" in content_lower:
            tool_request = ToolCallRequest(
                session_id=session_id,
                tool_name="price_feed_agent",
                parameters={"query": content},
                requester_id=sender,
                call_id=call_id
            )
        elif "transaction" in content_lower:
            tool_request = ToolCallRequest(
                session_id=session_id,
                tool_name="transaction_agent",
                parameters={"query": content},
                requester_id=sender,
                call_id=call_id
            )
        elif "mempool" in content_lower:
            tool_request = ToolCallRequest(
                session_id=session_id,
                tool_name="mempool_agent",
                parameters={"query": content},
                requester_id=sender,
                call_id=call_id
            )
        else:
            return
        
        # Route tool call
        await self._route_tool_call(ctx, tool_request)
    
    async def _route_tool_call(self, ctx: Context, tool_request: ToolCallRequest):
        """Route tool call to appropriate agent"""
        
        tool_agent_mapping = {
            "price_feed_agent": "price_feed_agent_address",
            "transaction_agent": "transaction_agent_address",
            "mempool_agent": "mempool_agent_address",
            "user_data_agent": "user_data_agent_address",
            "net_status_agent": "net_status_agent_address"
        }
        
        agent_address = tool_agent_mapping.get(tool_request.tool_name)
        if agent_address and agent_address in self.registered_agents:
            await ctx.send(agent_address, tool_request)
    
    async def _send_tool_response_to_requester(self, ctx: Context, original_request: ToolCallRequest, response: ToolCallResponse):
        """Send tool response back to the original requester"""
        
        # Create chat message with tool response
        response_text = f"Tool '{response.tool_name}' result: {json.dumps(response.result, indent=2)}"
        
        chat_response = ChatMessage(
            timestamp=datetime.utcnow(),
            msg_id=uuid.uuid4(),
            content=[TextContent(type="text", text=response_text)]
        )
        
        await ctx.send(original_request.requester_id, chat_response)
    
    def register_agent(self, agent_id: str, agent_address: str, agent_type: str, capabilities: List[str]):
        """Register an agent with the chat protocol"""
        
        self.registered_agents[agent_address] = {
            "agent_id": agent_id,
            "agent_type": agent_type,
            "capabilities": capabilities,
            "registered_at": datetime.utcnow()
        }
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get status of an active session"""
        
        if session_id not in self.active_sessions:
            return None
        
        session = self.active_sessions[session_id]
        analyses = self.analysis_results.get(session_id, {})
        
        return {
            "session_id": session_id,
            "phase": session["phase"].value,
            "participants": session["participants"],
            "analyses_received": len(analyses),
            "start_time": session["start_time"].isoformat(),
            "message_count": len(self.message_history.get(session_id, [])),
            "pending_tool_calls": len([call for call in self.pending_tool_calls.values() if call.session_id == session_id])
        }
    
    async def start_coordinator(self):
        """Start the chat protocol coordinator"""
        await self.coordinator.run()

# Global instance for import
asi_chat_protocol = ASIChatProtocol()
