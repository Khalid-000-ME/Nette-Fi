"""
User Data Tool Agent - Gets user account info using /api/user
This agent makes real API calls to get user account data and transaction history
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

class UserDataToolAgent:
    """Agent that makes real API calls to get user account information"""
    
    def __init__(self, api_base_url: str = "http://localhost:3000"):
        self.api_base_url = api_base_url
        self.agent_id = f"user_agent_{uuid.uuid4().hex[:8]}"
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def get_user_account_info(
        self,
        user_address: str = None,
        include_balance: bool = True,
        include_history: bool = False
    ) -> Dict[str, Any]:
        """
        Get user account information using /api/user
        
        Args:
            user_address: User wallet address
            include_balance: Whether to include balance information
            include_history: Whether to include transaction history
            
        Returns:
            User account data with balances and history
        """
        
        if user_address is None:
            user_address = "0x8aa62d370585e28fd2333325d3dbaef6112279Ce"  # Default test account
        
        print(f"👤 {self.agent_id}: Getting account info for {user_address[:10]}...")
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            # Prepare API request
            params = {
                "address": user_address,
                "include_balance": str(include_balance).lower(),
                "include_history": str(include_history).lower()
            }
            
            print(f"   📡 Calling /api/user with params: {params}")
            
            # Make API call to get user data
            async with self.session.get(
                f"{self.api_base_url}/api/user",
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    
                    print(f"   ✅ User data retrieved successfully!")
                    
                    # Enhance the result with analysis
                    enhanced_result = {
                        "success": True,
                        "agent_id": self.agent_id,
                        "user_data": result,
                        "account_analysis": self._analyze_account_status(result),
                        "payroll_readiness": self._assess_payroll_readiness(result),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Log key account info
                    if "balance" in result:
                        balance = result["balance"]
                        if isinstance(balance, dict):
                            for token, amount in balance.items():
                                print(f"   💰 {token}: {amount}")
                        else:
                            print(f"   💰 Balance: {balance}")
                    
                    if "account_status" in result:
                        print(f"   📊 Status: {result['account_status']}")
                    
                    return enhanced_result
                    
                else:
                    error_text = await response.text()
                    print(f"   ❌ User API call failed with status {response.status}: {error_text}")
                    
                    return {
                        "success": False,
                        "agent_id": self.agent_id,
                        "error": f"User API failed: {response.status} - {error_text}",
                        "fallback_data": self._get_fallback_user_data(user_address)
                    }
                    
        except asyncio.TimeoutError:
            print(f"   ⏰ User API call timed out")
            return {
                "success": False,
                "agent_id": self.agent_id,
                "error": "User API timed out",
                "fallback_data": self._get_fallback_user_data(user_address)
            }
            
        except Exception as e:
            print(f"   💥 User API call failed: {str(e)}")
            return {
                "success": False,
                "agent_id": self.agent_id,
                "error": f"User data fetch failed: {str(e)}",
                "fallback_data": self._get_fallback_user_data(user_address)
            }
    
    def _analyze_account_status(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user account status"""
        
        analysis = {
            "account_health": "good",
            "transaction_capability": True,
            "risk_factors": [],
            "recommendations": []
        }
        
        # Check balance sufficiency
        if "balance" in user_data:
            balance = user_data["balance"]
            
            if isinstance(balance, dict):
                usdc_balance = balance.get("USDC", 0)
                eth_balance = balance.get("ETH", 0)
                
                if usdc_balance < 1000:
                    analysis["risk_factors"].append("low_usdc_balance")
                    analysis["recommendations"].append("Consider topping up USDC for payroll")
                
                if eth_balance < 0.1:
                    analysis["risk_factors"].append("low_eth_balance")
                    analysis["recommendations"].append("Ensure sufficient ETH for gas fees")
            
            elif isinstance(balance, (int, float)) and balance < 1000:
                analysis["risk_factors"].append("insufficient_balance")
                analysis["account_health"] = "warning"
        
        # Check account status
        account_status = user_data.get("account_status", "unknown")
        if account_status != "active":
            analysis["risk_factors"].append("inactive_account")
            analysis["transaction_capability"] = False
            analysis["account_health"] = "critical"
        
        return analysis
    
    def _assess_payroll_readiness(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess readiness for payroll processing"""
        
        readiness = {
            "ready_for_payroll": True,
            "readiness_score": 100,
            "blocking_issues": [],
            "warnings": []
        }
        
        # Check balance for payroll
        if "balance" in user_data:
            balance = user_data["balance"]
            
            if isinstance(balance, dict):
                usdc_balance = balance.get("USDC", 0)
                
                if usdc_balance < 10000:  # Minimum for small payroll
                    readiness["warnings"].append("Low USDC balance for large payroll")
                    readiness["readiness_score"] -= 20
                
                if usdc_balance < 1000:  # Critical threshold
                    readiness["blocking_issues"].append("Insufficient USDC for payroll")
                    readiness["ready_for_payroll"] = False
                    readiness["readiness_score"] -= 50
        
        # Check account activity
        if user_data.get("account_status") != "active":
            readiness["blocking_issues"].append("Account not active")
            readiness["ready_for_payroll"] = False
            readiness["readiness_score"] = 0
        
        # Check transaction history for patterns
        if "transaction_history" in user_data:
            history = user_data["transaction_history"]
            if isinstance(history, list) and len(history) == 0:
                readiness["warnings"].append("No recent transaction history")
                readiness["readiness_score"] -= 10
        
        return readiness
    
    def _get_fallback_user_data(self, user_address: str) -> Dict[str, Any]:
        """Get fallback user data when API fails"""
        
        return {
            "address": user_address,
            "balance": {
                "USDC": 2000,  # Conservative fallback
                "ETH": 0.5,
                "DAI": 1000
            },
            "account_status": "active",
            "last_transaction": datetime.now().isoformat(),
            "transaction_count": 25,
            "note": "Using fallback data due to API failure"
        }
    
    async def get_scheduled_transactions(self, user_address: str = None) -> Dict[str, Any]:
        """Get user's scheduled transactions"""
        
        if user_address is None:
            user_address = "0x8aa62d370585e28fd2333325d3dbaef6112279Ce"
        
        print(f"📅 {self.agent_id}: Getting scheduled transactions for {user_address[:10]}...")
        
        # Mock implementation - would call actual API in production
        return {
            "agent_id": self.agent_id,
            "user_address": user_address,
            "scheduled_transactions": [
                {
                    "id": "sched_001",
                    "type": "payroll",
                    "amount": 25000,
                    "currency": "USDC",
                    "scheduled_time": "2025-10-25T12:00:00Z",
                    "status": "pending"
                },
                {
                    "id": "sched_002", 
                    "type": "recurring_payment",
                    "amount": 5000,
                    "currency": "USDC",
                    "scheduled_time": "2025-10-30T09:00:00Z",
                    "status": "pending"
                }
            ],
            "total_scheduled_amount": 30000,
            "next_execution": "2025-10-25T12:00:00Z"
        }
    
    async def validate_payroll_capacity(
        self,
        payroll_amount: float,
        employee_count: int,
        user_address: str = None
    ) -> Dict[str, Any]:
        """Validate if user can process payroll of given size"""
        
        print(f"✅ {self.agent_id}: Validating payroll capacity for ${payroll_amount:,}")
        
        # Get current account info
        account_info = await self.get_user_account_info(user_address, include_balance=True)
        
        validation = {
            "agent_id": self.agent_id,
            "payroll_amount": payroll_amount,
            "employee_count": employee_count,
            "can_process": False,
            "validation_details": {},
            "recommendations": []
        }
        
        if account_info["success"]:
            user_data = account_info["user_data"]
            balance = user_data.get("balance", {})
            
            if isinstance(balance, dict):
                usdc_balance = balance.get("USDC", 0)
                
                # Check balance sufficiency (including gas buffer)
                gas_buffer = employee_count * 10  # $10 per employee for gas
                total_needed = payroll_amount + gas_buffer
                
                validation["validation_details"] = {
                    "current_usdc_balance": usdc_balance,
                    "payroll_amount": payroll_amount,
                    "estimated_gas_cost": gas_buffer,
                    "total_needed": total_needed,
                    "surplus_deficit": usdc_balance - total_needed
                }
                
                if usdc_balance >= total_needed:
                    validation["can_process"] = True
                    validation["recommendations"].append("Sufficient balance for payroll processing")
                else:
                    deficit = total_needed - usdc_balance
                    validation["recommendations"].append(f"Need additional ${deficit:,.2f} USDC")
                    validation["recommendations"].append("Consider reducing batch size or topping up balance")
        else:
            validation["recommendations"].append("Could not verify account balance - proceed with caution")
        
        return validation
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "agent_id": self.agent_id,
            "agent_type": "user_data_tool_agent",
            "capabilities": [
                "account_info_retrieval",
                "balance_checking",
                "payroll_readiness_assessment",
                "transaction_history",
                "capacity_validation"
            ],
            "api_endpoints": [
                "/api/user"
            ],
            "supported_tokens": ["USDC", "ETH", "DAI"]
        }

# Example usage and testing
async def test_user_data_agent():
    """Test the user data tool agent"""
    print("🧪 Testing User Data Tool Agent")
    print("=" * 50)
    
    async with UserDataToolAgent() as agent:
        
        # Test 1: Get account info
        print("\n1️⃣ Testing Account Info Retrieval...")
        account_result = await agent.get_user_account_info(
            include_balance=True,
            include_history=True
        )
        
        print(f"Account Result: {json.dumps(account_result, indent=2)}")
        
        # Test 2: Validate payroll capacity
        print("\n2️⃣ Testing Payroll Capacity Validation...")
        capacity_result = await agent.validate_payroll_capacity(
            payroll_amount=50000,
            employee_count=5
        )
        
        print(f"Capacity Result: {json.dumps(capacity_result, indent=2)}")
        
        # Test 3: Get scheduled transactions
        print("\n3️⃣ Testing Scheduled Transactions...")
        scheduled_result = await agent.get_scheduled_transactions()
        
        print(f"Scheduled Result: {json.dumps(scheduled_result, indent=2)}")
        
        # Test 4: Agent info
        print("\n4️⃣ Agent Information...")
        agent_info = agent.get_agent_info()
        print(f"Agent Info: {json.dumps(agent_info, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_user_data_agent())
