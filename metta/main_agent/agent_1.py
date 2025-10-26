#!/usr/bin/env python3
"""
Agent 1: ASI:One Tool Calling Agent
Uses ASI:One LLM with tool calling to interact with frontend APIs
"""

import os
import json
import requests
from typing import Dict, Any, List, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import our tools
from tool_1 import approve_batch_transactions, APPROVE_TOOL_SCHEMA
from tool_2 import get_live_price, PRICE_TOOL_SCHEMA
from tool_balance import get_user_balances, BALANCE_TOOL_SCHEMA
from tool_user import get_user_details, USER_TOOL_SCHEMA
from tool_upload_csv import process_payroll_csv, CSV_UPLOAD_TOOL_SCHEMA
from tool_payroll import process_safe_payroll, PAYROLL_TOOL_SCHEMA
from tool_netted_amm import get_netted_amm_status, NETTED_AMM_TOOL_SCHEMA

# ASI:One API configuration
ASI_API_KEY = os.getenv("ASI_API_KEY")
ASI_BASE_URL = "https://api.asi1.ai/v1/chat/completions"
ASI_MODEL = "asi1-mini"

class ASIOneAgent:
    """ASI:One powered agent with tool calling capabilities"""
    
    def __init__(self):
        if not ASI_API_KEY:
            raise ValueError("ASI_API_KEY not found in environment variables")
        
        self.headers = {
            "Authorization": f"Bearer {ASI_API_KEY}",
            "Content-Type": "application/json"
        }
        
        # Available tools
        self.tools = [APPROVE_TOOL_SCHEMA, PRICE_TOOL_SCHEMA, BALANCE_TOOL_SCHEMA, USER_TOOL_SCHEMA, CSV_UPLOAD_TOOL_SCHEMA, PAYROLL_TOOL_SCHEMA, NETTED_AMM_TOOL_SCHEMA]
        self.tool_functions = {
            "approve_batch_transactions": approve_batch_transactions,
            "get_live_price": get_live_price,
            "get_user_balances": get_user_balances,
            "get_user_details": get_user_details,
            "process_payroll_csv": process_payroll_csv,
            "process_safe_payroll": process_safe_payroll,
            "get_netted_amm_status": get_netted_amm_status
        }
        
        # Session management for wallet signature
        self.session = {
            "wallet_signature": None,
            "wallet_address": None,
            "user_authenticated": False,
            "last_balance_check": None
        }
        
        # Conversation history
        self.messages = [
            {
                "role": "system",
                "content": """You are an advanced DeFi assistant powered by ASI:One, specializing in Arcology blockchain operations and payroll management.

Your capabilities:
1. **Batch Transaction Execution**: Use approve_batch_transactions to execute payroll, swaps, or mixed transaction batches on Arcology blockchain with parallel processing and MEV protection.

2. **Live Price Data**: Use get_live_price to fetch real-time cryptocurrency prices from Pyth Network price feeds with volatility and confidence metrics.

3. **Balance Checking**: Use get_user_balances to fetch real-time token balances for all supported tokens (ETH, USDC, WETH, DAI, USDT, MATIC) from Arcology DevNet.

4. **User Analytics**: Use get_user_details to fetch comprehensive user statistics, transaction history, and platform-wide analytics including gas savings, transaction counts, and performance metrics.

5. **CSV Payroll Processing**: Use process_payroll_csv to process employee payroll data from CSV files or content. Supports both file paths and direct CSV content input. Automatically validates addresses, tokens, and amounts, then generates transaction specifications for batch execution.

6. **Safe Payroll Processing**: Use process_safe_payroll for large payroll batches with enhanced error handling and sequential processing. Perfect for paying multiple employees with reliable transaction execution.

7. **Netted AMM Status & Analytics**: Use get_netted_amm_status to get real-time status, metrics, and analytics from the Netted AMM system. Shows current netting batch status, gas savings, network statistics, contract performance metrics, active requests, and parallel processing threads. Can also queue new swap requests for netting optimization.

Session Management:
- You maintain a session with wallet signature storage for seamless transactions
- If a user hasn't provided their wallet signature, politely ask for it to enable balance checking and transactions
- Wallet signature format: 64-character hexadecimal string starting with 0x (private key)
- Once provided, store it for the session to avoid repeated requests
- Always prioritize security and explain why the signature is needed

Key Guidelines:
- ALWAYS execute tools immediately when users request transactions, prices, or balances - don't negotiate or ask for more details
- When users provide analysis_id, simulation_id, and batch details, execute approve_batch_transactions immediately
- For large payroll batches, use process_safe_payroll for enhanced error handling and sequential processing
- Accept any batch size - the system now handles direct batch execution without chunking limitations
- If users don't provide required parameters, use reasonable defaults: analysis_id="user_request", simulation_id=1
- Execute first, explain benefits after - users want action, not lengthy explanations
- For balance checks, show formatted balances and highlight tokens with non-zero amounts
- Use stored wallet signatures automatically for all tool calls

Example Tool Executions:
- User: "send 100 MATIC to 0x123..." → Execute approve_batch_transactions with analysis_id="user_request", simulation_id=1, batch_size=1
- User: "payroll batch size 2" → Execute approve_batch_transactions with batch_size=2
- User: "pay 5 employees: Alice:1000 USDC:0x123..., Bob:1500 DAI:0x456..." → Execute process_safe_payroll for enhanced error handling
- User: "large payroll batch" → Execute process_safe_payroll for reliable sequential processing
- User: "check my balances" → Execute get_user_balances immediately
- User: "ETH price" → Execute get_live_price for ETH immediately
- User: "process_payroll_csv(csv_file_path='payroll.csv')" → Execute process_payroll_csv with the file path immediately
- User: "process CSV file: employees.csv" → Execute process_payroll_csv with csv_file_path="employees.csv"
- User: "load payroll data from sample_payroll.csv" → Execute process_payroll_csv with the specified file path
- User: "show netted AMM status" → Execute get_netted_amm_status immediately
- User: "detailed netting analytics" → Execute get_netted_amm_status with detailed=true
- User: "queue swap 1.5 ETH for USDC" → Execute get_netted_amm_status with action="queue_swap", tokenIn="ETH", tokenOut="USDC", amountIn="1.5"
- User: "netting performance metrics" → Execute get_netted_amm_status to show gas savings and efficiency

Transaction Display Guidelines:
- Always show transaction hashes when available
- Display transaction status (✅ success, ⏳ pending, ❌ failed)
- Include gas usage and block numbers
- Show from/to addresses in readable format
- Provide summary statistics for batch transactions

You are knowledgeable about:
- Arcology blockchain and parallel transaction processing
- DeFi payroll management and batch optimization
- MEV protection and transaction netting
- Real-time price feeds and market analysis
- Blockchain gas optimization and cost savings
- Token balance management and wallet integration
- CSV payroll processing and employee payment automation
- File path handling and CSV content validation
- Session-based user authentication and security
- **Direct batch transaction execution and processing**
- **Enhanced error handling and sequential processing**
- **Netted AMM real-time status monitoring and analytics**
- **Transaction netting efficiency and gas savings optimization**
- **Parallel processing thread management and performance metrics**
- **Swap request queuing and batch netting strategies**

IMPORTANT: 
1. When users mention CSV files, file paths, or payroll processing, IMMEDIATELY use the process_payroll_csv tool. Don't ask for clarification - execute the tool with the provided file path or content.
2. For large payroll batches, use process_safe_payroll for enhanced error handling and sequential processing reliability.
3. The system now supports direct batch execution without chunking limitations - handle any batch size efficiently."""
            }
        ]
    
    def chat(self, user_input: str) -> str:
        """
        Process user input and return response, using tools when needed
        """
        print(f"🤖 Agent 1: Processing user input...")
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
                try:
                    error_data = response.json()
                    print(f"   Error details: {error_data}")
                except:
                    print(f"   Response: {response.text}")
                return None
                
        except requests.exceptions.Timeout:
            print(f"❌ ASI:One API timeout")
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
            tool_result = self._execute_tool_call_with_session(tool_call)
            
            # Add tool result to conversation
            self.messages.append({
                "role": "tool",
                "tool_call_id": tool_call["id"],
                "content": json.dumps(tool_result)
            })
        
        # Get final response from ASI:One with tool results
        final_response = self._make_asi_request()
        
        if final_response and "choices" in final_response:
            final_content = final_response["choices"][0]["message"]["content"]
            self.messages.append({
                "role": "assistant",
                "content": final_content
            })
            return final_content
        else:
            return "✅ Tool execution completed, but I couldn't generate a final response."
    
    def _execute_tool_call(self, tool_call: Dict) -> Dict:
        """Execute a single tool call"""
        function_name = tool_call["function"]["name"]
        
        print(f"🔧 Executing tool: {function_name}")
        
        try:
            # Parse arguments
            args_str = tool_call["function"]["arguments"]
            args = json.loads(args_str)
            print(f"   Arguments: {args}")
            
            # Execute the tool function
            if function_name in self.tool_functions:
                result = self.tool_functions[function_name](**args)
                print(f"   ✅ Tool execution successful")
                return result
            else:
                error_result = {
                    "success": False,
                    "error": f"Unknown tool function: {function_name}"
                }
                print(f"   ❌ Unknown tool function")
                return error_result
                
        except json.JSONDecodeError as e:
            error_result = {
                "success": False,
                "error": f"Invalid JSON arguments: {str(e)}"
            }
            print(f"   ❌ JSON decode error: {e}")
            return error_result
        except Exception as e:
            error_result = {
                "success": False,
                "error": f"Tool execution error: {str(e)}"
            }
            print(f"   ❌ Tool execution error: {e}")
            return error_result
    
    def get_conversation_history(self) -> List[Dict]:
        """Get the current conversation history"""
        return self.messages.copy()
    
    def reset_conversation(self):
        """Reset conversation to initial state"""
        self.messages = self.messages[:1]  # Keep only system message
    
    def set_wallet_signature(self, signature: str) -> Dict[str, Any]:
        """
        Set wallet signature for the session
        
        Args:
            signature: Wallet private key (64-character hex string starting with 0x)
        
        Returns:
            Dict with success status and derived address
        """
        try:
            # Basic validation
            if not signature.startswith('0x') or len(signature) != 66:
                return {
                    "success": False,
                    "error": "Invalid signature format. Expected 64-character hex string starting with 0x"
                }
            
            # Store in session
            self.session["wallet_signature"] = signature
            self.session["user_authenticated"] = True
            
            # Derive address (basic validation - in production, use proper crypto library)
            # For now, we'll use a placeholder
            self.session["wallet_address"] = f"0x{signature[2:42]}"  # Simplified derivation
            
            print(f"✅ Wallet signature stored for session")
            print(f"   Address: {self.session['wallet_address']}")
            
            return {
                "success": True,
                "address": self.session["wallet_address"],
                "message": "Wallet signature stored successfully for this session"
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to process wallet signature: {str(e)}"
            }
    
    def get_session_info(self) -> Dict[str, Any]:
        """Get current session information"""
        return {
            "authenticated": self.session["user_authenticated"],
            "has_signature": self.session["wallet_signature"] is not None,
            "wallet_address": self.session["wallet_address"],
            "last_balance_check": self.session["last_balance_check"]
        }
    
    def clear_session(self):
        """Clear session data"""
        self.session = {
            "wallet_signature": None,
            "wallet_address": None,
            "user_authenticated": False,
            "last_balance_check": None
        }
        print("🔄 Session cleared")
    
    def _execute_tool_call_with_session(self, tool_call: Dict) -> Dict:
        """Execute tool call with session context"""
        function_name = tool_call["function"]["name"]
        
        print(f"🔧 Executing tool: {function_name}")
        
        try:
            # Parse arguments
            args_str = tool_call["function"]["arguments"]
            args = json.loads(args_str)
            print(f"   Arguments: {args}")
            
            # Add session context for balance and transaction tools
            if function_name == "get_user_balances":
                # Auto-inject wallet signature if available and not provided
                if not args.get("wallet_signature") and not args.get("wallet_address"):
                    if self.session["wallet_signature"]:
                        args["wallet_signature"] = self.session["wallet_signature"]
                        print(f"   Using stored wallet signature from session")
                    elif self.session["wallet_address"]:
                        args["wallet_address"] = self.session["wallet_address"]
                        print(f"   Using stored wallet address from session")
                
                # Update last balance check time
                import datetime
                self.session["last_balance_check"] = datetime.datetime.now().isoformat()
            
            elif function_name == "approve_batch_transactions":
                # Auto-inject wallet signature if available and not provided
                if not args.get("wallet_signature") and self.session["wallet_signature"]:
                    args["wallet_signature"] = self.session["wallet_signature"]
                    print(f"   Using stored wallet signature from session")
                
                # Check if we need to extract custom transactions from the conversation context
                if not args.get("custom_transactions"):
                    # Look for transaction specifications in recent messages
                    for msg in reversed(self.messages[-3:]):  # Check last 3 messages
                        if msg.get("role") == "user":
                            content = msg.get("content", "")
                            # Check for patterns like "100 USDC to 0x..." or "send 200 DAI to 0x..."
                            import re
                            pattern = r'\d+(?:\.\d+)?\s+[A-Z]+\s+to\s+0x[a-fA-F0-9]{40}'
                            if re.search(pattern, content, re.IGNORECASE):
                                args["custom_transactions"] = content
                                print(f"   Extracted custom transactions from user input")
                                break
            
            elif function_name == "get_user_details":
                # Auto-inject wallet signature or address if available and not provided
                if not args.get("wallet_signature") and not args.get("wallet_address"):
                    if self.session["wallet_signature"]:
                        args["wallet_signature"] = self.session["wallet_signature"]
                        print(f"   Using stored wallet signature from session")
                    elif self.session["wallet_address"]:
                        args["wallet_address"] = self.session["wallet_address"]
                        print(f"   Using stored wallet address from session")
            
            elif function_name == "process_payroll_csv":
                # CSV processing - check if we should auto-execute transactions
                print(f"   Processing CSV payroll data...")
                
                # Store CSV result for potential batch execution
                csv_result = self.tool_functions[function_name](**args)
                
                if csv_result.get('success') and csv_result.get('data', {}).get('transaction_specs'):
                    # Store transaction specs for potential auto-execution
                    transaction_specs = csv_result['data']['transaction_specs']
                    self.session['last_csv_transaction_specs'] = transaction_specs
                    print(f"   Stored transaction specs for potential batch execution")
                
                return csv_result
            
            # Execute the tool function
            if function_name in self.tool_functions:
                result = self.tool_functions[function_name](**args)
                print(f"   ✅ Tool execution successful")
                return result
            else:
                error_result = {
                    "success": False,
                    "error": f"Unknown tool function: {function_name}"
                }
                print(f"   ❌ Unknown tool function")
                return error_result
                
        except json.JSONDecodeError as e:
            error_result = {
                "success": False,
                "error": f"Invalid JSON arguments: {str(e)}"
            }
            print(f"   ❌ JSON decode error: {e}")
            return error_result
        except Exception as e:
            error_result = {
                "success": False,
                "error": f"Tool execution error: {str(e)}"
            }
            print(f"   ❌ Tool execution error: {e}")
            return error_result

