# Sim-U-Fi - Predictive MEV Protection Platform

> *"One trade. Infinite simulations. Zero regrets."*

**Built for ETHGlobal Online 2025**

Sim-U-Fi is a revolutionary DeFi trading platform that uses AI-powered parallel execution simulation to protect users from MEV attacks. Leveraging **Arcology Network**, **Pyth Network**, **Blockscout**, and **ASI:One with MeTTa consensus**, it shows you what will happen **before** you trade, allowing you to make informed decisions about timing, gas prices, and execution strategies.

## 🌟 Key Features

- **🔮 Parallel Simulation**: Run 100+ trade simulations across different timing and gas conditions using **Arcology Network**
- **🤖 AI Agent Consensus**: Multi-agent AI system powered by **ASI:One** debates and reaches consensus on optimal execution using **MeTTa reasoning**
- **🛡️ MEV Detection**: Identify sandwich attacks and frontrunning patterns using **Blockscout** historical analysis
- **📊 Real-time Price Feeds**: Get accurate, live market data from **Pyth Network** with confidence intervals
- **📈 Visual Analysis**: Beautiful, modern UI showing all possible trade outcomes with detailed reasoning
- **⚡ Real-time Execution**: Get comprehensive analysis in under 10 seconds
- **🎯 Smart Timing**: Know exactly when to execute for maximum profit and minimum MEV exposure

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   MeTTa API     │    │  Smart Contracts│
│   (Next.js)     │◄──►│   (FastAPI)     │    │   (Solidity)    │
│                 │    │                 │    │                 │
│ • Trading UI    │    │ • AI Agents     │    │ • MEV Protection│
│ • Visualization │    │ • Consensus     │    │ • Trade Executor│
│ • User Controls │    │ • ASI:One       │    │ • Queue System  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌─────────────────────────────────────────────────┐
         │              External Services                  │
         │                                                 │
         │ • Arcology Network (Parallel Execution)        │
         │ • ASI:One (AI Reasoning)                       │
         │ • Blockscout (Mempool Data)                    │
         │ • Pyth Oracle (Price Feeds)                    │
         └─────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Python 3.9+
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/sim-u-fi.git
cd sim-u-fi
```

### 2. Setup Frontend

```bash
cd frontend
npm install
npm run dev
```

The frontend will be available at `http://localhost:3000`

### 3. Setup MeTTa Service

```bash
cd ../metta
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Optional: Set ASI:One API key for enhanced AI reasoning
export ASI_ONE_API_KEY="your-api-key-here"

uvicorn main:app --reload --port 8000
```

The MeTTa API will be available at `http://localhost:8000`

### 4. Setup Smart Contracts (Optional)

```bash
cd ../block
npm install

# Copy environment template
cp .env.example .env
# Edit .env with your RPC URLs and private keys

# Deploy to local network
npm run deploy:local

# Deploy to Base Sepolia testnet
npm run deploy:base-sepolia
```

## 📁 Project Structure

```
Sim-U-Fi/
├── frontend/              # Next.js 14 frontend application
│   ├── src/
│   │   ├── app/
│   │   │   ├── api/       # API routes for orchestration
│   │   │   ├── trade/     # Main trading interface
│   │   │   └── globals.css
│   │   └── lib/           # Utility functions
│   ├── package.json
│   └── README.md
│
├── metta/                 # FastAPI service for AI analysis
│   ├── agents/            # Individual AI agents
│   │   ├── mev_agent.py   # MEV protection specialist
│   │   ├── profit_agent.py # Profit maximization specialist
│   │   ├── speed_agent.py  # Speed optimization specialist
│   │   └── consensus_agent.py # MeTTa consensus reasoning
│   ├── main.py            # FastAPI application
│   └── requirements.txt
│
├── block/                 # Smart contracts and deployment
│   ├── contracts/
│   │   ├── SimUFiExecutor.sol    # Trade execution contract
│   │   └── MEVProtection.sol     # MEV detection contract
│   ├── scripts/
│   │   └── deploy.js      # Deployment script
│   ├── hardhat.config.js
│   └── package.json
│
├── flow/                  # Architecture diagrams
└── README.md             # This file
```

## 🔧 API Documentation

### Frontend API Routes

#### `POST /api/orchestrate`
Master endpoint that coordinates the entire simulation → decision flow.

**Request:**
```json
{
  "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "trade": {
    "from_token": "ETH",
    "to_token": "USDC",
    "amount": "5.0",
    "chain": "base"
  },
  "user_priority": "balanced",
  "risk_tolerance": "balanced",
  "max_wait_blocks": 5,
  "auto_execute": false
}
```

