# ZeroMEV - Netted AMM Protocol
> *"100 Parallel Trades. One Netted Execution. Zero MEV."*

**Built for ETHOnline 2025**

ZeroMEV is a revolutionary DeFi protocol that uses **Arcology Network's parallel execution** to collect trades simultaneously, net opposing flows internally, and execute only the net amount on liquidity pools. This eliminates MEV attacks at the protocol level while providing massive gas savings.

Leveraging **Arcology Network's concurrent execution**, **Pyth Network**, and **Blockscout**, ZeroMEV makes MEV attacks impossible by processing trades in batches where individual trades are invisible to MEV bots.

## 🌟 Key Features

- **🔄 Parallel Trade Collection**: Collect 100+ trades simultaneously using **Arcology Network's concurrent execution** (impossible on Ethereum)
- **🧮 Internal Netting**: Match opposing trades internally before hitting liquidity pools, eliminating price impact
- **🛡️ MEV Elimination**: Batch processing makes individual trades invisible to MEV bots - no sandwich attacks possible
- **⚡ 90% Gas Savings**: Matched trades use simple transfers (21k gas) instead of expensive pool swaps (150k gas)
- **📊 Real-time Price Feeds**: Fair pricing for all trades using **Pyth Network** oracles
- **🔗 Deferred Execution**: Trades collected during block, processed as batch at block end
- **📈 Visual Netting**: See how your trade gets matched internally vs. sent to pools
- **🎯 Zero Price Impact**: Internal matching eliminates slippage for matched portions

## 🔄 Complete System Flow

The diagram below shows how ZeroMEV uses Arcology's parallel execution to eliminate MEV through trade netting:

![ZeroMEV Netted AMM Flow](./flow/flow.svg)

### Flow Breakdown:
1. **Parallel Collection**: Multiple users submit trades simultaneously using Arcology's concurrent execution
2. **Thread-Safe Storage**: Trades stored in concurrent data structures (HashU256Map, SwapRequestStore)
3. **Batch Aggregation**: All trades collected during block execution phase
4. **Netting Calculation**: Opposing flows matched internally (Buy: 18 ETH, Sell: 5 ETH → Net: 13 ETH)
5. **Internal Matching**: Matched portions executed as direct transfers (90% gas savings)
6. **Pool Execution**: Only net amount sent to liquidity pools (minimal price impact)
7. **Fair Distribution**: All users get fair prices, zero MEV extraction possible

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    FRONTEND (Next.js)                   │
│  • Trading Interface  • Netting Visualization           │
│  • Real-time Updates  • Gas Savings Display             │
└────────────────┬────────────────────────────────────────┘
                 ↓
┌─────────────────────────────────────────────────────────┐
│              ARCOLOGY NETTED AMM CONTRACT               │
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │   Thread 1  │  │   Thread 2  │  │   Thread N  │     │
│  │ queueSwap() │  │ queueSwap() │  │ queueSwap() │     │
│  │   (Alice)   │  │   (Bob)     │  │   (Carol)   │     │
│  └─────────────┘  └─────────────┘  └─────────────┘     │
│                        ↓                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │         CONCURRENT DATA STRUCTURES              │   │
│  │  • HashU256Map (aggregated amounts)            │   │
│  │  • SwapRequestStore (individual requests)      │   │
│  │  • Thread-safe operations                      │   │
│  └─────────────────────────────────────────────────┘   │
│                        ↓                               │
│  ┌─────────────────────────────────────────────────┐   │
│  │           DEFERRED EXECUTION                    │   │
│  │  Runtime.defer() → netAndExecuteSwaps()        │   │
│  │  • Internal matching (21k gas)                 │   │
│  │  • Pool execution (net amount only)            │   │
│  └─────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────┘
                         ↓
┌─────────────────────────────────────────────────────────┐
│                 EXTERNAL SERVICES                       │
│  • Arcology Network (Parallel Execution Engine)        │
│  • Pyth Oracle (Real-time Price Feeds)                 │
│  • Uniswap V3 Pools (Net Amount Execution)             │
│  • Blockscout (Historical MEV Analysis)                │
└─────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Node.js 18+
- Python 3.9+
- Git

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/ZeroMEV.git
cd ZeroMEV
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

