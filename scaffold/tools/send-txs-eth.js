const fs = require("fs");
const readline = require("readline");
const hre = require("hardhat");

/**
 * This script reads in a file containing raw transaction data and sends them individually
 * using standard Ethereum eth_sendRawTransaction method.
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
  let successful=0;
  let failed=0;
  console.time('send time')
  const provider = new hre.ethers.providers.JsonRpcProvider(args[0]);
  const readStream = fs.createReadStream(args[1], 'utf-8');
  let rl = readline.createInterface({input: readStream})
  
  const sendTransaction = async (rawTx) => {
    try {
      const result = await provider.send("eth_sendRawTransaction", [rawTx]);
      console.log(`Transaction ${counter + 1} sent: ${result}`);
      successful++;
      return result;
    } catch (error) {
      console.error(`Transaction ${counter + 1} failed:`, error.message);
      failed++;
      return null;
    }
  };
  
  rl.on('line', async (line) => {
    if(line.length==0){
      return
    }
    const rawTx = line.split(',')[0];
    counter++;
    await sendTransaction(rawTx);
    
    // Add a small delay to avoid overwhelming the network
    if (counter % 10 === 0) {
      console.log(`Processed ${counter} transactions (${successful} successful, ${failed} failed)`);
      await new Promise(resolve => setTimeout(resolve, 100)); // 100ms delay every 10 transactions
    }
  });
  
  rl.on('error', (error) => console.log(error.message));
  
  rl.on('close', () => {
    console.log(`\nTransaction sending completed!`);
    console.log(`Total processed: ${counter}`);
    console.log(`Successful: ${successful}`);
    console.log(`Failed: ${failed}`);
    console.timeEnd('send time')
  })
}

// We recommend this pattern to be able to use async/await everywhere
// and properly handle errors.
main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
