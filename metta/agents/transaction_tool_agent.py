"""
Transaction Tool Agent - Actually mines transactions using /api/approve
This agent makes real API calls to execute transactions on the blockchain
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

class TransactionToolAgent:
    """Agent that makes real API calls to mine transactions"""
    
    def __init__(self, api_base_url: str = "http://localhost:3000"):
        self.api_base_url = api_base_url
        self.agent_id = f"transaction_agent_{uuid.uuid4().hex[:8]}"
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def mine_transactions(
        self,
        analysis_id: str,
        simulation_id: int,
        batch_size: int = 5,
        transaction_type: str = 'payroll',
        execute_immediately: bool = True,
        wallet_signature: str = "demo_signature_12345"
    ) -> Dict[str, Any]:
        """
        Mine transactions using /api/approve route
        
        Args:
            analysis_id: ID from analysis system
            simulation_id: Selected simulation ID
            batch_size: Number of transactions to batch
            transaction_type: Type of transactions ('payroll', 'swap', 'mixed')
            execute_immediately: Whether to execute now or queue
            wallet_signature: User wallet signature
            
        Returns:
            Transaction execution result with block numbers and mining status
        """
        
        print(f"🔨 {self.agent_id}: Mining {batch_size} {transaction_type} transactions...")
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            # Prepare API request payload
            payload = {
                "analysis_id": analysis_id,
                "simulation_id": simulation_id,
                "wallet_signature": wallet_signature,
                "execute_immediately": execute_immediately,
                "batch_size": batch_size,
                "transaction_type": transaction_type
            }
            
            print(f"   📡 Calling /api/approve with payload: {payload}")
            
            # Make API call to mine transactions
            async with self.session.post(
                f"{self.api_base_url}/api/approve",
                json=payload,
                headers={"Content-Type": "application/json"},
                timeout=aiohttp.ClientTimeout(total=30)
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    
                    print(f"   ✅ Transaction mining successful!")
                    print(f"   📦 Approval ID: {result.get('approval_id')}")
                    print(f"   🧱 Block Number: {result.get('block_number', 'Pending')}")
                    print(f"   💫 Transaction Count: {result.get('transaction_count', 0)}")
                    
                    if result.get('status') == 'executed':
                        print(f"   ⛏️ TRANSACTIONS MINED SUCCESSFULLY!")
                        print(f"   🎯 Batch Result: {result.get('batch_result', {})}")
                    
                    return {
                        "success": True,
                        "agent_id": self.agent_id,
                        "mining_result": result,
                        "transactions_mined": result.get('status') == 'executed',
                        "block_number": result.get('block_number'),
                        "transaction_count": result.get('transaction_count', 0),
                        "approval_id": result.get('approval_id'),
                        "execution_time": datetime.now().isoformat()
                    }
                    
                else:
                    error_text = await response.text()
                    print(f"   ❌ API call failed with status {response.status}: {error_text}")
                    
                    return {
                        "success": False,
                        "agent_id": self.agent_id,
                        "error": f"API call failed: {response.status} - {error_text}",
                        "transactions_mined": False
                    }
                    
        except asyncio.TimeoutError:
            print(f"   ⏰ Transaction mining timed out")
            return {
                "success": False,
                "agent_id": self.agent_id,
                "error": "Transaction mining timed out",
                "transactions_mined": False
            }
            
        except Exception as e:
            print(f"   💥 Transaction mining failed: {str(e)}")
            return {
                "success": False,
                "agent_id": self.agent_id,
                "error": f"Mining failed: {str(e)}",
                "transactions_mined": False
            }
    
    async def get_transaction_status(self, approval_id: str) -> Dict[str, Any]:
        """Get status of previously submitted transactions"""
        
        print(f"📊 {self.agent_id}: Checking status for approval {approval_id}")
        
        # For now, return mock status since we don't have a status endpoint
        # In a full implementation, this would call /api/status/{approval_id}
        return {
            "approval_id": approval_id,
            "status": "executed",
            "agent_id": self.agent_id,
            "last_checked": datetime.now().isoformat()
        }
    
    async def estimate_gas_costs(
        self,
        batch_size: int,
        transaction_type: str = 'payroll'
    ) -> Dict[str, Any]:
        """Estimate gas costs for transaction batch"""
        
        print(f"⛽ {self.agent_id}: Estimating gas for {batch_size} {transaction_type} transactions")
        
        # Base gas estimates (would be more sophisticated in production)
        base_gas_per_tx = {
            'payroll': 25000,
            'swap': 150000,
            'mixed': 100000
        }
        
        gas_per_tx = base_gas_per_tx.get(transaction_type, 100000)
        total_gas = gas_per_tx * batch_size
        
        # Estimate costs (mock gas price)
        gas_price_gwei = 2  # Low for Arcology
        gas_cost_eth = (total_gas * gas_price_gwei) / 1e9
        gas_cost_usd = gas_cost_eth * 2500  # Mock ETH price
        
        # Netting savings (Arcology's advantage)
        netting_efficiency = 0.65  # 65% netting rate
        savings_usd = gas_cost_usd * netting_efficiency
        
        result = {
            "agent_id": self.agent_id,
            "batch_size": batch_size,
            "transaction_type": transaction_type,
            "gas_estimate": {
                "total_gas": total_gas,
                "gas_per_transaction": gas_per_tx,
                "gas_price_gwei": gas_price_gwei,
                "estimated_cost_usd": round(gas_cost_usd, 2),
                "netting_savings_usd": round(savings_usd, 2),
                "final_cost_usd": round(gas_cost_usd - savings_usd, 2)
            },
            "netting_benefits": {
                "efficiency_rate": f"{netting_efficiency * 100}%",
                "parallel_execution": True,
                "mev_protection": True
            }
        }
        
        print(f"   💰 Estimated cost: ${result['gas_estimate']['final_cost_usd']} (${result['gas_estimate']['netting_savings_usd']} saved)")
        
        return result
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "agent_id": self.agent_id,
            "agent_type": "transaction_tool_agent",
            "capabilities": [
                "mine_transactions",
                "batch_processing", 
                "gas_estimation",
                "status_monitoring"
            ],
            "api_endpoints": [
                "/api/approve"
            ],
            "supported_transaction_types": ["payroll", "swap", "mixed"]
        }

# Example usage and testing
async def test_transaction_agent():
    """Test the transaction tool agent"""
    print("🧪 Testing Transaction Tool Agent")
    print("=" * 50)
    
    async with TransactionToolAgent() as agent:
        
        # Test 1: Mine transactions
        print("\n1️⃣ Testing Transaction Mining...")
        mining_result = await agent.mine_transactions(
            analysis_id="test_analysis_001",
            simulation_id=2,
            batch_size=3,
            transaction_type="payroll",
            execute_immediately=True
        )
        
        print(f"Mining Result: {json.dumps(mining_result, indent=2)}")
        
        # Test 2: Gas estimation
        print("\n2️⃣ Testing Gas Estimation...")
        gas_estimate = await agent.estimate_gas_costs(
            batch_size=5,
            transaction_type="payroll"
        )
        
        print(f"Gas Estimate: {json.dumps(gas_estimate, indent=2)}")
        
        # Test 3: Agent info
        print("\n3️⃣ Agent Information...")
        agent_info = agent.get_agent_info()
        print(f"Agent Info: {json.dumps(agent_info, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_transaction_agent())
