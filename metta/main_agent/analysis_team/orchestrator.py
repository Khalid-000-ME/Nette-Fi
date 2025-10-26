#!/usr/bin/env python3
"""
Analysis Team Orchestrator - Sophisticated Multi-Agent Coordinator
Coordinates between MEV, Speed, and Profit analysis agents using chat protocol
"""

import os
import json
import asyncio
from datetime import datetime
from uuid import uuid4
from typing import Dict, Any, List, Optional
from uagents import Agent, Protocol, Context
from dotenv import load_dotenv

# Import chat protocol components
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

# Import tools from main agent
import sys
sys.path.append('../')
from tool_2 import get_live_price, PRICE_TOOL_SCHEMA
from tool_balance import get_user_balances, BALANCE_TOOL_SCHEMA
from tool_user import get_user_details, USER_TOOL_SCHEMA

# Load environment variables
load_dotenv()

# ASI:One API configuration
ASI_API_KEY = os.getenv("ASI_API_KEY")
ASI_BASE_URL = "https://api.asi1.ai/v1/chat/completions"
ASI_MODEL = "asi1-mini"

class AnalysisOrchestrator:
    """Orchestrator that coordinates analysis agents with ASI:One reasoning"""
    
    def __init__(self):
        self.agent = Agent(
            name="orchestrator",
            port=8100,
            seed="orchestrator_seed_123",
            endpoint=["http://localhost:8100/submit"]
        )
        
        # Chat protocol
        self.chat_proto = Protocol(spec=chat_protocol_spec)
        
        # Agent addresses (will be populated when agents start)
        self.agent_addresses = {
            "mev_agent": None,
            "speed_agent": None, 
            "profit_agent": None
        }
        
        # Analysis state
        self.active_analyses = {}
        self.analysis_results = {}
        
        # ASI:One configuration
        if not ASI_API_KEY:
            print("⚠️ Orchestrator: ASI_API_KEY not found, running in demo mode")
            self.asi_enabled = False
        else:
            self.asi_enabled = True
            self.headers = {
                "Authorization": f"Bearer {ASI_API_KEY}",
                "Content-Type": "application/json"
            }
        
        # Available tools
        self.tools = [PRICE_TOOL_SCHEMA, BALANCE_TOOL_SCHEMA, USER_TOOL_SCHEMA]
        self.tool_functions = {
            "get_live_price": get_live_price,
            "get_user_balances": get_user_balances,
            "get_user_details": get_user_details
        }
        
        # Conversation history for direct chat
        self.messages = [
            {
                "role": "system",
                "content": """You are the Analysis Team Orchestrator, an advanced AI coordinator powered by ASI:One. You manage a team of specialized analysis agents and can provide comprehensive insights on DeFi operations.

Your Team:
🛡️ **MEV Agent**: Specializes in MEV detection, sandwich attack analysis, and protection strategies
⚡ **Speed Agent**: Focuses on transaction throughput, gas optimization, and performance analysis  
💰 **Profit Agent**: Expert in financial analysis, ROI calculations, and cost-benefit assessments

Your Direct Capabilities:
1. **Live Price Data**: Get real-time cryptocurrency prices with volatility metrics
2. **Balance Checking**: Fetch user token balances across all supported assets
3. **User Analytics**: Access comprehensive user statistics and platform metrics
4. **Multi-Agent Coordination**: Route complex requests to specialized agents
5. **Comprehensive Analysis**: Combine insights from multiple agents for complete reports

How You Work:
- For simple requests (prices, balances, user data): Handle directly with your tools
- For specialized analysis: Route to appropriate agent(s)
- For complex requests: Coordinate multiple agents and synthesize results
- Always provide actionable insights and clear recommendations

Example Interactions:
• "What's the current ETH price?" → Direct tool execution
• "Check my token balances" → Direct balance check
• "Analyze MEV risks for payroll batch" → Route to MEV Agent
• "Optimize gas costs for daily payments" → Route to Speed Agent  
• "Calculate ROI for netted transactions" → Route to Profit Agent
• "Comprehensive analysis of payroll system" → Multi-agent coordination

Agent Routing Guidelines:
- MEV-related queries → MEV Agent
- Performance/speed queries → Speed Agent
- Financial/profit queries → Profit Agent
- General data requests → Handle directly
- Complex multi-faceted requests → Coordinate multiple agents

You are knowledgeable about:
- DeFi protocols and blockchain operations
- Arcology network and parallel processing
- MEV protection and transaction optimization
- Financial analysis and cost optimization
- Multi-agent coordination and analysis synthesis

Always be helpful, direct, and provide comprehensive insights by leveraging your team of specialists."""
            }
        ]
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup agent event handlers"""
        
        @self.agent.on_event("startup")
        async def startup_handler(ctx: Context):
            ctx.logger.info(f"🎭 Orchestrator: Starting up at {ctx.agent.address}")
            print(f"🎭 Orchestrator: Analysis Team Coordinator Ready!")
            print(f"🎭 Address: {ctx.agent.address}")
            print(f"🎭 Waiting for analysis agents to connect...")
            
            # Wait for agents to register
            await asyncio.sleep(3)
            await self.discover_agents(ctx)
        
        @self.chat_proto.on_message(ChatMessage)
        async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
            await self.process_agent_message(ctx, sender, msg)
        
        @self.chat_proto.on_message(ChatAcknowledgement)
        async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
            print(f"🎭 Orchestrator: ✅ Agent acknowledged message {msg.acknowledged_msg_id}")
        
        # Include protocol
        self.agent.include(self.chat_proto, publish_manifest=True)
    
    async def discover_agents(self, ctx: Context):
        """Discover and register analysis agents"""
        print(f"🎭 Orchestrator: 🔍 Discovering analysis agents...")
        
        # In a real implementation, this would use agent discovery
        # For now, we'll use known addresses that agents will register with
        expected_agents = ["mev_agent", "speed_agent", "profit_agent"]
        
        for agent_name in expected_agents:
            print(f"🎭 Orchestrator: Waiting for {agent_name} to register...")
        
        print(f"🎭 Orchestrator: ✅ Agent discovery complete")
    
    def chat(self, user_input: str) -> str:
        """
        Direct chat interface similar to agent_1.py
        """
        print(f"🎭 Orchestrator: Processing user input...")
        print(f"   User: {user_input}")
        
        # Add user message to conversation
        self.messages.append({
            "role": "user",
            "content": user_input
        })
        
        try:
            # Make initial request to ASI:One
            response = self._make_asi_request()
            
            if not response:
                return "❌ Sorry, I couldn't process your request due to an API error."
            
            choice = response["choices"][0]["message"]
            
            # Check if model wants to use tools
            if "tool_calls" in choice and choice["tool_calls"]:
                return self._handle_tool_calls(choice, response)
            else:
                # Regular response without tools
                assistant_response = choice["content"]
                self.messages.append({
                    "role": "assistant", 
                    "content": assistant_response
                })
                return assistant_response
                
        except Exception as e:
            error_msg = f"❌ Error processing request: {str(e)}"
            print(error_msg)
            return error_msg
    
    def _make_asi_request(self) -> Optional[Dict]:
        """Make request to ASI:One API"""
        if not self.asi_enabled:
            return {
                "choices": [{
                    "message": {
                        "content": "🎭 Orchestrator Demo Mode: I can help coordinate analysis requests, but ASI:One API is not available. Please set ASI_API_KEY for full functionality."
                    }
                }]
            }
        
        payload = {
            "model": ASI_MODEL,
            "messages": self.messages,
            "tools": self.tools,
            "temperature": 0.7,
            "max_tokens": 2048
        }
        
        try:
            import requests
            print(f"🔮 Making ASI:One API request...")
            response = requests.post(
                ASI_BASE_URL,
                headers=self.headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ ASI:One API response received")
                return result
            else:
                print(f"❌ ASI:One API error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ ASI:One API exception: {e}")
            return None
    
    def _handle_tool_calls(self, choice: Dict, original_response: Dict) -> str:
        """Handle tool calls from ASI:One"""
        tool_calls = choice["tool_calls"]
        print(f"🔧 ASI:One requested {len(tool_calls)} tool call(s)")
        
        # Add assistant message with tool calls
        self.messages.append({
            "role": "assistant",
            "content": choice.get("content", ""),
            "tool_calls": tool_calls
        })
        
        # Execute each tool call
        for tool_call in tool_calls:
            tool_result = self._execute_tool_call(tool_call)
            
            # Add tool result to conversation
            self.messages.append({
                "role": "tool",
                "content": json.dumps(tool_result),
                "tool_call_id": tool_call["id"]
            })
        
        # Get final response from ASI:One
        final_response = self._make_asi_request()
        if final_response:
            final_content = final_response["choices"][0]["message"]["content"]
            self.messages.append({
                "role": "assistant",
                "content": final_content
            })
            return final_content
        else:
            return "✅ Tool execution completed, but couldn't generate final response."
    
    def _execute_tool_call(self, tool_call: Dict) -> Dict[str, Any]:
        """Execute a single tool call"""
        function = tool_call["function"]
        tool_name = function["name"]
        
        try:
            arguments = json.loads(function["arguments"])
            print(f"🔧 Executing tool: {tool_name}")
            print(f"   Arguments: {arguments}")
            
            if tool_name in self.tool_functions:
                result = self.tool_functions[tool_name](**arguments)
                print(f"   ✅ Tool execution successful")
                return {
                    "success": True,
                    "result": result
                }
            else:
                error_msg = f"Unknown tool: {tool_name}"
                print(f"   ❌ {error_msg}")
                return {
                    "success": False,
                    "error": error_msg
                }
                
        except Exception as e:
            error_msg = f"Tool execution error: {str(e)}"
            print(f"   ❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg
            }

    async def call_asi_one_llm(self, messages: List[Dict], tools: Optional[List] = None) -> Dict[str, Any]:
        """Call ASI:One LLM for reasoning and tool calling"""
        if not self.asi_enabled:
            return {"choices": [{"message": {"content": "ASI:One not available - using demo response"}}]}
        
        import requests
        
        payload = {
            "model": ASI_MODEL,
            "messages": messages,
            "temperature": 0.7,
            "max_tokens": 2000
        }
        
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"
        
        try:
            response = requests.post(ASI_BASE_URL, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"🎭 Orchestrator: ❌ ASI:One API error: {e}")
            return {"error": str(e)}
    
    async def execute_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool function"""
        if tool_name not in self.tool_functions:
            return {"error": f"Unknown tool: {tool_name}"}
        
        try:
            result = self.tool_functions[tool_name](**arguments)
            return {"success": True, "result": result}
        except Exception as e:
            return {"error": str(e)}
    
    async def process_agent_message(self, ctx: Context, sender: str, msg: ChatMessage):
        """Process messages from analysis agents"""
        for item in msg.content:
            if isinstance(item, TextContent):
                print(f"🎭 Orchestrator: 📨 Message from {sender}: {item.text}")
                
                # Send acknowledgment
                ack = ChatAcknowledgement(
                    timestamp=datetime.utcnow(),
                    acknowledged_msg_id=msg.msg_id
                )
                await ctx.send(sender, ack)
                
                # Process the message
                await self.handle_agent_request(ctx, sender, item.text)
    
    async def handle_agent_request(self, ctx: Context, sender: str, message: str):
        """Handle requests from analysis agents using ASI:One reasoning"""
        
        # Use ASI:One to understand the request and determine response
        system_prompt = f"""You are the Analysis Team Orchestrator. You coordinate between MEV, Speed, and Profit analysis agents.

Available tools:
- get_live_price: Get real-time token prices
- get_user_balances: Get user wallet balances  
- get_user_details: Get user account information

Agent {sender} sent: "{message}"

Analyze this request and determine:
1. What information/tools are needed
2. How to respond to the agent
3. Whether to involve other agents

Respond with your analysis and any tool calls needed."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Agent request: {message}"}
        ]
        
        # Call ASI:One with tools
        response = await self.call_asi_one_llm(messages, self.tools)
        
        if "error" in response:
            await self.send_error_response(ctx, sender, response["error"])
            return
        
        # Process ASI:One response
        choice = response.get("choices", [{}])[0]
        message_content = choice.get("message", {})
        
        # Handle tool calls if any
        tool_results = []
        if "tool_calls" in message_content:
            for tool_call in message_content["tool_calls"]:
                function = tool_call["function"]
                tool_name = function["name"]
                arguments = json.loads(function["arguments"])
                
                print(f"🎭 Orchestrator: 🔧 Executing tool: {tool_name}")
                result = await self.execute_tool(tool_name, arguments)
                tool_results.append({"tool": tool_name, "result": result})
        
        # Generate response using ASI:One
        response_messages = messages + [
            {"role": "assistant", "content": message_content.get("content", "")},
            {"role": "user", "content": f"Tool results: {json.dumps(tool_results)}. Now provide a comprehensive response to the agent."}
        ]
        
        final_response = await self.call_asi_one_llm(response_messages)
        
        if "error" not in final_response:
            response_text = final_response.get("choices", [{}])[0].get("message", {}).get("content", "")
            await self.send_response_to_agent(ctx, sender, response_text)
        else:
            await self.send_error_response(ctx, sender, final_response["error"])
    
    async def send_response_to_agent(self, ctx: Context, agent_address: str, response_text: str):
        """Send response back to an analysis agent"""
        response_msg = ChatMessage(
            timestamp=datetime.utcnow(),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=response_text)]
        )
        
        await ctx.send(agent_address, response_msg)
        print(f"🎭 Orchestrator: 📤 Sent response to {agent_address}")
    
    async def send_error_response(self, ctx: Context, agent_address: str, error: str):
        """Send error response to an analysis agent"""
        error_msg = ChatMessage(
            timestamp=datetime.utcnow(),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=f"❌ Error: {error}")]
        )
        
        await ctx.send(agent_address, error_msg)
        print(f"🎭 Orchestrator: ❌ Sent error to {agent_address}: {error}")
    
    async def coordinate_multi_agent_analysis(self, ctx: Context, analysis_request: str):
        """Coordinate analysis across multiple agents"""
        analysis_id = str(uuid4())
        self.active_analyses[analysis_id] = {
            "request": analysis_request,
            "timestamp": datetime.utcnow(),
            "agents_involved": [],
            "results": {}
        }
        
        # Use ASI:One to determine which agents to involve
        coordination_prompt = f"""Analysis request: "{analysis_request}"