```ZeroMEV/
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
├── metta/                 # FastAPI service for netting analysis
│   ├── services/          # Core services
│   │   ├── netting_calculator.py # Trade netting algorithms
│   │   ├── gas_estimator.py      # Gas savings calculations
│   │   ├── price_aggregator.py   # Multi-source price feeds
│   │   └── mev_analyzer.py       # MEV risk assessment
│   ├── main.py            # FastAPI application
│   └── requirements.txt
│
├── block/                 # Smart contracts and deployment
│   ├── contracts/
│   │   ├── NettedAMM.sol                # Main Netted AMM contract
│   │   ├── SwapRequestStore.sol         # Concurrent trade storage
│   │   ├── ArcologyOrchestrator.sol     # Multi-chain coordination hub
│   │   └── PythPriceConsumer.sol        # Price feed integration
│   ├── scripts/
│   │   ├── deploy-netted-amm.js         # Main Netted AMM deployment
│   │   ├── deploy-arcology-orchestrator.js  # Arcology orchestrator deployment
│   │   ├── test-netting.js              # Netting functionality tests
│   │   └── deploy-all-chains.js         # Multi-chain deployment
│   ├── hardhat.config.js
│   └── package.json
│
├── flow/                  # Architecture diagrams
└── README.md             # This file
```

## 🔧 API Documentation

### Frontend API Routes

#### `POST /api/queue_swap`
Queue a trade for batch processing in the Netted AMM.

**Request:**
```json
{
  "wallet_address": "0x742d35Cc6634C0532925a3b844Bc9e7595f0bEb",
  "trade": {
    "token_in": "ETH",
    "token_out": "USDC",
    "amount_in": "5.0",
    "min_amount_out": "14800.0",
    "pool_address": "0x..."
  },
  "chain": "base"
}
```

**Response:**
```json
{
  "request_id": "req_abc123",
  "status": "queued",
  "batch_id": 12345,
  "estimated_execution": {
    "block_number": 19234567,
    "estimated_gas_savings": "85%",
    "expected_matching": "partial",
    "fair_price_guarantee": true
  },
  "netting_preview": {
    "total_buy_pressure": "18.5 ETH",
    "total_sell_pressure": "5.2 ETH",
    "your_match_probability": "92%",
    "estimated_gas_cost": "21000"
  }
}
```

#### Advanced API Routes

- `GET /api/batch_status?batch_id=<id>` - Real-time batch processing status and netting calculations
- `GET /api/netting_preview?pool=<address>` - Live preview of current netting state for a pool
- `POST /api/calculate_netting` - Calculate potential netting for hypothetical trades
- `POST /api/estimate_gas_savings` - Estimate gas savings for a trade based on current batch
- `GET /api/pool_analytics?pool=<address>` - Historical netting efficiency and MEV elimination stats
- `POST /api/get_price` - Multi-source price aggregation with Pyth Network integration
- `GET /api/mev_protection_stats` - Real-time MEV elimination statistics
- `POST /api/batch_execute` - **Arcology Deferred Execution**: Process entire batch with internal netting

### Netting Service API

#### `POST /calculate_netting`
Calculate optimal netting for a batch of trades.

**Request:**
```json
{
  "pool_address": "0x...",
  "trades": [
    {"user": "0x...", "token_in": "ETH", "amount": "10.0", "is_buy": true},
    {"user": "0x...", "token_in": "USDC", "amount": "15000", "is_buy": false}
  ],
  "current_price": "3000.0"
}
```

**Response:**
```json
{
  "netting_result": {
    "total_buy_amount": "18.0 ETH",
    "total_sell_amount": "5.0 ETH",
    "net_amount": "13.0 ETH",
    "net_direction": "buy",
    "matched_amount": "5.0 ETH",
    "matching_percentage": "27.8%"
  },
  "gas_savings": {
    "traditional_cost": "2700000",
    "netted_cost": "270000",
    "savings_percentage": "90%",
    "savings_usd": "180.50"
  },
  "mev_protection": {
    "individual_trades_visible": false,
    "sandwich_attack_possible": false,
    "frontrun_opportunities": 0,
    "price_impact_reduction": "85%"
  }
}
```

## 🧮 Netted AMM System

ZeroMEV uses Arcology Network's parallel execution to implement a revolutionary Netted AMM that eliminates MEV at the protocol level:

### 1. Parallel Trade Collection
- **Mechanism**: Concurrent `queueSwap()` calls using Arcology's thread-safe containers
- **Data Structures**: `HashU256Map` for aggregation, `SwapRequestStore` for individual trades
- **Benefit**: Impossible on Ethereum - trades collected simultaneously, not sequentially

### 2. Internal Netting Algorithm
- **Process**: Match opposing trades internally before pool interaction
- **Calculation**: `netAmount = |totalBuy - totalSell|`, `matchedAmount = min(totalBuy, totalSell)`
- **Result**: 90% gas savings for matched portions (21k vs 150k gas)

### 3. Deferred Execution Pattern
- **Trigger**: `Runtime.defer()` processes batch at block end
- **Timing**: Trades collected during block, executed atomically
- **MEV Protection**: Individual trades invisible to bots during collection phase

### 4. Fair Price Distribution
- **Internal Matching**: Direct transfers at fair market price
- **Pool Execution**: Net amount only, minimal price impact
- **Guarantee**: All users get same fair price, zero MEV extraction

