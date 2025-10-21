// frontend/lib/mev-blockscout.ts
import { MEVAnalysis } from './mev-analysis';

export class BlockscoutMEVDetector {
  private baseUrl: string;
  private apiKey?: string;
  
  constructor(baseUrl: string, apiKey?: string) {
    this.baseUrl = baseUrl.replace(/\/$/, ''); // Remove trailing slash
    this.apiKey = apiKey;
  }
  
  async analyzeCurrentBlock(): Promise<MEVAnalysis> {
    console.log('🔍 Starting Blockscout MEV analysis...');
    
    // Add timeout to prevent hanging
    const timeoutPromise = new Promise<MEVAnalysis>((_, reject) => {
      setTimeout(() => reject(new Error('Blockscout analysis timeout after 30 seconds')), 30000);
    });
    
    const analysisPromise = this.performBlockscoutAnalysis();
    
    try {
      return await Promise.race([analysisPromise, timeoutPromise]);
    } catch (error) {
      console.error('❌ Blockscout MEV analysis failed:', error);
      return this.getEmptyAnalysis();
    }
  }
  
  private async performBlockscoutAnalysis(): Promise<MEVAnalysis> {
    try {
      // Step 1: Get multiple recent blocks for comprehensive historical analysis
      const latestBlock = await this.getLatestBlockNumber();
      console.log(`📦 Starting Blockscout historical analysis from block ${latestBlock}`);
      
      // Step 2: Analyze last 3 blocks for better MEV pattern detection
      const blockRange = 3;
      const historicalAnalysis = await this.analyzeHistoricalBlocks(latestBlock, blockRange);
      
      console.log('✅ Blockscout historical MEV analysis completed:', historicalAnalysis);
      return historicalAnalysis;
      
    } catch (error) {
      console.error('❌ Blockscout analysis failed:', error);
      return this.getEmptyAnalysis();
    }
  }
  
