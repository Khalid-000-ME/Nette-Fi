// frontend/lib/mev-analysis.ts
import { ethers } from 'ethers';

export class SimpleMEVDetector {
  private provider: ethers.JsonRpcProvider;
  private recentTxs: any[] = [];
  
  constructor(rpcUrl: string) {
    this.provider = new ethers.JsonRpcProvider(rpcUrl, undefined, {
      staticNetwork: true, // Avoid unnecessary network calls
      batchMaxCount: 8,    // Limit batch size
      batchMaxSize: 1024 * 1024, // 1MB batch limit
      batchStallTime: 10   // Wait 10ms before sending batch
    });
  }
  
  async analyzeCurrentBlock(): Promise<MEVAnalysis> {
    console.log('🔍 Starting MEV analysis...');
    
    // Add timeout to prevent hanging
    const timeoutPromise = new Promise<MEVAnalysis>((_, reject) => {
      setTimeout(() => reject(new Error('Analysis timeout after 30 seconds')), 30000);
    });
    
    const analysisPromise = this.performAnalysis();
    
    try {
      return await Promise.race([analysisPromise, timeoutPromise]);
    } catch (error) {
      console.error('❌ MEV analysis failed:', error);
      return this.getEmptyAnalysis();
    }
  }
  
  private async performAnalysis(): Promise<MEVAnalysis> {
    try {
      const blockNumber = await this.provider.getBlockNumber();
      console.log(`📦 Analyzing current block ${blockNumber} for real-time MEV detection`);
      
      // Step 1: Get pending transactions for real-time MEV detection
      const pendingTxs = await this.getPendingTransactions();
      console.log(`🔄 Found ${pendingTxs.length} pending transactions`);
      
      // Step 2: Get recent confirmed block for pattern analysis
      const block = await this.provider.getBlock(blockNumber, false);
      
      if (!block || !block.transactions) {
        console.log('⚠️ No block found, analyzing pending transactions only');
        return this.analyzePendingTransactions(pendingTxs, blockNumber);
      }
      
      console.log(`📊 Found ${block.transactions.length} confirmed transactions in latest block`);
      
      const recentTxs = await this.fetchTransactionsBatched(
        block.transactions.slice(0, 20) // Reduced for faster real-time analysis
      );
      console.log(`📋 Retrieved ${recentTxs.length} recent transaction details`);
      
      // Step 4: Combine pending and recent transactions for comprehensive analysis
      const combinedAnalysis = await this.analyzeRealTimeMEV(pendingTxs, recentTxs, blockNumber);
      
      return combinedAnalysis;
      
    } catch (error) {
      console.error('❌ MEV analysis failed:', error);
      return this.getEmptyAnalysis();
    }
  }
  
  private async fetchTransactionsBatched(txHashes: string[]): Promise<any[]> {
    const BATCH_SIZE = 8; // Conservative batch size to avoid rate limits
    const DELAY_MS = 100; // Small delay between batches
    const validTxs: any[] = [];
    
    console.log(`🔄 Fetching ${txHashes.length} transactions in batches of ${BATCH_SIZE}...`);
    
    for (let i = 0; i < txHashes.length; i += BATCH_SIZE) {
      const batch = txHashes.slice(i, i + BATCH_SIZE);
      console.log(`  📦 Batch ${Math.floor(i / BATCH_SIZE) + 1}: Processing ${batch.length} transactions...`);
      
      try {
        const batchTxs = await Promise.all(
          batch.map(hash => this.provider.getTransaction(hash))
        );
        
        const validBatchTxs = batchTxs.filter(tx => tx !== null);
        validTxs.push(...validBatchTxs);
        console.log(`  ✅ Batch completed: ${validBatchTxs.length}/${batch.length} valid transactions`);
        
        // Add delay between batches to avoid rate limiting
        if (i + BATCH_SIZE < txHashes.length) {
          await new Promise(resolve => setTimeout(resolve, DELAY_MS));
        }
        
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : String(error);
        console.log(`  ⚠️ Batch failed, skipping: ${errorMessage}`);
        // Continue with next batch instead of failing completely
      }
    }
    
    return validTxs;
  }
  