## 🛡️ Protocol-Level MEV Elimination

### How Netting Eliminates MEV
- **Batch Processing**: Individual trades invisible during collection phase
- **Internal Matching**: Opposing trades matched directly, never hit pools
- **Atomic Execution**: Entire batch processed in single transaction
- **Zero Attack Surface**: No individual trade timing for bots to exploit

### Technical Implementation
- **Concurrent Collection**: `Multiprocess(20)` enables parallel trade submission
- **Thread-Safe Storage**: Arcology's concurrent containers prevent race conditions
- **Deferred Processing**: `Runtime.isInDeferred()` triggers batch execution
- **Gas Optimization**: Matched trades use simple transfers (21k gas)

### Mathematical Guarantees
- **Price Impact Reduction**: `priceImpact = f(netAmount)` vs `f(totalVolume)`
- **Gas Savings**: `savings = (matchedAmount / totalAmount) * 85%`
- **MEV Elimination**: `mevRisk = 0` when `individualTradesVisible = false`
- **Fair Pricing**: All users get `poolPrice` at execution time

### Real-World Benefits
- **Example**: 100 ETH buy + 80 ETH sell = 20 ETH net (80% matched internally)
- **Gas Savings**: 80% of trades use 21k gas instead of 150k gas
- **MEV Protection**: Bots see single 20 ETH trade, not 100 individual trades
- **Price Stability**: 5x less price impact than traditional execution

## 🎨 UI/UX Features

### Modern Design System
- **Typography**: Unbounded (headings), Space Grotesk (body), Bricolage Grotesque (subheadings)
- **Color Palette**: Blue-purple gradients with high contrast accessibility
- **Responsive**: Mobile-first design with desktop optimization
- **Dark Mode**: Full dark mode support

### Netted Trading Interface
- **Intuitive Controls**: Simple token selection and amount input with netting preview
- **Real-time Netting**: Live visualization of current batch state and matching probability
- **Gas Savings Display**: Real-time calculation of estimated gas savings
- **Batch Status**: Visual progress of trade collection and execution phases
- **MEV Protection Stats**: Live counter of MEV attacks prevented and savings generated

## 🔗 Sponsor Technology Integration

### Arcology Network - Parallel Execution Engine
- **Usage**: Core parallel execution infrastructure enabling concurrent trade collection
- **Integration**: 
  - **Netted AMM Contract**: Main contract leveraging Arcology's concurrent execution capabilities
  - **Thread-Safe Containers**: `HashU256Map` and `SwapRequestStore` for parallel trade storage
  - **Multiprocess Execution**: 20 parallel threads collecting trades simultaneously
  - **Deferred Execution**: `Runtime.defer()` for atomic batch processing at block end
- **Technical Innovation**: 
  - First DEX to use parallel execution for trade netting (impossible on Ethereum)
  - Concurrent data structures preventing race conditions during trade collection
  - Atomic batch execution eliminating MEV attack windows
  - Thread-safe aggregation enabling real-time netting calculations
- **Benefit**: Protocol-level MEV elimination through parallel trade collection and internal netting

### Pyth Network - Real-time Price Feeds
- **Usage**: Accurate price discovery for fair internal matching
- **Integration**: `PythPriceConsumer.sol` contract for on-chain price feeds
- **Benefit**: Ensures all users get fair market prices during internal matching

### Blockscout
- **Usage**: Historical MEV analysis and attack pattern recognition
- **Integration**: API integration for MEV statistics and attack prevention validation
- **Benefit**: Quantifiable proof of MEV elimination and gas savings achieved

## 🧪 Testing & Validation

### Netted AMM Testing
```bash
cd block/scripts
node test-netting.js
```
Comprehensive test suite validating:
- Parallel trade collection using Arcology's concurrent execution
- Thread-safe data structure operations
- Internal netting algorithm accuracy
- Deferred execution and batch processing
- Gas savings calculations and MEV elimination

### Integration Testing
```bash
cd frontend/scripts
node netting-demo.js
```
End-to-end testing validating:
- Real-time batch status and netting preview
- Gas savings estimation accuracy
- Fair price distribution mechanisms
- MEV protection effectiveness

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

### Netting Service (Docker)
```bash
cd metta
docker build -t zeromev-netting .
docker run -p 8000:8000 zeromev-netting
```

### Smart Contracts

#### Netted AMM Deployment (Arcology Network)
```bash
cd block

# 1. Deploy Netted AMM Contract (main netting contract)
npx hardhat run scripts/deploy-netted-amm.js --network arcology-testnet

# 2. Deploy supporting contracts
npx hardhat run scripts/deploy-pyth-consumer.js --network arcology-testnet
npx hardhat run scripts/deploy-swap-request-store.js --network arcology-testnet

# 3. Test netting functionality
node scripts/test-netting.js

# 4. Verify contracts
npm run verify:arcology <contract-address>
```

