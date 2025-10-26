// helpers.js - Arcology Devnet Helper Functions
const { ethers } = require("ethers");

/**
 * Arcology Devnet Helper Functions
 * Provides utility functions for interacting with Arcology devnet
 */

class ArcologyHelpers {
  constructor(rpcUrl = "http://192.168.29.121:8545") {
    this.provider = new ethers.providers.JsonRpcProvider(rpcUrl);
  }

  /**
   * Scan blocks for transactions in a given range
   * @param {number} startBlock - Starting block number
   * @param {number} endBlock - Ending block number
   * @param {boolean} verbose - Show detailed output
   * @returns {Array} Array of blocks with transaction information
   */
  async scanBlocksForTransactions(startBlock = 0, endBlock = null, verbose = false) {
    if (!endBlock) {
      endBlock = await this.provider.getBlockNumber();
    }

    const blocksWithTxs = [];
    
    if (verbose) {
      console.log(`Scanning blocks ${startBlock} to ${endBlock} for transactions...`);
      console.log('Block | Transactions | Hashes');
      console.log('------|-------------|--------');
    }

    for (let i = startBlock; i <= endBlock; i++) {
      try {
        const block = await this.provider.getBlock(i);
        
        if (block.transactions.length > 0) {
          const blockWithTxs = await this.provider.getBlockWithTransactions(i);
          blocksWithTxs.push({
            blockNumber: i,
            transactionCount: block.transactions.length,
            transactions: blockWithTxs.transactions,
            timestamp: block.timestamp,
            hash: block.hash
          });

          if (verbose) {
            const hashes = blockWithTxs.transactions.map(tx => tx.hash.substring(0, 10) + '...').join(', ');
            console.log(`${i.toString().padStart(5)} | ${block.transactions.length.toString().padStart(11)} | ${hashes}`);
          }
        } else if (verbose && i % 50 === 0) {
          console.log(`${i.toString().padStart(5)} | ${block.transactions.length.toString().padStart(11)} | (empty)`);
        }
      } catch (error) {
        if (verbose) {
          console.log(`${i.toString().padStart(5)} | ERROR       | ${error.message}`);
        }
        break;
      }
    }

    return blocksWithTxs;
  }

  /**
   * Get all transaction hashes from blocks with transactions
   * @param {number} startBlock - Starting block number
   * @param {number} endBlock - Ending block number
   * @returns {Array} Array of all transaction hashes
   */
  async getAllTransactionHashes(startBlock = 0, endBlock = null) {
    const blocksWithTxs = await this.scanBlocksForTransactions(startBlock, endBlock, false);
    const allHashes = [];

    blocksWithTxs.forEach(block => {
      block.transactions.forEach(tx => {
        allHashes.push({
          hash: tx.hash,
          blockNumber: block.blockNumber,
          from: tx.from,
          to: tx.to,
          value: tx.value,
          nonce: tx.nonce
        });
      });
    });

    return allHashes;
  }

  /**
   * Send batch transactions using Arcology's batch method
   * @param {Array} rawTransactions - Array of signed raw transactions
   * @returns {number} Number of transactions processed
   */
  async sendBatchTransactions(rawTransactions) {
    if (!Array.isArray(rawTransactions) || rawTransactions.length === 0) {
      throw new Error("rawTransactions must be a non-empty array");
    }

    if (rawTransactions.length > 5000) {
      throw new Error("Batch size cannot exceed 5,000 transactions");
    }

    try {
      const result = await this.provider.send("arn_sendRawTransactions", rawTransactions);
      return result; // Returns count of processed transactions
    } catch (error) {
      throw new Error(`Batch transaction failed: ${error.message}`);
    }
  }

  /**
   * Send individual transaction
   * @param {string} rawTransaction - Signed raw transaction
   * @returns {string} Transaction hash
   */
  async sendTransaction(rawTransaction) {
    try {
      const hash = await this.provider.send("eth_sendRawTransaction", [rawTransaction]);
      return hash;
    } catch (error) {
      throw new Error(`Transaction failed: ${error.message}`);
    }
  }

