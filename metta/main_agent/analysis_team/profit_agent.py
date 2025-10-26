#!/usr/bin/env python3
"""
Profit Analysis Agent - Specialized in Financial Analysis and Profit Optimization
Uses ASI:One LLM for sophisticated profit analysis and communicates via chat protocol
"""

import os
import json
import asyncio
import requests
from datetime import datetime
from uuid import uuid4
from typing import Dict, Any, List, Optional
from uagents import Agent, Protocol, Context
from dotenv import load_dotenv

# Import chat protocol components
from uagents_core.contrib.protocols.chat import (
    ChatAcknowledgement,
    ChatMessage,
    TextContent,
    chat_protocol_spec,
)

# Load environment variables
load_dotenv()

# ASI:One API configuration
ASI_API_KEY = os.getenv("ASI_API_KEY")
ASI_BASE_URL = "https://api.asi1.ai/v1/chat/completions"
ASI_MODEL = "asi1-mini"

class ProfitAnalysisAgent:
    """Profit Analysis Agent with ASI:One reasoning capabilities"""
    
    def __init__(self):
        self.agent = Agent(
            name="profit_agent",
            port=8103,
            seed="profit_agent_seed_abc",
            endpoint=["http://localhost:8103/submit"]
        )
        
        # Chat protocol
        self.chat_proto = Protocol(spec=chat_protocol_spec)
        
        # Orchestrator address (will be set when orchestrator registers)
        self.orchestrator_address = "agent1qvh3vgk0s8h8j8z8k8l8m8n8o8p8q8r8s8t8u8v8w8x8y8z8"  # Placeholder
        
        # Profit analysis state
        self.financial_metrics = {}
        self.optimization_strategies = {}
        
        # ASI:One configuration
        if not ASI_API_KEY:
            print("⚠️ Profit Agent: ASI_API_KEY not found, running in demo mode")
            self.asi_enabled = False
        else:
            self.asi_enabled = True
            self.headers = {
                "Authorization": f"Bearer {ASI_API_KEY}",
                "Content-Type": "application/json"
            }
        
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup agent event handlers"""
        
        @self.agent.on_event("startup")
        async def startup_handler(ctx: Context):
            ctx.logger.info(f"💰 Profit Agent: Starting up at {ctx.agent.address}")
            print(f"💰 Profit Agent: Financial Analysis Specialist Ready!")
            print(f"💰 Address: {ctx.agent.address}")
            print(f"💰 Specializations:")
            print(f"   • Cost-benefit analysis")
            print(f"   • ROI optimization")
            print(f"   • Gas cost analysis")
            print(f"   • Profit margin calculations")
            
            # Register with orchestrator
            await asyncio.sleep(2)
            await self.register_with_orchestrator(ctx)
        
        @self.chat_proto.on_message(ChatMessage)
        async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
            await self.process_message(ctx, sender, msg)
        
        @self.chat_proto.on_message(ChatAcknowledgement)
        async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
            print(f"💰 Profit Agent: ✅ Message {msg.acknowledged_msg_id} acknowledged")
        
        # Include protocol
        self.agent.include(self.chat_proto, publish_manifest=True)
    
    async def register_with_orchestrator(self, ctx: Context):
        """Register with the orchestrator"""
        registration_msg = ChatMessage(
            timestamp=datetime.utcnow(),
            msg_id=uuid4(),
            content=[TextContent(type="text", text="REGISTER:profit_agent:Profit Analysis Specialist - Ready for financial analysis, ROI optimization, and cost-benefit calculations")]
        )
        
        await ctx.send(self.orchestrator_address, registration_msg)
        print(f"💰 Profit Agent: 📤 Registered with orchestrator")
    
    async def call_asi_one_llm(self, messages: List[Dict]) -> Dict[str, Any]:
        """Call ASI:One LLM for profit analysis reasoning"""
        if not self.asi_enabled:
            return {"choices": [{"message": {"content": "ASI:One not available - using demo response"}}]}
        
        payload = {
            "model": ASI_MODEL,
            "messages": messages,
            "temperature": 0.1,  # Very low temperature for precise financial calculations
            "max_tokens": 1500
        }
        
        try:
            response = requests.post(ASI_BASE_URL, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"💰 Profit Agent: ❌ ASI:One API error: {e}")
            return {"error": str(e)}
    
    async def process_message(self, ctx: Context, sender: str, msg: ChatMessage):
        """Process messages from orchestrator or other agents"""
        for item in msg.content:
            if isinstance(item, TextContent):
                print(f"💰 Profit Agent: 📨 Message from {sender}: {item.text}")
                
                # Send acknowledgment
                ack = ChatAcknowledgement(
                    timestamp=datetime.utcnow(),
                    acknowledged_msg_id=msg.msg_id
                )
                await ctx.send(sender, ack)
                
                # Process the request
                if item.text.startswith("ANALYSIS_REQUEST:"):
                    await self.handle_analysis_request(ctx, sender, item.text)
                else:
                    await self.handle_general_request(ctx, sender, item.text)
    
    async def handle_analysis_request(self, ctx: Context, sender: str, request: str):
        """Handle formal analysis requests from orchestrator"""
        parts = request.split(":", 2)
        if len(parts) >= 3:
            analysis_id = parts[1]
            analysis_request = parts[2]
            
            print(f"💰 Profit Agent: 🔍 Processing analysis request {analysis_id}")
            
            # Perform profit analysis using ASI:One
            analysis_result = await self.perform_profit_analysis(analysis_request)
            
            # Send result back
            response_msg = ChatMessage(
                timestamp=datetime.utcnow(),
                msg_id=uuid4(),
                content=[TextContent(type="text", text=f"ANALYSIS_RESULT:{analysis_id}:{analysis_result}")]
            )
            
            await ctx.send(sender, response_msg)
            print(f"💰 Profit Agent: 📤 Sent analysis result for {analysis_id}")
    
    async def handle_general_request(self, ctx: Context, sender: str, message: str):
        """Handle general requests and questions"""
        # Use ASI:One to analyze the request
        system_prompt = """You are a specialized Financial and Profit Analysis agent. You are an expert in:

