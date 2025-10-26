#!/usr/bin/env python3
"""
MEV Analysis Agent - Specialized in MEV Detection and Protection
Uses ASI:One LLM for sophisticated MEV analysis and communicates via chat protocol
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

class MEVAnalysisAgent:
    """MEV Analysis Agent with ASI:One reasoning capabilities"""
    
    def __init__(self):
        self.agent = Agent(
            name="mev_agent",
            port=8101,
            seed="mev_agent_seed_456",
            endpoint=["http://localhost:8101/submit"]
        )
        
        # Chat protocol
        self.chat_proto = Protocol(spec=chat_protocol_spec)
        
        # Orchestrator address (will be set when orchestrator registers)
        self.orchestrator_address = "agent1qvh3vgk0s8h8j8z8k8l8m8n8o8p8q8r8s8t8u8v8w8x8y8z8"  # Placeholder
        
        # MEV analysis state
        self.mev_patterns = {}
        self.protection_strategies = {}
        
        # ASI:One configuration
        if not ASI_API_KEY:
            print("⚠️ MEV Agent: ASI_API_KEY not found, running in demo mode")
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
            ctx.logger.info(f"🛡️ MEV Agent: Starting up at {ctx.agent.address}")
            print(f"🛡️ MEV Agent: MEV Analysis Specialist Ready!")
            print(f"🛡️ Address: {ctx.agent.address}")
            print(f"🛡️ Specializations:")
            print(f"   • Sandwich attack detection")
            print(f"   • Front-running analysis")
            print(f"   • MEV protection strategies")
            print(f"   • Transaction ordering analysis")
            
            # Register with orchestrator
            await asyncio.sleep(2)
            await self.register_with_orchestrator(ctx)
        
        @self.chat_proto.on_message(ChatMessage)
        async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
            await self.process_message(ctx, sender, msg)
        
        @self.chat_proto.on_message(ChatAcknowledgement)
        async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
            print(f"🛡️ MEV Agent: ✅ Message {msg.acknowledged_msg_id} acknowledged")
        
        # Include protocol
        self.agent.include(self.chat_proto, publish_manifest=True)
    
    async def register_with_orchestrator(self, ctx: Context):
        """Register with the orchestrator"""
        registration_msg = ChatMessage(
            timestamp=datetime.utcnow(),
            msg_id=uuid4(),
            content=[TextContent(type="text", text="REGISTER:mev_agent:MEV Analysis Specialist - Ready for sandwich attack detection, front-running analysis, and MEV protection strategies")]
        )
        
        await ctx.send(self.orchestrator_address, registration_msg)
        print(f"🛡️ MEV Agent: 📤 Registered with orchestrator")
    
    async def call_asi_one_llm(self, messages: List[Dict]) -> Dict[str, Any]:
        """Call ASI:One LLM for MEV analysis reasoning"""
        if not self.asi_enabled:
            return {"choices": [{"message": {"content": "ASI:One not available - using demo response"}}]}
        
        payload = {
            "model": ASI_MODEL,
            "messages": messages,
            "temperature": 0.3,  # Lower temperature for more focused analysis
            "max_tokens": 1500
        }
        
        try:
            response = requests.post(ASI_BASE_URL, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"🛡️ MEV Agent: ❌ ASI:One API error: {e}")
            return {"error": str(e)}
    
    async def process_message(self, ctx: Context, sender: str, msg: ChatMessage):
        """Process messages from orchestrator or other agents"""
        for item in msg.content:
            if isinstance(item, TextContent):
                print(f"🛡️ MEV Agent: 📨 Message from {sender}: {item.text}")
                
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
            
            print(f"🛡️ MEV Agent: 🔍 Processing analysis request {analysis_id}")
            
            # Perform MEV analysis using ASI:One
            analysis_result = await self.perform_mev_analysis(analysis_request)
            
            # Send result back
            response_msg = ChatMessage(
                timestamp=datetime.utcnow(),
                msg_id=uuid4(),
                content=[TextContent(type="text", text=f"ANALYSIS_RESULT:{analysis_id}:{analysis_result}")]
            )
            
            await ctx.send(sender, response_msg)
            print(f"🛡️ MEV Agent: 📤 Sent analysis result for {analysis_id}")
    
    async def handle_general_request(self, ctx: Context, sender: str, message: str):
        """Handle general requests and questions"""
        # Use ASI:One to analyze the request
        system_prompt = """You are a specialized MEV (Maximum Extractable Value) analysis agent. You are an expert in:

1. MEV Attack Detection:
   - Sandwich attacks
   - Front-running
   - Back-running
   - Arbitrage extraction
   - Liquidation MEV

2. MEV Protection Strategies:
   - Private mempools
   - Commit-reveal schemes
   - Batch auctions
   - MEV-resistant protocols

3. Transaction Analysis:
   - Gas price analysis
   - Transaction ordering
   - Block builder behavior
   - Validator MEV extraction

Analyze the user's request and provide expert MEV-focused insights."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        response = await self.call_asi_one_llm(messages)
        
        if "error" not in response:
            analysis = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Enhance with MEV-specific insights
            enhanced_analysis = await self.enhance_with_mev_insights(analysis, message)
            
            response_msg = ChatMessage(
                timestamp=datetime.utcnow(),
                msg_id=uuid4(),
                content=[TextContent(type="text", text=enhanced_analysis)]
            )
            
            await ctx.send(sender, response_msg)
            print(f"🛡️ MEV Agent: 📤 Sent MEV analysis response")
        else:
            error_msg = ChatMessage(
                timestamp=datetime.utcnow(),
                msg_id=uuid4(),
                content=[TextContent(type="text", text=f"❌ MEV Analysis Error: {response['error']}")]
            )
            await ctx.send(sender, error_msg)
    
    async def perform_mev_analysis(self, request: str) -> str:
        """Perform comprehensive MEV analysis"""
        
        # Use ASI:One for deep MEV analysis
        analysis_prompt = f"""Perform a comprehensive MEV analysis for: "{request}"

Analyze the following aspects:

1. MEV Risk Assessment:
   - Potential sandwich attack vectors
   - Front-running vulnerabilities
   - Arbitrage opportunities
   - Liquidation risks

2. Protection Recommendations:
   - Specific MEV protection strategies
   - Gas optimization techniques
   - Transaction timing recommendations
   - Protocol-level protections

3. Market Impact Analysis:
   - Slippage considerations
   - Market manipulation risks
   - Cross-DEX arbitrage potential

4. Technical Mitigation:
   - Private mempool usage
   - Batch transaction strategies
   - MEV-resistant routing

Provide actionable insights and specific recommendations."""

        messages = [{"role": "user", "content": analysis_prompt}]
        response = await self.call_asi_one_llm(messages)
        
        if "error" not in response:
            return response.get("choices", [{}])[0].get("message", {}).get("content", "")
        else:
            return f"MEV Analysis Error: {response['error']}"
    
    async def enhance_with_mev_insights(self, base_analysis: str, original_request: str) -> str:
        """Enhance analysis with additional MEV-specific insights"""
        
        enhancement_prompt = f"""Base analysis: "{base_analysis}"
Original request: "{original_request}"

Enhance this analysis with additional MEV-specific insights:

1. Add specific MEV attack patterns to watch for
2. Include gas optimization strategies
3. Suggest MEV protection tools and services
4. Provide transaction timing recommendations
5. Include relevant MEV statistics or benchmarks

Format as a comprehensive MEV analysis report."""

        messages = [{"role": "user", "content": enhancement_prompt}]
        response = await self.call_asi_one_llm(messages)
        
        if "error" not in response:
            enhanced = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            return f"🛡️ MEV ANALYSIS REPORT 🛡️\n\n{enhanced}\n\n--- MEV Agent Analysis Complete ---"
        else:
            return f"🛡️ MEV ANALYSIS 🛡️\n\n{base_analysis}\n\n⚠️ Enhancement failed: {response['error']}"
    
    def run(self):
        """Start the MEV analysis agent"""
        print("🛡️ Starting MEV Analysis Agent")
        print("=" * 50)
        print("Specializations:")
        print("✅ Sandwich attack detection and prevention")
        print("✅ Front-running and back-running analysis")
        print("✅ MEV protection strategy recommendations")
        print("✅ Transaction ordering optimization")
        print("✅ Gas price and timing analysis")
        print("✅ Private mempool and batch strategies")
        print()
        self.agent.run()

# Global MEV agent instance
mev_agent = MEVAnalysisAgent()

if __name__ == '__main__':
    mev_agent.run()