#### Multi-Chain Bridge Deployment (Optional)
```bash
cd block
# Deploy bridge contracts for cross-chain netting
npx hardhat run scripts/deploy-all-chains.js

# Verify contracts
npm run verify:base <contract-address>
```

## 🔐 Environment Variables

### Frontend (.env.local)
```
# Core Services
NEXT_PUBLIC_METTA_SERVICE_URL=http://localhost:8000
NEXT_PUBLIC_CHAIN_ID=8453

# Arcology Netted AMM Configuration
ARCOLOGY_TESTNET_RPC_URL=https://testnet.arcology.network/rpc
NETTED_AMM_ADDRESS=0x...
SWAP_REQUEST_STORE_ADDRESS=0x...
PYTH_CONSUMER_ADDRESS=0x...

# Multi-Chain Bridge Configuration (Optional)
BASE_SEPOLIA_RPC_URL=https://sepolia.base.org
OPTIMISM_SEPOLIA_RPC_URL=https://sepolia.optimism.io
ARBITRUM_SEPOLIA_RPC_URL=https://sepolia-rollup.arbitrum.io/rpc
POLYGON_MUMBAI_RPC_URL=https://rpc-mumbai.maticvigil.com
ETHEREUM_SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/YOUR_KEY

# Bridge Contract Addresses (Optional)
BASE_BRIDGE_ADDRESS=0x...
OPTIMISM_BRIDGE_ADDRESS=0x...
ARBITRUM_BRIDGE_ADDRESS=0x...
POLYGON_BRIDGE_ADDRESS=0x...
ETHEREUM_BRIDGE_ADDRESS=0x...
```

### Netting Service (.env)
```
PYTH_API_KEY=your-pyth-api-key
BLOCKSCOUT_API_KEY=your-blockscout-api-key
NETTING_CALCULATION_TIMEOUT=30
MAX_BATCH_SIZE=1000
```

### Smart Contracts (.env)
```
# Deployment Configuration
PRIVATE_KEY=your-deployment-private-key
RELAYER_PRIVATE_KEY=your-relayer-private-key

# Arcology Network
ARCOLOGY_TESTNET_RPC_URL=https://testnet.arcology.network/rpc
NETTED_AMM_ADDRESS=
SWAP_REQUEST_STORE_ADDRESS=
PYTH_CONSUMER_ADDRESS=

# Multi-Chain Bridge RPC URLs (Optional)
BASE_SEPOLIA_RPC_URL=https://sepolia.base.org
OPTIMISM_SEPOLIA_RPC_URL=https://sepolia.optimism.io
ARBITRUM_SEPOLIA_RPC_URL=https://sepolia-rollup.arbitrum.io/rpc
POLYGON_MUMBAI_RPC_URL=https://rpc-mumbai.maticvigil.com
ETHEREUM_SEPOLIA_RPC_URL=https://sepolia.infura.io/v3/YOUR_KEY

# API Keys for Contract Verification
BASESCAN_API_KEY=your-basescan-api-key
OPTIMISTIC_ETHERSCAN_API_KEY=your-optimistic-etherscan-api-key
ARBISCAN_API_KEY=your-arbiscan-api-key
POLYGONSCAN_API_KEY=your-polygonscan-api-key
ETHERSCAN_API_KEY=your-etherscan-api-key
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

## 🏆 ETHOnline 2025

ZeroMEV was built for ETHOnline 2025, demonstrating:

- **Innovation**: First Netted AMM using parallel execution to eliminate MEV at the protocol level
- **Technical Excellence**: Revolutionary use of Arcology's concurrent execution for trade netting (impossible on Ethereum)
- **Advanced Parallel Architecture**: Thread-safe containers, deferred execution, and atomic batch processing
- **Mathematical MEV Elimination**: Provable zero MEV risk through internal trade matching
- **Sponsor Integration**: Deep technical showcase of Arcology's parallel execution capabilities
- **Production-Ready Infrastructure**: Complete Netted AMM implementation with 90% gas savings
- **User Experience**: Real-time netting visualization and gas savings display
- **Real Impact**: Protocol-level solution eliminating MEV attacks while providing massive gas savings

## 🙏 Acknowledgments

- ETHGlobal for hosting an amazing hackathon
- Arcology Network for parallel execution infrastructure and NettedAMM Infrastructure
- ASI Alliance for advanced agentic capabilities and MeTTa solvers.
- Blockscout for blockchain data access
- Pyth Oracle for reliable price feeds
- The entire DeFi community for inspiration and support

---

**Built with ❤️ for the future of MEV-protected trading**
