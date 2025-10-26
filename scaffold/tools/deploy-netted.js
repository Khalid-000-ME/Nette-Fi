#!/usr/bin/env node

/**
 * Deploy NettedAMM Contract and Test Parallel Netting
 */

const { ethers } = require('ethers');
const fs = require('fs');
const path = require('path');

// Network Configuration
const RPC_URL = 'http://192.168.29.121:8545';
const CHAIN_ID = 118;

// Test Accounts from network.json
const ACCOUNTS = [
    {
        name: "Account 2",
        address: "0x21522c86A586e696961b68aa39632948D9F11170",
        privateKey: "0x2289ae919f03075448d567c9c4a22846ce3711731c895f1bea572cef25bb346f"
    },
    {
        name: "Account 3", 
        address: "0xa75Cd05BF16BbeA1759DE2A66c0472131BC5Bd8D",
        privateKey: "0x19c439237a1e2c86f87b2d31438e5476738dd67297bf92d752b16bdb4ff37aa2"
    },
    {
        name: "Account 4",
        address: "0x2c7161284197e40E83B1b657e98B3bb8FF3C90ed", 
        privateKey: "0x236c7b430c2ea13f19add3920b0bb2795f35a969f8be617faa9629bc5f6201f1"
    }
];

// Token Addresses
const TOKENS = {
    ETH: "0x0000000000000000000000000000000000000000",
    USDC: "0x1642dD5c38642f91E4aa0025978b572fe30Ed89d",
    DAI: "0x2249977665260A63307Cf72a4D65385cC0817CB5"
};

// Contract ABI (simplified)
const NETTED_AMM_ABI = [
    "function requestSwap(address tokenA, address tokenB, uint256 amountA, uint256 minAmountB) external payable returns (bytes32 requestId, bool wasNetted)",
    "function executeIndividualSwap(bytes32 requestId) external",
    "function getStats() external view returns (uint256, uint256, uint256, uint256)",
    "function getPrice(address tokenA, address tokenB) external view returns (uint256)",
    "event SwapRequested(address indexed user, address tokenA, address tokenB, uint256 amountA, uint256 timestamp)",
    "event SwapNetted(address indexed userA, address indexed userB, address tokenA, address tokenB, uint256 nettedAmount, bytes32 txHash)",
    "event SwapExecuted(address indexed user, address tokenA, address tokenB, uint256 amountA, uint256 amountB, bytes32 txHash)"
];

// Contract Bytecode (you'll need to compile the contract first)
const CONTRACT_BYTECODE = "0x608060405234801561001057600080fd5b50..."; // This will be filled after compilation

let deployedContractAddress = null;

async function main() {
    console.log('🚀 NettedAMM Deployment and Testing');
    console.log('=' .repeat(80));
    
    try {
        // Step 1: Deploy Contract
        console.log('\n📦 Step 1: Deploying NettedAMM Contract...');
        deployedContractAddress = await deployContract();
        
        // Step 2: Test Individual Swaps
        console.log('\n🔄 Step 2: Testing Individual Swaps...');
        await testIndividualSwaps();
        
        // Step 3: Test Parallel Netting
        console.log('\n⚡ Step 3: Testing Parallel Netting...');
        await testParallelNetting();
        
        // Step 4: Show Results
        console.log('\n📊 Step 4: Final Statistics...');
        await showFinalStats();
        
    } catch (error) {
        console.error('❌ Error:', error.message);
    }
}

async function deployContract() {
    const provider = new ethers.JsonRpcProvider(RPC_URL);
    const deployer = new ethers.Wallet(ACCOUNTS[0].privateKey, provider);
    
    console.log(`Deploying from: ${deployer.address}`);
    
    // Read compiled contract
    const contractPath = path.join(__dirname, '../contracts/NettedAMM.sol');
    console.log(`Contract source: ${contractPath}`);
    
    // For now, we'll use a simple deployment
    // In a real scenario, you'd compile with Hardhat/Foundry first
    
    const contractFactory = new ethers.ContractFactory(
        NETTED_AMM_ABI,
        CONTRACT_BYTECODE,
        deployer
    );
    
    console.log('Deploying contract...');
    const contract = await contractFactory.deploy();
    await contract.waitForDeployment();
    
    const address = await contract.getAddress();
    console.log(`✅ Contract deployed at: ${address}`);
    
    return address;
}

