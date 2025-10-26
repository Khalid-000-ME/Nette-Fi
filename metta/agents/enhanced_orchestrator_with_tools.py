"""
Enhanced Multi-Agent Orchestrator with Tool Calling
Combines MeTTa reasoning with real API tool calls for transaction mining
"""

import asyncio
import json
from typing import Dict, Any, List, Optional
from datetime import datetime
import uuid

# Import MeTTa components
try:
    from .metta_knowledge_base import initialize_defi_knowledge_graph, DeFiMeTTaRAG, USING_REAL_METTA
except ImportError:
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from metta_knowledge_base import initialize_defi_knowledge_graph, DeFiMeTTaRAG, USING_REAL_METTA

# Import enhanced agents with MeTTa
try:
    from .enhanced_mev_agent import EnhancedMEVAgent
    from .enhanced_profit_agent import EnhancedProfitAgent  
    from .enhanced_speed_agent import EnhancedSpeedAgent
except ImportError:
    from enhanced_mev_agent import EnhancedMEVAgent
    from enhanced_profit_agent import EnhancedProfitAgent  
    from enhanced_speed_agent import EnhancedSpeedAgent

# Import tool agents
try:
    from .transaction_tool_agent import TransactionToolAgent
    from .price_tool_agent import PriceToolAgent
    from .mempool_tool_agent import MempoolToolAgent
except ImportError:
    from transaction_tool_agent import TransactionToolAgent
    from price_tool_agent import PriceToolAgent
    from mempool_tool_agent import MempoolToolAgent

# Import MeTTa
try:
    from hyperon import MeTTa
    print("✅ Using real Hyperon/MeTTa for orchestration")
except ImportError:
    from mock_hyperon import MeTTa
    print("⚠️ Using mock MeTTa for orchestration")

