const fs = require("fs");
const readline = require("readline");
const hre = require("hardhat");

/**
 * This script reads in a file containing raw transaction data, splits the data into individual transactions,
 * and sends them in batches of 1000 to the Arcology network.
 * 
 * @async
 * @function main
 * @returns {Promise<void>} A Promise that resolves when the transactions are sent.
 */
async function main() {
  var args = process.argv.splice(2);
  if(args.length<2){
    console.log('Please provide the RPC provider and the file containing the transaction data.');
    return;
  }
  let counter=0;
  let lineNumber = 0;
  const START_TRANSACTION = 501; // Start from transaction 501
  const END_TRANSACTION = 700;   // End at transaction 600
  const MAX_TRANSACTIONS = END_TRANSACTION - START_TRANSACTION + 1; // Process 100 transactions (501-600)
  console.time('send time')
  const provider = new hre.ethers.providers.JsonRpcProvider(args[0]);
  var txs=new Array();
  const readStream = fs.createReadStream(args[1], 'utf-8');
  let rl = readline.createInterface({input: readStream})
  
  rl.on('line', async (line) => {
    lineNumber++;
    
    if(line.length==0){
      return
    }
    
    // Skip transactions before START_TRANSACTION
    if(lineNumber < START_TRANSACTION) {
      return;
    }
    
    // Stop reading if we've reached the end transaction
    if(lineNumber > END_TRANSACTION) {
      console.log(`Reached end transaction ${END_TRANSACTION}, stopping...`);
      rl.close();
      return;
    }
    
    // Stop reading if we've reached the limit
    if(counter + txs.length >= MAX_TRANSACTIONS) {
      console.log(`Reached limit of ${MAX_TRANSACTIONS} transactions, stopping...`);
      rl.close();
      return;
    }
    
    txs.push(line.split(',')[0])
    
    // Send in smaller batches or when we reach the limit
    if(txs.length >= 50 || counter + txs.length >= MAX_TRANSACTIONS){
      try {
        console.log(`Sending batch of ${txs.length} transactions...`);
        
        // Send individual transactions to get hashes
        const hashes = [];
        for (let i = 0; i < txs.length; i++) {
          try {
            const hash = await provider.send("arn_sendRawTransactions", [txs[i]]);
            hashes.push(hash);
            console.log(`Transaction ${START_TRANSACTION + counter + i}: ${hash}`);
          } catch (txError) {
            console.error(`Failed to send transaction ${START_TRANSACTION + counter + i}:`, txError.message);
          }
        }
        
        counter += txs.length;
        console.log(`Successfully sent ${counter} transactions so far`);
        console.log(`Batch hashes: ${hashes.join(', ')}`);
        txs = new Array();
        
        // Stop if we've reached the limit
        if(counter >= MAX_TRANSACTIONS) {
          console.log(`Reached limit of ${MAX_TRANSACTIONS} transactions, stopping...`);
          rl.close();
          return;
        }
      } catch (error) {
        console.error('Error sending batch:', error.message);
      }
    }
  });
  
  rl.on('error', (error) => console.log(error.message));
  
  rl.on('close', async () => {
    if(txs.length>0 && counter < MAX_TRANSACTIONS){
      try {
        console.log(`Sending final batch of ${txs.length} transactions...`);
        
        // Send individual transactions to get hashes
        const hashes = [];
        for (let i = 0; i < txs.length; i++) {
          try {
            const hash = await provider.send("eth_sendRawTransaction", [txs[i]]);
            hashes.push(hash);
            console.log(`Final transaction ${START_TRANSACTION + counter + i}: ${hash}`);
          } catch (txError) {
            console.error(`Failed to send final transaction ${START_TRANSACTION + counter + i}:`, txError.message);
          }
        }
        
        counter += txs.length;
        console.log(`Successfully sent final batch`);
        console.log(`Final batch hashes: ${hashes.join(', ')}`);
      } catch (error) {
        console.error('Error sending final batch:', error.message);
      }
    }
    console.log(`Transactions Send completed, processed transactions ${START_TRANSACTION}-${START_TRANSACTION + counter - 1}, total: ${counter}`);
    console.timeEnd('send time')
  })
}

// We recommend this pattern to be able to use async/await everywhere
// and properly handle errors.
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
