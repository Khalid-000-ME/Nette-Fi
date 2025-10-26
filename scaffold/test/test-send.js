// test/test-send.js
const { ethers } = require("ethers");

async function main() {
  const provider = new ethers.providers.JsonRpcProvider("http://localhost:8545");
  
  // Use one of your test accounts
  const privateKey = "0x5bb1315c3ffa654c89f1f8b27f93cb4ef6b0474c4797cf2eb40d1bdd98dc26e7";
  const wallet = new ethers.Wallet(privateKey, provider);
  
  console.log("Sending from:", wallet.address);
  const balance = await provider.getBalance(wallet.address);
  console.log("Balance:", ethers.utils.formatEther(balance), "ETH");
  
  // Get current nonce
  const nonce = await provider.getTransactionCount(wallet.address);
  console.log("Current nonce:", nonce);
  
  // Create multiple raw transactions for batch sending
  const rawTransactions = [];
  const numTxs = 3; // Send 3 transactions in batch
  
  for (let i = 0; i < numTxs; i++) {
    const tx = {
      to: "0x21522c86A586e696961b68aa39632948D9F11170",
      value: ethers.utils.parseEther("0.001"), // Smaller amount for testing
      nonce: nonce + i,
      gasLimit: 21000,
      gasPrice: ethers.utils.parseUnits("20", "gwei")
    };
    
    const signedTx = await wallet.signTransaction(tx);
    rawTransactions.push(signedTx);
    console.log(`Created transaction ${i + 1} with nonce ${nonce + i}`);
  }
  
  console.log(`\nSending batch of ${rawTransactions.length} transactions using arn_sendRawTransactions...`);
  
  try {
    // Use Arcology's batch method
    const result = await provider.send("arn_sendRawTransactions", rawTransactions);
    console.log("✓ Batch sent successfully!");
    console.log("Transaction hashes:", result);
    
    // Wait a bit and check if transactions were mined
    console.log("\nWaiting 5 seconds to check transaction status...");
    await new Promise(resolve => setTimeout(resolve, 5000));
    
    // Check transaction status - arn_sendRawTransactions returns count, not hashes
    if (typeof result === 'number') {
      console.log(`✓ Successfully processed ${result} transactions`);
      
      // Check recent blocks for our transactions
      console.log("Checking recent blocks for transaction confirmations...");
      const latestBlock = await provider.getBlockNumber();
      
      for (let blockNum = latestBlock; blockNum >= Math.max(1, latestBlock - 5); blockNum--) {
        try {
          const block = await provider.getBlockWithTransactions(blockNum);
          if (block.transactions.length > 0) {
            console.log(`Block ${blockNum} has ${block.transactions.length} transactions`);
            
            // Check if any transactions are from our wallet
            const ourTxs = block.transactions.filter(tx => 
              tx.from && tx.from.toLowerCase() === wallet.address.toLowerCase()
            );
            
            if (ourTxs.length > 0) {
              console.log(`✓ Found ${ourTxs.length} transactions from our wallet in block ${blockNum}:`);
              ourTxs.forEach((tx, idx) => {
                console.log(`  Transaction ${idx + 1}: ${tx.hash}`);
              });
            }
          }
        } catch (error) {
          console.log(`Error checking block ${blockNum}:`, error.message);
        }
      }
    } else if (Array.isArray(result)) {
      // Handle array of transaction hashes
      for (let i = 0; i < result.length; i++) {
        try {
          const receipt = await provider.getTransactionReceipt(result[i]);
          if (receipt) {
            console.log(`✓ Transaction ${i + 1} (${result[i]}) mined in block ${receipt.blockNumber}`);
          } else {
            console.log(`⏳ Transaction ${i + 1} (${result[i]}) still pending`);
          }
        } catch (error) {
          console.log(`❌ Error checking transaction ${i + 1}:`, error.message);
        }
      }
    } else {
      console.log("Unexpected result format:", typeof result, result);
    }
    
  } catch (error) {
    console.error("❌ Batch method failed:", error.message);
    console.log("\n🔄 Falling back to individual transactions...");
    
    // Fallback to individual transactions
    for (let i = 0; i < rawTransactions.length; i++) {
      try {
        const txHash = await provider.send("eth_sendRawTransaction", [rawTransactions[i]]);
        console.log(`✓ Individual transaction ${i + 1} sent: ${txHash}`);
      } catch (txError) {
        console.error(`❌ Individual transaction ${i + 1} failed:`, txError.message);
      }
    }
  }
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error("Error:", error);
    process.exit(1);
  });