def main():
    """Interactive chat loop"""
    print("🚀 ASI:One Tool Calling Agent")
    print("=" * 60)
    print("Features:")
    print("✅ ASI:One LLM reasoning with asi1-mini model")
    print("✅ Tool 1: Batch transaction execution via /api/approve")
    print("✅ Tool 2: Live price feeds via /api/get_price")
    print("✅ Tool 3: Balance checking via /api/get_balance")
    print("✅ Tool 4: User analytics via /api/user")
    print("✅ Tool 5: CSV payroll processing and batch execution")
    print("✅ Tool 6: Safe payroll processing with enhanced error handling")
    print("✅ Tool 7: Netted AMM status and analytics via /api/net_status")
    print("✅ Session management with wallet signature storage")
    print("✅ Intelligent tool selection based on user intent")
    print("✅ Complete conversation context and memory")
    print()
    print("Example commands:")
    print("• 'Check my token balances'")
    print("• 'Show my user statistics and gas savings'")
    print("• 'Execute a payroll batch for 5 employees'")
    print("• 'Process CSV payroll data for batch transactions'")
    print("• 'Get the current price of ETH, SOL, AVAX, LINK'")
    print("• 'What are the global platform statistics?'")
    print("• 'Show netted AMM status and performance metrics'")
    print("• 'Get detailed netting analytics with thread status'")
    print("• 'Queue a swap: 2.5 ETH for USDC'")
    print("• 'Set my wallet signature: 0x123...'")
    print()
    print("Session commands:")
    print("• 'session' - View session info")
    print("• 'clear' - Clear session data")
    print("• 'reset' - Reset conversation")
    print("• 'quit' - Exit")
    print()
    print("💡 Tip: Provide your wallet signature for enhanced functionality!")
    print("   Format: 64-character hex string starting with 0x")
    print("=" * 60)
    
    try:
        agent = ASIOneAgent()
        
        while True:
            user_input = input("\n👤 You: ").strip()
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            elif user_input.lower() == 'reset':
                agent.reset_conversation()
                print("🔄 Conversation reset!")
                continue
            elif user_input.lower() == 'clear':
                agent.clear_session()
                print("🔄 Session cleared!")
                continue
            elif user_input.lower() == 'session':
                session_info = agent.get_session_info()
                print("📊 Session Information:")
                print(f"   Authenticated: {session_info['authenticated']}")
                print(f"   Has Signature: {session_info['has_signature']}")
                print(f"   Wallet Address: {session_info['wallet_address'] or 'Not set'}")
                print(f"   Last Balance Check: {session_info['last_balance_check'] or 'Never'}")
                continue
            elif user_input.lower().startswith('set signature:') or user_input.lower().startswith('signature:'):
                # Extract signature from user input
                signature_part = user_input.split(':', 1)[1].strip()
                result = agent.set_wallet_signature(signature_part)
                if result['success']:
                    print(f"✅ {result['message']}")
                    print(f"   Address: {result['address']}")
                else:
                    print(f"❌ {result['error']}")
                continue
            elif not user_input:
                continue
            
            print()
            response = agent.chat(user_input)
            print(f"\n🤖 Agent: {response}")
            
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")

if __name__ == "__main__":
    main()