  // NEW: Get pending transactions for real-time MEV detection
  private async getPendingTransactions(): Promise<any[]> {
    try {
      console.log('🔄 Fetching pending transactions from mempool...');
      
      // Use eth_getBlockByNumber with "pending" to get pending transactions
      const pendingBlock = await this.provider.send('eth_getBlockByNumber', ['pending', true]);
      
      if (!pendingBlock || !pendingBlock.transactions) {
        console.log('⚠️ No pending transactions found');
        return [];
      }
      
      // Filter for valid transactions with proper structure
      const validPendingTxs = pendingBlock.transactions.filter((tx: any) => 
        tx && tx.hash && tx.to && tx.from && tx.gasPrice
      );
      
      console.log(`✅ Retrieved ${validPendingTxs.length} valid pending transactions`);
      return validPendingTxs;
      
    } catch (error) {
      console.log('⚠️ Failed to get pending transactions, using alternative method...');
      
      // Fallback: Try to get recent mempool data via txpool (if available)
      try {
        const txpool = await this.provider.send('txpool_content', []);
        const pending = txpool?.pending || {};
        
        const pendingTxs: any[] = [];
        Object.values(pending).forEach((addressTxs: any) => {
          Object.values(addressTxs).forEach((tx: any) => {
            if (tx && tx.hash) {
              pendingTxs.push(tx);
            }
          });
        });
        
        console.log(`✅ Retrieved ${pendingTxs.length} transactions from txpool`);
        return pendingTxs.slice(0, 50); // Limit for performance
        
      } catch (txpoolError) {
        console.log('⚠️ Txpool access failed, returning empty array');
        return [];
      }
    }
  }
  
  // NEW: Analyze pending transactions for immediate MEV threats
  private async analyzePendingTransactions(pendingTxs: any[], blockNumber: number): Promise<MEVAnalysis> {
    console.log(`🔍 Analyzing ${pendingTxs.length} pending transactions for MEV threats...`);
    
    // Filter DEX transactions in mempool
    const pendingDexTxs = pendingTxs.filter(tx => this.isDEXTx(tx));
    console.log(`🔄 Found ${pendingDexTxs.length} pending DEX transactions`);
    
    // Detect high-gas transactions (potential MEV bots)
    const highGasTxs = pendingDexTxs.filter(tx => {
      if (!tx.gasPrice) return false;
      const gasPrice = BigInt(tx.gasPrice);
      const avgGasPrice = this.calculateAverageGasPrice(pendingDexTxs);
      return gasPrice > BigInt(avgGasPrice) * BigInt(15) / BigInt(10); // 50% above average
    });
    
    console.log(`🤖 Identified ${highGasTxs.length} high-gas pending transactions`);
    
    // Detect potential sandwich setups in mempool
    const sandwichThreats = this.detectPendingSandwichThreats(pendingTxs);
    console.log(`🥪 Detected ${sandwichThreats.length} potential sandwich threats in mempool`);
    
    return {
      block_number: blockNumber,
      total_txs: pendingTxs.length,
      dex_txs: pendingDexTxs.length,
      suspicious_high_gas: highGasTxs.length,
      detected_sandwiches: sandwichThreats.length,
      avg_gas_price: this.calculateAvgGas(pendingDexTxs),
      mev_risk_score: this.calculateRealTimeRiskScore(highGasTxs.length, sandwichThreats.length, pendingDexTxs.length)
    };
  }
  
  // NEW: Comprehensive real-time MEV analysis combining pending and recent data
  private async analyzeRealTimeMEV(pendingTxs: any[], recentTxs: any[], blockNumber: number): Promise<MEVAnalysis> {
    console.log(`🔍 Performing comprehensive real-time MEV analysis...`);
    
    // Analyze pending transactions
    const pendingAnalysis = await this.analyzePendingTransactions(pendingTxs, blockNumber);
    
    // Analyze recent confirmed transactions for patterns
    const recentDexTxs = recentTxs.filter(tx => this.isDEXTx(tx));
    const recentSandwiches = this.detectSandwichPatterns(recentTxs);
    
    console.log(`📊 Recent block analysis: ${recentDexTxs.length} DEX txs, ${recentSandwiches.length} sandwiches`);
    
    // Combine analyses for comprehensive risk assessment
    const totalDexTxs = pendingAnalysis.dex_txs + recentDexTxs.length;
    const totalSandwiches = pendingAnalysis.detected_sandwiches + recentSandwiches.length;
    const totalSuspicious = pendingAnalysis.suspicious_high_gas;
    
    // Enhanced risk scoring based on both pending and recent activity
    const enhancedRiskScore = this.calculateEnhancedRiskScore(
      totalSuspicious,
      totalSandwiches,
      totalDexTxs,
      pendingTxs.length
    );
    
    return {
      block_number: blockNumber,
      total_txs: pendingTxs.length + recentTxs.length,
      dex_txs: totalDexTxs,
      suspicious_high_gas: totalSuspicious,
      detected_sandwiches: totalSandwiches,
      avg_gas_price: this.calculateCombinedAvgGas(pendingTxs, recentTxs),
      mev_risk_score: enhancedRiskScore
    };
  }
  
  private isDEXTx(tx: any): boolean {
    if (!tx || !tx.to) return false;
    
    const DEX_ROUTERS = [
      '0x94cC0AaC535CCDB3C01d6787D6413C739ae12bc4', // Uniswap V3 Base Sepolia
      '0x4752ba5dbc23f44d87826276bf6fd6b1c372ad24', // Another router
      '0x7a250d5630b4cf539739df2c5dacb4c659f2488d', // Uniswap V2 Router
      '0xe592427a0aece92de3edee1f18e0157c05861564', // Uniswap V3 Router
      '0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45', // Uniswap V3 Router 2
    ];
    
    return DEX_ROUTERS.some(router => 
      tx.to.toLowerCase() === router.toLowerCase()
    );
  }
  
