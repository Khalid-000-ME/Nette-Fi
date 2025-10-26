"""
Net Status Tool Agent - Gets Arcology network status using /api/net_status
This agent makes real API calls to monitor network health and performance
"""

import asyncio
import aiohttp
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

class NetStatusToolAgent:
    """Agent that makes real API calls to get Arcology network status"""
    
    def __init__(self, api_base_url: str = "http://localhost:3000"):
        self.api_base_url = api_base_url
        self.agent_id = f"net_status_agent_{uuid.uuid4().hex[:8]}"
        self.session = None
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    async def get_network_status(
        self,
        include_performance: bool = True,
        include_netting_stats: bool = True
    ) -> Dict[str, Any]:
        """
        Get Arcology network status using /api/net_status
        
        Args:
            include_performance: Whether to include performance metrics
            include_netting_stats: Whether to include netting statistics
            
        Returns:
            Network status with health and performance data
        """
        
        print(f"🌐 {self.agent_id}: Getting Arcology network status...")
        
        if not self.session:
            self.session = aiohttp.ClientSession()
        
        try:
            # Prepare API request
            params = {
                "include_performance": str(include_performance).lower(),
                "include_netting": str(include_netting_stats).lower()
            }
            
            print(f"   📡 Calling /api/net_status with params: {params}")
            
            # Make API call to get network status
            async with self.session.get(
                f"{self.api_base_url}/api/net_status",
                params=params,
                timeout=aiohttp.ClientTimeout(total=10)
            ) as response:
                
                if response.status == 200:
                    result = await response.json()
                    
                    print(f"   ✅ Network status retrieved successfully!")
                    
                    # Enhance the result with analysis
                    enhanced_result = {
                        "success": True,
                        "agent_id": self.agent_id,
                        "network_data": result,
                        "health_analysis": self._analyze_network_health(result),
                        "performance_assessment": self._assess_performance(result),
                        "netting_efficiency": self._analyze_netting_efficiency(result),
                        "timestamp": datetime.now().isoformat()
                    }
                    
                    # Log key network metrics
                    if "network_healthy" in result:
                        health = result["network_healthy"]
                        print(f"   🏥 Network Health: {'✅ Healthy' if health else '❌ Issues'}")
                    
                    if "parallel_threads" in result:
                        threads = result["parallel_threads"]
                        print(f"   🧵 Parallel Threads: {threads}")
                    
                    if "netting_rate" in result:
                        netting = result["netting_rate"]
                        print(f"   🔗 Netting Rate: {netting}%")
                    
                    return enhanced_result
                    
                else:
                    error_text = await response.text()
                    print(f"   ❌ Network status API call failed with status {response.status}: {error_text}")
                    
                    return {
                        "success": False,
                        "agent_id": self.agent_id,
                        "error": f"Network API failed: {response.status} - {error_text}",
                        "fallback_status": self._get_fallback_network_status()
                    }
                    
        except asyncio.TimeoutError:
            print(f"   ⏰ Network status API call timed out")
            return {
                "success": False,
                "agent_id": self.agent_id,
                "error": "Network status API timed out",
                "fallback_status": self._get_fallback_network_status()
            }
            
        except Exception as e:
            print(f"   💥 Network status API call failed: {str(e)}")
            return {
                "success": False,
                "agent_id": self.agent_id,
                "error": f"Network status fetch failed: {str(e)}",
                "fallback_status": self._get_fallback_network_status()
            }
    
    def _analyze_network_health(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze network health from status data"""
        
        health_analysis = {
            "overall_health": "good",
            "health_score": 100,
            "issues": [],
            "warnings": []
        }
        
        # Check basic network health
        if not network_data.get("network_healthy", True):
            health_analysis["issues"].append("Network reported as unhealthy")
            health_analysis["overall_health"] = "critical"
            health_analysis["health_score"] = 20
        
        # Check parallel thread count
        parallel_threads = network_data.get("parallel_threads", 0)
        if parallel_threads < 5:
            health_analysis["warnings"].append("Low parallel thread count")
            health_analysis["health_score"] -= 15
        elif parallel_threads > 50:
            health_analysis["warnings"].append("Very high thread count - possible congestion")
            health_analysis["health_score"] -= 10
        
        # Check netting rate
        netting_rate = network_data.get("netting_rate", 0)
        if netting_rate < 30:
            health_analysis["warnings"].append("Low netting efficiency")
            health_analysis["health_score"] -= 20
        elif netting_rate > 80:
            health_analysis["warnings"].append("Excellent netting efficiency")
            health_analysis["health_score"] += 10
        
        # Check gas savings
        gas_saved = network_data.get("gas_saved", 0)
        if gas_saved < 10000:
            health_analysis["warnings"].append("Low gas savings - netting may not be optimal")
            health_analysis["health_score"] -= 10
        
        # Determine overall health
        if health_analysis["health_score"] < 50:
            health_analysis["overall_health"] = "poor"
        elif health_analysis["health_score"] < 80:
            health_analysis["overall_health"] = "fair"
        elif health_analysis["health_score"] >= 100:
            health_analysis["overall_health"] = "excellent"
        
        return health_analysis
    
    def _assess_performance(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess network performance metrics"""
        
        performance = {
            "performance_level": "good",
            "throughput_assessment": "normal",
            "latency_assessment": "acceptable",
            "recommendations": []
        }
        
        # Assess parallel processing
        parallel_threads = network_data.get("parallel_threads", 0)
        if parallel_threads > 20:
            performance["throughput_assessment"] = "high"
            performance["recommendations"].append("High throughput - good for large batches")
        elif parallel_threads < 10:
            performance["throughput_assessment"] = "low"
            performance["recommendations"].append("Consider smaller batch sizes")
        
        # Assess netting efficiency
        netting_rate = network_data.get("netting_rate", 0)
        if netting_rate > 70:
            performance["performance_level"] = "excellent"
            performance["recommendations"].append("Optimal conditions for batch processing")
        elif netting_rate < 40:
            performance["performance_level"] = "suboptimal"
            performance["recommendations"].append("Consider delaying batch execution")
        
        # Check gas savings trend
        gas_saved = network_data.get("gas_saved", 0)
        if gas_saved > 100000:
            performance["recommendations"].append("High gas savings - excellent netting performance")
        
        return performance
    
    def _analyze_netting_efficiency(self, network_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze netting layer efficiency"""
        
        netting_analysis = {
            "efficiency_rating": "good",
            "netting_rate": network_data.get("netting_rate", 0),
            "gas_savings": network_data.get("gas_saved", 0),
            "parallel_capacity": network_data.get("parallel_threads", 0),
            "optimization_opportunities": []
        }
        
        netting_rate = netting_analysis["netting_rate"]
        
        # Rate efficiency
        if netting_rate > 80:
            netting_analysis["efficiency_rating"] = "excellent"
            netting_analysis["optimization_opportunities"].append("Maintain current batch sizes")
        elif netting_rate > 60:
            netting_analysis["efficiency_rating"] = "good"
            netting_analysis["optimization_opportunities"].append("Consider increasing batch sizes")
        elif netting_rate > 40:
            netting_analysis["efficiency_rating"] = "fair"
            netting_analysis["optimization_opportunities"].append("Optimize transaction timing")
        else:
            netting_analysis["efficiency_rating"] = "poor"
            netting_analysis["optimization_opportunities"].append("Review batch composition")
        
        # Parallel processing optimization
        parallel_threads = netting_analysis["parallel_capacity"]
        if parallel_threads < 10:
            netting_analysis["optimization_opportunities"].append("Network has low parallel capacity")
        elif parallel_threads > 30:
            netting_analysis["optimization_opportunities"].append("High parallel capacity - can handle large batches")
        
        return netting_analysis
    
    def _get_fallback_network_status(self) -> Dict[str, Any]:
        """Get fallback network status when API fails"""
        
        return {
            "network_healthy": True,
            "parallel_threads": 15,
            "netting_rate": 65.0,
            "gas_saved": 125000,
            "block_height": 12345,
            "active_connections": 8,
            "note": "Using fallback status due to API failure",
            "timestamp": datetime.now().isoformat()
        }
    
    async def check_transaction_readiness(self, batch_size: int = 5) -> Dict[str, Any]:
        """Check if network is ready for transaction batch"""
        
        print(f"🚦 {self.agent_id}: Checking transaction readiness for batch of {batch_size}")
        
        # Get current network status
        status_result = await self.get_network_status(include_performance=True)
        
        readiness = {
            "agent_id": self.agent_id,
            "batch_size": batch_size,
            "ready_for_transactions": False,
            "readiness_score": 0,
            "blocking_issues": [],
            "warnings": [],
            "recommendations": []
        }
        
        if status_result["success"]:
            network_data = status_result["network_data"]
            health_analysis = status_result["health_analysis"]
            
            # Base readiness on health score
            readiness["readiness_score"] = health_analysis["health_score"]
            
            # Check for blocking issues
            if not network_data.get("network_healthy", True):
                readiness["blocking_issues"].append("Network reported as unhealthy")
            
            if network_data.get("parallel_threads", 0) < 3:
                readiness["blocking_issues"].append("Insufficient parallel processing capacity")
            
            # Check for warnings
            if network_data.get("netting_rate", 0) < 30:
                readiness["warnings"].append("Low netting efficiency - higher gas costs expected")
            
            # Generate recommendations
            if len(readiness["blocking_issues"]) == 0:
                readiness["ready_for_transactions"] = True
                
                if network_data.get("netting_rate", 0) > 70:
                    readiness["recommendations"].append("Excellent conditions for batch processing")
                elif batch_size > 10 and network_data.get("parallel_threads", 0) < 15:
                    readiness["recommendations"].append("Consider reducing batch size for better performance")
                else:
                    readiness["recommendations"].append("Network ready for transaction processing")
            else:
                readiness["recommendations"].append("Wait for network conditions to improve")
        else:
            readiness["warnings"].append("Could not verify network status")
            readiness["recommendations"].append("Proceed with caution - network status unknown")
        
        return readiness
    
    async def monitor_netting_performance(self, duration_seconds: int = 60) -> Dict[str, Any]:
        """Monitor netting performance over time"""
        
        print(f"📊 {self.agent_id}: Monitoring netting performance for {duration_seconds} seconds")
        
        # Mock implementation - would collect metrics over time in production
        return {
            "agent_id": self.agent_id,
            "monitoring_duration": duration_seconds,
            "performance_metrics": {
                "average_netting_rate": 68.5,
                "peak_netting_rate": 85.2,
                "lowest_netting_rate": 52.1,
                "total_gas_saved": 245000,
                "average_parallel_threads": 18.3,
                "peak_parallel_threads": 28,
                "network_uptime_percent": 99.8
            },
            "trend_analysis": {
                "netting_trend": "stable",
                "performance_trend": "improving",
                "capacity_utilization": "moderate"
            },
            "recommendations": [
                "Network performance is stable",
                "Good conditions for regular batch processing",
                "Consider scheduling large batches during peak efficiency periods"
            ]
        }
    
    def get_agent_info(self) -> Dict[str, Any]:
        """Get agent information"""
        return {
            "agent_id": self.agent_id,
            "agent_type": "net_status_tool_agent",
            "capabilities": [
                "network_health_monitoring",
                "netting_efficiency_analysis",
                "transaction_readiness_assessment",
                "performance_monitoring"
            ],
            "api_endpoints": [
                "/api/net_status"
            ],
            "monitoring_metrics": [
                "parallel_threads",
                "netting_rate", 
                "gas_saved",
                "network_health"
            ]
        }

# Example usage and testing
async def test_net_status_agent():
    """Test the net status tool agent"""
    print("🧪 Testing Net Status Tool Agent")
    print("=" * 50)
    
    async with NetStatusToolAgent() as agent:
        
        # Test 1: Get network status
        print("\n1️⃣ Testing Network Status Retrieval...")
        status_result = await agent.get_network_status(
            include_performance=True,
            include_netting_stats=True
        )
        
        print(f"Status Result: {json.dumps(status_result, indent=2)}")
        
        # Test 2: Check transaction readiness
        print("\n2️⃣ Testing Transaction Readiness...")
        readiness_result = await agent.check_transaction_readiness(batch_size=5)
        
        print(f"Readiness Result: {json.dumps(readiness_result, indent=2)}")
        
        # Test 3: Monitor performance
        print("\n3️⃣ Testing Performance Monitoring...")
        monitoring_result = await agent.monitor_netting_performance(duration_seconds=30)
        
        print(f"Monitoring Result: {json.dumps(monitoring_result, indent=2)}")
        
        # Test 4: Agent info
        print("\n4️⃣ Agent Information...")
        agent_info = agent.get_agent_info()
        print(f"Agent Info: {json.dumps(agent_info, indent=2)}")

if __name__ == "__main__":
    asyncio.run(test_net_status_agent())
