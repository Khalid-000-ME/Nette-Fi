#!/usr/bin/env node

/**
 * P1 - Parallel Swap Tester (Account 2)
 * Sends timed swap requests to test netting
 */

const ethers = require('ethers');

// Configuration
const RPC_URL = 'http://192.168.29.121:8545';
const CONTRACT_ADDRESS = process.env.NETTED_AMM_ADDRESS || '0xe66aa5e1bc2B6B0f1F685a50463ef0D18efc1b9B';

// Account 2 Details
const ACCOUNT = {
    name: "Account 2 (P1)",
    address: "0x21522c86A586e696961b68aa39632948D9F11170",
    privateKey: "0x2289ae919f03075448d567c9c4a22846ce3711731c895f1bea572cef25bb346f"
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
    console.log('🟢 P1 Starting - Account 2 Swap Tester');
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
    
    // Swap patterns for P1 (creates opportunities for netting)
    const swapPatterns = [
        { from: TOKENS.ETH, to: TOKENS.USDC, amount: "0.1", label: "ETH→USDC" },
        { from: TOKENS.ETH, to: TOKENS.DAI, amount: "0.05", label: "ETH→DAI" },
        { from: TOKENS.ETH, to: TOKENS.USDC, amount: "0.2", label: "ETH→USDC" },
        { from: TOKENS.ETH, to: TOKENS.DAI, amount: "0.15", label: "ETH→DAI" }
    ];
    
    console.log('\n🔄 Starting timed swap requests...');
    
    for (let i = 0; i < swapPatterns.length; i++) {
        const pattern = swapPatterns[i];
        
        try {
            console.log(`\n[${i + 1}/${swapPatterns.length}] ${pattern.label} - ${pattern.amount} ETH`);
            
            const amountWei = ethers.utils.parseEther(pattern.amount);
            const value = pattern.from === TOKENS.ETH ? amountWei : 0;
            
            console.log('Sending transaction...');
            
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
                            console.log(`🎯 NETTING DETECTED! Users: ${parsed.args.userA} ↔ ${parsed.args.userB}`);
                            console.log(`   Netted Amount: ${parsed.args.nettedAmount.toString()}`);
                            console.log(`   Netting TX Hash: ${parsed.args.txHash}`);
                            nettingFound = true;
                        }
                    } catch (e) {
                        // Ignore parsing errors for non-contract events
                    }
                }
                
                if (!nettingFound) {
                    console.log('📋 No netting occurred - request queued');
                }
            } else {
                console.log('📋 Transaction sent - waiting for DevNet confirmation');
            }
            
        } catch (error) {
            console.error(`❌ Swap ${i + 1} failed:`, error.message);
        }
        
        // Wait between swaps (staggered timing)
        if (i < swapPatterns.length - 1) {
            const waitTime = 2000 + (i * 500); // 2-4 seconds
            console.log(`⏳ Waiting ${waitTime}ms before next swap...`);
            await new Promise(resolve => setTimeout(resolve, waitTime));
        }
    }
    
    // Final stats
    console.log('\n📊 Getting final contract stats...');
    try {
        const stats = await contract.getStats();
        console.log(`Total Swaps: ${stats[0].toString()}`);
        console.log(`Total Netted: ${stats[1].toString()}`);
        console.log(`Gas Saved: ${stats[2].toString()}`);
        console.log(`Active Requests: ${stats[3].toString()}`);
    } catch (error) {
        console.error('Failed to get stats:', error.message);
    }
    
    console.log('\n🟢 P1 Complete!');
}

main().catch(error => {
    console.error('❌ P1 Fatal Error:', error.message);
    process.exit(1);
});