Available agents:
- mev_agent: MEV analysis and protection strategies
- speed_agent: Transaction speed and optimization analysis  
- profit_agent: Profit analysis and financial metrics

Determine which agents should be involved and what specific questions to ask each agent."""

        messages = [{"role": "user", "content": coordination_prompt}]
        response = await self.call_asi_one_llm(messages)
        
        if "error" not in response:
            coordination_plan = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            print(f"🎭 Orchestrator: 📋 Coordination plan: {coordination_plan}")
            
            # Execute coordination plan (simplified for demo)
            for agent_name, agent_address in self.agent_addresses.items():
                if agent_address and agent_name in coordination_plan.lower():
                    await self.send_analysis_request_to_agent(ctx, agent_address, analysis_request, analysis_id)
    
    async def send_analysis_request_to_agent(self, ctx: Context, agent_address: str, request: str, analysis_id: str):
        """Send analysis request to a specific agent"""
        request_msg = ChatMessage(
            timestamp=datetime.utcnow(),
            msg_id=uuid4(),
            content=[TextContent(type="text", text=f"ANALYSIS_REQUEST:{analysis_id}:{request}")]
        )
        
        await ctx.send(agent_address, request_msg)
        print(f"🎭 Orchestrator: 📤 Sent analysis request {analysis_id} to {agent_address}")
    
    def reset_conversation(self):
        """Reset conversation history"""
        self.messages = self.messages[:1]  # Keep system message only
    
    def run_agent_mode(self):
        """Start the orchestrator in agent mode (uAgents protocol)"""
        print("🎭 Starting Analysis Team Orchestrator - Agent Mode")
        print("=" * 60)
        print("Features:")
        print("✅ ASI:One LLM reasoning and tool calling")
        print("✅ Multi-agent coordination via chat protocol")
        print("✅ Real-time price, balance, and user data tools")
        print("✅ Sophisticated analysis request routing")
        print("✅ Cross-agent communication and result aggregation")
        print()
        self.agent.run()
    
    def run_chat_mode(self):
        """Start the orchestrator in interactive chat mode"""
        print("🎭 Analysis Team Orchestrator - Interactive Chat Mode")
        print("=" * 70)
        print("Your Analysis Team:")
        print("🛡️ MEV Agent - MEV detection and protection strategies")
        print("⚡ Speed Agent - Performance optimization and gas analysis")
        print("💰 Profit Agent - Financial analysis and ROI calculations")
        print()
        print("Direct Capabilities:")
        print("✅ Real-time price feeds for all major cryptocurrencies")
        print("✅ Token balance checking across supported networks")
        print("✅ User analytics and platform statistics")
        print("✅ Multi-agent coordination for complex analysis")
        print("✅ ASI:One reasoning for intelligent request routing")
        print()
        print("Example commands:")
        print("• 'What's the current ETH price?'")
        print("• 'Check token balances for user analytics'")
        print("• 'Analyze MEV risks for a 50-employee payroll batch'")
        print("• 'Optimize gas costs for daily payment processing'")
        print("• 'Calculate ROI for switching to netted transactions'")
        print("• 'Comprehensive analysis of our DeFi payroll system'")
        print()
        print("Commands:")
        print("• 'reset' - Reset conversation")
        print("• 'quit' - Exit")
        print("=" * 70)
        
        try:
            while True:
                user_input = input("\n👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                elif user_input.lower() == 'reset':
                    self.reset_conversation()
                    print("🔄 Conversation reset!")
                    continue
                elif not user_input:
                    continue
                
                print()
                response = self.chat(user_input)
                print(f"\n🎭 Orchestrator: {response}")
                
        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
        except Exception as e:
            print(f"\n❌ Fatal error: {e}")

def main():
    """Main function with mode selection"""
    print("🎭 ANALYSIS TEAM ORCHESTRATOR")
    print("=" * 50)
    print("Choose mode:")
    print("1. Interactive Chat Mode (recommended)")
    print("2. Agent Protocol Mode (for multi-agent system)")
    print()
    
    try:
        choice = input("Select mode (1 or 2): ").strip()
        
        orchestrator = AnalysisOrchestrator()
        
        if choice == "1":
            orchestrator.run_chat_mode()
        elif choice == "2":
            orchestrator.run_agent_mode()
        else:
            print("Invalid choice. Starting chat mode...")
            orchestrator.run_chat_mode()
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Error: {e}")

# Global orchestrator instance for backwards compatibility
orchestrator = AnalysisOrchestrator()

if __name__ == '__main__':
    main()