# 🎭 Multi-Agent Analysis Team

A sophisticated multi-agent system for DeFi analysis using ASI:One LLM reasoning and uAgents chat protocol.

## 🏗️ Architecture

```
🎭 Orchestrator (Port 8100)
├── 🛡️ MEV Agent (Port 8101) - MEV Analysis & Protection
├── ⚡ Speed Agent (Port 8102) - Performance Optimization  
└── 💰 Profit Agent (Port 8103) - Financial Analysis
```

## 🚀 Features

### 🎭 **Orchestrator**
- **ASI:One LLM Integration**: Uses ASI1-mini for intelligent request routing
- **Tool Access**: Price feeds, balance checking, user analytics
- **Multi-Agent Coordination**: Routes requests to specialized agents
- **Chat Protocol**: Sophisticated inter-agent communication

### 🛡️ **MEV Agent**
- **Sandwich Attack Detection**: Identifies MEV vulnerabilities
- **Front-running Analysis**: Analyzes transaction ordering risks
- **Protection Strategies**: Recommends MEV mitigation techniques
- **Gas Optimization**: Suggests optimal transaction timing

### ⚡ **Speed Agent**
- **Throughput Analysis**: TPS optimization and bottleneck identification
- **Latency Optimization**: Reduces confirmation times
- **Batch Processing**: Optimizes batch sizes and timing
- **Performance Metrics**: Real-time performance monitoring

### 💰 **Profit Agent**
- **ROI Calculations**: Financial return analysis
- **Cost-Benefit Analysis**: Comprehensive financial modeling
- **Gas Cost Optimization**: Minimizes transaction costs
- **Profit Projections**: Long-term financial forecasting

## 📋 Use Cases

### 1. **DeFi Payroll Analysis**
```python
# Orchestrator receives request
"Analyze MEV risks and optimize costs for 100 employee payroll batch"

# Routes to all agents:
# 🛡️ MEV Agent: Identifies sandwich attack risks
# ⚡ Speed Agent: Optimizes batch size and timing
# 💰 Profit Agent: Calculates cost savings vs individual transactions
```

### 2. **Transaction Optimization**
```python
# Multi-agent collaboration
"What's the optimal strategy for processing daily payments?"

# Coordinated analysis:
# - MEV protection recommendations
# - Performance optimization strategies  
# - Financial impact assessment
```

### 3. **Risk Assessment**
```python
# Comprehensive risk analysis
"Evaluate risks of switching from individual to batched transactions"

# Each agent provides specialized insights:
# - Security vulnerabilities (MEV)
# - Performance implications (Speed)
# - Financial trade-offs (Profit)
```

## 🛠️ Setup

### Prerequisites
```bash
pip install uagents requests python-dotenv
```

### Environment Variables
```bash
# .env file
ASI_API_KEY=your_asi_one_api_key_here
```

### Running the System

#### Option 1: Demo Script (Recommended)
```bash
cd analysis_team
python demo_multi_agent.py
```

#### Option 2: Manual Start
```bash
# Terminal 1 - Orchestrator
python orchestrator.py

# Terminal 2 - MEV Agent  
python mev_agent.py

# Terminal 3 - Speed Agent
python speed_agent.py

# Terminal 4 - Profit Agent
python profit_agent.py
```

## 🔄 Communication Protocol

### Agent Registration
```python
# Agents register with orchestrator on startup
REGISTER:agent_name:Agent Description and Capabilities
```

### Analysis Requests
```python
# Orchestrator sends formal analysis requests
ANALYSIS_REQUEST:analysis_id:request_description

# Agents respond with results
ANALYSIS_RESULT:analysis_id:detailed_analysis
```

### Chat Messages
```python
# Standard chat protocol for general communication
ChatMessage(
    timestamp=datetime.utcnow(),
    msg_id=uuid4(),
    content=[TextContent(type="text", text="message")]
)
```

## 🎯 Example Interactions

### MEV Analysis Request
```python
# User asks orchestrator
"What MEV risks exist for a 50-transaction payroll batch?"

# Orchestrator uses ASI:One to understand request
# Routes to MEV Agent with context
# MEV Agent performs comprehensive analysis
# Returns detailed MEV protection recommendations
```

### Multi-Agent Coordination
```python
# Complex request requiring multiple agents
"Optimize our payroll system for cost, speed, and security"

# Orchestrator coordinates:
# 1. MEV Agent: Security analysis
# 2. Speed Agent: Performance optimization  
# 3. Profit Agent: Cost-benefit analysis
# 4. Synthesizes results into comprehensive report
```

## 📊 Agent Specializations

| Agent | Focus | Key Metrics | Tools |
|-------|-------|-------------|-------|
| 🛡️ MEV | Security | MEV Risk Score, Protection Coverage | Attack Detection, Mitigation Strategies |
| ⚡ Speed | Performance | TPS, Latency, Throughput | Batch Optimization, Gas Analysis |
| 💰 Profit | Finance | ROI, Cost Savings, NPV | Financial Modeling, Risk Assessment |

## 🔧 Technical Details

### ASI:One Integration
- **Model**: asi1-mini for reasoning and analysis
- **Temperature**: Optimized per agent (0.1-0.7)
- **Tool Calling**: Automatic tool selection and execution
- **Context Management**: Maintains conversation state

### Chat Protocol
- **Framework**: uAgents with chat protocol specification
- **Message Types**: ChatMessage, ChatAcknowledgement
- **Content Types**: TextContent for analysis reports
- **Reliability**: Acknowledgment-based message delivery

### Error Handling
- **Graceful Degradation**: Continues operation if ASI:One unavailable
- **Timeout Management**: 30-second API timeouts
- **Retry Logic**: Automatic retry for failed requests
- **Fallback Responses**: Demo responses when API unavailable

## 🎮 Demo Scenarios

The demo script showcases:

1. **Agent Startup**: All agents initialize and register
2. **Communication**: Inter-agent message passing
3. **Analysis Coordination**: Multi-agent collaboration
4. **Tool Integration**: Real-time data access
5. **Error Handling**: Graceful failure management

## 🚀 Future Enhancements

- **Agent Discovery**: Dynamic agent registration and discovery
- **Load Balancing**: Distribute requests across agent instances
- **Persistent State**: Database integration for analysis history
- **Web Interface**: Dashboard for monitoring agent activities
- **Custom Agents**: Framework for adding specialized agents

## 📝 Notes

- Agents run on separate ports (8100-8103)
- Each agent has specialized ASI:One prompts
- Tool access is managed through the orchestrator
- Chat protocol ensures reliable message delivery
- Demo mode available when ASI:One API unavailable
