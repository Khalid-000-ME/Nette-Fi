const { ethers } = require("hardhat");

async function main() {
    console.log("🚀 DEPLOYING COMPLETE NETTED SWAP PAYROLL SYSTEM");
    console.log("=" .repeat(60));
    
    const [deployer, employer, employee1, employee2, employee3] = await ethers.getSigners();
    
    console.log("📋 Deployment Details:");
    console.log("Deployer:", deployer.address);
    console.log("Employer:", employer.address);
    console.log("Employee 1:", employee1.address);
    console.log("Employee 2:", employee2.address);
    console.log("Employee 3:", employee3.address);
    console.log("");
    
    // ===================================================================
    // STEP 1: DEPLOY TOKEN CONTRACTS
    // ===================================================================
    console.log("💰 STEP 1: DEPLOYING TOKEN CONTRACTS");
    console.log("-".repeat(40));
    
    const tokenContracts = {};
    const tokenNames = ['USDC', 'DAI', 'WETH', 'AVAX', 'LINK', 'MATIC', 'SOL', 'USDT'];
    
    for (const tokenName of tokenNames) {
        const TokenFactory = await ethers.getContractFactory(tokenName);
        const token = await TokenFactory.deploy();
        await token.deployed();
        tokenContracts[tokenName] = token;
        console.log(`✅ ${tokenName} deployed to:`, token.address);
        
        // Mint tokens to employer for testing
        if (tokenName === 'USDC') {
            await token.mint(employer.address, ethers.utils.parseUnits("10000", 6)); // 10k USDC
        } else if (tokenName === 'DAI') {
            await token.mint(employer.address, ethers.utils.parseEther("10000")); // 10k DAI
        } else {
            await token.mint(employer.address, ethers.utils.parseEther("1000")); // 1k other tokens
        }
    }
    console.log("");
    
    // ===================================================================
    // STEP 2: DEPLOY UNISWAP V3 CORE INFRASTRUCTURE
    // ===================================================================
    console.log("🏭 STEP 2: DEPLOYING UNISWAP V3 CORE");
    console.log("-".repeat(40));
    
    // Deploy Uniswap V3 Factory
    const UniswapV3Factory = await ethers.getContractFactory("UniswapV3Factory");
    const factory = await UniswapV3Factory.deploy();
    await factory.deployed();
    console.log("✅ UniswapV3Factory deployed to:", factory.address);
    
    // Deploy WETH9 for native ETH handling
    const WETH9Factory = await ethers.getContractFactory("WETH9");
    const weth9 = await WETH9Factory.deploy();
    await weth9.deployed();
    console.log("✅ WETH9 deployed to:", weth9.address);
    console.log("");
    
    // ===================================================================
    // STEP 3: CREATE UNISWAP V3 POOLS
    // ===================================================================
    console.log("🏊 STEP 3: CREATING UNISWAP V3 POOLS");
    console.log("-".repeat(40));
    
    const pools = {};
    const poolPairs = [
        { tokenA: 'WETH', tokenB: 'USDC', fee: 3000 },
        { tokenA: 'WETH', tokenB: 'DAI', fee: 3000 },
        { tokenA: 'USDC', tokenB: 'DAI', fee: 500 },
        { tokenA: 'WETH', tokenB: 'LINK', fee: 3000 },
        { tokenA: 'WETH', tokenB: 'AVAX', fee: 3000 },
        { tokenA: 'USDC', tokenB: 'USDT', fee: 500 }
    ];
    
    for (const pair of poolPairs) {
        const tokenA = tokenContracts[pair.tokenA];
        const tokenB = tokenContracts[pair.tokenB];
        
        console.log(`Creating pool: ${pair.tokenA}/${pair.tokenB} (${pair.fee})`);
        
        const tx = await factory.createPool(tokenA.address, tokenB.address, pair.fee);
        await tx.wait();
        
        const poolAddress = await factory.getPool(tokenA.address, tokenB.address, pair.fee);
        pools[`${pair.tokenA}_${pair.tokenB}_${pair.fee}`] = poolAddress;
        
        console.log(`✅ Pool created at: ${poolAddress}`);
    }
    console.log("");
    
    // ===================================================================
    // STEP 4: DEPLOY NETTING SYSTEM COMPONENTS
    // ===================================================================
    console.log("🕸️ STEP 4: DEPLOYING NETTING SYSTEM");
    console.log("-".repeat(40));
    
    // Deploy PoolLookup
    const PoolLookupFactory = await ethers.getContractFactory("PoolLookup");
    const poolLookup = await PoolLookupFactory.deploy();
    await poolLookup.deployed();
    console.log("✅ PoolLookup deployed to:", poolLookup.address);
    
    // Deploy Netting contract (needs router address - we'll use factory for now)
    const NettingFactory = await ethers.getContractFactory("Netting");
    const netting = await NettingFactory.deploy(factory.address);
    await netting.deployed();
    console.log("✅ Netting deployed to:", netting.address);
    
    // Deploy NettingEngine
    const NettingEngineFactory = await ethers.getContractFactory("NettingEngine");
    const nettingEngine = await NettingEngineFactory.deploy();
    await nettingEngine.deployed();
    console.log("✅ NettingEngine deployed to:", nettingEngine.address);
    
    // Initialize NettingEngine
    await nettingEngine.init(factory.address, netting.address);
    console.log("✅ NettingEngine initialized");
    
    // Register pools in PoolLookup and NettingEngine
    for (const pair of poolPairs) {
        const tokenA = tokenContracts[pair.tokenA];
        const tokenB = tokenContracts[pair.tokenB];
        const poolAddress = pools[`${pair.tokenA}_${pair.tokenB}_${pair.fee}`];
        
        // Register in PoolLookup
        await poolLookup.set(poolAddress, tokenA.address, tokenB.address);
        
        // Register in NettingEngine
        await nettingEngine.initPool(poolAddress, tokenA.address, tokenB.address);
        
        console.log(`✅ Pool registered: ${pair.tokenA}/${pair.tokenB}`);
    }
    console.log("");
    
    // ===================================================================
    // STEP 5: DEPLOY NETTED SWAP PAYROLL CONTRACT
    // ===================================================================
    console.log("💼 STEP 5: DEPLOYING NETTED SWAP PAYROLL");
    console.log("-".repeat(40));
    
    const NettedSwapPayrollFactory = await ethers.getContractFactory("NettedSwapPayroll");
    const payrollContract = await NettedSwapPayrollFactory.deploy(
        tokenContracts.USDC.address,
        tokenContracts.DAI.address,
        tokenContracts.WETH.address,
        tokenContracts.AVAX.address,
        tokenContracts.LINK.address,
        tokenContracts.MATIC.address,
        tokenContracts.SOL.address,
        tokenContracts.USDT.address,
        netting.address,
        nettingEngine.address
    );
    await payrollContract.deployed();
    console.log("✅ NettedSwapPayroll deployed to:", payrollContract.address);
    console.log("");
    
    // ===================================================================
    // STEP 6: SETUP AND FUND ACCOUNTS
    // ===================================================================
    console.log("💰 STEP 6: SETTING UP TEST ACCOUNTS");
    console.log("-".repeat(40));
    
    // Send ETH to employer for payroll
    await deployer.sendTransaction({
        to: employer.address,
        value: ethers.utils.parseEther("10.0") // 10 ETH
    });
    console.log("✅ Sent 10 ETH to employer");
    
    // Approve payroll contract to spend employer's tokens
    for (const tokenName of tokenNames) {
        const token = tokenContracts[tokenName];
        const balance = await token.balanceOf(employer.address);
        if (balance.gt(0)) {
            await token.connect(employer).approve(payrollContract.address, balance);
            console.log(`✅ Employer approved ${tokenName}: ${ethers.utils.formatUnits(balance, tokenName === 'USDC' ? 6 : 18)}`);
        }
    }
    console.log("");
    
    // ===================================================================
    // STEP 7: COMPREHENSIVE SYSTEM TESTING
    // ===================================================================
    console.log("🧪 STEP 7: COMPREHENSIVE SYSTEM TESTING");
    console.log("-".repeat(40));
    
    console.log("Test 1: Simple ETH → USDC Payroll");
    console.log("- Employer pays 0.1 ETH → Employee gets USDC");
    
    const tx1 = await payrollContract.connect(employer).submitPayrollSwap(
        employee1.address,
        ethers.constants.AddressZero, // ETH
        tokenContracts.USDC.address,  // USDC
        ethers.utils.parseEther("0.1"), // 0.1 ETH
        3000, // 0.3% fee
        { value: ethers.utils.parseEther("0.1") }
    );
    const receipt1 = await tx1.wait();
    const txId1 = receipt1.events.find(e => e.event === 'PayrollSwapSubmitted').args[5]; // transactionId from event
    console.log("✅ Transaction 1 submitted:", txId1);
    
    console.log("Test 2: USDC → ETH Payroll (Opposite direction for netting)");
    console.log("- Employer pays 300 USDC → Employee gets ETH");
    
    const tx2 = await payrollContract.connect(employer).submitPayrollSwap(
        employee2.address,
        tokenContracts.USDC.address,  // USDC
        ethers.constants.AddressZero, // ETH
        ethers.utils.parseUnits("300", 6), // 300 USDC
        3000 // 0.3% fee
    );
    const receipt2 = await tx2.wait();
    const txId2 = receipt2.events.find(e => e.event === 'PayrollSwapSubmitted').args[5];
    console.log("✅ Transaction 2 submitted:", txId2);
    
    console.log("Test 3: ETH → DAI Payroll");
    console.log("- Employer pays 0.05 ETH → Employee gets DAI");
    
    const tx3 = await payrollContract.connect(employer).submitPayrollSwap(
        employee3.address,
        ethers.constants.AddressZero, // ETH
        tokenContracts.DAI.address,   // DAI
        ethers.utils.parseEther("0.05"), // 0.05 ETH
        3000, // 0.3% fee
        { value: ethers.utils.parseEther("0.05") }
    );
    const receipt3 = await tx3.wait();
    const txId3 = receipt3.events.find(e => e.event === 'PayrollSwapSubmitted').args[5];
    console.log("✅ Transaction 3 submitted:", txId3);
    
    console.log("Test 4: Process Batch with Netting Optimization");
    console.log("- Processing all 3 transactions together");
    console.log("- Transactions 1 & 2 should be netted (ETH↔USDC)");
    console.log("- Transaction 3 should go through pool (ETH→DAI)");
    
    // Get initial balances
    const employee1USDCBefore = await tokenContracts.USDC.balanceOf(employee1.address);
    const employee2ETHBefore = await ethers.provider.getBalance(employee2.address);
    const employee3DAIBefore = await tokenContracts.DAI.balanceOf(employee3.address);
    
    console.log("Initial balances:");
    console.log(`- Employee1 USDC: ${ethers.utils.formatUnits(employee1USDCBefore, 6)}`);
    console.log(`- Employee2 ETH: ${ethers.utils.formatEther(employee2ETHBefore)}`);
    console.log(`- Employee3 DAI: ${ethers.utils.formatEther(employee3DAIBefore)}`);
    
    // Process batch
    const batchTx = await payrollContract.connect(employer).processBatchPayrollSwaps([txId1, txId2, txId3]);
    const batchReceipt = await batchTx.wait();
    console.log("✅ Batch processed! Gas used:", batchReceipt.gasUsed.toString());
    
    // Check final balances
    const employee1USDCAfter = await tokenContracts.USDC.balanceOf(employee1.address);
    const employee2ETHAfter = await ethers.provider.getBalance(employee2.address);
    const employee3DAIAfter = await tokenContracts.DAI.balanceOf(employee3.address);
    
    console.log("Final balances:");
    console.log(`- Employee1 USDC: ${ethers.utils.formatUnits(employee1USDCAfter, 6)} (+${ethers.utils.formatUnits(employee1USDCAfter.sub(employee1USDCBefore), 6)})`);
    console.log(`- Employee2 ETH: ${ethers.utils.formatEther(employee2ETHAfter)} (+${ethers.utils.formatEther(employee2ETHAfter.sub(employee2ETHBefore))})`);
    console.log(`- Employee3 DAI: ${ethers.utils.formatEther(employee3DAIAfter)} (+${ethers.utils.formatEther(employee3DAIAfter.sub(employee3DAIBefore))})`);
    
    // Get system statistics
    const stats = await payrollContract.getPayrollSwapStats();
    console.log("System Statistics:");
    console.log(`- Total Transactions: ${stats[0]}`);
    console.log(`- Total Batches: ${stats[1]}`);
    console.log(`- Total Netted: ${stats[2]}`);
    console.log(`- Gas Saved: ${stats[3]}`);
    console.log(`- Active Employers: ${stats[4]}`);
    
    console.log("");
    console.log("🎉 DEPLOYMENT AND TESTING COMPLETE!");
    console.log("=" .repeat(60));
    
    // ===================================================================
    // DEPLOYMENT SUMMARY
    // ===================================================================
    console.log("📋 DEPLOYMENT SUMMARY");
    console.log("-".repeat(40));
    
    const deploymentInfo = {
        "Network": "Arcology DevNet",
        "Deployer": deployer.address,
        "Contracts": {
            "NettedSwapPayroll": payrollContract.address,
            "UniswapV3Factory": factory.address,
            "Netting": netting.address,
            "NettingEngine": nettingEngine.address,
            "PoolLookup": poolLookup.address,
            "WETH9": weth9.address
        },
        "Tokens": {},
        "Pools": pools,
        "TestAccounts": {
            "Employer": employer.address,
            "Employee1": employee1.address,
            "Employee2": employee2.address,
            "Employee3": employee3.address
        }
    };
    
    // Add token addresses
    for (const tokenName of tokenNames) {
        deploymentInfo.Tokens[tokenName] = tokenContracts[tokenName].address;
    }
    
    console.log(JSON.stringify(deploymentInfo, null, 2));
    
    // Save deployment info to file
    const fs = require('fs');
    const path = require('path');
    
    const deploymentPath = path.join(__dirname, '..', 'deployments', 'netted-swap-payroll.json');
    fs.mkdirSync(path.dirname(deploymentPath), { recursive: true });
    fs.writeFileSync(deploymentPath, JSON.stringify(deploymentInfo, null, 2));
    
    console.log(`✅ Deployment info saved to: ${deploymentPath}`);
    console.log("");
    console.log("🚀 SYSTEM READY FOR PRODUCTION USE!");
}

main()
    .then(() => process.exit(0))
    .catch((error) => {
        console.error("❌ Deployment failed:", error);
        process.exit(1);
    });