  /**
   * Get transaction details by hash
   * @param {string} txHash - Transaction hash
   * @returns {Object} Transaction details
   */
  async getTransactionDetails(txHash) {
    try {
      const tx = await this.provider.getTransaction(txHash);
      const receipt = await this.provider.getTransactionReceipt(txHash);
      
      return {
        transaction: tx,
        receipt: receipt,
        status: receipt ? (receipt.status === 1 ? 'SUCCESS' : 'FAILED') : 'PENDING'
      };
    } catch (error) {
      throw new Error(`Failed to get transaction details: ${error.message}`);
    }
  }

  /**
   * Monitor network for new blocks and transactions
   * @param {number} intervalMs - Monitoring interval in milliseconds
   * @param {Function} callback - Callback function for new blocks
   */
  async monitorNetwork(intervalMs = 5000, callback = null) {
    let lastBlockNumber = await this.provider.getBlockNumber();
    console.log(`Starting network monitoring from block ${lastBlockNumber}`);

    setInterval(async () => {
      try {
        const currentBlock = await this.provider.getBlockNumber();
        
        if (currentBlock > lastBlockNumber) {
          for (let i = lastBlockNumber + 1; i <= currentBlock; i++) {
            const block = await this.provider.getBlockWithTransactions(i);
            
            const blockInfo = {
              blockNumber: i,
              transactionCount: block.transactions.length,
              transactions: block.transactions,
              timestamp: new Date(block.timestamp * 1000).toISOString()
            };

            console.log(`New Block ${i}: ${block.transactions.length} transactions`);
            
            if (block.transactions.length > 0) {
              block.transactions.forEach((tx, idx) => {
                console.log(`  TX ${idx + 1}: ${tx.hash}`);
              });
            }

            if (callback) {
              callback(blockInfo);
            }
          }
          
          lastBlockNumber = currentBlock;
        }
      } catch (error) {
        console.error('Monitoring error:', error.message);
      }
    }, intervalMs);
  }

  /**
   * Get network statistics
   * @returns {Object} Network statistics
   */
  async getNetworkStats() {
    try {
      const latestBlock = await this.provider.getBlockNumber();
      const blocksWithTxs = await this.scanBlocksForTransactions(0, latestBlock, false);
      
      const totalTransactions = blocksWithTxs.reduce((sum, block) => sum + block.transactionCount, 0);
      const emptyBlocks = latestBlock + 1 - blocksWithTxs.length;

      return {
        latestBlockNumber: latestBlock,
        totalBlocks: latestBlock + 1,
        blocksWithTransactions: blocksWithTxs.length,
        emptyBlocks: emptyBlocks,
        totalTransactions: totalTransactions,
        averageTxPerBlock: blocksWithTxs.length > 0 ? (totalTransactions / blocksWithTxs.length).toFixed(2) : 0,
        networkHealth: 'ACTIVE'
      };
    } catch (error) {
      throw new Error(`Failed to get network stats: ${error.message}`);
    }
  }

  /**
   * Create and sign multiple transactions for batch processing
   * @param {Object} wallet - Ethers wallet instance
   * @param {Array} recipients - Array of recipient addresses
   * @param {string} value - Value to send (in ETH)
   * @returns {Array} Array of signed raw transactions
   */
  async createBatchTransactions(wallet, recipients, value = "0.001") {
    const nonce = await this.provider.getTransactionCount(wallet.address);
    const gasPrice = await this.provider.getGasPrice();
    const rawTransactions = [];

    for (let i = 0; i < recipients.length; i++) {
      const tx = {
        to: recipients[i],
        value: ethers.utils.parseEther(value),
        nonce: nonce + i,
        gasLimit: 21000,
        gasPrice: gasPrice
      };

      const signedTx = await wallet.signTransaction(tx);
      rawTransactions.push(signedTx);
    }

    return rawTransactions;
  }
}

// Export for use in other files
module.exports = ArcologyHelpers;

// Example usage if run directly
if (require.main === module) {
  async function example() {
    const helpers = new ArcologyHelpers();
    
    console.log("=== Arcology Network Statistics ===");
    const stats = await helpers.getNetworkStats();
    console.log(stats);
    
    console.log("\n=== Scanning for Transactions ===");
    const txHashes = await helpers.getAllTransactionHashes(50, 70);
    console.log(`Found ${txHashes.length} transactions:`);
    txHashes.forEach((tx, i) => {
      console.log(`${i + 1}. ${tx.hash} (Block ${tx.blockNumber})`);
    });
  }
  
  // Uncomment to run example
  // example().catch(console.error);
}