**Response:**
```json
{
  "request_id": "req_abc123",
  "status": "ready",
  "recommendation": {
    "execute_at_block": 19234567,
    "blocks_to_wait": 3,
    "expected_output_usd": "15120.45",
    "confidence": 92,
    "savings_vs_immediate": "124.00"
  },
  "agent_reasoning": {
    "mev_agent": "Option 2 avoids 3 detected sandwich bots",
    "profit_agent": "Option 2 yields $120 more than immediate execution",
    "consensus": "Recommended option balances MEV safety with profit"
  }
}
```

#### Advanced API Routes

- `GET /api/get_trade?request_id=<id>` - Retrieve comprehensive trade analysis status and results
- `GET /api/mempool?chain=<chain>` - Real-time mempool analysis with MEV risk assessment
- `GET /api/mempool?chain=<chain>&live=true` - Live blockchain RPC analysis for real-time MEV detection
- `GET /api/mempool?chain=<chain>&blockscout=true` - Historical MEV pattern analysis via Blockscout API
- `POST /api/get_price` - Multi-source price aggregation with volatility analysis
- `POST /api/simulate` - Parallel execution simulation across 100+ scenarios
- `POST /api/analyze` - Multi-agent AI consensus analysis with MEV risk scoring
- `POST /api/approve` - Secure trade approval with optimal timing execution

### MeTTa Service API

#### `POST /analyze`
Multi-agent analysis of trade simulations.

**Request:**
```json
{
  "simulations": [...],
  "user_priority": "mev_protection",
  "risk_tolerance": "balanced",
  "user_context": {
    "trade_size_usd": 15000,
    "is_time_sensitive": false
  }
}
```

**Response:**
```json
{
  "consensus_recommendation": {
    "recommended_id": 14,
    "confidence": 92,
    "reasoning": "...",
    "agent_agreement": "2/3 agents agree (mev + profit)"
  },
  "mev_protection_agent": {...},
  "profit_maximizer_agent": {...},
  "speed_optimizer_agent": {...}
}
```

## 🤖 AI Agent System

Sim-U-Fi uses a sophisticated multi-agent AI system where specialized agents analyze trade simulations:

### 1. MEV Protection Agent
- **Focus**: Minimize MEV risk and protect from sandwich attacks
- **Analysis**: Mempool bot detection, risk scoring, timing optimization
- **Output**: Safest execution strategy

### 2. Profit Maximizer Agent  
- **Focus**: Maximize net profit after gas costs and MEV risks
- **Analysis**: Net profit calculation, cost-benefit analysis
- **Output**: Most profitable execution strategy

### 3. Speed Optimizer Agent
- **Focus**: Minimize execution time while maintaining acceptable profit
- **Analysis**: Time vs profit tradeoffs, market volatility exposure
- **Output**: Fastest acceptable execution strategy

### 4. Consensus Agent (MeTTa + ASI:One)
- **Focus**: Combine agent recommendations based on user priorities
- **Analysis**: Weighted scoring, conflict resolution, final decision
- **Output**: Optimal balanced recommendation

## 🛡️ Advanced MEV Protection System

### Multi-Source MEV Analysis
- **Real-time Blockchain Analysis**: Direct RPC connection for live mempool monitoring and pending transaction analysis
- **Blockscout Integration**: Historical MEV pattern analysis using confirmed transaction data
- **Hybrid Detection**: Combines real-time and historical data for comprehensive MEV risk assessment

### Detection Mechanisms
- **Sandwich Attack Patterns**: Advanced pattern recognition identifying high-gas transactions surrounding user trades
- **MEV Bot Identification**: Machine learning-based detection of known MEV bot addresses and behaviors
- **Mempool State Analysis**: Real-time monitoring of transaction pool conditions and gas price anomalies
- **Cross-block Pattern Analysis**: Historical analysis of MEV attack patterns across multiple blocks

### Protection Strategies
- **Predictive Timing Optimization**: AI-powered analysis determines optimal execution timing to minimize MEV exposure
- **Dynamic Gas Price Calculation**: Intelligent gas pricing to avoid sandwich attack windows
- **Multi-scenario Simulation**: Parallel execution of 100+ scenarios to identify safest execution paths
- **Adaptive Slippage Protection**: Real-time slippage adjustment based on current MEV risk levels

## 🎨 UI/UX Features

