"""
Transaction Agent - Handles transaction execution and monitoring
Integrates with frontend /api/approve route for real transaction processing
"""

from uagents import Agent, Context, Model
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)
from typing import Dict, List, Any, Optional
import json
import requests
import asyncio
from datetime import datetime
import uuid

from .chat_protocol import (
    ASIChatProtocol, ToolCallRequest, ToolCallResponse
)

class TransactionExecutionRequest(Model):
    session_id: str
    analysis_id: str
    simulation_id: int
    wallet_signature: str
    execute_immediately: bool
    batch_size: Optional[int] = 5
    transaction_type: Optional[str] = "swap"

class TransactionStatusRequest(Model):
    session_id: str
    execution_id: str

class TransactionAgent:
    """
    Transaction Agent for handling real transaction execution via Arcology DevNet
    
    Features:
    - Integration with /api/approve route
    - Real-time transaction monitoring
    - Batch transaction optimization
    - Execution status tracking
    """
    
    def __init__(self, agent_port: int = 8010):
        # Initialize uAgent
        self.agent = Agent(
            name="transaction_agent",
            seed="transaction_agent_seed_11111",
            port=agent_port,
            endpoint=[f"http://localhost:{agent_port}/submit"]
        )
        
        self.agent_id = "transaction_agent"
        self.agent_type = "transaction_execution"
        self.name = "Transaction Agent"
        
        # Frontend API configuration
        self.frontend_api_base = "http://localhost:3000/api"
        
        # Chat protocol integration
        self.chat_protocol = ASIChatProtocol()
        
        # Transaction tracking
        self.active_transactions: Dict[str, Dict[str, Any]] = {}
        
        # Setup agent handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup agent event handlers and message protocols"""
        
        @self.agent.on_event("startup")
        async def startup_handler(ctx: Context):
            ctx.logger.info(f"Transaction Agent started: {ctx.agent.address}")
            ctx.logger.info("Connected to Arcology DevNet transaction system")
            
            # Register with chat protocol coordinator
            self.chat_protocol.register_agent(
                agent_id=self.agent_id,
                agent_address=ctx.agent.address,
                agent_type=self.agent_type,
                capabilities=["transaction_execution", "batch_processing", "status_monitoring"]
            )
        
        # Tool Call Handler
        @self.agent.on_message(model=ToolCallRequest)
        async def handle_tool_call(ctx: Context, sender: str, msg: ToolCallRequest):
            """Handle transaction-related tool calls"""
            
            result = {}
            success = True
            
            try:
                if msg.tool_name == "execute_transaction":
                    result = await self._execute_transaction(msg.parameters)
                elif msg.tool_name == "check_transaction_status":
                    result = await self._check_transaction_status(msg.parameters)
                elif msg.tool_name == "batch_transactions":
                    result = await self._batch_transactions(msg.parameters)
                elif msg.tool_name == "estimate_gas":
                    result = await self._estimate_gas_cost(msg.parameters)
                else:
                    result = {"error": f"Unknown tool: {msg.tool_name}"}
                    success = False
            
            except Exception as e:
                result = {"error": str(e)}
                success = False
            
            response = ToolCallResponse(
                session_id=msg.session_id,
                call_id=msg.call_id,
                tool_name=msg.tool_name,
                result=result,
                success=success
            )
            
            await ctx.send(sender, response)
        
        # Chat Message Handler
        @self.agent.on_message(model=ChatMessage)
        async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
            """Handle chat messages about transactions"""
            
            for item in msg.content:
                if isinstance(item, TextContent):
                    response_text = await self._process_transaction_query(item.text)
                    
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
    
    async def _execute_transaction(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute transaction via frontend /api/approve route"""
        
        try:
            # Prepare transaction request
            tx_request = {
                "analysis_id": parameters.get("analysis_id", f"tx_{uuid.uuid4().hex[:8]}"),
                "simulation_id": parameters.get("simulation_id", 0),
                "wallet_signature": parameters.get("wallet_signature", "0x" + "a" * 130),
                "execute_immediately": parameters.get("execute_immediately", True),
                "batch_size": parameters.get("batch_size", 3),
                "transaction_type": parameters.get("transaction_type", "swap")
            }
            
            # Call frontend API
            response = requests.post(
                f"{self.frontend_api_base}/approve",
                json=tx_request,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Track transaction
                if "approval_id" in result:
                    self.active_transactions[result["approval_id"]] = {
                        "request": tx_request,
                        "result": result,
                        "timestamp": datetime.utcnow().isoformat(),
                        "status": result.get("status", "unknown")
                    }
                
                return {
                    "success": True,
                    "approval_id": result.get("approval_id"),
                    "status": result.get("status"),
                    "transaction_count": result.get("transaction_count", 0),
                    "block_number": result.get("block_number"),
                    "message": result.get("message", "Transaction executed"),
                    "execution_details": result
                }
            else:
                return {
                    "success": False,
                    "error": f"API call failed with status {response.status_code}",
                    "details": response.text
                }
        
        except Exception as e:
            return {
                "success": False,
                "error": f"Transaction execution failed: {str(e)}"
            }
    
    async def _check_transaction_status(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Check status of a transaction"""
        
        approval_id = parameters.get("approval_id")
        
        if not approval_id:
            return {"error": "approval_id required"}
        
        # Check local tracking first
        if approval_id in self.active_transactions:
            local_data = self.active_transactions[approval_id]
            
            # Try to get updated status from API if execution_id available
            execution_id = local_data.get("result", {}).get("execution_id")
            if execution_id:
                try:
                    response = requests.get(
                        f"{self.frontend_api_base}/execution/{execution_id}",
                        timeout=10
                    )
                    
                    if response.status_code == 200:
                        updated_status = response.json()
                        local_data["updated_status"] = updated_status
                        local_data["last_checked"] = datetime.utcnow().isoformat()
                        
                        return {
                            "approval_id": approval_id,
                            "status": updated_status.get("status", "unknown"),
                            "progress": updated_status.get("progress", {}),
                            "local_data": local_data,
                            "last_updated": local_data["last_checked"]
                        }
                
                except Exception as e:
                    pass  # Fall back to local data
            
            return {
                "approval_id": approval_id,
                "status": local_data["status"],
                "local_data": local_data,
                "note": "Using cached data"
            }
        else:
            return {
                "error": f"Transaction {approval_id} not found in local tracking"
            }
    
    async def _batch_transactions(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle batch transaction processing"""
        
        transactions = parameters.get("transactions", [])
        
        if not transactions:
            return {"error": "No transactions provided"}
        
        batch_results = []
        
        for i, tx in enumerate(transactions):
            try:
                # Add batch context
                tx_params = {
                    **tx,
                    "batch_index": i,
                    "batch_total": len(transactions),
                    "batch_size": min(len(transactions), 5)  # Limit batch size
                }
                
                result = await self._execute_transaction(tx_params)
                batch_results.append({
                    "index": i,
                    "transaction": tx,
                    "result": result
                })
                
                # Small delay between transactions
                await asyncio.sleep(0.5)
                
            except Exception as e:
                batch_results.append({
                    "index": i,
                    "transaction": tx,
                    "result": {"success": False, "error": str(e)}
                })
        
        successful = sum(1 for r in batch_results if r["result"].get("success", False))
        
        return {
            "batch_size": len(transactions),
            "successful": successful,
            "failed": len(transactions) - successful,
            "results": batch_results,
            "summary": f"Processed {len(transactions)} transactions: {successful} successful, {len(transactions) - successful} failed"
        }
    
    async def _estimate_gas_cost(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Estimate gas costs for transactions"""
        
        transaction_type = parameters.get("transaction_type", "swap")
        batch_size = parameters.get("batch_size", 1)
        
        # Base gas estimates (simplified)
        gas_estimates = {
            "swap": 150000,
            "payroll": 100000,
            "mixed": 125000
        }
        
        base_gas = gas_estimates.get(transaction_type, 150000)
        total_gas = base_gas * batch_size
        
        # Estimate gas price (would be fetched from network in real implementation)
        estimated_gas_price_gwei = 20
        gas_cost_eth = (total_gas * estimated_gas_price_gwei) / 1e9
        
        # Estimate ETH price (simplified)
        eth_price_usd = 2500
        gas_cost_usd = gas_cost_eth * eth_price_usd
        
        return {
            "transaction_type": transaction_type,
            "batch_size": batch_size,
            "estimated_gas_per_tx": base_gas,
            "total_gas_estimate": total_gas,
            "gas_price_gwei": estimated_gas_price_gwei,
            "gas_cost_eth": gas_cost_eth,
            "gas_cost_usd": round(gas_cost_usd, 2),
            "breakdown": {
                "base_cost": base_gas,
                "batch_multiplier": batch_size,
                "network_fee": estimated_gas_price_gwei
            }
        }
    
    async def _process_transaction_query(self, query: str) -> Optional[str]:
        """Process chat queries about transactions"""
        
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in ['execute', 'transaction', 'send', 'approve']):
            if 'status' in query_lower:
                active_count = len(self.active_transactions)
                return f"I'm tracking {active_count} active transactions. Provide an approval_id to check specific status."
            elif 'batch' in query_lower:
                return "I can process batch transactions efficiently. Provide transaction details and I'll handle the execution."
            elif 'gas' in query_lower:
                return "I can estimate gas costs for your transactions. What type and batch size are you planning?"
            else:
                return "I can help execute transactions on Arcology DevNet. What would you like to do?"
        
        return None
    
    def get_transaction_history(self) -> Dict[str, Any]:
        """Get transaction history"""
        
        return {
            "total_transactions": len(self.active_transactions),
            "transactions": list(self.active_transactions.values()),
            "summary": {
                "executed": len([tx for tx in self.active_transactions.values() if tx["status"] == "executed"]),
                "queued": len([tx for tx in self.active_transactions.values() if tx["status"] == "queued"]),
                "failed": len([tx for tx in self.active_transactions.values() if tx["status"] == "failed"])
            }
        }
    
    async def start_agent(self):
        """Start the transaction agent"""
        await self.agent.run()

# Global instance for import
transaction_agent = TransactionAgent()
