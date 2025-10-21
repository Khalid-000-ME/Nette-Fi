const { ethers } = require("hardhat");

async function main() {
  console.log("Deploying Sim-U-Fi contracts...");

  // Get the contract factories
  const MEVProtection = await ethers.getContractFactory("MEVProtection");
  const SimUFiExecutor = await ethers.getContractFactory("SimUFiExecutor");

  // Deploy MEVProtection contract
  console.log("Deploying MEVProtection...");
  const mevProtection = await MEVProtection.deploy();
  await mevProtection.deployed();
  console.log("MEVProtection deployed to:", mevProtection.address);

  // Deploy SimUFiExecutor contract
  console.log("Deploying SimUFiExecutor...");
  const executor = await SimUFiExecutor.deploy();
  await executor.deployed();
  console.log("SimUFiExecutor deployed to:", executor.address);

  // Set up initial configuration
  console.log("Setting up initial configuration...");
  
  // Set execution fee to 0.001 ETH
  await executor.setExecutionFee(ethers.utils.parseEther("0.001"));
  console.log("Execution fee set to 0.001 ETH");

  // Authorize deployer as executor (in production, this would be the bot address)
  const [deployer] = await ethers.getSigners();
  await executor.setAuthorizedExecutor(deployer.address, true);
  console.log("Deployer authorized as executor");

  console.log("\nDeployment Summary:");
  console.log("==================");
  console.log(`MEVProtection: ${mevProtection.address}`);
  console.log(`SimUFiExecutor: ${executor.address}`);
  console.log(`Deployer: ${deployer.address}`);
  
  // Save deployment addresses
  const deploymentInfo = {
    network: await ethers.provider.getNetwork(),
    contracts: {
      MEVProtection: mevProtection.address,
      SimUFiExecutor: executor.address
    },
    deployer: deployer.address,
    timestamp: new Date().toISOString()
  };

  const fs = require("fs");
  fs.writeFileSync(
    "deployment.json", 
    JSON.stringify(deploymentInfo, null, 2)
  );
  
  console.log("\nDeployment info saved to deployment.json");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });
