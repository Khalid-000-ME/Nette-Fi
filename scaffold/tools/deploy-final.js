const { ethers } = require("hardhat");

async function main() {
    console.log("🚀 Starting DeFi Payroll Manager - Scaffold Contracts Deployment");
    
    const [deployer] = await ethers.getSigners();
    console.log("📝 Deploying contracts with account:", deployer.address);
    console.log("💰 Account balance:", (await deployer.getBalance()).toString());

    // Contract addresses will be stored here
    const deployedContracts = {};

    try {
        // 1. Deploy UserContract
        console.log("\n👤 Deploying UserContract...");
        const UserContract = await ethers.getContractFactory("UserContract");
        const userContract = await UserContract.deploy();
        await userContract.deployed();
        deployedContracts.UserContract = userContract.address;
        console.log("✅ UserContract deployed to:", userContract.address);

        // 2. Setup initial configuration
        console.log("\n⚙️ Setting up initial configuration...");
        
        // Register the deployer as the first user
        await userContract.registerUser();
        console.log("✅ Deployer registered as first user");

        // 3. Generate deployment summary
        console.log("\n📋 DEPLOYMENT SUMMARY");
        console.log("=" .repeat(50));
        console.log("👤 UserContract:", deployedContracts.UserContract);
        
        // 4. Save deployment info to file
        const fs = require('fs');
        const deploymentInfo = {
            network: "arcology-devnet",
            chainId: 118,
            deployer: deployer.address,
            deployedAt: new Date().toISOString(),
            contracts: deployedContracts,
            gasUsed: {
                // Will be filled by actual deployment
            }
        };
        
        // Create deployments directory if it doesn't exist
        if (!fs.existsSync('./deployments')) {
            fs.mkdirSync('./deployments');
        }
        
        fs.writeFileSync(
            './deployments/scaffold-contracts.json',
            JSON.stringify(deploymentInfo, null, 2)
        );
        
        console.log("\n💾 Deployment info saved to ./deployments/scaffold-contracts.json");
        
        // 5. Verification instructions
        console.log("\n🔍 VERIFICATION INSTRUCTIONS:");
        console.log("To verify contracts on block explorer, run:");
        console.log(`npx hardhat verify --network arcology ${deployedContracts.UserContract}`);
        
        // 6. Integration instructions
        console.log("\n🔗 INTEGRATION INSTRUCTIONS:");
        console.log("Update your frontend API routes with these contract addresses:");
        console.log(`UserContract: ${deployedContracts.UserContract}`);
        console.log("\nAdd to your environment variables:");
        console.log(`USER_CONTRACT_ADDRESS=${deployedContracts.UserContract}`);
        
        console.log("\n🎉 Deployment completed successfully!");
        
        return deployedContracts;
        
    } catch (error) {
        console.error("❌ Deployment failed:", error);
        throw error;
    }
}

// Execute deployment
if (require.main === module) {
    main()
        .then(() => process.exit(0))
        .catch((error) => {
            console.error(error);
            process.exit(1);
        });
}

module.exports = main;