1. Financial Analysis:
   - Cost-benefit analysis
   - ROI (Return on Investment) calculations
   - Profit margin optimization
   - Break-even analysis

2. DeFi Economics:
   - Gas cost optimization
   - Transaction fee analysis
   - Yield farming strategies
   - Liquidity provision profitability

3. Risk Assessment:
   - Financial risk evaluation
   - Market volatility analysis
   - Impermanent loss calculations
   - Portfolio optimization

4. Performance Metrics:
   - APY/APR calculations
   - Total Value Locked (TVL) analysis
   - Fee generation analysis
   - Capital efficiency metrics

5. Optimization Strategies:
   - Cost reduction techniques
   - Revenue maximization
   - Tax efficiency
   - Cash flow optimization

Analyze the user's request and provide expert financial and profit insights."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        response = await self.call_asi_one_llm(messages)
        
        if "error" not in response:
            analysis = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Enhance with profit-specific insights
            enhanced_analysis = await self.enhance_with_profit_insights(analysis, message)
            
            response_msg = ChatMessage(
                timestamp=datetime.utcnow(),
                msg_id=uuid4(),
                content=[TextContent(type="text", text=enhanced_analysis)]
            )
            
            await ctx.send(sender, response_msg)
            print(f"💰 Profit Agent: 📤 Sent profit analysis response")
        else:
            error_msg = ChatMessage(
                timestamp=datetime.utcnow(),
                msg_id=uuid4(),
                content=[TextContent(type="text", text=f"❌ Profit Analysis Error: {response['error']}")]
            )
            await ctx.send(sender, error_msg)
    
    async def perform_profit_analysis(self, request: str) -> str:
        """Perform comprehensive profit analysis"""
        
        # Use ASI:One for deep profit analysis
        analysis_prompt = f"""Perform a comprehensive financial and profit analysis for: "{request}"

Analyze the following aspects:

1. Cost Analysis:
   - Gas costs and transaction fees
   - Operational expenses
   - Infrastructure costs
   - Opportunity costs

2. Revenue Analysis:
   - Direct revenue streams
   - Indirect benefits
   - Fee savings
   - Efficiency gains

3. ROI Calculations:
   - Return on investment metrics
   - Payback period analysis
   - Net present value (NPV)
   - Internal rate of return (IRR)

4. Profit Optimization:
   - Cost reduction opportunities
   - Revenue enhancement strategies
   - Efficiency improvements
   - Risk mitigation benefits

5. Financial Projections:
   - Short-term profit forecasts
   - Long-term financial impact
   - Scalability economics
   - Break-even analysis

6. Comparative Analysis:
   - Alternative solution costs
   - Market benchmark comparisons
   - Competitive advantage assessment

Provide detailed financial metrics and actionable profit optimization recommendations."""

        messages = [{"role": "user", "content": analysis_prompt}]
        response = await self.call_asi_one_llm(messages)
        
        if "error" not in response:
            return response.get("choices", [{}])[0].get("message", {}).get("content", "")
        else:
            return f"Profit Analysis Error: {response['error']}"
    
    async def enhance_with_profit_insights(self, base_analysis: str, original_request: str) -> str:
        """Enhance analysis with additional profit-specific insights"""
        
        enhancement_prompt = f"""Base analysis: "{base_analysis}"
Original request: "{original_request}"

Enhance this analysis with additional financial and profit insights:

1. Add specific financial benchmarks and KPIs
2. Include real-world profitability case studies
3. Suggest financial monitoring and tracking tools
4. Provide investment and budgeting recommendations
5. Include relevant financial statistics and market data

Format as a comprehensive financial analysis report with actionable insights."""

        messages = [{"role": "user", "content": enhancement_prompt}]
        response = await self.call_asi_one_llm(messages)
        
        if "error" not in response:
            enhanced = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            return f"💰 PROFIT ANALYSIS REPORT 💰\n\n{enhanced}\n\n--- Profit Agent Analysis Complete ---"
        else:
            return f"💰 PROFIT ANALYSIS 💰\n\n{base_analysis}\n\n⚠️ Enhancement failed: {response['error']}"
    
    def run(self):
        """Start the profit analysis agent"""
        print("💰 Starting Profit Analysis Agent")
        print("=" * 50)
        print("Specializations:")
        print("✅ Cost-benefit analysis and ROI calculations")
        print("✅ Gas cost optimization strategies")
        print("✅ Financial risk assessment")
        print("✅ Profit margin optimization")
        print("✅ DeFi yield and liquidity analysis")
        print("✅ Investment and budgeting recommendations")
        print()
        self.agent.run()

# Global profit agent instance
profit_agent = ProfitAnalysisAgent()

if __name__ == '__main__':
    profit_agent.run()