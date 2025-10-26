"""
User Data Agent - Handles user transaction history and account management
Integrates with frontend /api/user route for user-specific data
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
from datetime import datetime
import uuid

from .chat_protocol import ASIChatProtocol, ToolCallRequest, ToolCallResponse

class UserDataAgent:
    """
    User Data Agent for managing user transactions and account information
    
    Features:
    - Integration with /api/user route
    - Transaction history tracking
    - User preference management
    - Scheduled transaction monitoring
    """
    
    def __init__(self, agent_port: int = 8013):
        self.agent = Agent(
            name="user_data_agent",
            seed="user_data_agent_seed_44444",
            port=agent_port,
            endpoint=[f"http://localhost:{agent_port}/submit"]
        )
        
        self.agent_id = "user_data_agent"
        self.agent_type = "user_management"
        self.name = "User Data Agent"
        
        self.frontend_api_base = "http://localhost:3000/api"
        self.chat_protocol = ASIChatProtocol()
        self.user_cache: Dict[str, Dict[str, Any]] = {}
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        @self.agent.on_event("startup")
        async def startup_handler(ctx: Context):
            ctx.logger.info(f"User Data Agent started: {ctx.agent.address}")
            
            self.chat_protocol.register_agent(
                agent_id=self.agent_id,
                agent_address=ctx.agent.address,
                agent_type=self.agent_type,
                capabilities=["user_data", "transaction_history", "preferences", "scheduling"]
            )
        
        @self.agent.on_message(model=ToolCallRequest)
        async def handle_tool_call(ctx: Context, sender: str, msg: ToolCallRequest):
            result = {}
            success = True
            
            try:
                if msg.tool_name == "get_user_data":
                    result = await self._get_user_data(msg.parameters)
                elif msg.tool_name == "get_transaction_history":
                    result = await self._get_transaction_history(msg.parameters)
                elif msg.tool_name == "get_scheduled_transactions":
                    result = await self._get_scheduled_transactions(msg.parameters)
                elif msg.tool_name == "update_user_preferences":
                    result = await self._update_user_preferences(msg.parameters)
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
        
        @self.agent.on_message(model=ChatMessage)
        async def handle_chat_message(ctx: Context, sender: str, msg: ChatMessage):
            for item in msg.content:
                if isinstance(item, TextContent):
                    response_text = await self._process_user_query(item.text)
                    
                    ack = ChatAcknowledgement(
                        timestamp=datetime.utcnow(),
                        acknowledged_msg_id=msg.msg_id
                    )
                    await ctx.send(sender, ack)
                    
                    if response_text:
                        response = ChatMessage(
                            timestamp=datetime.utcnow(),
                            msg_id=uuid.uuid4(),
                            content=[TextContent(type="text", text=response_text)]
                        )
                        await ctx.send(sender, response)
    
    async def _get_user_data(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get user account data via frontend API"""
        
        user_address = parameters.get("user_address")
        if not user_address:
            return {"error": "user_address required"}
        
        try:
            response = requests.get(
                f"{self.frontend_api_base}/user",
                params={"address": user_address},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Cache user data
                self.user_cache[user_address] = {
                    **result,
                    "last_updated": datetime.utcnow().isoformat()
                }
                
                # Enhanced user profile
                enhanced_result = {
                    **result,
                    "profile_analysis": self._analyze_user_profile(result),
                    "recommendations": self._get_user_recommendations(result),
                    "risk_profile": self._assess_user_risk_profile(result)
                }
                
                return enhanced_result
            else:
                return {"error": f"User API failed: {response.status_code}"}
        
        except Exception as e:
            return {"error": f"Failed to get user data: {str(e)}"}
    
    def _analyze_user_profile(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze user trading profile"""
        
        transaction_count = user_data.get("transaction_count", 0)
        total_volume = user_data.get("total_volume_usd", 0)
        avg_transaction_size = total_volume / max(transaction_count, 1)
        
        # User classification
        if transaction_count > 100 and total_volume > 100000:
            user_tier = "power_user"
        elif transaction_count > 20 and total_volume > 10000:
            user_tier = "active_user"
        elif transaction_count > 5:
            user_tier = "regular_user"
        else:
            user_tier = "new_user"
        
        return {
            "user_tier": user_tier,
            "transaction_count": transaction_count,
            "total_volume_usd": total_volume,
            "average_transaction_size": round(avg_transaction_size, 2),
            "activity_level": self._calculate_activity_level(user_data)
        }
    
    def _calculate_activity_level(self, user_data: Dict[str, Any]) -> str:
        """Calculate user activity level"""
        
        last_transaction = user_data.get("last_transaction_date")
        if not last_transaction:
            return "inactive"
        
        try:
            last_tx_date = datetime.fromisoformat(last_transaction.replace('Z', '+00:00'))
            days_since_last = (datetime.utcnow() - last_tx_date.replace(tzinfo=None)).days
            
            if days_since_last <= 1:
                return "very_active"
            elif days_since_last <= 7:
                return "active"
            elif days_since_last <= 30:
                return "moderate"
            else:
                return "inactive"
        except:
            return "unknown"
    
    def _get_user_recommendations(self, user_data: Dict[str, Any]) -> List[str]:
        """Get personalized recommendations for user"""
        
        recommendations = []
        transaction_count = user_data.get("transaction_count", 0)
        total_volume = user_data.get("total_volume_usd", 0)
        
        if transaction_count < 5:
            recommendations.extend([
                "Start with smaller transactions to get familiar with the platform",
                "Enable transaction notifications for better tracking"
            ])
        
        if total_volume > 50000:
            recommendations.extend([
                "Consider using batch transactions for gas optimization",
                "Enable MEV protection for large trades"
            ])
        
        # Check for scheduled transactions
        if user_data.get("has_scheduled_transactions", False):
            recommendations.append("Review your scheduled transactions for optimal timing")
        
        return recommendations
    
    def _assess_user_risk_profile(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess user's risk profile based on transaction history"""
        
        avg_transaction_size = user_data.get("total_volume_usd", 0) / max(user_data.get("transaction_count", 1), 1)
        failed_transactions = user_data.get("failed_transaction_count", 0)
        total_transactions = user_data.get("transaction_count", 1)
        
        # Risk scoring
        risk_score = 50  # Base score
        
        if avg_transaction_size > 10000:
            risk_score += 20  # Higher risk for large transactions
        elif avg_transaction_size < 100:
            risk_score -= 10  # Lower risk for small transactions
        
        failure_rate = failed_transactions / total_transactions
        if failure_rate > 0.1:
            risk_score += 15  # Higher risk if many failed transactions
        
        # Risk classification
        if risk_score > 70:
            risk_level = "high"
        elif risk_score > 40:
            risk_level = "medium"
        else:
            risk_level = "low"
        
        return {
            "risk_score": min(100, max(0, risk_score)),
            "risk_level": risk_level,
            "failure_rate": round(failure_rate * 100, 2),
            "average_transaction_size": round(avg_transaction_size, 2),
            "risk_factors": self._identify_risk_factors(user_data, failure_rate, avg_transaction_size)
        }
    
    def _identify_risk_factors(self, user_data: Dict[str, Any], failure_rate: float, avg_size: float) -> List[str]:
        """Identify specific risk factors for the user"""
        
        risk_factors = []
        
        if failure_rate > 0.15:
            risk_factors.append("High transaction failure rate")
        
        if avg_size > 50000:
            risk_factors.append("Large average transaction size increases MEV risk")
        
        if user_data.get("transaction_count", 0) < 10:
            risk_factors.append("Limited transaction history")
        
        activity_level = self._calculate_activity_level(user_data)
        if activity_level == "inactive":
            risk_factors.append("Inactive user - may lack recent market knowledge")
        
        return risk_factors
    
    async def _get_transaction_history(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get user transaction history"""
        
        user_address = parameters.get("user_address")
        limit = parameters.get("limit", 50)
        
        if not user_address:
            return {"error": "user_address required"}
        
        try:
            response = requests.get(
                f"{self.frontend_api_base}/user/transactions",
                params={"address": user_address, "limit": limit},
                timeout=15
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Analyze transaction patterns
                analysis = self._analyze_transaction_patterns(result.get("transactions", []))
                
                return {
                    **result,
                    "pattern_analysis": analysis,
                    "summary": self._generate_transaction_summary(result.get("transactions", []))
                }
            else:
                return {"error": f"Transaction history API failed: {response.status_code}"}
        
        except Exception as e:
            return {"error": f"Failed to get transaction history: {str(e)}"}
    
    def _analyze_transaction_patterns(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze patterns in user transactions"""
        
        if not transactions:
            return {"pattern": "no_data"}
        
        # Analyze transaction timing
        transaction_hours = []
        transaction_amounts = []
        
        for tx in transactions:
            try:
                tx_time = datetime.fromisoformat(tx.get("timestamp", "").replace('Z', '+00:00'))
                transaction_hours.append(tx_time.hour)
                transaction_amounts.append(float(tx.get("amount_usd", 0)))
            except:
                continue
        
        # Find most active hours
        if transaction_hours:
            most_active_hour = max(set(transaction_hours), key=transaction_hours.count)
        else:
            most_active_hour = None
        
        # Analyze transaction sizes
        if transaction_amounts:
            avg_amount = sum(transaction_amounts) / len(transaction_amounts)
            max_amount = max(transaction_amounts)
            min_amount = min(transaction_amounts)
        else:
            avg_amount = max_amount = min_amount = 0
        
        return {
            "most_active_hour": most_active_hour,
            "average_amount_usd": round(avg_amount, 2),
            "max_transaction_usd": round(max_amount, 2),
            "min_transaction_usd": round(min_amount, 2),
            "transaction_frequency": len(transactions),
            "preferred_trading_time": "morning" if most_active_hour and most_active_hour < 12 else "afternoon" if most_active_hour and most_active_hour < 18 else "evening"
        }
    
    def _generate_transaction_summary(self, transactions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate summary of user transactions"""
        
        total_transactions = len(transactions)
        successful_transactions = len([tx for tx in transactions if tx.get("status") == "success"])
        failed_transactions = total_transactions - successful_transactions
        
        total_volume = sum(float(tx.get("amount_usd", 0)) for tx in transactions)
        
        return {
            "total_transactions": total_transactions,
            "successful_transactions": successful_transactions,
            "failed_transactions": failed_transactions,
            "success_rate": round((successful_transactions / max(total_transactions, 1)) * 100, 2),
            "total_volume_usd": round(total_volume, 2),
            "period_covered": self._calculate_period_covered(transactions)
        }
    
    def _calculate_period_covered(self, transactions: List[Dict[str, Any]]) -> str:
        """Calculate the time period covered by transactions"""
        
        if not transactions:
            return "no_data"
        
        try:
            timestamps = [datetime.fromisoformat(tx.get("timestamp", "").replace('Z', '+00:00')) 
                         for tx in transactions if tx.get("timestamp")]
            
            if timestamps:
                earliest = min(timestamps)
                latest = max(timestamps)
                days_covered = (latest - earliest).days
                
                if days_covered < 1:
                    return "less_than_1_day"
                elif days_covered < 7:
                    return f"{days_covered}_days"
                elif days_covered < 30:
                    return f"{days_covered // 7}_weeks"
                else:
                    return f"{days_covered // 30}_months"
            else:
                return "unknown"
        except:
            return "unknown"
    
    async def _get_scheduled_transactions(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get user's scheduled transactions"""
        
        user_address = parameters.get("user_address")
        
        if not user_address:
            return {"error": "user_address required"}
        
        try:
            response = requests.get(
                f"{self.frontend_api_base}/user/scheduled",
                params={"address": user_address},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Analyze scheduled transactions
                scheduled_analysis = self._analyze_scheduled_transactions(result.get("scheduled_transactions", []))
                
                return {
                    **result,
                    "schedule_analysis": scheduled_analysis,
                    "optimization_suggestions": self._get_scheduling_suggestions(result.get("scheduled_transactions", []))
                }
            else:
                return {"error": f"Scheduled transactions API failed: {response.status_code}"}
        
        except Exception as e:
            return {"error": f"Failed to get scheduled transactions: {str(e)}"}
    
    def _analyze_scheduled_transactions(self, scheduled_txs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze scheduled transactions"""
        
        if not scheduled_txs:
            return {"status": "no_scheduled_transactions"}
        
        # Analyze scheduling patterns
        execution_times = []
        total_value = 0
        
        for tx in scheduled_txs:
            try:
                exec_time = datetime.fromisoformat(tx.get("scheduled_time", "").replace('Z', '+00:00'))
                execution_times.append(exec_time)
                total_value += float(tx.get("amount_usd", 0))
            except:
                continue
        
        # Find next execution
        now = datetime.utcnow()
        future_executions = [t for t in execution_times if t > now]
        next_execution = min(future_executions) if future_executions else None
        
        return {
            "total_scheduled": len(scheduled_txs),
            "total_value_usd": round(total_value, 2),
            "next_execution": next_execution.isoformat() if next_execution else None,
            "time_to_next": str(next_execution - now) if next_execution else None,
            "scheduling_frequency": self._calculate_scheduling_frequency(execution_times)
        }
    
    def _calculate_scheduling_frequency(self, execution_times: List[datetime]) -> str:
        """Calculate how frequently user schedules transactions"""
        
        if len(execution_times) < 2:
            return "insufficient_data"
        
        # Calculate average time between scheduled transactions
        execution_times.sort()
        intervals = [(execution_times[i+1] - execution_times[i]).days 
                    for i in range(len(execution_times)-1)]
        
        if intervals:
            avg_interval = sum(intervals) / len(intervals)
            
            if avg_interval < 1:
                return "daily"
            elif avg_interval < 7:
                return "weekly"
            elif avg_interval < 30:
                return "monthly"
            else:
                return "irregular"
        
        return "unknown"
    
    def _get_scheduling_suggestions(self, scheduled_txs: List[Dict[str, Any]]) -> List[str]:
        """Get suggestions for optimizing scheduled transactions"""
        
        suggestions = []
        
        if not scheduled_txs:
            suggestions.append("Consider scheduling regular transactions for better gas optimization")
            return suggestions
        
        # Check for clustering
        execution_times = []
        for tx in scheduled_txs:
            try:
                exec_time = datetime.fromisoformat(tx.get("scheduled_time", "").replace('Z', '+00:00'))
                execution_times.append(exec_time)
            except:
                continue
        
        if len(execution_times) > 1:
            execution_times.sort()
            close_executions = 0
            
            for i in range(len(execution_times)-1):
                if (execution_times[i+1] - execution_times[i]).total_seconds() < 3600:  # Within 1 hour
                    close_executions += 1
            
            if close_executions > 0:
                suggestions.append("Consider batching transactions scheduled within 1 hour of each other")
        
        # Check for off-peak scheduling
        peak_hours = [9, 10, 11, 14, 15, 16]  # Typical high-activity hours
        peak_scheduled = sum(1 for t in execution_times if t.hour in peak_hours)
        
        if peak_scheduled > len(execution_times) * 0.7:
            suggestions.append("Consider scheduling some transactions during off-peak hours for better gas prices")
        
        return suggestions
    
    async def _update_user_preferences(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Update user preferences"""
        
        user_address = parameters.get("user_address")
        preferences = parameters.get("preferences", {})
        
        if not user_address:
            return {"error": "user_address required"}
        
        try:
            response = requests.post(
                f"{self.frontend_api_base}/user/preferences",
                json={"address": user_address, "preferences": preferences},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Update cache
                if user_address in self.user_cache:
                    self.user_cache[user_address]["preferences"] = preferences
                    self.user_cache[user_address]["last_updated"] = datetime.utcnow().isoformat()
                
                return {
                    **result,
                    "updated_preferences": preferences,
                    "timestamp": datetime.utcnow().isoformat()
                }
            else:
                return {"error": f"Preferences update failed: {response.status_code}"}
        
        except Exception as e:
            return {"error": f"Failed to update preferences: {str(e)}"}
    
    async def _process_user_query(self, query: str) -> Optional[str]:
        """Process chat queries about user data"""
        
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in ['history', 'transactions', 'account', 'profile']):
            if 'history' in query_lower or 'transactions' in query_lower:
                return "I can provide your transaction history and analyze your trading patterns. What's your wallet address?"
            elif 'scheduled' in query_lower:
                return "I can show your scheduled transactions and suggest optimizations. Provide your address to get started."
            elif 'preferences' in query_lower:
                return "I can help update your trading preferences and risk settings. What would you like to change?"
            else:
                return "I manage user data including transaction history, preferences, and scheduled transactions. How can I help?"
        
        return None
    
    async def start_agent(self):
        """Start the user data agent"""
        await self.agent.run()

# Global instance for import
user_data_agent = UserDataAgent()
