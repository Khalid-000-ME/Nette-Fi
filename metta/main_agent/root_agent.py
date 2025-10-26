#!/usr/bin/env python3
"""
Root Agent - ASI Chat Protocol Interface
Primary user interface that communicates with Agent 1 via ASI's Chat Protocol
"""

from datetime import datetime
from uuid import uuid4
from uagents import Agent, Protocol, Context
import asyncio
import json
from typing import Dict, Any, Optional

# Import the necessary components from the chat protocol
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

# Initialize Root Agent
root_agent = Agent(
    name="root_agent",
    port=8002,
    seed="root_agent_seed_789",
    endpoint=["http://localhost:8002/submit"]
)

# Store Agent 1's address (will be updated when Agent 1 starts)
agent_1_address = "agent1qfmr8cnzfc9mdcdc2ueg6erwh0s0rnwm2dazq99285ql8x47rlcdkavfr5e"

# Initialize the chat protocol
chat_proto = Protocol(spec=chat_protocol_spec)

# Session management
session_data = {
    "user_authenticated": False,
    "wallet_signature": None,
    "wallet_address": None,
    "pending_requests": {},
    "conversation_history": []
}

# Mock responses for when Agent 1 fails
MOCK_RESPONSES = {
    "execute_transactions": {
        "success": True,
        "message": "Mock: Transaction execution simulated successfully",
        "transaction_hashes": ["0x1234567890abcdef", "0xfedcba0987654321"],
        "gas_saved": "45000",
        "status": "completed"
    },
    "get_prices": {
        "success": True,
        "message": "Mock: Price data retrieved successfully",
        "prices": {
            "ETH": {"price": 3200.50, "change_24h": 2.5},
            "USDC": {"price": 1.00, "change_24h": 0.1},
            "MATIC": {"price": 0.85, "change_24h": -1.2}
        }
    },
    "get_balances": {
        "success": True,
        "message": "Mock: Balance data retrieved successfully",
        "balances": {
            "ETH": "2.5",
            "USDC": "1500.00",
            "MATIC": "850.25"
        },
        "total_value_usd": "9850.75"
    },
    "wallet_signature": {
        "success": True,
        "message": "Mock: Wallet signature processed successfully",
        "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
        "authenticated": True
    }
}

