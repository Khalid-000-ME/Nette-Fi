#!/usr/bin/env node

/**
 * P2 - Parallel Swap Tester (Account 3)
 * Sends opposing swaps to create netting opportunities
 */

const ethers = require('ethers');

// Configuration
const RPC_URL = 'http://192.168.29.121:8545';
const CONTRACT_ADDRESS = process.env.NETTED_AMM_ADDRESS || '0xe66aa5e1bc2B6B0f1F685a50463ef0D18efc1b9B';

// Account 3 Details
const ACCOUNT = {
    name: "Account 3 (P2)",
    address: "0xa75Cd05BF16BbeA1759DE2A66c0472131BC5Bd8D",
    privateKey: "0x19c439237a1e2c86f87b2d31438e5476738dd67297bf92d752b16bdb4ff37aa2"
};

// Tokens
const TOKENS = {
    ETH: "0x0000000000000000000000000000000000000000",
    USDC: "0x1642dD5c38642f91E4aa0025978b572fe30Ed89d",
    DAI: "0x2249977665260A63307Cf72a4D65385cC0817CB5"
};

// Contract ABI
const ABI = [
    "function requestSwap(address tokenA, address tokenB, uint256 amountA, uint256 minAmountB) external payable returns (bytes32 requestId, bool wasNetted)",
    "function getStats() external view returns (uint256, uint256, uint256, uint256)",
    "event SwapRequested(address indexed user, address tokenA, address tokenB, uint256 amountA, uint256 timestamp)",
    "event SwapNetted(address indexed userA, address indexed userB, address tokenA, address tokenB, uint256 nettedAmount, bytes32 txHash)"
];

async function main() {
    console.log('🔵 P2 Starting - Account 3 Opposing Swaps');
    console.log('=' .repeat(60));
    
    const provider = new ethers.providers.JsonRpcProvider(RPC_URL);
    const wallet = new ethers.Wallet(ACCOUNT.privateKey, provider);
    const contract = new ethers.Contract(CONTRACT_ADDRESS, ABI, wallet);
    
    console.log(`Account: ${ACCOUNT.name}`);
    console.log(`Address: ${ACCOUNT.address}`);
    console.log(`Contract: ${CONTRACT_ADDRESS}`);
    
    // Get initial balance
    const balance = await provider.getBalance(ACCOUNT.address);
    console.log(`ETH Balance: ${ethers.utils.formatEther(balance)} ETH`);
    
    // P2 creates OPPOSITE swaps to P1 (for netting)
    const swapPatterns = [
        { from: TOKENS.ETH, to: TOKENS.DAI, amount: "0.08", label: "ETH→DAI", delay: 1500 },
        { from: TOKENS.ETH, to: TOKENS.USDC, amount: "0.12", label: "ETH→USDC", delay: 3000 },
        { from: TOKENS.ETH, to: TOKENS.DAI, amount: "0.18", label: "ETH→DAI", delay: 4500 },
        { from: TOKENS.ETH, to: TOKENS.USDC, amount: "0.25", label: "ETH→USDC", delay: 6000 }
    ];
    
    console.log('\n🔄 Starting opposing swap pattern...');
    console.log('💡 Strategy: Create opposite swaps to trigger netting with P1');
    
    for (let i = 0; i < swapPatterns.length; i++) {
        const pattern = swapPatterns[i];
        
        // Wait for the specified delay before this swap
        if (pattern.delay > 0) {
            console.log(`⏳ Waiting ${pattern.delay}ms for optimal netting timing...`);
            await new Promise(resolve => setTimeout(resolve, pattern.delay));
        }
        
        try {
            console.log(`\n[${i + 1}/${swapPatterns.length}] ${pattern.label} - ${pattern.amount} ETH`);
            
            const amountWei = ethers.utils.parseEther(pattern.amount);
            const value = pattern.from === TOKENS.ETH ? amountWei : 0;
            
            console.log('Sending opposing transaction...');
            
            // Use more robust transaction sending for Arcology DevNet
            const txParams = {
                to: CONTRACT_ADDRESS,
                value: value,
                gasLimit: 500000, // Fixed gas limit to avoid estimation issues
                gasPrice: ethers.utils.parseUnits('2', 'gwei'),
                data: contract.interface.encodeFunctionData('requestSwap', [
                    pattern.from,
                    pattern.to,
                    amountWei,
                    0
                ])
            };
            
            const tx = await wallet.sendTransaction(txParams);
            console.log(`📤 TX Hash: ${tx.hash || 'pending'}`);
            
            // Wait with timeout to handle DevNet issues
            let receipt = null;
            try {
                receipt = await Promise.race([
                    tx.wait(),
                    new Promise((_, reject) => 
                        setTimeout(() => reject(new Error('Transaction timeout')), 10000)
                    )
                ]);
                
                if (receipt && receipt.status === 1) {
                    console.log(`✅ Mined in block: ${receipt.blockNumber}`);
                    console.log(`⛽ Gas Used: ${receipt.gasUsed.toString()}`);
                } else if (receipt && receipt.status === 0) {
                    console.log(`❌ Transaction reverted in block: ${receipt.blockNumber}`);
                } else {
                    console.log(`⏳ Transaction pending...`);
                }
            } catch (waitError) {
                console.log(`⏳ Transaction sent but confirmation timeout: ${waitError.message}`);
            }
            
            // Check for netting events if receipt is available
            if (receipt && receipt.logs) {
                const events = receipt.logs;
                let nettingFound = false;
                
                for (const log of events) {
                    try {
                        const parsed = contract.interface.parseLog(log);
                        if (parsed.name === 'SwapNetted') {
                            console.log(`🎯 NETTING SUCCESS! Users: ${parsed.args.userA} ↔ ${parsed.args.userB}`);
                            console.log(`   Tokens: ${parsed.args.tokenA} ↔ ${parsed.args.tokenB}`);
                            console.log(`   Netted Amount: ${parsed.args.nettedAmount.toString()}`);
                            console.log(`   Netting TX Hash: ${parsed.args.txHash}`);
                            nettingFound = true;
                        }
                    } catch (e) {
                        // Ignore parsing errors for non-contract events
                    }
                }
                
                if (!nettingFound) {
                    console.log('📋 No immediate netting - request queued for future matching');
                }
            } else {
                console.log('📋 Transaction sent - waiting for DevNet confirmation');
            }
            
        } catch (error) {
            console.error(`❌ Swap ${i + 1} failed:`, error.message);
        }
        
        // Shorter wait between P2 swaps (more aggressive)
        if (i < swapPatterns.length - 1) {
            const waitTime = 1000; // 1 second
            console.log(`⏳ Quick wait ${waitTime}ms before next swap...`);
            await new Promise(resolve => setTimeout(resolve, waitTime));
        }
    }
    
    // Final stats
    console.log('\n📊 Getting updated contract stats...');
    try {
        const stats = await contract.getStats();
        console.log(`Total Swaps: ${stats[0].toString()}`);
        console.log(`Total Netted: ${stats[1].toString()}`);
        console.log(`Gas Saved: ${stats[2].toString()}`);
        console.log(`Active Requests: ${stats[3].toString()}`);
        
        const nettingRate = stats[0] > 0 ? (Number(stats[1]) / Number(stats[0]) * 100).toFixed(2) : 0;
        console.log(`Netting Rate: ${nettingRate}%`);
        
    } catch (error) {
        console.error('Failed to get stats:', error.message);
    }
    
    console.log('\n🔵 P2 Complete!');
}

main().catch(error => {
    console.error('❌ P2 Fatal Error:', error.message);
    process.exit(1);
});