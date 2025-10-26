const { ethers } = require("hardhat");

async function main() {
    console.log("⚡ QUICK DEPLOYMENT & TEST - Netted Swap Payroll");
    console.log("=" .repeat(50));
    
    const [deployer, employer, employee] = await ethers.getSigners();
    
    console.log("Deployer:", deployer.address);
    console.log("Employer:", employer.address);
    console.log("Employee:", employee.address);
    console.log("");
    
    // Deploy essential tokens only
    console.log("💰 Deploying Essential Tokens...");
    const USDCFactory = await ethers.getContractFactory("USDC");
    const usdc = await USDCFactory.deploy();
    await usdc.deployed();
    console.log("✅ USDC:", usdc.address);
    
    const WETHFactory = await ethers.getContractFactory("WETH");
    const weth = await WETHFactory.deploy();
    await weth.deployed();
    console.log("✅ WETH:", weth.address);
    
    // Mint tokens to employer
    await usdc.mint(employer.address, ethers.utils.parseUnits("10000", 6)); // 10k USDC
    await weth.mint(employer.address, ethers.utils.parseEther("100")); // 100 WETH
    console.log("✅ Tokens minted to employer");
    
    // Deploy Uniswap V3 Factory
    console.log("🏭 Deploying Uniswap V3...");
    const UniswapV3Factory = await ethers.getContractFactory("UniswapV3Factory");
    const factory = await UniswapV3Factory.deploy();
    await factory.deployed();
    console.log("✅ Factory:", factory.address);
    
    // Create ETH/USDC pool
    await factory.createPool(weth.address, usdc.address, 3000);
    const poolAddress = await factory.getPool(weth.address, usdc.address, 3000);
    console.log("✅ ETH/USDC Pool:", poolAddress);
    
    // Deploy netting components
    console.log("🕸️ Deploying Netting System...");
    const PoolLookupFactory = await ethers.getContractFactory("PoolLookup");
    const poolLookup = await PoolLookupFactory.deploy();
    await poolLookup.deployed();
    
    const NettingFactory = await ethers.getContractFactory("Netting");
    const netting = await NettingFactory.deploy(factory.address);
    await netting.deployed();
    
    const NettingEngineFactory = await ethers.getContractFactory("NettingEngine");
    const nettingEngine = await NettingEngineFactory.deploy();
    await nettingEngine.deployed();
    
    await nettingEngine.init(factory.address, netting.address);
    await poolLookup.set(poolAddress, weth.address, usdc.address);
    await nettingEngine.initPool(poolAddress, weth.address, usdc.address);
    console.log("✅ Netting system deployed");
    
    // Deploy payroll contract (minimal version for testing)
    console.log("💼 Deploying Payroll Contract...");
    
    // Create minimal token list for constructor
    const zeroAddress = "0x0000000000000000000000000000000000000000";
    
    const NettedSwapPayrollFactory = await ethers.getContractFactory("NettedSwapPayroll");
    const payroll = await NettedSwapPayrollFactory.deploy(
        usdc.address,    // USDC
        zeroAddress,     // DAI (not used in test)
        weth.address,    // WETH
        zeroAddress,     // AVAX (not used)
        zeroAddress,     // LINK (not used)
        zeroAddress,     // MATIC (not used)
        zeroAddress,     // SOL (not used)
        zeroAddress,     // USDT (not used)
        netting.address,
        nettingEngine.address
    );
    await payroll.deployed();
    console.log("✅ Payroll Contract:", payroll.address);
    
    // Setup approvals
    console.log("🔧 Setting up approvals...");
    await usdc.connect(employer).approve(payroll.address, ethers.utils.parseUnits("10000", 6));
    await weth.connect(employer).approve(payroll.address, ethers.utils.parseEther("100"));
    console.log("✅ Approvals set");
    
    // Send ETH to employer
    await deployer.sendTransaction({
        to: employer.address,
        value: ethers.utils.parseEther("5.0")
    });
    console.log("✅ ETH sent to employer");
    
    // Test the system
    console.log("");
    console.log("🧪 TESTING SYSTEM...");
    console.log("-".repeat(30));
    
    console.log("Test: ETH → USDC Payroll");
    
    // Check initial balances
    const employeeUSDCBefore = await usdc.balanceOf(employee.address);
    const employerETHBefore = await ethers.provider.getBalance(employer.address);
    
    console.log(`Employee USDC before: ${ethers.utils.formatUnits(employeeUSDCBefore, 6)}`);
    console.log(`Employer ETH before: ${ethers.utils.formatEther(employerETHBefore)}`);
    
    // Submit payroll transaction
    const tx = await payroll.connect(employer).submitPayrollSwap(
        employee.address,
        ethers.constants.AddressZero, // ETH
        usdc.address,                 // USDC
        ethers.utils.parseEther("0.1"), // 0.1 ETH
        3000, // 0.3% fee
        { value: ethers.utils.parseEther("0.1") }
    );
    
    const receipt = await tx.wait();
    console.log("✅ Transaction submitted, gas used:", receipt.gasUsed.toString());
    
    // Extract transaction ID from events
    const event = receipt.events.find(e => e.event === 'PayrollSwapSubmitted');
    const txId = event.args[5]; // Last argument should be the transaction ID
    console.log("Transaction ID:", txId);
    
    // Process the batch
    const batchTx = await payroll.connect(employer).processBatchPayrollSwaps([txId]);
    const batchReceipt = await batchTx.wait();
    console.log("✅ Batch processed, gas used:", batchReceipt.gasUsed.toString());
    
    // Check final balances
    const employeeUSDCAfter = await usdc.balanceOf(employee.address);
    const employerETHAfter = await ethers.provider.getBalance(employer.address);
    
    console.log(`Employee USDC after: ${ethers.utils.formatUnits(employeeUSDCAfter, 6)}`);
    console.log(`Employer ETH after: ${ethers.utils.formatEther(employerETHAfter)}`);
    
    const usdcReceived = employeeUSDCAfter.sub(employeeUSDCBefore);
    console.log(`USDC received: ${ethers.utils.formatUnits(usdcReceived, 6)}`);
    
    // Get system stats
    const stats = await payroll.getPayrollSwapStats();
    console.log("");
    console.log("📊 System Statistics:");
    console.log(`Total Transactions: ${stats[0]}`);
    console.log(`Total Batches: ${stats[1]}`);
    console.log(`Total Netted: ${stats[2]}`);
    console.log(`Gas Saved: ${stats[3]}`);
    
    console.log("");
    console.log("🎉 QUICK TEST COMPLETE!");
    
    // Return deployment addresses for frontend
    return {
        payrollContract: payroll.address,
        usdcToken: usdc.address,
        wethToken: weth.address,
        factory: factory.address,
        netting: netting.address,
        nettingEngine: nettingEngine.address,
        employer: employer.address,
        employee: employee.address
    };
}

if (require.main === module) {
    main()
        .then(() => process.exit(0))
        .catch((error) => {
            console.error("❌ Quick test failed:", error);
            process.exit(1);
        });
}

module.exports = main;
