#!/usr/bin/env python3
"""
Orchestrator Chat Interface - Direct chat with the Analysis Team Orchestrator
Similar interface to agent_1.py but with multi-agent coordination capabilities
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

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

class OrchestratorChat:
    """Interactive chat interface for the Analysis Team Orchestrator"""
    
    def __init__(self):
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
        
        # Conversation history
        self.messages = [
            {
                "role": "system",
                "content": """You are the Analysis Team Orchestrator, an advanced AI coordinator powered by ASI:One. You manage a team of specialized analysis agents and can provide comprehensive insights on DeFi operations.

Your Team (currently available for coordination):
🛡️ **MEV Agent**: Specializes in MEV detection, sandwich attack analysis, and protection strategies
⚡ **Speed Agent**: Focuses on transaction throughput, gas optimization, and performance analysis  
💰 **Profit Agent**: Expert in financial analysis, ROI calculations, and cost-benefit assessments

Your Direct Capabilities:
1. **Live Price Data**: Get real-time cryptocurrency prices with volatility metrics
2. **Balance Checking**: Fetch user token balances across all supported assets
3. **User Analytics**: Access comprehensive user statistics and platform metrics
4. **Analysis Coordination**: Provide expert insights on when to use specialized agents
5. **Comprehensive Recommendations**: Combine multiple perspectives for complete analysis

How You Work:
- For simple requests (prices, balances, user data): Handle directly with your tools
- For specialized analysis: Provide expert recommendations on which agents to consult
- For complex requests: Explain how multiple agents would collaborate
- Always provide actionable insights and clear recommendations

Example Interactions:
• "What's the current ETH price?" → Direct tool execution
• "Check my token balances" → Direct balance check
• "Analyze MEV risks for payroll batch" → Explain MEV analysis approach and recommend MEV Agent
• "Optimize gas costs for daily payments" → Explain optimization strategies and recommend Speed Agent  
• "Calculate ROI for netted transactions" → Explain financial analysis and recommend Profit Agent
• "Comprehensive analysis of payroll system" → Explain multi-agent coordination approach

Agent Coordination Guidelines:
- MEV-related queries → Recommend MEV Agent for sandwich attack analysis, protection strategies
- Performance/speed queries → Recommend Speed Agent for throughput optimization, gas analysis
- Financial/profit queries → Recommend Profit Agent for ROI calculations, cost-benefit analysis
- General data requests → Handle directly with available tools
- Complex multi-faceted requests → Explain how to coordinate multiple agents

You are knowledgeable about:
- DeFi protocols and blockchain operations
- Arcology network and parallel processing
- MEV protection and transaction optimization
- Financial analysis and cost optimization
- Multi-agent coordination and analysis synthesis
- When and how to leverage specialized expertise

Always be helpful, direct, and provide comprehensive insights. When you can't directly coordinate with agents (in chat mode), explain what analysis would be needed and how the team would approach it."""
            }
        ]
    
    def chat(self, user_input: str) -> str:
        """
        Process user input and return response, using tools when needed
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
                        "content": "🎭 Orchestrator Demo Mode: I can help coordinate analysis requests and explain how the team would approach your query, but ASI:One API is not available. Please set ASI_API_KEY for full functionality including direct tool execution."
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
    
    def reset_conversation(self):
        """Reset conversation history"""
        self.messages = self.messages[:1]  # Keep system message only

def main():
    """Interactive chat loop"""
    print("🎭 Analysis Team Orchestrator - Interactive Chat")
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
    print("✅ Multi-agent coordination recommendations")
    print("✅ ASI:One reasoning for intelligent analysis")
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
        orchestrator = OrchestratorChat()
        
        while True:
            user_input = input("\n👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            elif user_input.lower() == 'reset':
                orchestrator.reset_conversation()
                print("🔄 Conversation reset!")
                continue
            elif not user_input:
                continue
            
            print()
            response = orchestrator.chat(user_input)
            print(f"\n🎭 Orchestrator: {response}")
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")

if __name__ == "__main__":
    main()
