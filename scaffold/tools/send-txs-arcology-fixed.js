const fs = require("fs");
const readline = require("readline");
const hre = require("hardhat");

/**
 * Fixed version that properly uses Arcology's batch transaction method
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
  var txs=new Array();
  const readStream = fs.createReadStream(args[1], 'utf-8');
  let rl = readline.createInterface({input: readStream})
  
  rl.on('line', async (line) => {
    if(line.length==0){
      return
    }
    txs.push(line.split(',')[0])
    if(txs.length>=1000){
      try {
        console.log(`Sending batch of ${txs.length} transactions using arcol_sendRawTransactions...`);
        const result = await provider.send("arcol_sendRawTransactions", [...txs]);
        console.log('Batch sent successfully, result:', result);
        counter=counter+txs.length;
        txs=new Array();
      } catch (error) {
        console.error('Arcology batch method failed:', error.message);
        console.log('Falling back to individual eth_sendRawTransaction calls...');
        
        // Fallback to individual transactions
        for (const tx of txs) {
          try {
            await provider.send("eth_sendRawTransaction", [tx]);
            counter++;
          } catch (txError) {
            console.error(`Individual transaction failed: ${txError.message}`);
          }
        }
        txs=new Array();
      }
    }
  });
  
  rl.on('error', (error) => console.log(error.message));
  
  rl.on('close', async () => {
    if(txs.length>0){
      try {
        console.log(`Sending final batch of ${txs.length} transactions using arcol_sendRawTransactions...`);
        const result = await provider.send("arcol_sendRawTransactions", [...txs]);
        console.log('Final batch sent successfully, result:', result);
        counter=counter+txs.length;
      } catch (error) {
        console.error('Final Arcology batch method failed:', error.message);
        console.log('Falling back to individual eth_sendRawTransaction calls...');
        
        // Fallback to individual transactions
        for (const tx of txs) {
          try {
            await provider.send("eth_sendRawTransaction", [tx]);
            counter++;
          } catch (txError) {
            console.error(`Individual transaction failed: ${txError.message}`);
          }
        }
      }
    }
    console.log(`Transactions Send completed, total ${counter}`);
    console.timeEnd('send time')
  })
}

main().catch((error) => {
  console.error(error);
  process.exitCode = 1;
});