  private async getLatestBlockNumber(): Promise<number> {
    const url = `${this.baseUrl}/api/eth-rpc`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(this.apiKey && { 'Authorization': `Bearer ${this.apiKey}` })
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'eth_blockNumber',
        params: [],
        id: 1
      })
    });
    
    if (!response.ok) {
      throw new Error(`Failed to get latest block: ${response.status}`);
    }
    
    const data = await response.json();
    return parseInt(data.result, 16);
  }
  
  private async getBlockDetails(blockNumber: number): Promise<any> {
    const url = `${this.baseUrl}/api/eth-rpc`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(this.apiKey && { 'Authorization': `Bearer ${this.apiKey}` })
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'eth_getBlockByNumber',
        params: [`0x${blockNumber.toString(16)}`, true], // true = include full transaction objects
        id: 1
      })
    });
    
    if (!response.ok) {
      throw new Error(`Failed to get block details: ${response.status}`);
    }
    
    const data = await response.json();
    return data.result;
  }
  
  // NEW: Comprehensive historical analysis across multiple blocks
  private async analyzeHistoricalBlocks(latestBlock: number, blockRange: number): Promise<MEVAnalysis> {
    console.log(`📊 Analyzing ${blockRange} historical blocks for MEV patterns...`);
    
    const allTransactions: any[] = [];
    const allReceipts: any[] = [];
    let totalBlocks = 0;
    
    // Fetch multiple blocks for comprehensive analysis
    for (let i = 0; i < blockRange; i++) {
      const blockNumber = latestBlock - i;
      
      try {
        console.log(`  📦 Fetching block ${blockNumber}...`);
        const blockData = await this.getBlockDetails(blockNumber);
        
        if (blockData && blockData.transactions) {
          allTransactions.push(...blockData.transactions);
          totalBlocks++;
          
          // Get detailed receipts for MEV analysis
          const blockReceipts = await this.getBlockTransactionReceipts(blockData.transactions.slice(0, 10));
          allReceipts.push(...blockReceipts);
          
          console.log(`  ✅ Block ${blockNumber}: ${blockData.transactions.length} transactions, ${blockReceipts.length} receipts`);
        }
        
        // Small delay to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 200));
        
      } catch (error) {
        console.log(`  ⚠️ Failed to fetch block ${blockNumber}, continuing...`);
      }
    }
    
    console.log(`📋 Historical analysis: ${allTransactions.length} total transactions across ${totalBlocks} blocks`);
    
    // Perform comprehensive MEV analysis with receipts
    return await this.analyzeHistoricalMEVPatterns(allTransactions, allReceipts, latestBlock);
  }
  
  // NEW: Get transaction receipts for detailed analysis
  private async getBlockTransactionReceipts(transactions: any[]): Promise<any[]> {
    const receipts: any[] = [];
    const limitedTxs = transactions.slice(0, 8); // Limit to avoid rate limits
    
    for (const tx of limitedTxs) {
      try {
        const receipt = await this.getTransactionReceipt(tx.hash);
        if (receipt) {
          receipts.push({
            ...receipt,
            transaction: tx // Include original transaction data
          });
        }
        
        // Delay to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 150));
        
      } catch (error) {
        // Continue with other receipts if one fails
        console.log(`  ⚠️ Failed to get receipt for ${tx.hash}`);
      }
    }
    
    return receipts;
  }
  
  // NEW: Advanced MEV pattern analysis with transaction receipts
  private async analyzeHistoricalMEVPatterns(transactions: any[], receipts: any[], latestBlock: number): Promise<MEVAnalysis> {
    console.log(`🔍 Analyzing historical MEV patterns with ${receipts.length} detailed receipts...`);
    
    // Filter DEX transactions
    const dexTxs = transactions.filter(tx => this.isDEXTransaction(tx));
    console.log(`🔄 Found ${dexTxs.length} DEX transactions in historical data`);
    
    // Analyze gas efficiency and MEV profits using receipts
    const mevAnalysis = this.analyzeReceiptBasedMEV(receipts);
    console.log(`💰 Receipt analysis: ${mevAnalysis.profitableTxs} profitable, ${mevAnalysis.failedTxs} failed`);
    
    // Detect sophisticated sandwich patterns across blocks
    const crossBlockSandwiches = this.detectCrossBlockSandwiches(transactions);
    console.log(`🥪 Cross-block sandwich detection: ${crossBlockSandwiches.length} patterns found`);
    
    // Identify MEV bot addresses from historical data
    const mevBots = this.identifyMEVBotsFromHistory(transactions, receipts);
    console.log(`🤖 Identified ${mevBots.length} potential MEV bot addresses`);
    
    // Calculate sophisticated risk metrics
    const riskMetrics = this.calculateHistoricalRiskMetrics(dexTxs, mevAnalysis, crossBlockSandwiches, mevBots);
    
    return {
      block_number: latestBlock,
      total_txs: transactions.length,
      dex_txs: dexTxs.length,
      suspicious_high_gas: mevBots.length,
      detected_sandwiches: crossBlockSandwiches.length,
      avg_gas_price: this.calculateHistoricalAvgGas(dexTxs),
      mev_risk_score: riskMetrics.overallRisk
    };
  }
  
  // LIMITATION: Blockscout doesn't provide pending transactions via standard API
  // This method analyzes confirmed transactions for MEV patterns
  private async analyzeTransactionsForMEV(transactions: any[], blockNumber: number): Promise<MEVAnalysis> {
    console.log(`🔄 Analyzing ${transactions.length} confirmed transactions for MEV patterns...`);
    
    // Filter DEX transactions
    const dexTxs = transactions.filter(tx => this.isDEXTransaction(tx));
    console.log(`🔄 Found ${dexTxs.length} DEX transactions`);
    
    // Sort by gas price to identify high-gas transactions
    const sortedByGas = [...dexTxs].sort((a, b) => {
      const gasPriceA = a.gasPrice ? BigInt(a.gasPrice) : BigInt(0);
      const gasPriceB = b.gasPrice ? BigInt(b.gasPrice) : BigInt(0);
      return gasPriceA > gasPriceB ? -1 : 1;
    });
    
    // Identify suspicious high-gas transactions (top 20%)
    const threshold = Math.ceil(sortedByGas.length * 0.2);
    const suspiciousTxs = sortedByGas.slice(0, threshold);
    console.log(`🤖 Identified ${suspiciousTxs.length} suspicious high-gas transactions`);
    
    // Detect sandwich attack patterns
    const sandwiches = this.detectSandwichPatterns(transactions);
    console.log(`🥪 Detected ${sandwiches.length} potential sandwich attacks`);
    
    // Get additional transaction details for better analysis
    const enrichedAnalysis = await this.enrichWithTransactionDetails(suspiciousTxs);
    
    return {
      block_number: blockNumber,
      total_txs: transactions.length,
      dex_txs: dexTxs.length,
      suspicious_high_gas: suspiciousTxs.length,
      detected_sandwiches: sandwiches.length,
      avg_gas_price: this.calculateAvgGas(dexTxs),
      mev_risk_score: this.calculateRiskScore(suspiciousTxs.length, sandwiches.length)
    };
  }
  
  private isDEXTransaction(tx: any): boolean {
    if (!tx || !tx.to) return false;
    
    const DEX_ROUTERS = [
      '0x4752ba5dbc23f44d87826276bf6fd6b1c372ad24', // Base DEX Router
      '0x94cC0AaC535CCDB3C01d6787D6413C739ae12bc4', // Uniswap V3 Base Sepolia
      '0x7a250d5630b4cf539739df2c5dacb4c659f2488d', // Uniswap V2 Router
      '0xe592427a0aece92de3edee1f18e0157c05861564', // Uniswap V3 Router
      '0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45', // Uniswap V3 Router 2
      '0x3fC91A3afd70395Cd496C647d5a6CC9D4B2b7FAD', // Universal Router
    ];
    
    return DEX_ROUTERS.some(router => 
      tx.to.toLowerCase() === router.toLowerCase()
    );
  }
  
  private detectSandwichPatterns(transactions: any[]): any[] {
    const sandwiches = [];
    
    // Look for sandwich patterns: high gas -> normal gas -> high gas from same address
    for (let i = 0; i < transactions.length - 2; i++) {
      const tx1 = transactions[i];
      const tx2 = transactions[i + 1];
      const tx3 = transactions[i + 2];
      
      if (
        this.isDEXTransaction(tx1) && 
        this.isDEXTransaction(tx2) && 
        this.isDEXTransaction(tx3) &&
        tx1.gasPrice && tx2.gasPrice && tx3.gasPrice &&
        BigInt(tx1.gasPrice) > BigInt(tx2.gasPrice) * BigInt(15) / BigInt(10) &&
        BigInt(tx3.gasPrice) > BigInt(tx2.gasPrice) * BigInt(15) / BigInt(10) &&
        tx1.from?.toLowerCase() === tx3.from?.toLowerCase() &&
        tx1.from?.toLowerCase() !== tx2.from?.toLowerCase()
      ) {
        sandwiches.push({
          frontrun: tx1.hash,
          victim: tx2.hash,
          backrun: tx3.hash,
          attacker: tx1.from,
          victim_address: tx2.from,
          estimated_profit: 'Unknown' // Would need receipt analysis
        });
      }
    }
    
    return sandwiches;
  }
  
  private calculateAvgGas(txs: any[]): string {
    if (txs.length === 0) return '0';
    
    const validTxs = txs.filter(tx => tx.gasPrice);
    if (validTxs.length === 0) return '0';
    
    const sum = validTxs.reduce((acc, tx) => acc + BigInt(tx.gasPrice), BigInt(0));
    const avg = sum / BigInt(validTxs.length);
    
    // Convert from wei to gwei
    return (Number(avg) / 1e9).toFixed(2);
  }
  
  private calculateRiskScore(suspiciousCount: number, sandwichCount: number): number {
    let score = 0;
    score += suspiciousCount * 10; // Each suspicious tx adds 10 points
    score += sandwichCount * 30;   // Each sandwich adds 30 points
    return Math.min(100, score);
  }
  
  // ENHANCEMENT: Get additional transaction details using Blockscout API
  private async enrichWithTransactionDetails(transactions: any[]): Promise<void> {
    console.log(`📋 Enriching analysis with transaction receipts...`);
    
    // Limit to first 5 transactions to avoid rate limits
    const limitedTxs = transactions.slice(0, 5);
    
    for (const tx of limitedTxs) {
      try {
        // Get transaction receipt for gas usage and logs
        const receipt = await this.getTransactionReceipt(tx.hash);
        if (receipt) {
          tx.gasUsed = receipt.gasUsed;
          tx.logs = receipt.logs;
          tx.status = receipt.status;
        }
        
        // Small delay to avoid rate limiting
        await new Promise(resolve => setTimeout(resolve, 100));
        
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        console.log(`⚠️ Failed to get receipt for ${tx.hash}: ${errorMessage}`);
      }
    }
  }
  
  private async getTransactionReceipt(txHash: string): Promise<any> {
    const url = `${this.baseUrl}/api/eth-rpc`;
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(this.apiKey && { 'Authorization': `Bearer ${this.apiKey}` })
      },
      body: JSON.stringify({
        jsonrpc: '2.0',
        method: 'eth_getTransactionReceipt',
        params: [txHash],
        id: 1
      })
    });
    
    if (!response.ok) {
      throw new Error(`Failed to get transaction receipt: ${response.status}`);
    }
    
    const data = await response.json();
    return data.result;
  }
  
  // LIMITATION: Cannot get pending transactions from Blockscout
  // This would require access to mempool data which Blockscout doesn't expose
  async getPendingTransactions(): Promise<any[]> {
    console.log('⚠️ LIMITATION: Blockscout does not provide pending transaction data');
    console.log('📝 Returning empty array - use confirmed transactions instead');
    return [];
  }
  
  // LIMITATION: Cannot get real-time mempool data
  // This is a major limitation for MEV analysis
  async getMempoolData(): Promise<any> {
    console.log('⚠️ LIMITATION: Blockscout does not provide mempool/txpool data');
    console.log('📝 Real-time MEV detection requires mempool access');
    return {
      pending: [],
      queued: [],
      limitation: 'Blockscout does not expose mempool data'
    };
  }
  
  // NEW: Advanced historical analysis methods
  private analyzeReceiptBasedMEV(receipts: any[]): { profitableTxs: number, failedTxs: number, totalGasUsed: bigint } {
    let profitableTxs = 0;
    let failedTxs = 0;
    let totalGasUsed = BigInt(0);
    
    for (const receipt of receipts) {
      // Check transaction success
      if (receipt.status === '0x0') {
        failedTxs++;
      } else {
        // Analyze gas efficiency for successful transactions
        const gasUsed = BigInt(receipt.gasUsed || 0);
        const gasPrice = BigInt(receipt.transaction?.gasPrice || 0);
        const gasCost = gasUsed * gasPrice;
        
        totalGasUsed += gasUsed;
        
        // Heuristic: High gas usage with successful execution might indicate MEV profit
        if (gasUsed > BigInt(200000)) { // High gas usage threshold
          profitableTxs++;
        }
      }
    }
    
    return { profitableTxs, failedTxs, totalGasUsed };
  }
  
  private detectCrossBlockSandwiches(transactions: any[]): any[] {
    const sandwiches = [];
    const dexTxs = transactions.filter(tx => this.isDEXTransaction(tx));
    
    // Group transactions by block for cross-block analysis
    const txsByBlock: { [key: string]: any[] } = {};
    dexTxs.forEach(tx => {
      const blockNum = tx.blockNumber || '0';
      if (!txsByBlock[blockNum]) txsByBlock[blockNum] = [];
      txsByBlock[blockNum].push(tx);
    });
    
    // Analyze patterns across consecutive blocks
    const blockNumbers = Object.keys(txsByBlock).sort((a, b) => parseInt(a) - parseInt(b));
    
    for (let i = 0; i < blockNumbers.length - 1; i++) {
      const currentBlock = txsByBlock[blockNumbers[i]];
      const nextBlock = txsByBlock[blockNumbers[i + 1]];
      
      // Look for potential cross-block sandwich patterns
      for (const tx1 of currentBlock) {
        for (const tx2 of nextBlock) {
          if (this.isSandwichPattern(tx1, tx2)) {
            sandwiches.push({
              frontrun_block: blockNumbers[i],
              backrun_block: blockNumbers[i + 1],
              frontrun_tx: tx1.hash,
              backrun_tx: tx2.hash,
              attacker: tx1.from,
              pattern_type: 'cross_block_sandwich'
            });
          }
        }
      }
    }
    
    return sandwiches;
  }
  
  private identifyMEVBotsFromHistory(transactions: any[], receipts: any[]): string[] {
    const addressStats: { [key: string]: { txCount: number, highGasCount: number, successRate: number } } = {};
    
    // Analyze transaction patterns by address
    transactions.forEach(tx => {
      if (!tx.from || !this.isDEXTransaction(tx)) return;
      
      if (!addressStats[tx.from]) {
        addressStats[tx.from] = { txCount: 0, highGasCount: 0, successRate: 0 };
      }
      
      addressStats[tx.from].txCount++;
      
      // Check if high gas price (potential MEV bot behavior)
      if (tx.gasPrice && BigInt(tx.gasPrice) > BigInt('50000000000')) { // > 50 gwei
        addressStats[tx.from].highGasCount++;
      }
    });
    
    // Calculate success rates from receipts
    receipts.forEach(receipt => {
      const address = receipt.transaction?.from;
      if (address && addressStats[address]) {
        const isSuccess = receipt.status === '0x1';
        const current = addressStats[address].successRate;
        addressStats[address].successRate = (current + (isSuccess ? 1 : 0)) / 2;
      }
    });
    
    // Identify potential MEV bots based on patterns
    const mevBots: string[] = [];
    Object.entries(addressStats).forEach(([address, stats]) => {
      const highGasRatio = stats.highGasCount / stats.txCount;
      
      // Heuristics for MEV bot identification
      if (stats.txCount >= 3 && highGasRatio > 0.5 && stats.successRate > 0.8) {
        mevBots.push(address);
      }
    });
    
    return mevBots;
  }
  
  private calculateHistoricalRiskMetrics(dexTxs: any[], mevAnalysis: any, sandwiches: any[], mevBots: string[]): { overallRisk: number } {
    let riskScore = 0;
    
    // Base MEV activity scoring
    riskScore += mevBots.length * 15;
    riskScore += sandwiches.length * 25;
    riskScore += mevAnalysis.profitableTxs * 5;
    
    // Historical pattern adjustments
    if (dexTxs.length > 0) {
      const botRatio = mevBots.length / dexTxs.length;
      const sandwichRatio = sandwiches.length / dexTxs.length;
      
      riskScore += botRatio * 30;
      riskScore += sandwichRatio * 40;
    }
    
    // Failed transaction penalty (indicates competitive MEV environment)
    if (mevAnalysis.failedTxs > 0) {
      riskScore += mevAnalysis.failedTxs * 3;
    }
    
    return { overallRisk: Math.min(100, riskScore) };
  }
  
  private calculateHistoricalAvgGas(txs: any[]): string {
    if (txs.length === 0) return '0';
    
    const validTxs = txs.filter(tx => tx.gasPrice);
    if (validTxs.length === 0) return '0';
    
    const sum = validTxs.reduce((acc, tx) => acc + BigInt(tx.gasPrice), BigInt(0));
    const avg = sum / BigInt(validTxs.length);
    
    // Convert from wei to gwei
    return (Number(avg) / 1e9).toFixed(2);
  }
  
  private isSandwichPattern(tx1: any, tx2: any): boolean {
    // Simple heuristic for sandwich pattern detection
    return (
      tx1.from === tx2.from && // Same attacker
      tx1.to === tx2.to && // Same DEX
      tx1.gasPrice && tx2.gasPrice &&
      BigInt(tx1.gasPrice) > BigInt('30000000000') && // High gas prices
      BigInt(tx2.gasPrice) > BigInt('30000000000')
    );
  }

  private getEmptyAnalysis(): MEVAnalysis {
    return {
      block_number: 0,
      total_txs: 0,
      dex_txs: 0,
      suspicious_high_gas: 0,
      detected_sandwiches: 0,
      avg_gas_price: '0',
      mev_risk_score: 0
    };
  }
}

