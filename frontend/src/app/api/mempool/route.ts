import { NextRequest, NextResponse } from 'next/server';
import { SimpleMEVDetector } from '@/lib/mev-analysis';
import { BlockscoutMEVDetector, getBlockscoutUrl, BLOCKSCOUT_LIMITATIONS } from '@/lib/mev-blockscout';

// Mock function to analyze MEV patterns
function analyzeMEVPatterns(txs: any[]) {
  // Simple heuristic: High gas, DEX interaction, bot-like address
  const potentialBots = txs.filter(tx => 
    tx.gas_price > 150 && 
    isDexInteraction(tx) &&
    hasHighNonce(tx)
  );
  
  return {
    detected_bots: potentialBots.length,
    recent_sandwich_attacks: detectSandwichPatterns(txs),
    avg_attack_cost_percentage: 2.4 // Can be calculated from historical data
  };
}

function isDexInteraction(tx: any): boolean {
  // Check if transaction is interacting with known DEX contracts
  const dexContracts = [
    '0x7a250d5630b4cf539739df2c5dacb4c659f2488d', // Uniswap V2 Router
    '0xe592427a0aece92de3edee1f18e0157c05861564', // Uniswap V3 Router
    '0x68b3465833fb72a70ecdf485e0e4c7bd8665fc45', // Uniswap V3 Router 2
  ];
  return dexContracts.includes(tx.to?.toLowerCase());
}

function hasHighNonce(tx: any): boolean {
  // Bot addresses typically have high nonces from frequent transactions
  return tx.nonce > 100;
}

function detectSandwichPatterns(txs: any[]): number {
  // Simplified sandwich detection - look for high gas transactions around DEX swaps
  let sandwichCount = 0;
  
  for (let i = 1; i < txs.length - 1; i++) {
    const prev = txs[i - 1];
    const curr = txs[i];
    const next = txs[i + 1];
    
    // Pattern: High gas tx -> DEX swap -> High gas tx from same address
    if (
      prev.gas_price > 200 &&
      isDexInteraction(curr) &&
      next.gas_price > 200 &&
      prev.from === next.from &&
      prev.from !== curr.from
    ) {
      sandwichCount++;
    }
  }
  
  return sandwichCount;
}

