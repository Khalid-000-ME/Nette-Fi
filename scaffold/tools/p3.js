#!/usr/bin/env node

/**
 * P3 - Parallel Swap Tester (Account 4)
 * Sends random swaps to stress test the netting system
 */

const ethers = require('ethers');

// Configuration
const RPC_URL = 'http://192.168.29.121:8545';
const CONTRACT_ADDRESS = process.env.NETTED_AMM_ADDRESS || '0xe66aa5e1bc2B6B0f1F685a50463ef0D18efc1b9B';

// Account 4 Details
const ACCOUNT = {
    name: "Account 4 (P3)",
    address: "0x2c7161284197e40E83B1b657e98B3bb8FF3C90ed",
    privateKey: "0x236c7b430c2ea13f19add3920b0bb2795f35a969f8be617faa9629bc5f6201f1"
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
    console.log('🟡 P3 Starting - Account 4 Stress Tester');
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
    
    // P3 creates RANDOM swaps to stress test the system
    const swapPatterns = [
        { from: TOKENS.ETH, to: TOKENS.USDC, amount: "0.05", label: "ETH→USDC", delay: 2000 },
        { from: TOKENS.ETH, to: TOKENS.DAI, amount: "0.03", label: "ETH→DAI", delay: 2500 },
        { from: TOKENS.ETH, to: TOKENS.USDC, amount: "0.07", label: "ETH→USDC", delay: 3500 },
        { from: TOKENS.ETH, to: TOKENS.DAI, amount: "0.09", label: "ETH→DAI", delay: 5000 },
        { from: TOKENS.ETH, to: TOKENS.USDC, amount: "0.04", label: "ETH→USDC", delay: 6500 },
        { from: TOKENS.ETH, to: TOKENS.DAI, amount: "0.06", label: "ETH→DAI", delay: 8000 }
    ];
    
    console.log('\n🔄 Starting stress test pattern...');
    console.log('💡 Strategy: Random timing to create diverse netting opportunities');
    
    for (let i = 0; i < swapPatterns.length; i++) {
        const pattern = swapPatterns[i];
        
        // Wait for the specified delay before this swap
        if (pattern.delay > 0) {
            console.log(`⏳ Waiting ${pattern.delay}ms for stress test timing...`);
            await new Promise(resolve => setTimeout(resolve, pattern.delay));
        }
        
        try {
            console.log(`\n[${i + 1}/${swapPatterns.length}] ${pattern.label} - ${pattern.amount} ETH`);
            
            const amountWei = ethers.utils.parseEther(pattern.amount);
            const value = pattern.from === TOKENS.ETH ? amountWei : 0;
            
            console.log('Sending stress test transaction...');
            
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
                            console.log(`🎯 STRESS TEST NETTING! Users: ${parsed.args.userA} ↔ ${parsed.args.userB}`);
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
                    console.log('📋 No netting - adding to queue for future matches');
                }
            } else {
                console.log('📋 Transaction sent - waiting for DevNet confirmation');
            }
            
            // Get current stats after each transaction
            try {
                const stats = await contract.getStats();
                console.log(`📊 Current: ${stats[0]} swaps, ${stats[1]} netted, ${stats[3]} pending`);
            } catch (e) {
                // Ignore stats errors
            }
            
        } catch (error) {
            console.error(`❌ Swap ${i + 1} failed:`, error.message);
        }
        
        // Variable wait times for stress testing
        if (i < swapPatterns.length - 1) {
            const waitTime = 800 + Math.random() * 400; // 800-1200ms random
            console.log(`⏳ Random wait ${Math.round(waitTime)}ms...`);
            await new Promise(resolve => setTimeout(resolve, waitTime));
        }
    }
    
    // Final comprehensive stats
    console.log('\n📊 Final stress test results...');
    try {
        const stats = await contract.getStats();
        console.log(`Total Swaps: ${stats[0].toString()}`);
        console.log(`Total Netted: ${stats[1].toString()}`);
        console.log(`Gas Saved: ${stats[2].toString()}`);
        console.log(`Active Requests: ${stats[3].toString()}`);
        
        const totalSwaps = Number(stats[0]);
        const totalNetted = Number(stats[1]);
        const gasSaved = Number(stats[2]);
        
        if (totalSwaps > 0) {
            const nettingRate = (totalNetted / totalSwaps * 100).toFixed(2);
            const avgGasSaved = totalNetted > 0 ? Math.round(gasSaved / totalNetted) : 0;
            
            console.log(`\n🎯 Performance Metrics:`);
            console.log(`   Netting Rate: ${nettingRate}%`);
            console.log(`   Avg Gas Saved per Net: ${avgGasSaved}`);
            console.log(`   Total Gas Efficiency: ${gasSaved.toLocaleString()}`);
        }
        
    } catch (error) {
        console.error('Failed to get final stats:', error.message);
    }
    
    console.log('\n🟡 P3 Stress Test Complete!');
}

main().catch(error => {
    console.error('❌ P3 Fatal Error:', error.message);
    process.exit(1);
});