class EnhancedOrchestratorWithTools:
    """
    Enhanced orchestrator that combines:
    1. MeTTa symbolic reasoning
    2. Enhanced agent analysis
    3. Real tool API calls
    4. Transaction mining
    """
    
    def __init__(self, api_base_url: str = "http://localhost:3000"):
        self.orchestrator_id = f"enhanced_orchestrator_{uuid.uuid4().hex[:8]}"
        self.api_base_url = api_base_url
        
        # Initialize MeTTa knowledge base
        self.metta = MeTTa()
        initialize_defi_knowledge_graph(self.metta)
        self.metta_rag = DeFiMeTTaRAG(self.metta)
        
        # Initialize enhanced agents
        self.mev_agent = EnhancedMEVAgent()
        self.profit_agent = EnhancedProfitAgent()
        self.speed_agent = EnhancedSpeedAgent()
        
        # Initialize tool agents
        self.transaction_agent = None
        self.price_agent = None
        self.mempool_agent = None
        
        # Session tracking
        self.active_sessions = {}
        
    async def __aenter__(self):
        """Async context manager entry"""
        self.transaction_agent = TransactionToolAgent(self.api_base_url)
        self.price_agent = PriceToolAgent(self.api_base_url)
        self.mempool_agent = MempoolToolAgent(self.api_base_url)
        
        await self.transaction_agent.__aenter__()
        await self.price_agent.__aenter__()
        await self.mempool_agent.__aenter__()
        
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.transaction_agent:
            await self.transaction_agent.__aexit__(exc_type, exc_val, exc_tb)
        if self.price_agent:
            await self.price_agent.__aexit__(exc_type, exc_val, exc_tb)
        if self.mempool_agent:
            await self.mempool_agent.__aexit__(exc_type, exc_val, exc_tb)
    
    async def orchestrate_payroll_execution(
        self,
        payroll_data: Dict[str, Any],
        user_preferences: Dict[str, Any] = None,
        execute_transactions: bool = True
    ) -> Dict[str, Any]:
        """
        Complete payroll orchestration with MeTTa reasoning and tool calls
        
        Args:
            payroll_data: Payroll information (employees, amounts, etc.)
            user_preferences: User preferences for execution
            execute_transactions: Whether to actually mine transactions
            
        Returns:
            Complete orchestration result with mined transactions
        """
        
        session_id = str(uuid.uuid4())
        print(f"🎭 {self.orchestrator_id}: Starting payroll orchestration session {session_id}")
        
        if user_preferences is None:
            user_preferences = {"priority": "safety", "payroll_priority": "cost"}
        
        # Initialize session
        self.active_sessions[session_id] = {
            "session_id": session_id,
            "start_time": datetime.now(),
            "status": "initializing",
            "payroll_data": payroll_data,
            "user_preferences": user_preferences
        }
        
        try:
            # Phase 1: MeTTa Knowledge Processing
            print(f"\n1️⃣ MeTTa Knowledge Processing...")
            metta_analysis = await self._process_metta_knowledge(payroll_data, user_preferences)
            self.active_sessions[session_id]["metta_analysis"] = metta_analysis
            
            # Phase 2: Tool Agent Data Gathering
            print(f"\n2️⃣ Tool Agent Data Gathering...")
            tool_data = await self._gather_tool_data(payroll_data)
            self.active_sessions[session_id]["tool_data"] = tool_data
            
            # Phase 3: Enhanced Agent Analysis
            print(f"\n3️⃣ Enhanced Agent Analysis...")
            agent_analyses = await self._run_enhanced_agent_analysis(
                payroll_data, user_preferences, metta_analysis, tool_data
            )
            self.active_sessions[session_id]["agent_analyses"] = agent_analyses
            
            # Phase 4: MeTTa Consensus Decision
            print(f"\n4️⃣ MeTTa Consensus Decision...")
            consensus_decision = await self._generate_metta_consensus(
                metta_analysis, agent_analyses, tool_data
            )
            self.active_sessions[session_id]["consensus_decision"] = consensus_decision
            
            # Phase 5: Transaction Execution (if requested)
            execution_result = None
            if execute_transactions:
                print(f"\n5️⃣ Transaction Execution...")
                execution_result = await self._execute_transactions(
                    consensus_decision, payroll_data, tool_data
                )
                self.active_sessions[session_id]["execution_result"] = execution_result
            
            # Phase 6: Final Results
            self.active_sessions[session_id]["status"] = "completed"
            self.active_sessions[session_id]["completion_time"] = datetime.now()
            
            final_result = {
                "session_id": session_id,
                "orchestrator_id": self.orchestrator_id,
                "status": "success",
                "using_real_metta": USING_REAL_METTA,
                "phases_completed": {
                    "metta_knowledge_processing": True,
                    "tool_data_gathering": True,
                    "enhanced_agent_analysis": True,
                    "metta_consensus": True,
                    "transaction_execution": execute_transactions and execution_result is not None
                },
                "results": {
                    "metta_analysis": metta_analysis,
                    "tool_data": tool_data,
                    "agent_analyses": agent_analyses,
                    "consensus_decision": consensus_decision,
                    "execution_result": execution_result
                },
                "session_metadata": {
                    "duration_seconds": (self.active_sessions[session_id]["completion_time"] - 
                                       self.active_sessions[session_id]["start_time"]).total_seconds(),
                    "payroll_amount": payroll_data.get("total_amount", 0),
                    "employee_count": len(payroll_data.get("employees", [])),
                    "transactions_mined": execution_result.get("transactions_mined", False) if execution_result else False
                }
            }
            
            print(f"\n🎉 Orchestration completed successfully!")
            print(f"   • MeTTa Reasoning: {'Real' if USING_REAL_METTA else 'Mock'}")
            print(f"   • Consensus Decision: {consensus_decision.get('final_recommendation', 'N/A')}")
            print(f"   • Transactions Mined: {final_result['session_metadata']['transactions_mined']}")
            
            return final_result
            
        except Exception as e:
            print(f"💥 Orchestration failed: {str(e)}")
            self.active_sessions[session_id]["status"] = "failed"
            self.active_sessions[session_id]["error"] = str(e)
            
            return {
                "session_id": session_id,
                "status": "failed",
                "error": str(e),
                "orchestrator_id": self.orchestrator_id
            }
    
    async def _process_metta_knowledge(
        self, 
        payroll_data: Dict[str, Any], 
        user_preferences: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Process payroll scenario through MeTTa knowledge graphs"""
        
        print(f"   🧠 Processing payroll scenario through MeTTa...")
        
        # Create payroll-specific scenario for MeTTa
        payroll_scenario = {
            "mev_factors": ["batch_processing", "payroll_reliability"],
            "profit_factors": ["cost_optimization", "gas_savings"],
            "speed_factors": ["payroll_deadline", "employee_satisfaction"]
        }
        
        # Add risk factors based on payroll size
        employee_count = len(payroll_data.get("employees", []))
        if employee_count > 10:
            payroll_scenario["mev_factors"].append("large_batch_risk")
        
        total_amount = payroll_data.get("total_amount", 0)
        if total_amount > 100000:  # Large payroll
            payroll_scenario["mev_factors"].append("high_value_target")
        
        # Query MeTTa knowledge base
        metta_results = self.metta_rag.query_complex_scenario(payroll_scenario)
        metta_recommendation = self.metta_rag.generate_recommendation(
            metta_results, user_preferences.get("priority", "balanced")
        )
        
        print(f"   ✅ MeTTa processed {len(metta_results)} knowledge factors")
        print(f"   ✅ MeTTa recommendation: {metta_recommendation['primary_recommendation']}")
        
        return {
            "scenario": payroll_scenario,
            "knowledge_factors": metta_results,
            "metta_recommendation": metta_recommendation,
            "using_real_metta": USING_REAL_METTA
        }
    
    async def _gather_tool_data(self, payroll_data: Dict[str, Any]) -> Dict[str, Any]:
        """Gather data from all tool agents"""
        
        print(f"   🔧 Gathering data from tool agents...")
        
        # Gather data in parallel
        price_task = self.price_agent.get_token_prices(["ETH/USDC", "USDC/USD"])
        mempool_task = self.mempool_agent.analyze_mev_risks("payroll", len(payroll_data.get("employees", [])))
        gas_task = self.transaction_agent.estimate_gas_costs(len(payroll_data.get("employees", [])), "payroll")
        
        price_data, mempool_data, gas_data = await asyncio.gather(
            price_task, mempool_task, gas_task, return_exceptions=True
        )
        
        print(f"   ✅ Tool data gathered from {3} agents")
        
        return {
            "price_data": price_data if not isinstance(price_data, Exception) else {"error": str(price_data)},
            "mempool_data": mempool_data if not isinstance(mempool_data, Exception) else {"error": str(mempool_data)},
            "gas_data": gas_data if not isinstance(gas_data, Exception) else {"error": str(gas_data)},
            "timestamp": datetime.now().isoformat()
        }
    
    async def _run_enhanced_agent_analysis(
        self,
        payroll_data: Dict[str, Any],
        user_preferences: Dict[str, Any],
        metta_analysis: Dict[str, Any],
        tool_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Run enhanced agent analysis with MeTTa insights"""
        
        print(f"   🤖 Running enhanced agent analysis...")
        
        # Create simulation data for agents
        simulation_data = {
            "simulations": [
                {
                    "id": 1,
                    "strategy": "immediate_execution",
                    "mev_risk_score": 35,
                    "estimated_output_usd": payroll_data.get("total_amount", 50000) * 0.98,
                    "gas_cost_usd": 45,
                    "execution_time_seconds": 30
                },
                {
                    "id": 2,
                    "strategy": "delayed_batch_execution",
                    "mev_risk_score": 15,
                    "estimated_output_usd": payroll_data.get("total_amount", 50000) * 0.995,
                    "gas_cost_usd": 25,
                    "execution_time_seconds": 120
                }
            ]
        }
        
        # Run agent analyses with MeTTa context
        mev_analysis = await self.mev_agent.enhanced_mev_analysis(
            simulation_data, user_preferences, metta_context=metta_analysis
        )
        
        profit_analysis = await self.profit_agent.enhanced_profit_analysis(
            simulation_data, user_preferences, metta_context=metta_analysis
        )
        
        speed_analysis = await self.speed_agent.enhanced_speed_analysis(
            simulation_data, user_preferences, metta_context=metta_analysis
        )
        
        print(f"   ✅ Enhanced agent analyses completed")
        print(f"      • MEV Agent: Recommends simulation {mev_analysis.get('recommended_simulation_id', 'N/A')}")
        print(f"      • Profit Agent: Recommends simulation {profit_analysis.get('recommended_simulation_id', 'N/A')}")
        print(f"      • Speed Agent: Recommends simulation {speed_analysis.get('recommended_simulation_id', 'N/A')}")
        
        return {
            "mev_analysis": mev_analysis,
            "profit_analysis": profit_analysis,
            "speed_analysis": speed_analysis,
            "simulation_data": simulation_data
        }
    
    async def _generate_metta_consensus(
        self,
        metta_analysis: Dict[str, Any],
        agent_analyses: Dict[str, Any],
        tool_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate consensus decision using MeTTa reasoning"""
        
        print(f"   🧠 Generating MeTTa consensus...")
        
        # Extract agent recommendations
        mev_rec = agent_analyses["mev_analysis"].get("recommended_simulation_id", 2)
        profit_rec = agent_analyses["profit_analysis"].get("recommended_simulation_id", 1)
        speed_rec = agent_analyses["speed_analysis"].get("recommended_simulation_id", 1)
        
        # MeTTa-based consensus logic
        metta_rec = metta_analysis["metta_recommendation"]["primary_recommendation"]
        
        # For payroll, prioritize safety (MEV agent) when MeTTa recommends protection
        if "protection" in metta_rec.lower() or "safety" in metta_rec.lower():
            final_recommendation = mev_rec
            reasoning = "MeTTa knowledge graphs prioritize safety for payroll operations"
        elif "profit" in metta_rec.lower() or "cost" in metta_rec.lower():
            final_recommendation = profit_rec
            reasoning = "MeTTa analysis favors cost optimization"
        else:
            # Default to MEV agent for payroll safety
            final_recommendation = mev_rec
            reasoning = "Default to safety-first approach for payroll"
        
        consensus_decision = {
            "final_recommendation": final_recommendation,
            "reasoning": reasoning,
            "metta_influence": metta_rec,
            "agent_votes": {
                "mev_agent": mev_rec,
                "profit_agent": profit_rec,
                "speed_agent": speed_rec
            },
            "confidence_score": 85,
            "consensus_method": "metta_enhanced_reasoning"
        }
        
        print(f"   ✅ MeTTa consensus: Simulation {final_recommendation}")
        print(f"   ✅ Reasoning: {reasoning}")
        
        return consensus_decision
    
    async def _execute_transactions(
        self,
        consensus_decision: Dict[str, Any],
        payroll_data: Dict[str, Any],
        tool_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute transactions using the transaction tool agent"""
        
        print(f"   ⛏️ Executing transactions...")
        
        # Determine execution parameters from consensus
        simulation_id = consensus_decision["final_recommendation"]
        employee_count = len(payroll_data.get("employees", []))
        
        # Execute transactions using tool agent
        execution_result = await self.transaction_agent.mine_transactions(
            analysis_id=f"payroll_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            simulation_id=simulation_id,
            batch_size=min(employee_count, 5),  # Respect container limits
            transaction_type="payroll",
            execute_immediately=True
        )
        
        print(f"   ✅ Transaction execution completed")
        print(f"   ⛏️ Transactions mined: {execution_result.get('transactions_mined', False)}")
        
        return execution_result
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get status of orchestration session"""
        return self.active_sessions.get(session_id)
    
    def get_orchestrator_info(self) -> Dict[str, Any]:
        """Get orchestrator information"""
        return {
            "orchestrator_id": self.orchestrator_id,
            "orchestrator_type": "enhanced_with_tools",
            "capabilities": [
                "metta_symbolic_reasoning",
                "enhanced_agent_coordination",
                "real_api_tool_calls",
                "transaction_mining",
                "payroll_processing"
            ],
            "components": {
                "metta_knowledge_base": USING_REAL_METTA,
                "enhanced_agents": ["mev", "profit", "speed"],
                "tool_agents": ["transaction", "price", "mempool"],
                "api_endpoints": ["/api/approve", "/api/get_price", "/api/mempool"]
            }
        }

# Example usage and testing
async def test_enhanced_orchestrator():
    """Test the enhanced orchestrator with tools"""
    print("🧪 Testing Enhanced Orchestrator with Tools")
    print("=" * 60)
    
    # Sample payroll data
    payroll_data = {
        "total_amount": 75000,
        "employees": [
            {"id": 1, "address": "0x123...", "amount": 25000},
            {"id": 2, "address": "0x456...", "amount": 25000},
            {"id": 3, "address": "0x789...", "amount": 25000}
        ],
        "currency": "USDC",
        "deadline": "2025-10-25T12:00:00Z"
    }
    
    user_preferences = {
        "priority": "safety",
        "payroll_priority": "cost",
        "max_gas_cost": 100
    }
    
    async with EnhancedOrchestratorWithTools() as orchestrator:
        
        # Test orchestration with transaction execution
        result = await orchestrator.orchestrate_payroll_execution(
            payroll_data=payroll_data,
            user_preferences=user_preferences,
            execute_transactions=True  # Actually mine transactions!
        )
        
        print(f"\n🎉 Orchestration Result:")
        print(f"Status: {result['status']}")
        print(f"Using Real MeTTa: {result.get('using_real_metta', False)}")
        print(f"Transactions Mined: {result['session_metadata']['transactions_mined']}")
        
        if result.get('results', {}).get('execution_result'):
            exec_result = result['results']['execution_result']
            print(f"Block Number: {exec_result.get('block_number', 'N/A')}")
            print(f"Transaction Count: {exec_result.get('transaction_count', 0)}")

if __name__ == "__main__":
    asyncio.run(test_enhanced_orchestrator())