async function getCurrentBlock(chain: string): Promise<number> {
  // In production, fetch from actual blockchain RPC
  // For demo, return mock block number
  return 19234564;
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const chain = searchParams.get('chain') || 'base';
    const useLive = searchParams.get('live') === 'true';
    const useBlockscout = searchParams.get('blockscout') === 'true';
    
    console.log(`🌐 Fetching mempool data for chain: ${chain}, live: ${useLive}, blockscout: ${useBlockscout}`);
    
    if (useBlockscout) {
      // Use Blockscout MEV analysis
      console.log('🟦 Using BLOCKSCOUT MEV analysis...');
      
      const blockscoutUrl = getBlockscoutUrl(chain);
      console.log(`🔗 Connecting to Blockscout: ${blockscoutUrl}`);
      
      const blockscoutDetector = new BlockscoutMEVDetector(blockscoutUrl);
      
      try {
        const blockscoutAnalysis = await blockscoutDetector.analyzeCurrentBlock();
        console.log('✅ Blockscout MEV analysis completed:', blockscoutAnalysis);
        
        const response = {
          chain,
          block_number: blockscoutAnalysis.block_number,
          pending_tx_count: blockscoutAnalysis.total_txs,
          pending_transactions: [], // Blockscout doesn't provide pending transactions
          mev_bot_activity: {
            detected_bots: blockscoutAnalysis.suspicious_high_gas,
            recent_sandwich_attacks: blockscoutAnalysis.detected_sandwiches,
            avg_attack_cost_percentage: Math.min(5, blockscoutAnalysis.mev_risk_score / 20),
            dex_transactions: blockscoutAnalysis.dex_txs,
            avg_gas_price_gwei: blockscoutAnalysis.avg_gas_price,
            risk_score: blockscoutAnalysis.mev_risk_score
          },
          data_source: 'blockscout_api',
          analysis_timestamp: new Date().toISOString(),
          limitations: BLOCKSCOUT_LIMITATIONS
        };
        
        return NextResponse.json(response);
        
      } catch (analysisError) {
        console.error('❌ Blockscout MEV analysis failed:', analysisError);
        // Fall back to mock data
        console.log('🔄 Falling back to mock data...');
      }
    }
    
    if (useLive) {
      // Use live MEV analysis
      console.log('🔴 Using LIVE MEV analysis...');
      
      // Get RPC URL based on chain
      const rpcUrl = getRpcUrl(chain);
      if (!rpcUrl) {
        console.log('❌ No RPC URL configured for chain:', chain);
        return NextResponse.json(
          { error: `No RPC configuration for chain: ${chain}` },
          { status: 400 }
        );
      }
      
      console.log(`🔗 Connecting to RPC: ${rpcUrl}`);
      const mevDetector = new SimpleMEVDetector(rpcUrl);
      
      try {
        const liveAnalysis = await mevDetector.analyzeCurrentBlock();
        console.log('✅ Live MEV analysis completed:', liveAnalysis);
        
        const response = {
          chain,
          block_number: liveAnalysis.block_number,
          pending_tx_count: liveAnalysis.total_txs,
          pending_transactions: [], // Live analysis doesn't return individual txs for privacy
          mev_bot_activity: {
            detected_bots: liveAnalysis.suspicious_high_gas,
            recent_sandwich_attacks: liveAnalysis.detected_sandwiches,
            avg_attack_cost_percentage: Math.min(5, liveAnalysis.mev_risk_score / 20),
            dex_transactions: liveAnalysis.dex_txs,
            avg_gas_price_gwei: liveAnalysis.avg_gas_price,
            risk_score: liveAnalysis.mev_risk_score
          },
          data_source: 'live_blockchain',
          analysis_timestamp: new Date().toISOString()
        };
        
        return NextResponse.json(response);
        
      } catch (analysisError) {
        console.error('❌ Live MEV analysis failed:', analysisError);
        // Fall back to mock data
        console.log('🔄 Falling back to mock data...');
      }
    }
    
    // Mock data path (default or fallback)
    console.log('🎭 Using mock mempool data...');
    
    const mockPendingTxs = [
      {
        hash: "0x1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef",
        from: "0x742d35cc6634c0532925a3b844bc9e7595f0beb1",
        to: "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",
        value: "1.5",
        gas_price_gwei: 150,
        nonce: 45,
        function: "swapExactTokensForTokens",
        is_potential_mev_bot: false
      },
      {
        hash: "0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890",
        from: "0x8ba1f109551bd432803012645hac136c4c73e57e",
        to: "0x7a250d5630b4cf539739df2c5dacb4c659f2488d",
        value: "0.1",
        gas_price_gwei: 250,
        nonce: 156,
        function: "swapExactETHForTokens",
        is_potential_mev_bot: true
      },
      {
        hash: "0xfedcba0987654321fedcba0987654321fedcba0987654321fedcba0987654321",
        from: "0x3f5ce5fbfe3e9af3971dd833d26ba9b5c936f0be",
        to: "0xe592427a0aece92de3edee1f18e0157c05861564",
        value: "2.3",
        gas_price_gwei: 180,
        nonce: 23,
        function: "exactInputSingle",
        is_potential_mev_bot: false
      }
    ];
    
    // Analyze for MEV patterns
    const mevAnalysis = analyzeMEVPatterns(mockPendingTxs);
    
    const response = {
      chain,
      block_number: await getCurrentBlock(chain),
      pending_tx_count: mockPendingTxs.length,
      pending_transactions: mockPendingTxs.slice(0, 20), // Return top 20
      mev_bot_activity: mevAnalysis,
      data_source: 'mock_data',
      analysis_timestamp: new Date().toISOString()
    };
    
    return NextResponse.json(response);
    
  } catch (error) {
    console.error('❌ Mempool fetch error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch mempool data' },
      { status: 500 }
    );
  }
}

function getRpcUrl(chain: string): string | null {
  const rpcUrls: { [key: string]: string } = {
    // Use environment variables first, then fallback to public RPCs with better rate limits
    'base': process.env.BASE_RPC_URL || 'https://base-rpc.publicnode.com',
    'base-sepolia': process.env.BASE_SEPOLIA_RPC_URL || 'https://sepolia.base.org',
    'ethereum': process.env.ETHEREUM_RPC_URL || 'https://ethereum-rpc.publicnode.com',
    'polygon': process.env.POLYGON_RPC_URL || 'https://polygon-rpc.com'
  };
  
  return rpcUrls[chain] || null;
}