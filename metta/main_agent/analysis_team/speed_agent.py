#!/usr/bin/env python3
"""
Speed Analysis Agent - Specialized in Transaction Speed and Performance Optimization
Uses ASI:One LLM for sophisticated speed analysis and communicates via chat protocol
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

class SpeedAnalysisAgent:
    """Speed Analysis Agent with ASI:One reasoning capabilities"""
    
    def __init__(self):
        self.agent = Agent(
            name="speed_agent",
            port=8102,
            seed="speed_agent_seed_789",
            endpoint=["http://localhost:8102/submit"]
        )
        
        # Chat protocol
        self.chat_proto = Protocol(spec=chat_protocol_spec)
        
        # Orchestrator address (will be set when orchestrator registers)
        self.orchestrator_address = "agent1qvh3vgk0s8h8j8z8k8l8m8n8o8p8q8r8s8t8u8v8w8x8y8z8"  # Placeholder
        
        # Speed analysis state
        self.performance_metrics = {}
        self.optimization_strategies = {}
        
        # ASI:One configuration
        if not ASI_API_KEY:
            print("⚠️ Speed Agent: ASI_API_KEY not found, running in demo mode")
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
            ctx.logger.info(f"⚡ Speed Agent: Starting up at {ctx.agent.address}")
            print(f"⚡ Speed Agent: Transaction Speed Specialist Ready!")
            print(f"⚡ Address: {ctx.agent.address}")
            print(f"⚡ Specializations:")
            print(f"   • Transaction throughput analysis")
            print(f"   • Gas optimization strategies")
            print(f"   • Network congestion analysis")
            print(f"   • Batch processing optimization")
            
            # Register with orchestrator
            await asyncio.sleep(2)
            await self.register_with_orchestrator(ctx)
        
        @self.chat_proto.on_message(ChatMessage)
        async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
            await self.process_message(ctx, sender, msg)
        
        @self.chat_proto.on_message(ChatAcknowledgement)
        async def handle_acknowledgement(ctx: Context, sender: str, msg: ChatAcknowledgement):
            print(f"⚡ Speed Agent: ✅ Message {msg.acknowledged_msg_id} acknowledged")
        
        # Include protocol
        self.agent.include(self.chat_proto, publish_manifest=True)
    
    async def register_with_orchestrator(self, ctx: Context):
        """Register with the orchestrator"""
        registration_msg = ChatMessage(
            timestamp=datetime.utcnow(),
            msg_id=uuid4(),
            content=[TextContent(type="text", text="REGISTER:speed_agent:Speed Analysis Specialist - Ready for throughput analysis, gas optimization, and performance tuning")]
        )
        
        await ctx.send(self.orchestrator_address, registration_msg)
        print(f"⚡ Speed Agent: 📤 Registered with orchestrator")
    
    async def call_asi_one_llm(self, messages: List[Dict]) -> Dict[str, Any]:
        """Call ASI:One LLM for speed analysis reasoning"""
        if not self.asi_enabled:
            return {"choices": [{"message": {"content": "ASI:One not available - using demo response"}}]}
        
        payload = {
            "model": ASI_MODEL,
            "messages": messages,
            "temperature": 0.2,  # Lower temperature for precise technical analysis
            "max_tokens": 1500
        }
        
        try:
            response = requests.post(ASI_BASE_URL, headers=self.headers, json=payload, timeout=30)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"⚡ Speed Agent: ❌ ASI:One API error: {e}")
            return {"error": str(e)}
    
    async def process_message(self, ctx: Context, sender: str, msg: ChatMessage):
        """Process messages from orchestrator or other agents"""
        for item in msg.content:
            if isinstance(item, TextContent):
                print(f"⚡ Speed Agent: 📨 Message from {sender}: {item.text}")
                
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
            
            print(f"⚡ Speed Agent: 🔍 Processing analysis request {analysis_id}")
            
            # Perform speed analysis using ASI:One
            analysis_result = await self.perform_speed_analysis(analysis_request)
            
            # Send result back
            response_msg = ChatMessage(
                timestamp=datetime.utcnow(),
                msg_id=uuid4(),
                content=[TextContent(type="text", text=f"ANALYSIS_RESULT:{analysis_id}:{analysis_result}")]
            )
            
            await ctx.send(sender, response_msg)
            print(f"⚡ Speed Agent: 📤 Sent analysis result for {analysis_id}")
    
    async def handle_general_request(self, ctx: Context, sender: str, message: str):
        """Handle general requests and questions"""
        # Use ASI:One to analyze the request
        system_prompt = """You are a specialized Transaction Speed and Performance Analysis agent. You are an expert in:

