"""
Net Status Agent - Handles Arcology netted layer status and monitoring
Integrates with frontend /api/net_status route for real-time netting data
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

class NetStatusAgent:
    """
    Net Status Agent for monitoring Arcology netted transaction layer
    
    Features:
    - Integration with /api/net_status route
    - Real-time netting statistics
    - Network health monitoring
    - Performance analytics
    """
    
    def __init__(self, agent_port: int = 8014):
        self.agent = Agent(
            name="net_status_agent",
            seed="net_status_agent_seed_55555",
            port=agent_port,
            endpoint=[f"http://localhost:{agent_port}/submit"]
        )
        
        self.agent_id = "net_status_agent"
        self.agent_type = "network_monitoring"
        self.name = "Net Status Agent"
        
        self.frontend_api_base = "http://localhost:3000/api"
        self.chat_protocol = ASIChatProtocol()
        self.status_cache: Dict[str, Any] = {}
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        @self.agent.on_event("startup")
        async def startup_handler(ctx: Context):
            ctx.logger.info(f"Net Status Agent started: {ctx.agent.address}")
            
            self.chat_protocol.register_agent(
                agent_id=self.agent_id,
                agent_address=ctx.agent.address,
                agent_type=self.agent_type,
                capabilities=["network_status", "netting_analytics", "performance_monitoring", "health_checks"]
            )
        
        @self.agent.on_message(model=ToolCallRequest)
        async def handle_tool_call(ctx: Context, sender: str, msg: ToolCallRequest):
            result = {}
            success = True
            
            try:
                if msg.tool_name == "get_net_status":
                    result = await self._get_net_status(msg.parameters)
                elif msg.tool_name == "analyze_netting_performance":
                    result = await self._analyze_netting_performance(msg.parameters)
                elif msg.tool_name == "monitor_network_health":
                    result = await self._monitor_network_health(msg.parameters)
                elif msg.tool_name == "get_efficiency_metrics":
                    result = await self._get_efficiency_metrics(msg.parameters)
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
                    response_text = await self._process_status_query(item.text)
                    
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
    
    async def _get_net_status(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get network status via frontend API"""
        
        detailed = parameters.get("detailed", False)
        
        try:
            response = requests.get(
                f"{self.frontend_api_base}/net_status",
                params={"detailed": "true" if detailed else "false"},
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Cache the result
                self.status_cache = {
                    **result,
                    "last_updated": datetime.utcnow().isoformat()
                }
                
                # Enhanced analysis
                enhanced_result = {
                    **result,
                    "performance_analysis": self._analyze_performance(result),
                    "health_status": self._assess_network_health(result),
                    "optimization_suggestions": self._get_optimization_suggestions(result)
                }
                
                return enhanced_result
            else:
                return {"error": f"Net status API failed: {response.status_code}"}
        
        except Exception as e:
            return {"error": f"Failed to get network status: {str(e)}"}
    
    def _analyze_performance(self, status_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze network performance metrics"""
        
        current_batch = status_data.get("currentBatch", {})
        stats = status_data.get("stats", {})
        
        # Extract key metrics
        total_swaps = int(stats.get("totalSwaps", 0))
        total_netted = int(stats.get("totalNetted", 0))
        active_requests = int(stats.get("activeRequests", 0))
        gas_saved = int(stats.get("totalGasSaved", 0))
        
        # Calculate performance indicators
        netting_rate = (total_netted / max(total_swaps, 1)) * 100
        efficiency_score = min(100, netting_rate + (gas_saved / 1000))
        
        # Performance classification
        if efficiency_score > 80:
            performance_level = "excellent"
        elif efficiency_score > 60:
            performance_level = "good"
        elif efficiency_score > 40:
            performance_level = "fair"
        else:
            performance_level = "poor"
        
        return {
            "netting_rate_percent": round(netting_rate, 2),
            "efficiency_score": round(efficiency_score, 2),
            "performance_level": performance_level,
            "total_transactions_processed": total_swaps,
            "successful_netting_operations": total_netted,
            "pending_requests": active_requests,
            "cumulative_gas_savings": gas_saved
        }
    
    def _assess_network_health(self, status_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess overall network health"""
        
        network = status_data.get("network", {})
        current_batch = status_data.get("currentBatch", {})
        
        # Health indicators
        is_connected = network.get("isConnected", False)
        current_block = network.get("currentBlock", {})
        parallel_threads = network.get("parallelThreads", 0)
        
        health_score = 0
        health_issues = []
        
        # Connection health
        if is_connected:
            health_score += 30
        else:
            health_issues.append("Network connection issues")
        
        # Block processing health
        if current_block and current_block.get("number", 0) > 0:
            health_score += 25
        else:
            health_issues.append("Block processing issues")
        
        # Threading health
        if parallel_threads >= 10:
            health_score += 25
        elif parallel_threads >= 5:
            health_score += 15
        else:
            health_issues.append("Insufficient parallel processing capacity")
        
        # Processing mode health
        processing_mode = current_batch.get("processingMode", "")
        if processing_mode == "immediate-netting":
            health_score += 20
        elif processing_mode == "real-time-processing":
            health_score += 15
        else:
            health_issues.append("Suboptimal processing mode")
        
        # Overall health classification
        if health_score >= 90:
            health_status = "excellent"
        elif health_score >= 70:
            health_status = "good"
        elif health_score >= 50:
            health_status = "fair"
        else:
            health_status = "poor"
        
        return {
            "health_score": health_score,
            "health_status": health_status,
            "is_operational": is_connected and health_score >= 50,
            "health_issues": health_issues,
            "uptime_status": "operational" if is_connected else "degraded",
            "processing_capacity": f"{parallel_threads} threads"
        }
    
    def _get_optimization_suggestions(self, status_data: Dict[str, Any]) -> List[str]:
        """Get optimization suggestions based on current status"""
        
        suggestions = []
        performance_analysis = self._analyze_performance(status_data)
        health_status = self._assess_network_health(status_data)
        
        # Performance-based suggestions
        netting_rate = performance_analysis.get("netting_rate_percent", 0)
        if netting_rate < 50:
            suggestions.append("Low netting rate detected - consider batching similar transactions")
        
        active_requests = int(status_data.get("stats", {}).get("activeRequests", 0))
        if active_requests > 50:
            suggestions.append("High number of active requests - optimal for netting opportunities")
        elif active_requests < 10:
            suggestions.append("Low activity period - good time for maintenance operations")
        
        # Health-based suggestions
        if health_status.get("health_score", 0) < 70:
            suggestions.extend([
                "Network health is suboptimal - monitor for issues",
                "Consider reducing transaction load temporarily"
            ])
        
        # Threading suggestions
        parallel_threads = status_data.get("network", {}).get("parallelThreads", 0)
        if parallel_threads < 10:
            suggestions.append("Consider increasing parallel processing threads for better performance")
        
        return suggestions
    
    async def _analyze_netting_performance(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze netting performance over time"""
        
        # Get current status
        status_data = await self._get_net_status({"detailed": True})
        
        if "error" in status_data:
            return status_data
        
        performance_analysis = status_data.get("performance_analysis", {})
        stats = status_data.get("stats", {})
        
        # Historical performance simulation (in real implementation, this would use actual historical data)
        historical_metrics = self._simulate_historical_performance(stats)
        
        return {
            "current_performance": performance_analysis,
            "historical_trends": historical_metrics,
            "performance_comparison": self._compare_performance(performance_analysis, historical_metrics),
            "optimization_opportunities": self._identify_optimization_opportunities(performance_analysis, historical_metrics)
        }
    
    def _simulate_historical_performance(self, current_stats: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate historical performance data"""
        
        # This would be replaced with actual historical data in production
        current_swaps = int(current_stats.get("totalSwaps", 0))
        current_netted = int(current_stats.get("totalNetted", 0))
        
        return {
            "24h_ago": {
                "total_swaps": max(0, current_swaps - 50),
                "total_netted": max(0, current_netted - 20),
                "netting_rate": 35.0
            },
            "7d_ago": {
                "total_swaps": max(0, current_swaps - 200),
                "total_netted": max(0, current_netted - 80),
                "netting_rate": 30.0
            },
            "30d_ago": {
                "total_swaps": max(0, current_swaps - 1000),
                "total_netted": max(0, current_netted - 400),
                "netting_rate": 25.0
            }
        }
    
    def _compare_performance(self, current: Dict[str, Any], historical: Dict[str, Any]) -> Dict[str, Any]:
        """Compare current performance with historical data"""
        
        current_rate = current.get("netting_rate_percent", 0)
        rate_24h = historical.get("24h_ago", {}).get("netting_rate", 0)
        rate_7d = historical.get("7d_ago", {}).get("netting_rate", 0)
        
        return {
            "24h_change": round(current_rate - rate_24h, 2),
            "7d_change": round(current_rate - rate_7d, 2),
            "trend": "improving" if current_rate > rate_24h else "declining" if current_rate < rate_24h else "stable",
            "performance_trajectory": "upward" if current_rate > rate_7d else "downward" if current_rate < rate_7d else "flat"
        }
    
    def _identify_optimization_opportunities(self, current: Dict[str, Any], historical: Dict[str, Any]) -> List[str]:
        """Identify optimization opportunities"""
        
        opportunities = []
        current_rate = current.get("netting_rate_percent", 0)
        efficiency_score = current.get("efficiency_score", 0)
        
        if current_rate < 40:
            opportunities.append("Netting rate below optimal - investigate transaction patterns")
        
        if efficiency_score < 60:
            opportunities.append("Overall efficiency can be improved - optimize gas usage")
        
        pending_requests = current.get("pending_requests", 0)
        if pending_requests > 100:
            opportunities.append("High pending requests - opportunity for batch processing")
        
        return opportunities
    
    async def _monitor_network_health(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor network health indicators"""
        
        # Get current status
        status_data = await self._get_net_status({"detailed": True})
        
        if "error" in status_data:
            return status_data
        
        health_status = status_data.get("health_status", {})
        network_info = status_data.get("network", {})
        
        # Additional health checks
        health_checks = {
            "connectivity": self._check_connectivity(network_info),
            "processing_capacity": self._check_processing_capacity(network_info),
            "transaction_flow": self._check_transaction_flow(status_data),
            "resource_utilization": self._check_resource_utilization(status_data)
        }
        
        # Overall health assessment
        passed_checks = sum(1 for check in health_checks.values() if check.get("status") == "healthy")
        total_checks = len(health_checks)
        overall_health = (passed_checks / total_checks) * 100
        
        return {
            "overall_health_percent": round(overall_health, 2),
            "health_status": health_status,
            "detailed_checks": health_checks,
            "recommendations": self._get_health_recommendations(health_checks),
            "monitoring_timestamp": datetime.utcnow().isoformat()
        }
    
    def _check_connectivity(self, network_info: Dict[str, Any]) -> Dict[str, Any]:
        """Check network connectivity"""
        
        is_connected = network_info.get("isConnected", False)
        current_block = network_info.get("currentBlock", {})
        
        if is_connected and current_block.get("number", 0) > 0:
            return {"status": "healthy", "message": "Network connectivity is good"}
        else:
            return {"status": "unhealthy", "message": "Network connectivity issues detected"}
    
    def _check_processing_capacity(self, network_info: Dict[str, Any]) -> Dict[str, Any]:
        """Check processing capacity"""
        
        parallel_threads = network_info.get("parallelThreads", 0)
        
        if parallel_threads >= 15:
            return {"status": "healthy", "message": f"Excellent processing capacity: {parallel_threads} threads"}
        elif parallel_threads >= 10:
            return {"status": "healthy", "message": f"Good processing capacity: {parallel_threads} threads"}
        elif parallel_threads >= 5:
            return {"status": "warning", "message": f"Moderate processing capacity: {parallel_threads} threads"}
        else:
            return {"status": "unhealthy", "message": f"Low processing capacity: {parallel_threads} threads"}
    
    def _check_transaction_flow(self, status_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check transaction flow health"""
        
        current_batch = status_data.get("currentBatch", {})
        active_requests = current_batch.get("activeRequests", 0)
        processing_mode = current_batch.get("processingMode", "")
        
        if processing_mode in ["immediate-netting", "real-time-processing"] and active_requests >= 0:
            return {"status": "healthy", "message": f"Transaction flow is normal: {active_requests} active requests"}
        else:
            return {"status": "warning", "message": "Transaction flow may be suboptimal"}
    
    def _check_resource_utilization(self, status_data: Dict[str, Any]) -> Dict[str, Any]:
        """Check resource utilization"""
        
        stats = status_data.get("stats", {})
        total_swaps = int(stats.get("totalSwaps", 0))
        gas_saved = int(stats.get("totalGasSaved", 0))
        
        # Simple resource efficiency check
        if total_swaps > 0 and gas_saved > 0:
            efficiency = gas_saved / total_swaps
            if efficiency > 1000:  # Good gas savings per transaction
                return {"status": "healthy", "message": "Excellent resource utilization"}
            else:
                return {"status": "warning", "message": "Resource utilization could be improved"}
        else:
            return {"status": "warning", "message": "Insufficient data for resource utilization assessment"}
    
    def _get_health_recommendations(self, health_checks: Dict[str, Any]) -> List[str]:
        """Get health-based recommendations"""
        
        recommendations = []
        
        for check_name, check_result in health_checks.items():
            if check_result.get("status") == "unhealthy":
                if check_name == "connectivity":
                    recommendations.append("Check network connection and RPC endpoint")
                elif check_name == "processing_capacity":
                    recommendations.append("Increase parallel processing threads")
                elif check_name == "transaction_flow":
                    recommendations.append("Investigate transaction processing bottlenecks")
                elif check_name == "resource_utilization":
                    recommendations.append("Optimize resource usage and gas efficiency")
        
        if not recommendations:
            recommendations.append("All health checks passed - system is operating optimally")
        
        return recommendations
    
    async def _get_efficiency_metrics(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Get detailed efficiency metrics"""
        
        # Get current status
        status_data = await self._get_net_status({"detailed": True})
        
        if "error" in status_data:
            return status_data
        
        stats = status_data.get("stats", {})
        performance_analysis = status_data.get("performance_analysis", {})
        
        # Calculate detailed efficiency metrics
        total_swaps = int(stats.get("totalSwaps", 0))
        total_netted = int(stats.get("totalNetted", 0))
        gas_saved = int(stats.get("totalGasSaved", 0))
        active_requests = int(stats.get("activeRequests", 0))
        
        efficiency_metrics = {
            "netting_efficiency": {
                "rate": performance_analysis.get("netting_rate_percent", 0),
                "absolute_netted": total_netted,
                "potential_savings": total_swaps - total_netted if total_swaps > total_netted else 0
            },
            "gas_efficiency": {
                "total_saved": gas_saved,
                "average_per_transaction": gas_saved / max(total_swaps, 1),
                "efficiency_rating": "high" if gas_saved > 10000 else "medium" if gas_saved > 1000 else "low"
            },
            "throughput_efficiency": {
                "active_requests": active_requests,
                "processing_rate": "optimal" if active_requests < 100 else "high_load",
                "capacity_utilization": min(100, (active_requests / 200) * 100)  # Assuming 200 is max capacity
            },
            "overall_efficiency": performance_analysis.get("efficiency_score", 0)
        }
        
        return {
            "efficiency_metrics": efficiency_metrics,
            "benchmark_comparison": self._compare_with_benchmarks(efficiency_metrics),
            "improvement_suggestions": self._get_efficiency_improvements(efficiency_metrics)
        }
    
    def _compare_with_benchmarks(self, metrics: Dict[str, Any]) -> Dict[str, Any]:
        """Compare metrics with industry benchmarks"""
        
        # Simplified benchmark comparison
        netting_rate = metrics.get("netting_efficiency", {}).get("rate", 0)
        gas_efficiency = metrics.get("gas_efficiency", {}).get("efficiency_rating", "low")
        overall_efficiency = metrics.get("overall_efficiency", 0)
        
        return {
            "netting_rate_vs_benchmark": "above" if netting_rate > 40 else "below",
            "gas_efficiency_vs_benchmark": "above" if gas_efficiency in ["high", "medium"] else "below",
            "overall_performance": "excellent" if overall_efficiency > 80 else "good" if overall_efficiency > 60 else "needs_improvement"
        }
    
    def _get_efficiency_improvements(self, metrics: Dict[str, Any]) -> List[str]:
        """Get efficiency improvement suggestions"""
        
        improvements = []
        
        netting_rate = metrics.get("netting_efficiency", {}).get("rate", 0)
        if netting_rate < 50:
            improvements.append("Increase netting rate by encouraging complementary transactions")
        
        gas_rating = metrics.get("gas_efficiency", {}).get("efficiency_rating", "low")
        if gas_rating == "low":
            improvements.append("Optimize gas usage through better transaction batching")
        
        capacity_util = metrics.get("throughput_efficiency", {}).get("capacity_utilization", 0)
        if capacity_util > 80:
            improvements.append("Consider scaling processing capacity")
        elif capacity_util < 20:
            improvements.append("Underutilized capacity - opportunity for more transactions")
        
        return improvements
    
    async def _process_status_query(self, query: str) -> Optional[str]:
        """Process chat queries about network status"""
        
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in ['status', 'network', 'netting', 'health', 'performance']):
            if 'health' in query_lower:
                return "I monitor network health including connectivity, processing capacity, and resource utilization. Would you like a health check?"
            elif 'performance' in query_lower or 'efficiency' in query_lower:
                return "I can analyze netting performance and efficiency metrics. What specific performance data interests you?"
            elif 'netting' in query_lower:
                return "I track real-time netting statistics including rates, gas savings, and active requests. Need current netting data?"
            else:
                return "I monitor the Arcology netted layer status including performance, health, and efficiency metrics. What would you like to know?"
        
        return None
    
    async def start_agent(self):
        """Start the net status agent"""
        await self.agent.run()

# Global instance for import
net_status_agent = NetStatusAgent()
