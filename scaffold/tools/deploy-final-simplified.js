const hre = require("hardhat");

async function main() {
    console.log("🚀 Deploying Simplified Arcology-Compatible Contracts...");
    
    // Get the deployer account
    const [deployer] = await hre.ethers.getSigners();
    console.log("📍 Deploying with account:", deployer.address);
    
    // Get account balance
    const balance = await deployer.provider.getBalance(deployer.address);
    console.log("💰 Account balance:", hre.ethers.utils.formatEther(balance), "ETH");
    
    try {
        // Deploy UserContract
        console.log("\n📄 Deploying UserContract...");
        const UserContract = await hre.ethers.getContractFactory("UserContract");
        const userContract = await UserContract.deploy();
        await userContract.deployed();
        const userContractAddress = userContract.address;
        console.log("✅ UserContract deployed to:", userContractAddress);
        
        // Deploy NettedAMM
        console.log("\n📄 Deploying NettedAMM...");
        const NettedAMM = await hre.ethers.getContractFactory("NettedAMM");
        const nettedAMM = await NettedAMM.deploy();
        await nettedAMM.deployed();
        const nettedAMMAddress = nettedAMM.address;
        console.log("✅ NettedAMM deployed to:", nettedAMMAddress);
        
        // Set NettedAMM address in UserContract
        console.log("\n🔗 Linking contracts...");
        const setNettedAMMTx = await userContract.setNettedAMM(nettedAMMAddress);
        await setNettedAMMTx.wait();
        console.log("✅ NettedAMM address set in UserContract");
        
        // Test basic functionality
        console.log("\n🧪 Testing basic functionality...");
        
        // Register deployer as user
        const registerTx = await userContract.registerUser();
        await registerTx.wait();
        console.log("✅ Deployer registered as user");
        
        // Get global stats
        const globalStats = await userContract.getGlobalStats();
        console.log("📊 Global Stats:", {
            totalUsers: globalStats[0].toString(),
            totalTransactions: globalStats[1].toString(),
            totalGasSaved: globalStats[2].toString(),
            totalValue: hre.ethers.utils.formatEther(globalStats[3]),
            avgGasSavings: globalStats[4].toString()
        });
        
        // Get user stats
        const userStats = await userContract.getUserStats(deployer.address);
        console.log("👤 User Stats:", {
            totalTransactions: userStats[0].toString(),
            totalGasSaved: userStats[1].toString(),
            totalAmountProcessed: hre.ethers.utils.formatEther(userStats[2]),
            averageGasSavings: userStats[3].toString(),
            lastTransactionTime: userStats[4].toString(),
            isRegistered: userStats[5]
        });
        
        // Test NettedAMM stats
        const ammStats = await nettedAMM.getStats();
        console.log("🔄 AMM Stats:", {
            totalSwaps: ammStats[0].toString(),
            totalNetted: ammStats[1].toString(),
            gasSaved: ammStats[2].toString(),
            activeRequests: ammStats[3].toString()
        });
        
        // Save deployment info
        const deploymentInfo = {
            network: "arcology-devnet",
            chainId: 118,
            deployer: deployer.address,
            deployedAt: new Date().toISOString(),
            contracts: {
                UserContract: userContractAddress,
                NettedAMM: nettedAMMAddress
            },
            gasUsed: {
                UserContract: "Estimated",
                NettedAMM: "Estimated"
            }
        };
        
        console.log("\n📋 Deployment Summary:");
        console.log(JSON.stringify(deploymentInfo, null, 2));
        
        // Write to file
        const fs = require('fs');
        fs.writeFileSync('./deployments/final-contracts.json', JSON.stringify(deploymentInfo, null, 2));
        console.log("💾 Deployment info saved to deployments/final-contracts.json");
        
        console.log("\n🎉 Deployment completed successfully!");
        console.log("🔧 These contracts are optimized for Arcology's parallel execution");
        console.log("📝 Update your API endpoints to use these new addresses");
        
    } catch (error) {
        console.error("❌ Deployment failed:", error);
        process.exit(1);
    }
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error(error);
        process.exit(1);
    });