1. Transaction Performance:
   - Throughput optimization
   - Latency reduction
   - Gas efficiency analysis
   - Block confirmation times

2. Network Analysis:
   - Congestion patterns
   - Peak usage times
   - Network bottlenecks
   - Scalability solutions

3. Optimization Strategies:
   - Batch processing techniques
   - Gas price optimization
   - Transaction timing
   - Parallel processing

4. Performance Metrics:
   - TPS (Transactions Per Second)
   - Confirmation times
   - Gas usage efficiency
   - Cost-performance ratios

Analyze the user's request and provide expert speed and performance insights."""

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        response = await self.call_asi_one_llm(messages)
        
        if "error" not in response:
            analysis = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            
            # Enhance with speed-specific insights
            enhanced_analysis = await self.enhance_with_speed_insights(analysis, message)
            
            response_msg = ChatMessage(
                timestamp=datetime.utcnow(),
                msg_id=uuid4(),
                content=[TextContent(type="text", text=enhanced_analysis)]
            )
            
            await ctx.send(sender, response_msg)
            print(f"⚡ Speed Agent: 📤 Sent speed analysis response")
        else:
            error_msg = ChatMessage(
                timestamp=datetime.utcnow(),
                msg_id=uuid4(),
                content=[TextContent(type="text", text=f"❌ Speed Analysis Error: {response['error']}")]
            )
            await ctx.send(sender, error_msg)
    
    async def perform_speed_analysis(self, request: str) -> str:
        """Perform comprehensive speed analysis"""
        
        # Use ASI:One for deep speed analysis
        analysis_prompt = f"""Perform a comprehensive speed and performance analysis for: "{request}"

Analyze the following aspects:

1. Throughput Analysis:
   - Current transaction throughput (TPS)
   - Bottleneck identification
   - Scalability limitations
   - Peak performance capacity

2. Latency Optimization:
   - Transaction confirmation times
   - Network propagation delays
   - Processing queue analysis
   - Real-time performance metrics

3. Gas Efficiency:
   - Gas usage optimization
   - Cost-performance ratios
   - Gas price strategies
   - Batch processing benefits

4. Performance Recommendations:
   - Specific optimization techniques
   - Timing strategies
   - Batch size recommendations
   - Network congestion avoidance

5. Technical Improvements:
   - Parallel processing opportunities
   - Caching strategies
   - Load balancing techniques
   - Infrastructure scaling

Provide actionable performance optimization recommendations."""

        messages = [{"role": "user", "content": analysis_prompt}]
        response = await self.call_asi_one_llm(messages)
        
        if "error" not in response:
            return response.get("choices", [{}])[0].get("message", {}).get("content", "")
        else:
            return f"Speed Analysis Error: {response['error']}"
    
    async def enhance_with_speed_insights(self, base_analysis: str, original_request: str) -> str:
        """Enhance analysis with additional speed-specific insights"""
        
        enhancement_prompt = f"""Base analysis: "{base_analysis}"
Original request: "{original_request}"

Enhance this analysis with additional speed and performance insights:

1. Add specific performance benchmarks and targets
2. Include real-world optimization case studies
3. Suggest performance monitoring tools
4. Provide timing and scheduling recommendations
5. Include relevant performance statistics

Format as a comprehensive speed optimization report."""

        messages = [{"role": "user", "content": enhancement_prompt}]
        response = await self.call_asi_one_llm(messages)
        
        if "error" not in response:
            enhanced = response.get("choices", [{}])[0].get("message", {}).get("content", "")
            return f"⚡ SPEED ANALYSIS REPORT ⚡\n\n{enhanced}\n\n--- Speed Agent Analysis Complete ---"
        else:
            return f"⚡ SPEED ANALYSIS ⚡\n\n{base_analysis}\n\n⚠️ Enhancement failed: {response['error']}"
    
    def run(self):
        """Start the speed analysis agent"""
        print("⚡ Starting Speed Analysis Agent")
        print("=" * 50)
        print("Specializations:")
        print("✅ Transaction throughput optimization")
        print("✅ Latency reduction strategies")
        print("✅ Gas efficiency analysis")
        print("✅ Network congestion management")
        print("✅ Batch processing optimization")
        print("✅ Performance monitoring and metrics")
        print()
        self.agent.run()

# Global speed agent instance
speed_agent = SpeedAnalysisAgent()

if __name__ == '__main__':
    speed_agent.run()