### Modern Design System
- **Typography**: Unbounded (headings), Space Grotesk (body), Bricolage Grotesque (subheadings)
- **Color Palette**: Blue-purple gradients with high contrast accessibility
- **Responsive**: Mobile-first design with desktop optimization
- **Dark Mode**: Full dark mode support

### Trading Interface
- **Intuitive Controls**: Simple token selection and amount input
- **Priority Selection**: Choose between MEV protection, profit, speed, or balanced
- **Real-time Analysis**: Live updates during simulation process
- **Visual Results**: Clear comparison of simulation outcomes
- **Agent Reasoning**: Transparent AI decision-making process

## 🔗 Sponsor Technology Integration

### Arcology Network
- **Usage**: Parallel execution simulation infrastructure
- **Integration**: Run 100+ trade simulations simultaneously
- **Benefit**: Comprehensive analysis of all possible execution scenarios

### ASI Alliance (ASI:One)
- **Usage**: Advanced AI reasoning for consensus decisions
- **Integration**: Multi-agent system coordination and decision making
- **Benefit**: Sophisticated analysis combining multiple AI perspectives

### Blockscout
- **Usage**: Historical blockchain data analysis and MEV pattern recognition
- **Integration**: Multi-chain transaction analysis and confirmed MEV attack detection
- **Benefit**: Comprehensive historical MEV data for pattern learning and risk assessment

### Pyth Oracle
- **Usage**: Real-time price feeds and volatility data
- **Integration**: Accurate token pricing for profit calculations
- **Benefit**: Reliable price data for simulation accuracy

## 🧪 Testing & Validation

### MEV Analysis Testing
```bash
cd frontend/scripts
node MEV.js
```
Comprehensive test suite validating:
- Real-time blockchain MEV detection
- Blockscout historical analysis integration
- Multi-chain compatibility
- API endpoint functionality

### Frontend Testing
```bash
cd frontend
npm test
```

### MeTTa Service Testing
```bash
cd metta
python -m pytest tests/
```

### Smart Contract Testing
```bash
cd block
npm test
```

## 🚀 Deployment

### Frontend (Vercel)
```bash
cd frontend
npm run build
# Deploy to Vercel or your preferred platform
```

### MeTTa Service (Docker)
```bash
cd metta
docker build -t sim-u-fi-metta .
docker run -p 8000:8000 sim-u-fi-metta
```

### Smart Contracts
```bash
cd block
# Deploy to Base mainnet
npm run deploy:base

# Verify contracts
npm run verify:base <contract-address>
```

## 🔐 Environment Variables

### Frontend (.env.local)
```
NEXT_PUBLIC_METTA_SERVICE_URL=http://localhost:8000
NEXT_PUBLIC_CHAIN_ID=8453
BASE_RPC_URL=https://mainnet.base.org
ETHEREUM_RPC_URL=https://eth.llamarpc.com
```

### MeTTa Service (.env)
```
ASI_ONE_API_KEY=your-asi-one-api-key
PYTH_API_KEY=your-pyth-api-key
```

### Smart Contracts (.env)
```
PRIVATE_KEY=your-private-key
BASE_RPC_URL=https://mainnet.base.org
BASESCAN_API_KEY=your-basescan-api-key
```

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow
1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🏆 ETHGlobal Online 2025

Sim-U-Fi was built for ETHGlobal Online 2025, demonstrating:

- **Innovation**: First predictive MEV protection platform with multi-source analysis
- **Technical Excellence**: Multi-agent AI system with real-time blockchain integration
- **Advanced MEV Detection**: Hybrid approach combining live RPC and historical Blockscout data
- **Sponsor Integration**: Deep integration with Arcology, ASI:One, Blockscout, and Pyth Oracle
- **User Experience**: Beautiful, intuitive interface making complex MEV protection accessible
- **Real Impact**: Production-ready solution to protect users from MEV attacks

## 📞 Contact

- **Team**: Sim-U-Fi Team
- **Email**: team@sim-u-fi.com
- **Twitter**: [@SimUFi](https://twitter.com/SimUFi)
- **Discord**: [Join our community](https://discord.gg/sim-u-fi)

## 🙏 Acknowledgments

- ETHGlobal for hosting an amazing hackathon
- Arcology Network for parallel execution infrastructure
- ASI Alliance for advanced AI capabilities
- Blockscout for blockchain data access
- Pyth Oracle for reliable price feeds
- The entire DeFi community for inspiration and support

---

**Built with ❤️ for the future of MEV-protected trading**
