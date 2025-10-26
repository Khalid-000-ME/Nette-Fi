const fs = require("fs");
const readline = require("readline");
const hre = require("hardhat");

/**
 * Debug version to test Arcology's arn_sendRawTransactions method
 */
async function main() {
  var args = process.argv.splice(2);
  if(args.length<2){
    console.log('Please provide the RPC provider and the file containing the transaction data.');
    return;
  }
  
  let counter=0;
  console.time('send time')
  const provider = new hre.ethers.providers.JsonRpcProvider(args[0]);
  
  // First, let's test if the Arcology method exists
  console.log('Testing Arcology RPC methods...');
  
  try {
    // Test with a small batch first
    console.log('Testing arn_sendRawTransactions with empty array...');
    const testResult = await provider.send("arn_sendRawTransactions", []);
    console.log('arn_sendRawTransactions test result:', testResult);
  } catch (error) {
    console.log('arn_sendRawTransactions test error:', error.message);
    console.log('Full error:', error);
  }
  
  // Test other possible method names
  const alternativeMethods = [
    'arn_sendRawTransactions',
    'arn_sendRawTransactions',
    'arn_sendRawTransaction', // singular
    'eth_sendRawTransactions'
  ];
  
  for (const method of alternativeMethods) {
    try {
      console.log(`Testing ${method}...`);
      const result = await provider.send(method, []);
      console.log(`${method} works! Result:`, result);
    } catch (error) {
      console.log(`${method} error:`, error.message);
    }
  }
  
  // Now try to read and send transactions
  var txs = new Array();
  const readStream = fs.createReadStream(args[1], 'utf-8');
  let rl = readline.createInterface({input: readStream})
  
  rl.on('line', (line) => {
    if(line.length==0){
      return
    }
    txs.push(line.split(',')[0])
    
    // Send smaller batches for testing
    if(txs.length >= 10) {
      console.log(`Sending batch of ${txs.length} transactions...`);
      sendBatch(provider, [...txs])
        .then(result => {
          console.log('Batch sent successfully:', result);
          counter += txs.length;
        })
        .catch(error => {
          console.error('Batch send failed:', error.message);
          console.error('Full error:', error);
        });
      txs = new Array();
    }
  });
  
  rl.on('error', (error) => console.log(error.message));
  
  rl.on('close', () => {
    if(txs.length > 0){
      console.log(`Sending final batch of ${txs.length} transactions...`);
      sendBatch(provider, [...txs])
        .then(result => {
          console.log('Final batch sent successfully:', result);
          counter += txs.length;
          console.log(`Total transactions sent: ${counter}`);
          console.timeEnd('send time');
        })
        .catch(error => {
          console.error('Final batch send failed:', error.message);
          console.error('Full error:', error);
          console.timeEnd('send time');
        });
    } else {
      console.log(`Total transactions sent: ${counter}`);
      console.timeEnd('send time');
    }
  });
}

async function sendBatch(provider, transactions) {
  // Try different method names
  const methods = ['arn_sendRawTransactions', 'arn_sendRawTransactions'];
  
  for (const method of methods) {
    try {
      console.log(`Trying ${method} with ${transactions.length} transactions...`);
      const result = await provider.send(method, transactions);
      console.log(`${method} succeeded!`);
      return result;
    } catch (error) {
      console.log(`${method} failed:`, error.message);
    }
  }
  
  throw new Error('All Arcology batch methods failed');
}

main().catch((error) => {
  console.error('Main error:', error);
  process.exitCode = 1;
});