  private detectSandwichPatterns(txs: any[]): any[] {
    // Simple pattern: 3 consecutive txs to same pool
    // First and last have high gas, middle has normal gas
    const sandwiches = [];
    
    for (let i = 0; i < txs.length - 2; i++) {
      const tx1 = txs[i];
      const tx2 = txs[i + 1];
      const tx3 = txs[i + 2];
      
      if (
        this.isDEXTx(tx1) && 
        this.isDEXTx(tx2) && 
        this.isDEXTx(tx3) &&
        tx1.gasPrice && tx2.gasPrice && tx3.gasPrice &&
        BigInt(tx1.gasPrice) > BigInt(tx2.gasPrice) * BigInt(15) / BigInt(10) &&
        BigInt(tx3.gasPrice) > BigInt(tx2.gasPrice) * BigInt(15) / BigInt(10)
      ) {
        sandwiches.push({
          frontrun: tx1.hash,
          victim: tx2.hash,
          backrun: tx3.hash,
          estimated_profit: 'Unknown' // Could calculate if you parse logs
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
    return ethers.formatUnits(avg, 'gwei');
  }
  
  private calculateRiskScore(suspiciousCount: number, sandwichCount: number): number {
    // Simple scoring
    let score = 0;
    score += suspiciousCount * 10; // Each suspicious tx adds 10 points
    score += sandwichCount * 30;   // Each sandwich adds 30 points
    return Math.min(100, score);
  }
  
  // NEW: Helper methods for real-time MEV analysis
  private calculateAverageGasPrice(txs: any[]): string {
    if (txs.length === 0) return '0';
    
    const validTxs = txs.filter(tx => tx.gasPrice);
    if (validTxs.length === 0) return '0';
    
    const sum = validTxs.reduce((acc, tx) => acc + BigInt(tx.gasPrice), BigInt(0));
    const avg = sum / BigInt(validTxs.length);
    return avg.toString();
  }
  
  private detectPendingSandwichThreats(pendingTxs: any[]): any[] {
    const threats = [];
    const dexTxs = pendingTxs.filter(tx => this.isDEXTx(tx));
    
    // Look for high-gas transactions that could be frontrunning setups
    for (const tx of dexTxs) {
      if (!tx.gasPrice) continue;
      
      const gasPrice = BigInt(tx.gasPrice);
      const avgGasPrice = BigInt(this.calculateAverageGasPrice(dexTxs));
      
      // If gas price is significantly higher than average, it's a potential MEV bot
      if (gasPrice > avgGasPrice * BigInt(2)) {
        threats.push({
          hash: tx.hash,
          from: tx.from,
          to: tx.to,
          gasPrice: tx.gasPrice,
          threat_type: 'potential_frontrun',
          risk_level: gasPrice > avgGasPrice * BigInt(3) ? 'high' : 'medium'
        });
      }
    }
    
    return threats;
  }
  
  private calculateRealTimeRiskScore(suspiciousCount: number, sandwichCount: number, totalDexTxs: number): number {
    let score = 0;
    
    // Base scoring
    score += suspiciousCount * 15; // Higher weight for real-time threats
    score += sandwichCount * 25;   // Sandwich threats are critical
    
    // Adjust based on DEX activity level
    if (totalDexTxs > 0) {
      const suspiciousRatio = suspiciousCount / totalDexTxs;
      score += suspiciousRatio * 30; // High ratio of suspicious to total DEX txs
    }
    
    return Math.min(100, score);
  }
  
  private calculateEnhancedRiskScore(suspicious: number, sandwiches: number, totalDex: number, totalPending: number): number {
    let score = 0;
    
    // Weighted scoring for combined analysis
    score += suspicious * 12;
    score += sandwiches * 30;
    
    // Activity-based adjustments
    if (totalDex > 0 && totalPending > 0) {
      const dexRatio = totalDex / totalPending;
      const suspiciousRatio = suspicious / totalDex;
      
      score += dexRatio * 20;        // High DEX activity increases risk
      score += suspiciousRatio * 25;  // High suspicious ratio is dangerous
    }
    
    // Mempool congestion factor
    if (totalPending > 100) {
      score += 10; // Congested mempool increases MEV risk
    }
    
    return Math.min(100, score);
  }
  
  private calculateCombinedAvgGas(pendingTxs: any[], recentTxs: any[]): string {
    const allTxs = [...pendingTxs, ...recentTxs];
    const dexTxs = allTxs.filter(tx => this.isDEXTx(tx));
    return this.calculateAvgGas(dexTxs);
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

export interface MEVAnalysis {
  block_number: number;
  total_txs: number;
  dex_txs: number;
  suspicious_high_gas: number;
  detected_sandwiches: number;
  avg_gas_price: string;
  mev_risk_score: number;
}