class RootAgentAPI:
    """API interface for Root Agent to handle HTTP requests"""
    
    def __init__(self, root_agent_instance):
        self.root_agent = root_agent_instance
        self.pending_responses = {}
    
    async def process_user_request(self, message: str, context: Dict = None) -> Dict[str, Any]:
        """
        Process user request and communicate with Agent 1
        Returns response in standardized format
        """
        print(f"🌟 Root Agent: Processing user request: {message}")
        
        # Store conversation
        session_data["conversation_history"].append({
            "timestamp": datetime.now().isoformat(),
            "role": "user",
            "message": message,
            "context": context or {}
        })
        
        # Determine request type and format JSON message for Agent 1
        request_type = self._classify_request(message)
        json_request = self._format_request_for_agent1(request_type, message, context)
        
        try:
            # Send request to Agent 1 via ASI Chat Protocol
            response = await self._send_to_agent1(json_request)
            
            if response and response.get("success"):
                return {
                    "success": True,
                    "response": response.get("message", "Request processed successfully"),
                    "data": response.get("data", {}),
                    "tool": response.get("tool", "Agent 1"),
                    "status": "success"
                }
            else:
                # Agent 1 failed, use mock response
                print("⚠️ Root Agent: Agent 1 failed, using mock response")
                mock_response = self._get_mock_response(request_type)
                return {
                    "success": True,
                    "response": f"Mock Response: {mock_response['message']}",
                    "data": mock_response,
                    "tool": "Mock Agent",
                    "status": "mock"
                }
                
        except Exception as e:
            print(f"❌ Root Agent: Error communicating with Agent 1: {e}")
            # Use mock response on error
            mock_response = self._get_mock_response(request_type)
            return {
                "success": True,
                "response": f"Mock Response (Error Fallback): {mock_response['message']}",
                "data": mock_response,
                "tool": "Mock Agent",
                "status": "mock_error"
            }
    
    def _classify_request(self, message: str) -> str:
        """Classify user request type"""
        message_lower = message.lower()
        
        if any(word in message_lower for word in ["execute", "transaction", "send", "transfer", "pay"]):
            return "execute_transactions"
        elif any(word in message_lower for word in ["price", "cost", "value", "rate"]):
            return "get_prices"
        elif any(word in message_lower for word in ["balance", "wallet", "funds", "tokens"]):
            return "get_balances"
        elif any(word in message_lower for word in ["signature", "sign", "authenticate", "login"]):
            return "wallet_signature"
        else:
            return "general"
    
    def _format_request_for_agent1(self, request_type: str, message: str, context: Dict = None) -> Dict[str, Any]:
        """Format request in JSON format for Agent 1"""
        base_request = {
            "message": message,
            "request_type": request_type,
            "timestamp": datetime.now().isoformat(),
            "context": context or {}
        }
        
        # Add session data if available
        if session_data["wallet_signature"]:
            base_request["wallet_signature"] = session_data["wallet_signature"]
        if session_data["wallet_address"]:
            base_request["wallet_address"] = session_data["wallet_address"]
        
        return base_request
    
    async def _send_to_agent1(self, json_request: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Send request to Agent 1 via ASI Chat Protocol"""
        global agent_context
        
        try:
            # Check if we have agent context
            if not agent_context:
                print(f"🌟 Root Agent: ⚠️ No agent context available, using mock response")
                return None
            
            # Create unique request ID
            request_id = str(uuid4())
            
            # Store pending request
            self.pending_responses[request_id] = {
                "status": "pending",
                "timestamp": datetime.now(),
                "request": json_request,
                "response": None
            }
            
            # Format as chat message
            chat_message = ChatMessage(
                timestamp=datetime.utcnow(),
                msg_id=request_id,
                content=[TextContent(type="text", text=json.dumps(json_request))]
            )
            
            print(f"🌟 Root Agent: 📤 Sending JSON request to Agent 1...")
            print(f"   Request ID: {request_id}")
            print(f"   Agent 1 Address: {agent_1_address}")
            print(f"   Request Type: {json_request.get('request_type', 'unknown')}")
            
            # Send via chat protocol using the agent context
            try:
                await agent_context.send(agent_1_address, chat_message)
                print(f"🌟 Root Agent: ✅ Message sent to Agent 1")
            except Exception as send_error:
                print(f"🌟 Root Agent: ❌ Failed to send message: {send_error}")
                print(f"   This is likely a network resolution issue with the Almanac")
                print(f"   Agent 1 may still be running and responsive")
                # Don't return None immediately, still wait for response in case it gets through
                print(f"🌟 Root Agent: 🔄 Continuing to wait for response despite send error...")
            
            # Wait for response with multiple checks
            print(f"🌟 Root Agent: ⏳ Waiting for response from Agent 1...")
            
            # Check for response multiple times over 6 seconds
            for attempt in range(12):  # 12 attempts * 0.5 seconds = 6 seconds total
                await asyncio.sleep(0.5)
                
                # Check if we got a response for this specific request
                if request_id in self.pending_responses and self.pending_responses[request_id].get("response"):
                    response = self.pending_responses[request_id]["response"]
                    print(f"🌟 Root Agent: ✅ Received response from Agent 1 (attempt {attempt + 1})")
                    return response
                
                # Also check if any recent pending request got a response (fallback)
                for req_id, req_data in self.pending_responses.items():
                    if (req_data.get("status") == "completed" and 
                        req_data.get("response") and
                        (datetime.now() - req_data["timestamp"]).total_seconds() < 30):  # Only use responses from last 30 seconds
                        response = req_data["response"]
                        print(f"🌟 Root Agent: ✅ Found recent completed response from Agent 1 (fallback match)")
                        # Mark this request as used
                        req_data["status"] = "used"
                        return response
            
            print(f"🌟 Root Agent: ⏰ No response from Agent 1 after 6 seconds, using mock")
            print(f"   Pending requests: {list(self.pending_responses.keys())}")
            return None
            
        except Exception as e:
            print(f"❌ Root Agent: Failed to send to Agent 1: {e}")
            return None
    
    def _get_mock_response(self, request_type: str) -> Dict[str, Any]:
        """Get mock response for request type"""
        return MOCK_RESPONSES.get(request_type, {
            "success": True,
            "message": "Mock: Request processed successfully",
            "data": {}
        })

# Global API instance and agent context
root_api = None
agent_context = None

@root_agent.on_event("startup")
async def root_startup_handler(ctx: Context):
    global root_api, agent_context
    ctx.logger.info(f"🌟 Root Agent: My name is {ctx.agent.name} and my address is {ctx.agent.address}")
    print(f"🌟 Root Agent: Starting up! My address is {ctx.agent.address}")
    print(f"🌟 Root Agent: Will communicate with Agent 1 at {agent_1_address}")
    print(f"🌟 Root Agent: Ready to handle user requests via chat protocol")
    
    # Store agent context for message sending
    agent_context = ctx
    
    # Initialize API instance
    root_api = RootAgentAPI(root_agent)

@chat_proto.on_message(ChatMessage)
async def root_handle_message(ctx: Context, sender: str, msg: ChatMessage):
    """Handle messages from Agent 1"""
    global root_api
    
    for item in msg.content:
        if isinstance(item, TextContent):
            ctx.logger.info(f"🌟 Root Agent: Received message from {sender}: {item.text}")
            
            try:
                # Parse JSON response from Agent 1
                response_data = json.loads(item.text)
                print(f"🌟 Root Agent: 📊 Received response from Agent 1:")
                print(f"   Success: {response_data.get('success', False)}")
                print(f"   Message: {response_data.get('message', 'No message')}")
                print(f"   Tool: {response_data.get('tool', 'Unknown')}")
                
                # Store response for pending requests - try multiple ID matching strategies
                response_msg_id = str(msg.msg_id)
                stored = False
                
                # Strategy 1: Try to match by message ID
                if root_api and response_msg_id in root_api.pending_responses:
                    root_api.pending_responses[response_msg_id]["response"] = response_data
                    root_api.pending_responses[response_msg_id]["status"] = "completed"
                    print(f"🌟 Root Agent: ✅ Stored response for request {response_msg_id}")
                    stored = True
                
                # Strategy 2: If no exact match, store in the most recent pending request
                elif root_api and root_api.pending_responses:
                    # Find the most recent pending request
                    pending_requests = [
                        (req_id, req_data) for req_id, req_data in root_api.pending_responses.items()
                        if req_data.get("status") == "pending"
                    ]
                    
                    if pending_requests:
                        # Sort by timestamp and get the most recent
                        pending_requests.sort(key=lambda x: x[1]["timestamp"], reverse=True)
                        most_recent_id = pending_requests[0][0]
                        
                        root_api.pending_responses[most_recent_id]["response"] = response_data
                        root_api.pending_responses[most_recent_id]["status"] = "completed"
                        print(f"🌟 Root Agent: ✅ Stored response for most recent pending request {most_recent_id}")
                        stored = True
                
                if not stored:
                    print(f"🌟 Root Agent: ⚠️ No pending request found for ID {response_msg_id}")
                    print(f"   Available pending requests: {list(root_api.pending_responses.keys()) if root_api else 'None'}")
                
                # Send acknowledgment
                ack = ChatAcknowledgement(
                    timestamp=datetime.utcnow(),
                    acknowledged_msg_id=msg.msg_id
                )
                await ctx.send(sender, ack)
                print(f"🌟 Root Agent: ✅ Sent acknowledgment to Agent 1")
                
            except json.JSONDecodeError:
                # Handle non-JSON messages
                print(f"🌟 Root Agent: Agent 1 said: '{item.text}'")
                
                # Send acknowledgment
                ack = ChatAcknowledgement(
                    timestamp=datetime.utcnow(),
                    acknowledged_msg_id=msg.msg_id
                )
                await ctx.send(sender, ack)

@chat_proto.on_message(ChatAcknowledgement)
async def root_handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
    ctx.logger.info(f"🌟 Root Agent: Received acknowledgement from {sender} for message: {msg.acknowledged_msg_id}")
    print(f"🌟 Root Agent: ✅ Agent 1 acknowledged my message {msg.acknowledged_msg_id}")

# Include the protocol in the agent
root_agent.include(chat_proto, publish_manifest=True)

# HTTP Server functionality for frontend integration
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    import uvicorn
    from pydantic import BaseModel
    FASTAPI_AVAILABLE = True
except ImportError:
    print("⚠️ FastAPI not available. HTTP server will be disabled.")
    FASTAPI_AVAILABLE = False

if FASTAPI_AVAILABLE:
    app = FastAPI(title="Root Agent API")

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    class ChatRequest(BaseModel):
        message: str
        context: Dict[str, Any] = {}

    class ChatResponse(BaseModel):
        success: bool
        response: str
        data: Dict[str, Any] = {}
        tool: str = "Root Agent"
        status: str = "success"

    @app.post("/chat", response_model=ChatResponse)
    async def chat_endpoint(request: ChatRequest):
        """HTTP endpoint for frontend to communicate with Root Agent"""
        if not root_api:
            raise HTTPException(status_code=503, detail="Root Agent not initialized")
        
        try:
            print(f"🌟 Root Agent HTTP: Processing request: {request.message}")
            result = await root_api.process_user_request(request.message, request.context)
            print(f"🌟 Root Agent HTTP: Returning result: {result.get('success', False)}")
            return ChatResponse(**result)
        except Exception as e:
            print(f"🌟 Root Agent HTTP: Error: {e}")
            raise HTTPException(status_code=500, detail=f"Error processing request: {str(e)}")

    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {"status": "healthy", "agent": "root_agent", "timestamp": datetime.now().isoformat()}

    @app.get("/session")
    async def get_session():
        """Get current session information"""
        return {
            "authenticated": session_data["user_authenticated"],
            "wallet_address": session_data["wallet_address"],
            "conversation_count": len(session_data["conversation_history"])
        }

    async def run_http_server():
        """Run the HTTP server"""
        config = uvicorn.Config(app, host="0.0.0.0", port=8003, log_level="info")
        server = uvicorn.Server(config)
        await server.serve()

    async def run_both_servers():
        """Run both the uAgent and HTTP server"""
        # Start HTTP server in background
        http_task = asyncio.create_task(run_http_server())
        
        # Start uAgent in a separate task
        def run_agent():
            root_agent.run()
        
        agent_task = asyncio.get_event_loop().run_in_executor(None, run_agent)
        
        # Wait for both
        await asyncio.gather(http_task, agent_task)

else:
    # Fallback when FastAPI is not available
    async def run_both_servers():
        """Run only the uAgent when FastAPI is not available"""
        print("⚠️ Running in uAgent-only mode (no HTTP server)")
        root_agent.run()

if __name__ == '__main__':
    print("🌟 Starting Root Agent with ASI Chat Protocol")
    print("=" * 70)
    print("Features:")
    print("✅ ASI Chat Protocol communication with Agent 1")
    if FASTAPI_AVAILABLE:
        print("✅ HTTP API for frontend integration (port 8003)")
    else:
        print("⚠️ HTTP API disabled (FastAPI not available)")
    print("✅ Session management with wallet signature storage")
    print("✅ Mock responses when Agent 1 fails")
    print("✅ JSON request/response format with Agent 1")
    print("✅ Conversation history and context management")
    print()
    if FASTAPI_AVAILABLE:
        print("Endpoints:")
        print("• POST /chat - Main chat interface")
        print("• GET /health - Health check")
        print("• GET /session - Session information")
        print()
    print("Agent Communication:")
    print(f"• Root Agent: http://localhost:8002/submit")
    if FASTAPI_AVAILABLE:
        print(f"• HTTP API: http://localhost:8003")
    print(f"• Agent 1 Address: {agent_1_address}")
    print()
    
    try:
        if FASTAPI_AVAILABLE:
            print("🚀 Starting both uAgent and HTTP server...")
            asyncio.run(run_both_servers())
        else:
            print("🚀 Starting uAgent only...")
            root_agent.run()
    except KeyboardInterrupt:
        print("\n👋 Root Agent shutting down!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")