// BLOCKSCOUT LIMITATIONS SUMMARY:
export const BLOCKSCOUT_LIMITATIONS = {
  // ❌ MAJOR LIMITATIONS
  no_pending_transactions: "Blockscout doesn't provide pending/mempool transaction data",
  no_real_time_mev: "Cannot detect MEV attacks in real-time before they happen",
  no_txpool_access: "No access to transaction pool for pre-execution analysis",
  
  // ⚠️ PARTIAL LIMITATIONS  
  rate_limits: "API rate limits may affect analysis speed",
  confirmed_only: "Can only analyze confirmed transactions (post-MEV)",
  
  // ✅ AVAILABLE FEATURES
  historical_analysis: "Can analyze confirmed transactions for MEV patterns",
  block_data: "Full access to block and transaction data",
  transaction_receipts: "Can get detailed transaction execution data",
  gas_analysis: "Can analyze gas prices and usage patterns",
  dex_detection: "Can identify DEX transactions and patterns"
};

// Helper function to get appropriate Blockscout URL for different chains
export function getBlockscoutUrl(chain: string): string {
  const urls: { [key: string]: string } = {
    'ethereum': 'https://eth.blockscout.com',
    'base': 'https://base.blockscout.com', 
    'base-sepolia': 'https://base-sepolia.blockscout.com',
    'polygon': 'https://polygon.blockscout.com',
    'optimism': 'https://optimism.blockscout.com',
    'arbitrum': 'https://arbitrum.blockscout.com'
  };
  
  return urls[chain] || urls['ethereum'];
}