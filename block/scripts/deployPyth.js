const hre = require("hardhat");

// Pyth contract addresses on different networks
const PYTH_CONTRACT_ADDRESSES = {
  // Ethereum Mainnet
  "ethereum": "0x4305FB66699C3B2702D4d05CF36551390A4c69C6",
  
  // Base Mainnet
  "base": "0x8250f4aF4B972684F7b336503E2D6dFeDeB1487a",
  
  // Base Sepolia Testnet
  "base-sepolia": "0xA2aa501b19aff244D90cc15a4Cf739D2725B5729",
  
  // Arbitrum One
  "arbitrum": "0xff1a0f4744e8582DF1aE09D5611b887B6a12925C",
  
  // Polygon Mainnet
  "polygon": "0xff1a0f4744e8582DF1aE09D5611b887B6a12925C",
  
  // Optimism Mainnet
  "optimism": "0xff1a0f4744e8582DF1aE09D5611b887B6a12925C"
};

async function main() {
  console.log("🚀 Starting Pyth Price Consumer deployment...");
  
  const network = hre.network.name;
  console.log(`📡 Network: ${network}`);
  
  // Get Pyth contract address for the current network
  const pythAddress = PYTH_CONTRACT_ADDRESSES[network];
  
  if (!pythAddress) {
    console.error(`❌ Pyth contract address not found for network: ${network}`);
    console.log("Available networks:", Object.keys(PYTH_CONTRACT_ADDRESSES));
    process.exit(1);
  }
  
  console.log(`🔮 Pyth Contract Address: ${pythAddress}`);
  
  // Debug environment variables
  console.log(`🔍 Debug: PRIVATE_KEY exists: ${!!process.env.PRIVATE_KEY}`);
  console.log(`🔍 Debug: PRIVATE_KEY length: ${process.env.PRIVATE_KEY ? process.env.PRIVATE_KEY.length : 'undefined'}`);
  
  // Get the deployer account
  const signers = await hre.ethers.getSigners();
  console.log(`🔍 Debug: Number of signers: ${signers.length}`);
  
  if (signers.length === 0) {
    console.error("❌ No signers found! Please check your PRIVATE_KEY in .env.local");
    console.error("Make sure your .env.local file contains:");
    console.error("PRIVATE_KEY=your_private_key_without_0x_prefix");
    process.exit(1);
  }
  
  const [deployer] = signers;
  console.log(`👤 Deploying with account: ${deployer.address}`);
  
  // Check deployer balance
  const balance = await hre.ethers.provider.getBalance(deployer.address);
  console.log(`💰 Account balance: ${hre.ethers.formatEther(balance)} ETH`);
  
  // Deploy PythPriceConsumer
  console.log("\n📦 Deploying PythPriceConsumer...");
  const PythPriceConsumer = await hre.ethers.getContractFactory("PythPriceConsumer");
  
  const pythPriceConsumer = await PythPriceConsumer.deploy(pythAddress);
  await pythPriceConsumer.waitForDeployment();
  
  const contractAddress = await pythPriceConsumer.getAddress();
  console.log(`✅ PythPriceConsumer deployed to: ${contractAddress}`);
  
  // Wait for a few block confirmations
  console.log("⏳ Waiting for block confirmations...");
  const deployTx = pythPriceConsumer.deploymentTransaction();
  if (deployTx) {
    await deployTx.wait(3);
  }
  
  // Verify deployment
  console.log("\n🔍 Verifying deployment...");
  try {
    const owner = await pythPriceConsumer.owner();
    console.log(`👑 Contract owner: ${owner}`);
    
    // Test getting a price feed ID
    const ethPriceId = await pythPriceConsumer.getPriceFeedId("ETH");
    console.log(`🔗 ETH Price Feed ID: 0x${ethPriceId.slice(2)}`);
    
    console.log("✅ Contract verification successful!");
    
  } catch (error) {
    console.error("❌ Contract verification failed:", error.message);
  }
  
  // Save deployment info
  const deploymentInfo = {
    network: network,
    pythPriceConsumer: contractAddress,
    pythContract: pythAddress,
    deployer: deployer.address,
    deploymentTime: new Date().toISOString(),
    transactionHash: deployTx ? deployTx.hash : 'N/A'
  };
  
  console.log("\n📋 Deployment Summary:");
  console.log("=".repeat(50));
  console.log(`Network: ${deploymentInfo.network}`);
  console.log(`PythPriceConsumer: ${deploymentInfo.pythPriceConsumer}`);
  console.log(`Pyth Contract: ${deploymentInfo.pythContract}`);
  console.log(`Deployer: ${deploymentInfo.deployer}`);
  console.log(`Transaction: ${deploymentInfo.transactionHash}`);
  console.log("=".repeat(50));
  
  // Instructions for verification on block explorers
  if (network !== "hardhat" && network !== "localhost") {
    console.log("\n🔍 To verify on block explorer, run:");
    console.log(`npx hardhat verify --network ${network} ${contractAddress} "${pythAddress}"`);
  }
  
  console.log("\n🎉 Deployment completed successfully!");
  
  return deploymentInfo;
}

// Execute deployment
main()
  .then((deploymentInfo) => {
    console.log("✅ Deployment script completed successfully");
    process.exit(0);
  })
  .catch((error) => {
    console.error("❌ Deployment failed:", error);
    process.exit(1);
  });

module.exports = { main, PYTH_CONTRACT_ADDRESSES };
