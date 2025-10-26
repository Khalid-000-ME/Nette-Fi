#!/usr/bin/env python3
"""
Multi-Agent Analysis Team Demo
Demonstrates sophisticated chat protocol between orchestrator and analysis agents
"""

import asyncio
import subprocess
import sys
import time
from datetime import datetime

def print_banner():
    """Print demo banner"""
    print("=" * 80)
    print("🎭 MULTI-AGENT ANALYSIS TEAM DEMO 🎭")
    print("=" * 80)
    print()
    print("This demo showcases:")
    print("✅ Orchestrator coordinating multiple specialized agents")
    print("✅ ASI:One LLM reasoning and tool calling")
    print("✅ Chat protocol communication between agents")
    print("✅ MEV, Speed, and Profit analysis specialists")
    print("✅ Real-time price, balance, and user data integration")
    print()
    print("Architecture:")
    print("🎭 Orchestrator (Port 8100) - Coordinates analysis requests")
    print("🛡️ MEV Agent (Port 8101) - MEV analysis and protection")
    print("⚡ Speed Agent (Port 8102) - Performance optimization")
    print("💰 Profit Agent (Port 8103) - Financial analysis")
    print()

def start_agent(script_name, agent_name):
    """Start an agent in a separate process"""
    try:
        print(f"🚀 Starting {agent_name}...")
        process = subprocess.Popen([
            sys.executable, script_name
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        
        # Give the agent time to start
        time.sleep(2)
        
        # Check if process is still running
        if process.poll() is None:
            print(f"✅ {agent_name} started successfully (PID: {process.pid})")
            return process
        else:
            stdout, stderr = process.communicate()
            print(f"❌ {agent_name} failed to start:")
            print(f"   STDOUT: {stdout}")
            print(f"   STDERR: {stderr}")
            return None
    except Exception as e:
        print(f"❌ Error starting {agent_name}: {e}")
        return None

def main():
    """Main demo function"""
    print_banner()
    
    # Check dependencies
    print("🔍 Checking dependencies...")
    try:
        import uagents
        import requests
        from dotenv import load_dotenv
        print("✅ All dependencies found")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please install: pip install uagents requests python-dotenv")
        return
    
    print()
    print("🎬 DEMO SEQUENCE")
    print("-" * 40)
    
    # Start agents
    agents = []
    
    # Start orchestrator first
    orchestrator = start_agent("orchestrator.py", "Orchestrator")
    if orchestrator:
        agents.append(("Orchestrator", orchestrator))
    
    # Start analysis agents
    mev_agent = start_agent("mev_agent.py", "MEV Agent")
    if mev_agent:
        agents.append(("MEV Agent", mev_agent))
    
    speed_agent = start_agent("speed_agent.py", "Speed Agent")
    if speed_agent:
        agents.append(("Speed Agent", speed_agent))
    
    profit_agent = start_agent("profit_agent.py", "Profit Agent")
    if profit_agent:
        agents.append(("Profit Agent", profit_agent))
    
    if not agents:
        print("❌ No agents started successfully. Exiting.")
        return
    
    print()
    print(f"🎉 Successfully started {len(agents)} agents!")
    print()
    
    # Demo scenarios
    print("📋 DEMO SCENARIOS")
    print("-" * 40)
    print()
    print("1. 🛡️ MEV Protection Analysis")
    print("   - Analyze payroll batch for MEV vulnerabilities")
    print("   - Recommend protection strategies")
    print("   - Suggest optimal transaction timing")
    print()
    print("2. ⚡ Performance Optimization")
    print("   - Analyze transaction throughput")
    print("   - Optimize gas usage")
    print("   - Recommend batch sizes")
    print()
    print("3. 💰 Financial Analysis")
    print("   - Calculate cost savings")
    print("   - ROI analysis for netted transactions")
    print("   - Profit optimization strategies")
    print()
    print("4. 🎭 Multi-Agent Coordination")
    print("   - Orchestrator routes complex queries")
    print("   - Agents collaborate on analysis")
    print("   - Comprehensive reports generated")
    print()
    
    # Interactive demo
    try:
        print("🎮 INTERACTIVE DEMO")
        print("-" * 40)
        print("The agents are now running and communicating!")
        print()
        print("To interact with the system:")
        print("1. Send HTTP requests to the orchestrator (localhost:8100)")
        print("2. Use the chat protocol to send analysis requests")
        print("3. Watch the console output for agent communications")
        print()
        print("Example analysis requests:")
        print('- "Analyze MEV risks for 50 employee payroll batch"')
        print('- "Optimize gas costs for daily payment processing"')
        print('- "Calculate ROI for switching to netted transactions"')
        print()
        print("Press Ctrl+C to stop all agents...")
        
        # Keep demo running
        while True:
            time.sleep(1)
            
            # Check if any agent died
            for name, process in agents:
                if process.poll() is not None:
                    print(f"⚠️ {name} has stopped unexpectedly")
    
    except KeyboardInterrupt:
        print("\n🛑 Stopping demo...")
    
    finally:
        # Clean up processes
        print("🧹 Cleaning up agents...")
        for name, process in agents:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {name} stopped")
            except subprocess.TimeoutExpired:
                process.kill()
                print(f"🔪 {name} force killed")
            except Exception as e:
                print(f"⚠️ Error stopping {name}: {e}")
        
        print()
        print("🎬 Demo completed!")
        print("=" * 80)

if __name__ == '__main__':
    main()
