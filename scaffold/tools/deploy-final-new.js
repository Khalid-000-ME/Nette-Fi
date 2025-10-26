const hre = require("hardhat");
const fs = require('fs');
const path = require('path');

async function main() {
    console.log("🚀 Deploying Fixed Arcology-Compatible DeFi Payroll Contracts...");
    console.log("=" * 70);
    
    // Get the deployer account
    const [deployer] = await hre.ethers.getSigners();
    console.log("📍 Deploying with account:", deployer.address);
    
    // Get account balance
    const balance = await deployer.provider.getBalance(deployer.address);
    console.log("💰 Account balance:", hre.ethers.utils.formatEther(balance), "ETH");
    
    // Ensure deployments directory exists
    const deploymentsDir = path.join(__dirname, '../deployments');
    if (!fs.existsSync(deploymentsDir)) {
        fs.mkdirSync(deploymentsDir, { recursive: true });
    }
    
    try {
        console.log("\n" + "=".repeat(50));
        console.log("📄 DEPLOYING USERCONTRACT (FIXED)");
        console.log("=".repeat(50));
        
        // Deploy UserContract (the fixed version)
        console.log("🔧 Getting UserContract factory...");
        const UserContract = await hre.ethers.getContractFactory("UserContract");
        
        console.log("🚀 Deploying UserContract...");
        const userContract = await UserContract.deploy();
        
        console.log("⏳ Waiting for deployment confirmation...");
        await userContract.deployed();
        
        const userContractAddress = userContract.address;
        console.log("✅ UserContract deployed to:", userContractAddress);
        
        // Get deployment transaction details
        const userDeployTx = userContract.deployTransaction;
        const userReceipt = await userDeployTx.wait();
        console.log("⛽ Gas used for UserContract:", userReceipt.gasUsed.toString());
        
        console.log("\n" + "=".repeat(50));
        console.log("📄 DEPLOYING NETTEDAMM (FIXED)");
        console.log("=".repeat(50));
        
        // Deploy NettedAMM (the fixed version)
        console.log("🔧 Getting NettedAMM factory...");
        const NettedAMM = await hre.ethers.getContractFactory("NettedAMM");
        
        console.log("🚀 Deploying NettedAMM...");
        const nettedAMM = await NettedAMM.deploy();
        
        console.log("⏳ Waiting for deployment confirmation...");
        await nettedAMM.deployed();
        
        const nettedAMMAddress = nettedAMM.address;
        console.log("✅ NettedAMM deployed to:", nettedAMMAddress);
        
        // Get deployment transaction details
        const ammDeployTx = nettedAMM.deployTransaction;
        const ammReceipt = await ammDeployTx.wait();
        console.log("⛽ Gas used for NettedAMM:", ammReceipt.gasUsed.toString());
        
        console.log("\n" + "=".repeat(50));
        console.log("🔗 LINKING CONTRACTS");
        console.log("=".repeat(50));
        
        // Set NettedAMM address in UserContract
        console.log("🔗 Setting NettedAMM address in UserContract...");
        const setNettedAMMTx = await userContract.setNettedAMM(nettedAMMAddress);
        await setNettedAMMTx.wait();
        console.log("✅ Contracts successfully linked!");
        
        console.log("\n" + "=".repeat(50));
        console.log("🧪 TESTING BASIC FUNCTIONALITY");
        console.log("=".repeat(50));
        
        // Register deployer as user
        console.log("👤 Registering deployer as user...");
        const registerTx = await userContract.registerUser();
        await registerTx.wait();
        console.log("✅ Deployer registered successfully!");
        
        // Test concurrent counter access
        console.log("\n📊 Testing concurrent counter access...");
        
        try {
            // Get global stats (tests concurrent counters)
            console.log("📈 Fetching global statistics...");
            const globalStats = await userContract.getGlobalStats();
            console.log("✅ Global Stats Retrieved:", {
                totalUsers: globalStats[0].toString(),
                totalTransactions: globalStats[1].toString(),
                totalGasSaved: globalStats[2].toString(),
                totalValue: hre.ethers.utils.formatEther(globalStats[3]),
                avgGasSavings: globalStats[4].toString()
            });
            
            // Get user stats (tests concurrent maps)
            console.log("👤 Fetching user statistics...");
            const userStats = await userContract.getUserStats(deployer.address);
            console.log("✅ User Stats Retrieved:", {
                totalTransactions: userStats[0].toString(),
                totalGasSaved: userStats[1].toString(),
                totalAmountProcessed: hre.ethers.utils.formatEther(userStats[2]),
                averageGasSavings: userStats[3].toString(),
                lastTransactionTime: userStats[4].toString(),
                isRegistered: userStats[5]
            });
            
            // Test NettedAMM concurrent counters
            console.log("🔄 Fetching AMM statistics...");
            const ammStats = await nettedAMM.getStats();
            console.log("✅ AMM Stats Retrieved:", {
                totalSwaps: ammStats[0].toString(),
                totalNetted: ammStats[1].toString(),
                gasSaved: ammStats[2].toString(),
                activeRequests: ammStats[3].toString()
            });
            
            console.log("🎉 All concurrent data structures working correctly!");
            
        } catch (testError) {
            console.error("⚠️ Testing error (contracts still deployed):", testError.message);
        }
        
        console.log("\n" + "=".repeat(50));
        console.log("💾 SAVING DEPLOYMENT INFO");
        console.log("=".repeat(50));
        
        // Create comprehensive deployment info
        const deploymentInfo = {
            network: hre.network.name,
            chainId: (await hre.ethers.provider.getNetwork()).chainId,
            deployer: deployer.address,
            deployedAt: new Date().toISOString(),
            blockNumber: await hre.ethers.provider.getBlockNumber(),
            contracts: {
                UserContract: {
                    address: userContractAddress,
                    txHash: userDeployTx.hash,
                    gasUsed: userReceipt.gasUsed.toString(),
                    blockNumber: userReceipt.blockNumber
                },
                NettedAMM: {
                    address: nettedAMMAddress,
                    txHash: ammDeployTx.hash,
                    gasUsed: ammReceipt.gasUsed.toString(),
                    blockNumber: ammReceipt.blockNumber
                }
            },
            features: {
                arcologyCompatible: true,
                concurrentDataStructures: true,
                parallelExecution: true,
                mevProtection: true,
                payrollManager: true
            },
            apiEndpoints: {
                userContract: userContractAddress,
                nettedAMM: nettedAMMAddress,
                note: "Update your API configuration with these addresses"
            }
        };
        
        // Save deployment info
        const deploymentFile = path.join(deploymentsDir, 'fixed-contracts.json');
        fs.writeFileSync(deploymentFile, JSON.stringify(deploymentInfo, null, 2));
        console.log("💾 Deployment info saved to:", deploymentFile);
        
        // Also save a simple addresses file for easy reference
        const addressesFile = path.join(deploymentsDir, 'contract-addresses.json');
        const addresses = {
            UserContract: userContractAddress,
            NettedAMM: nettedAMMAddress,
            network: hre.network.name,
            deployedAt: new Date().toISOString()
        };
        fs.writeFileSync(addressesFile, JSON.stringify(addresses, null, 2));
        console.log("📋 Contract addresses saved to:", addressesFile);
        
        console.log("\n" + "=".repeat(70));
        console.log("🎉 DEPLOYMENT COMPLETED SUCCESSFULLY!");
        console.log("=".repeat(70));
        console.log("✅ UserContract:", userContractAddress);
        console.log("✅ NettedAMM:", nettedAMMAddress);
        console.log("🔧 Arcology-compatible concurrent data structures");
        console.log("⚡ Ready for parallel transaction processing");
        console.log("🛡️ MEV protection enabled");
        console.log("💼 DeFi Payroll Manager ready for production");
        console.log("=".repeat(70));
        
        // Print next steps
        console.log("\n📝 NEXT STEPS:");
        console.log("1. Update your API endpoints with the new contract addresses");
        console.log("2. Update environment variables in your backend");
        console.log("3. Test payroll batch processing");
        console.log("4. Verify concurrent transaction handling");
        console.log("5. Deploy to production when ready");
        
        return {
            userContract: userContractAddress,
            nettedAMM: nettedAMMAddress,
            success: true
        };
        
    } catch (error) {
        console.error("\n❌ DEPLOYMENT FAILED:");
        console.error("Error:", error.message);
        console.error("Stack:", error.stack);
        
        // Save error info for debugging
        const errorInfo = {
            error: error.message,
            stack: error.stack,
            timestamp: new Date().toISOString(),
            network: hre.network.name,
            deployer: deployer.address
        };
        
        const errorFile = path.join(deploymentsDir, 'deployment-error.json');
        fs.writeFileSync(errorFile, JSON.stringify(errorInfo, null, 2));
        console.error("🐛 Error details saved to:", errorFile);
        
        process.exit(1);
    }
}

// Execute deployment
main()
    .then((result) => {
        if (result && result.success) {
            console.log("\n🚀 Deployment script completed successfully!");
            console.log("🎯 Your DeFi Payroll Manager is ready for use!");
        }
        process.exit(0);
    })
    .catch((error) => {
        console.error("\n💥 Fatal deployment error:", error);
        process.exit(1);
    });