async function testIndividualSwaps() {
    const provider = new ethers.JsonRpcProvider(RPC_URL);
    
    for (let i = 0; i < ACCOUNTS.length; i++) {
        const wallet = new ethers.Wallet(ACCOUNTS[i].privateKey, provider);
        const contract = new ethers.Contract(deployedContractAddress, NETTED_AMM_ABI, wallet);
        
        console.log(`\n${ACCOUNTS[i].name} requesting swap...`);
        
        try {
            const tx = await contract.requestSwap(
                TOKENS.ETH,
                TOKENS.USDC,
                ethers.parseEther("0.1"), // 0.1 ETH
                0, // min amount
                { value: ethers.parseEther("0.1") }
            );
            
            console.log(`Transaction sent: ${tx.hash}`);
            const receipt = await tx.wait();
            console.log(`✅ Mined in block: ${receipt.blockNumber}`);
            
            // Parse events
            const events = receipt.logs;
            console.log(`Events emitted: ${events.length}`);
            
        } catch (error) {
            console.error(`❌ ${ACCOUNTS[i].name} swap failed:`, error.message);
        }
        
        // Wait between transactions
        await new Promise(resolve => setTimeout(resolve, 1000));
    }
}

async function testParallelNetting() {
    const provider = new ethers.JsonRpcProvider(RPC_URL);
    
    console.log('Creating opposing swap requests simultaneously...');
    
    // Create opposing swaps that should net
    const swapPromises = [];
    
    // Account 2: ETH -> USDC
    const wallet1 = new ethers.Wallet(ACCOUNTS[0].privateKey, provider);
    const contract1 = new ethers.Contract(deployedContractAddress, NETTED_AMM_ABI, wallet1);
    
    swapPromises.push(
        contract1.requestSwap(
            TOKENS.ETH,
            TOKENS.USDC,
            ethers.parseEther("0.2"),
            0,
            { value: ethers.parseEther("0.2") }
        )
    );
    
    // Account 3: USDC -> ETH (opposite direction)
    const wallet2 = new ethers.Wallet(ACCOUNTS[1].privateKey, provider);
    const contract2 = new ethers.Contract(deployedContractAddress, NETTED_AMM_ABI, wallet2);
    
    swapPromises.push(
        contract2.requestSwap(
            TOKENS.USDC,
            TOKENS.ETH,
            ethers.parseUnits("600", 6), // 600 USDC
            0
        )
    );
    
    try {
        console.log('Sending parallel transactions...');
        const results = await Promise.all(swapPromises);
        
        console.log('\n📋 Transaction Results:');
        for (let i = 0; i < results.length; i++) {
            const tx = results[i];
            console.log(`${ACCOUNTS[i].name}: ${tx.hash}`);
            
            const receipt = await tx.wait();
            console.log(`  ✅ Block: ${receipt.blockNumber}, Gas: ${receipt.gasUsed.toString()}`);
            
            // Check if netting occurred
            const events = receipt.logs;
            const nettedEvents = events.filter(log => {
                try {
                    const parsed = contract1.interface.parseLog(log);
                    return parsed.name === 'SwapNetted';
                } catch {
                    return false;
                }
            });
            
            if (nettedEvents.length > 0) {
                console.log(`  🎯 NETTING OCCURRED! Events: ${nettedEvents.length}`);
            }
        }
        
    } catch (error) {
        console.error('❌ Parallel netting test failed:', error.message);
    }
}

async function showFinalStats() {
    const provider = new ethers.JsonRpcProvider(RPC_URL);
    const wallet = new ethers.Wallet(ACCOUNTS[0].privateKey, provider);
    const contract = new ethers.Contract(deployedContractAddress, NETTED_AMM_ABI, wallet);
    
    try {
        const stats = await contract.getStats();
        
        console.log('\n📊 Final Contract Statistics:');
        console.log(`Total Swaps: ${stats[0].toString()}`);
        console.log(`Total Netted: ${stats[1].toString()}`);
        console.log(`Gas Saved: ${stats[2].toString()}`);
        console.log(`Active Requests: ${stats[3].toString()}`);
        
        // Calculate netting efficiency
        const totalSwaps = parseInt(stats[0].toString());
        const totalNetted = parseInt(stats[1].toString());
        
        if (totalSwaps > 0) {
            const nettingRate = (totalNetted / totalSwaps) * 100;
            console.log(`Netting Efficiency: ${nettingRate.toFixed(2)}%`);
        }
        
    } catch (error) {
        console.error('❌ Failed to get stats:', error.message);
    }
}

// Export for use in other scripts
module.exports = {
    deployContract,
    testIndividualSwaps,
    testParallelNetting,
    ACCOUNTS,
    TOKENS,
    NETTED_AMM_ABI
};

if (require.main === module) {
    main().catch(error => {
        console.error('Fatal error:', error);
        process.exit(1);
    });
}
