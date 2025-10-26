"""
Mempool Agent - Handles mempool analysis and MEV risk assessment
Integrates with frontend /api/mempool route for real-time mempool data
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

class MempoolAgent:
    """
    Mempool Agent for real-time mempool analysis and MEV risk assessment
    
    Features:
    - Integration with /api/mempool route
    - MEV bot detection
    - Gas price analysis
    - Transaction congestion monitoring
    """
    
    def __init__(self, agent_port: int = 8012):
        self.agent = Agent(
            name="mempool_agent",
            seed="mempool_agent_seed_33333",
            port=agent_port,
            endpoint=[f"http://localhost:{agent_port}/submit"]
        )
        
        self.agent_id = "mempool_agent"
        self.agent_type = "mempool_analysis"
        self.name = "Mempool Agent"
        
        self.frontend_api_base = "http://localhost:3000/api"
        self.chat_protocol = ASIChatProtocol()
        self.mempool_cache: Dict[str, Dict[str, Any]] = {}
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        @self.agent.on_event("startup")
        async def startup_handler(ctx: Context):
            ctx.logger.info(f"Mempool Agent started: {ctx.agent.address}")
            
            self.chat_protocol.register_agent(
                agent_id=self.agent_id,
                agent_address=ctx.agent.address,
                agent_type=self.agent_type,
                capabilities=["mempool_analysis", "mev_detection", "gas_analysis", "congestion_monitoring"]
            )
        
        @self.agent.on_message(model=ToolCallRequest)
        async def handle_tool_call(ctx: Context, sender: str, msg: ToolCallRequest):
            result = {}
            success = True
            
            try:
                if msg.tool_name == "analyze_mempool":
                    result = await self._analyze_mempool(msg.parameters)
                elif msg.tool_name == "detect_mev_bots":
                    result = await self._detect_mev_bots(msg.parameters)
                elif msg.tool_name == "monitor_gas_prices":
                    result = await self._monitor_gas_prices(msg.parameters)
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
                    response_text = await self._process_mempool_query(item.text)
                    
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
    
    async def _analyze_mempool(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze mempool data via frontend API"""
        
        try:
            response = requests.get(
                f"{self.frontend_api_base}/mempool",
                params=parameters,
                timeout=10
            )
            
            if response.status_code == 200:
                result = response.json()
                
                # Enhanced analysis
                enhanced_result = {
                    **result,
                    "risk_assessment": self._assess_mev_risk(result),
                    "congestion_analysis": self._analyze_congestion(result),
                    "timing_recommendations": self._get_timing_recommendations(result),
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                return enhanced_result
            else:
                return {"error": f"Mempool API failed: {response.status_code}"}
        
        except Exception as e:
            return {"error": f"Mempool analysis failed: {str(e)}"}
    
    def _assess_mev_risk(self, mempool_data: Dict[str, Any]) -> Dict[str, Any]:
        """Assess MEV risk from mempool data"""
        
        pending_txs = mempool_data.get("pending_transactions", 0)
        sandwich_bots = mempool_data.get("sandwich_bots_detected", 0)
        avg_gas_price = mempool_data.get("average_gas_price_gwei", 20)
        
        # Risk scoring
        risk_score = 0
        if sandwich_bots > 0:
            risk_score += 40
        if pending_txs > 1000:
            risk_score += 30
        if avg_gas_price > 50:
            risk_score += 20
        
        risk_level = "high" if risk_score > 60 else "medium" if risk_score > 30 else "low"
        
        return {
            "risk_score": min(100, risk_score),
            "risk_level": risk_level,
            "mev_threats": {
                "sandwich_bots": sandwich_bots,
                "frontrunning_risk": "high" if pending_txs > 2000 else "medium" if pending_txs > 500 else "low"
            },
            "recommendations": self._get_mev_recommendations(risk_level, sandwich_bots)
        }
    
    def _analyze_congestion(self, mempool_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze network congestion"""
        
        pending_txs = mempool_data.get("pending_transactions", 0)
        avg_gas_price = mempool_data.get("average_gas_price_gwei", 20)
        
        if pending_txs > 2000:
            congestion_level = "severe"
        elif pending_txs > 1000:
            congestion_level = "high"
        elif pending_txs > 500:
            congestion_level = "moderate"
        else:
            congestion_level = "low"
        
        return {
            "congestion_level": congestion_level,
            "pending_transactions": pending_txs,
            "estimated_wait_time": self._estimate_wait_time(pending_txs, avg_gas_price),
            "gas_price_trend": "increasing" if avg_gas_price > 30 else "stable"
        }
    
    def _get_timing_recommendations(self, mempool_data: Dict[str, Any]) -> List[str]:
        """Get timing recommendations based on mempool state"""
        
        recommendations = []
        pending_txs = mempool_data.get("pending_transactions", 0)
        sandwich_bots = mempool_data.get("sandwich_bots_detected", 0)
        
        if sandwich_bots > 0:
            recommendations.append("Wait for MEV bot activity to decrease")
        
        if pending_txs > 1500:
            recommendations.append("Consider delaying transaction due to high congestion")
        elif pending_txs < 300:
            recommendations.append("Good time for transaction execution")
        
        return recommendations
    
    def _get_mev_recommendations(self, risk_level: str, sandwich_bots: int) -> List[str]:
        """Get MEV protection recommendations"""
        
        recommendations = []
        
        if risk_level == "high":
            recommendations.extend([
                "Use private mempool if available",
                "Consider splitting large orders",
                "Increase slippage tolerance"
            ])
        
        if sandwich_bots > 0:
            recommendations.append(f"Detected {sandwich_bots} sandwich bots - exercise caution")
        
        return recommendations
    
    def _estimate_wait_time(self, pending_txs: int, gas_price: float) -> Dict[str, Any]:
        """Estimate transaction wait time"""
        
        # Simplified estimation
        if gas_price > 50:
            base_wait = 30  # seconds
        elif gas_price > 30:
            base_wait = 60
        else:
            base_wait = 120
        
        congestion_multiplier = 1 + (pending_txs / 1000)
        estimated_seconds = base_wait * congestion_multiplier
        
        return {
            "estimated_seconds": int(estimated_seconds),
            "estimated_blocks": max(1, int(estimated_seconds / 12)),
            "confidence": "low" if pending_txs > 2000 else "medium"
        }
    
    async def _detect_mev_bots(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Detect MEV bot activity"""
        
        # Get mempool data
        mempool_data = await self._analyze_mempool(parameters)
        
        if "error" in mempool_data:
            return mempool_data
        
        # Extract bot detection data
        sandwich_bots = mempool_data.get("sandwich_bots_detected", 0)
        risk_assessment = mempool_data.get("risk_assessment", {})
        
        return {
            "mev_bots_detected": sandwich_bots,
            "bot_types": ["sandwich_bot"] if sandwich_bots > 0 else [],
            "threat_level": risk_assessment.get("risk_level", "low"),
            "protection_strategies": risk_assessment.get("recommendations", []),
            "detection_timestamp": datetime.utcnow().isoformat()
        }
    
    async def _monitor_gas_prices(self, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Monitor gas price trends"""
        
        # Get current mempool data
        mempool_data = await self._analyze_mempool(parameters)
        
        if "error" in mempool_data:
            return mempool_data
        
        current_gas = mempool_data.get("average_gas_price_gwei", 20)
        congestion_data = mempool_data.get("congestion_analysis", {})
        
        return {
            "current_gas_price_gwei": current_gas,
            "gas_trend": congestion_data.get("gas_price_trend", "stable"),
            "congestion_impact": congestion_data.get("congestion_level", "low"),
            "optimization_suggestions": self._get_gas_optimization_suggestions(current_gas),
            "monitoring_timestamp": datetime.utcnow().isoformat()
        }
    
    def _get_gas_optimization_suggestions(self, current_gas: float) -> List[str]:
        """Get gas optimization suggestions"""
        
        suggestions = []
        
        if current_gas > 50:
            suggestions.extend([
                "Consider waiting for lower gas prices",
                "Use Layer 2 solutions if available",
                "Batch multiple transactions"
            ])
        elif current_gas < 15:
            suggestions.append("Good time for gas-intensive operations")
        
        return suggestions
    
    async def _process_mempool_query(self, query: str) -> Optional[str]:
        """Process chat queries about mempool"""
        
        query_lower = query.lower()
        
        if any(keyword in query_lower for keyword in ['mempool', 'mev', 'sandwich', 'gas', 'congestion']):
            if 'mev' in query_lower or 'sandwich' in query_lower:
                return "I can detect MEV bot activity and assess sandwich attack risks. Would you like me to analyze current mempool conditions?"
            elif 'gas' in query_lower:
                return "I monitor gas prices and network congestion. I can help you find optimal timing for transactions."
            else:
                return "I analyze mempool data to detect MEV risks and network congestion. What specific analysis do you need?"
        
        return None
    
    async def start_agent(self):
        """Start the mempool agent"""
        await self.agent.run()

# Global instance for import
mempool_agent = MempoolAgent()
