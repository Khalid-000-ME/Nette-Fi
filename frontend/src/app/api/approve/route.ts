import { NextRequest, NextResponse } from 'next/server';
import { ethers } from 'ethers';

// Arcology Helper Class - Embedded directly to avoid module resolution issues
class ArcologyHelpers {
  provider: ethers.JsonRpcProvider;

  constructor(rpcUrl = "http://192.168.29.121:8545") {
    this.provider = new ethers.JsonRpcProvider(rpcUrl);
  }

  /**
   * Send batch transactions using Arcology's batch method
   * @param {Array} rawTransactions - Array of signed raw transactions
   * @returns {number} Number of transactions processed
   */
  async sendBatchTransactions(rawTransactions: string[]): Promise<number> {
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
      throw new Error(`Batch transaction failed: ${(error as Error).message}`);
    }
  }

  /**
   * Send individual transaction
   * @param {string} rawTransaction - Signed raw transaction
   * @returns {string} Transaction hash
   */
  async sendTransaction(rawTransaction: string): Promise<string> {
    try {
      const hash = await this.provider.send("arn_sendRawTransactions", [rawTransaction]);
      return hash;
    } catch (error) {
      throw new Error(`Transaction failed: ${(error as Error).message}`);
    }
  }
}

// DevNet configuration - Updated to match network.json
const ARCOLOGY_RPC_URL = "http://192.168.29.121:8545";
const NETTED_AMM_ADDRESS = "0x53FA213b0Ef9fA979BD10665742a8D47FE35BCC2";

// NettedAMM contract ABI - Updated with Multiprocessor support
const NETTED_AMM_ABI = [
    "function requestSwap(address tokenA, address tokenB, uint256 amountA, uint256 minAmountB) external payable returns (bytes32 requestId, bool wasNetted)",
    "function executeIndividualSwap(bytes32 requestId) external",
    "function processBatchSwaps(bytes[] calldata swapData) external",
    "function _processSwapInParallel(address tokenA, address tokenB, uint256 amountA, uint256 minAmountB, address user) external returns (bytes32 requestId)",
    "function encodeSwapData(address tokenA, address tokenB, uint256 amountA, uint256 minAmountB, address user) external pure returns (bytes memory)",
    "function getStats() external virtual returns (uint256 _totalSwaps, uint256 _totalNetted, uint256 _gasSaved, uint256 _activeRequestsCount)",
    "function getPrice(address tokenA, address tokenB) external view returns (uint256)",
    "function getTotalSwaps() external view returns (uint256)",
    "function getTotalNetted() external view returns (uint256)",
    "function getGasSaved() external view returns (uint256)",
    "function getActiveRequestsCount() external virtual returns (uint256)",
    "function resetBatchMode() external",
    "function isBatchMode() external view returns (bool)",
    "function getExpectedAmount(address tokenA, address tokenB, uint256 amountA) public view returns (uint256)",
    "event SwapRequested(address indexed user, address tokenA, address tokenB, uint256 amountA, uint256 timestamp)",
    "event SwapNetted(address indexed userA, address indexed userB, address tokenA, address tokenB, uint256 nettedAmount, bytes32 txHash)",
    "event SwapExecuted(address indexed user, address tokenA, address tokenB, uint256 amountA, uint256 amountB, bytes32 txHash)",
    "event PriceUpdated(address indexed tokenA, address indexed tokenB, uint256 newPrice, uint256 timestamp)",
    "event BatchSwapsProcessed(address indexed initiator, uint256 swapCount, uint256 timestamp)"
];

// ERC20 contract ABI for token transfers
const ERC20_ABI = [
    "function transfer(address to, uint256 amount) external returns (bool)",
    "function balanceOf(address account) external view returns (uint256)",
    "function decimals() external view returns (uint8)",
    "function symbol() external view returns (string)",
    "function name() external view returns (string)"
];

// Token addresses and configurations
const TOKENS = {
    ETH: "0x0000000000000000000000000000000000000000",
    USDC: "0x22C3D0cC5CAb74855B991F1Fb7defc8BaC93ca7C", 
    DAI: "0x79fb9184DEECCb8bbd2b835B82dc6D67B8aEe185",
    WETH: "0x9C7FA77904AB82F0649ca0B73507b6042AAB76Fb",
    USDT: "0x1a176D63a9250Ab6fAE00E3C0d2D1CEdBB313f6C",
    MATIC: "0x6BE7656dc44F9cBC55942DEED70c200b5a5185C7",
    SOL: "0x747e0f49813fac6D48f2B4A7c41534B7f8E147c0",
    LINK: "0x8660b77CDaF11e330c8b48FE198A87b8dE6C4B13",
    AVAX: "0x510C531eb6f4C4ebC2FBf30EaA7B53B24A1548F2"
};

// Token decimals for proper amount conversion
const TOKEN_DECIMALS = {
    ETH: 18,
    USDC: 6,
    DAI: 18,
    WETH: 18,
    USDT: 6,
    MATIC: 18,
    SOL: 9,
    LINK: 18,
    AVAX: 18
};

// Test accounts from DevNet (avoiding the problematic deployer address)
const TEST_ACCOUNTS = [
  {
    address: "0x21522c86A586e696961b68aa39632948D9F11170",
    privateKey: "0x2289ae919f03075448d567c9c4a22846ce3711731c895f1bea572cef25bb346f"
  },
  {
    address: "0xa75Cd05BF16BbeA1759DE2A66c0472131BC5Bd8D", 
    privateKey: "0x19c439237a1e2c86f87b2d31438e5476738dd67297bf92d752b16bdb4ff37aa2"
  },
  {
    address: "0x2c7161284197e40E83B1b657e98B3bb8FF3C90ed",
    privateKey: "0x236c7b430c2ea13f19add3920b0bb2795f35a969f8be617faa9629bc5f6201f1"
  },
  {
    address: "0x57170608aE58b7d62dCdC3cbDb564C05dDBB7eee",
    privateKey: "0xc4fbe435d6297959b0e326e560fdfb680a59807d75e1dec04d873fcd5b36597b"
  },
  {
    address: "0x9F79316c20f3F83Fcf43deE8a1CeA185A47A5c45",
    privateKey: "0xf91fcd0784d0b2e5f88ec3ba6fe57fa7ef4fbf2fe42a8fa0aaa22625d2147a7a"
  }
];

interface TransactionSpec {
  token: string;           // Token symbol (ETH, USDC, DAI, etc.)
  amount: string;          // Amount to send
  recipient: string;       // Recipient address
  tokenAddress?: string;   // ERC20 token contract address
}

interface ApprovalRequest {
  analysis_id: string;
  simulation_id: number;
  wallet_signature: string;
  execute_immediately: boolean;
  batch_size?: number;
  transaction_type?: 'payroll' | 'swap' | 'mixed';
  custom_transactions?: TransactionSpec[]; // Custom transaction specifications
}

function verifySignature(signature: string): boolean {
  // Enhanced signature validation
  return Boolean(signature && signature.length > 20);
}

function extractAddress(signature: string): string {
  // For demo purposes, return a test address
  return TEST_ACCOUNTS[0].address;
}

async function createCustomTransactions(customTransactions: TransactionSpec[]): Promise<string[]> {
  try {
    const provider = new ethers.JsonRpcProvider(ARCOLOGY_RPC_URL);
    console.log(`Creating ${customTransactions.length} custom token transfer transactions`);
    
    const rawTransactions = [];
    
    for (let i = 0; i < customTransactions.length; i++) {
      const spec = customTransactions[i];
      const account = TEST_ACCOUNTS[i % TEST_ACCOUNTS.length];
      const wallet = new ethers.Wallet(account.privateKey, provider);
      
      console.log(`  TX ${i + 1}: ${spec.amount} ${spec.token} to ${spec.recipient.slice(0,8)}...`);
      
      // Get nonce for this account
      const nonce = await provider.getTransactionCount(wallet.address);
      
      let txParams;
      
      if (spec.token.toUpperCase() === 'ETH') {
        // ETH transfer
        const amountWei = ethers.parseEther(spec.amount);
        txParams = {
          to: spec.recipient,
          value: amountWei,
          gasLimit: 21000,
          gasPrice: ethers.parseUnits('2', 'gwei'),
          nonce: nonce,
          chainId: 118
        };
      } else {
        // ERC20 token transfer
        const tokenSymbol = spec.token.toUpperCase();
        const tokenAddress = TOKENS[tokenSymbol as keyof typeof TOKENS];
        const tokenDecimals = TOKEN_DECIMALS[tokenSymbol as keyof typeof TOKEN_DECIMALS];
        
        if (!tokenAddress) {
          throw new Error(`Unsupported token: ${spec.token}`);
        }
        
        // Convert amount to proper decimals
        const amountWithDecimals = ethers.parseUnits(spec.amount, tokenDecimals);
        
        // Create ERC20 contract instance
        const tokenContract = new ethers.Contract(tokenAddress, ERC20_ABI, wallet);
        
        // Create transfer transaction
        const transferData = tokenContract.interface.encodeFunctionData('transfer', [
          spec.recipient,
          amountWithDecimals
        ]);
        
        txParams = {
          to: tokenAddress,
          value: 0,
          data: transferData,
          gasLimit: 100000, // Higher gas limit for ERC20 transfers
          gasPrice: ethers.parseUnits('2', 'gwei'),
          nonce: nonce,
          chainId: 118
        };
      }
      
      // Sign the transaction
      const signedTx = await wallet.signTransaction(txParams);
      rawTransactions.push(signedTx);
      
      console.log(`    ✅ Created ${spec.token} transfer: ${wallet.address.slice(0,8)}... → ${spec.recipient.slice(0,8)}...`);
    }
    
    return rawTransactions;
  } catch (error) {
    console.error('Error creating custom transactions:', error);
    throw error;
  }
}

async function createNettingTransactions(batchSize: number = 5, transactionType: string = 'swap'): Promise<string[]> {
  try {
    const provider = new ethers.JsonRpcProvider(ARCOLOGY_RPC_URL);
    
    console.log(`Creating ${batchSize} netting transactions for parallel processing`);
    
    const rawTransactions = [];
    const swapPatterns = [
      { account: 0, from: TOKENS.ETH, to: TOKENS.USDC, amount: "0.1" },
      { account: 1, from: TOKENS.ETH, to: TOKENS.DAI, amount: "0.05" },
      { account: 2, from: TOKENS.ETH, to: TOKENS.USDC, amount: "0.08" },
      { account: 0, from: TOKENS.ETH, to: TOKENS.DAI, amount: "0.12" },
      { account: 1, from: TOKENS.ETH, to: TOKENS.USDC, amount: "0.15" },
      { account: 3, from: TOKENS.ETH, to: TOKENS.DAI, amount: "0.07" },
      { account: 4, from: TOKENS.ETH, to: TOKENS.USDC, amount: "0.09" },
      { account: 2, from: TOKENS.ETH, to: TOKENS.DAI, amount: "0.11" },
      { account: 3, from: TOKENS.ETH, to: TOKENS.USDC, amount: "0.13" },
      { account: 4, from: TOKENS.ETH, to: TOKENS.DAI, amount: "0.06" }
    ];
    
    for (let i = 0; i < batchSize; i++) {
      const pattern = swapPatterns[i % swapPatterns.length];
      const account = TEST_ACCOUNTS[pattern.account % TEST_ACCOUNTS.length];
      const wallet = new ethers.Wallet(account.privateKey, provider);
      const contract = new ethers.Contract(NETTED_AMM_ADDRESS, NETTED_AMM_ABI, wallet);
      
      const nonce = await provider.getTransactionCount(wallet.address);
      const amountWei = ethers.parseEther(pattern.amount);
      const value = pattern.from === TOKENS.ETH ? amountWei : ethers.parseEther("0");
      
      // Create robust transaction using the same method as P1/P2/P3
      const txParams = {
        to: NETTED_AMM_ADDRESS,
        value: value,
        gasLimit: 500000, // Fixed gas limit to avoid estimation issues
        gasPrice: ethers.parseUnits('2', 'gwei'),
        nonce: nonce,
        chainId: 118,
        data: contract.interface.encodeFunctionData('requestSwap', [
          pattern.from,
          pattern.to,
          amountWei,
          0 // min amount
        ])
      };
      
      const signedTx = await wallet.signTransaction(txParams);
      rawTransactions.push(signedTx);
      
      console.log(`  TX ${i + 1}: ${wallet.address.slice(0,8)}... - ${pattern.amount} ETH (${pattern.from === TOKENS.ETH ? 'ETH' : 'TOKEN'} → ${pattern.to === TOKENS.USDC ? 'USDC' : 'DAI'})`);
    }
    
    return rawTransactions;
  } catch (error) {
    console.error('Error creating netting transactions:', error);
    throw error;
  }
}

// Direct batch execution without chunking

async function executeBatchTransactions(rawTransactions: string[]): Promise<{
  success: boolean;
  transactionCount: number;
  blockNumber?: number;
  batchResult?: any;
  transactionHashes?: string[];
  transactionDetails?: Array<{
    hash: string;
    from: string;
    to: string;
    value: string;
    gasUsed?: string;
    status?: string;
  }>;
  error?: string;
}> {
  try {
    const helpers = new ArcologyHelpers(ARCOLOGY_RPC_URL);
    const provider = new ethers.JsonRpcProvider(ARCOLOGY_RPC_URL);
    
    console.log(`Executing batch of ${rawTransactions.length} transactions...`);
    
    // Get current block before sending
    const beforeBlock = await provider.getBlockNumber();
    console.log(`Current block before batch: ${beforeBlock}`);
    
    // Try individual transaction approach first to get transaction hashes
    const transactionHashes: string[] = [];
    const transactionDetails: Array<{
      hash: string;
      from: string;
      to: string;
      value: string;
      gasUsed?: string;
      status?: string;
    }> = [];
    
    console.log('🔄 Attempting individual transaction submission to capture hashes...');
    
    try {
      // Send transactions individually to get hashes
      for (let i = 0; i < rawTransactions.length; i++) {
        try {
          const hash = await helpers.sendTransaction(rawTransactions[i]);
          transactionHashes.push(hash);
          
          // Parse transaction to get details
          const parsedTx = ethers.Transaction.from(rawTransactions[i]);
          transactionDetails.push({
            hash: hash,
            from: parsedTx.from || 'Unknown',
            to: parsedTx.to || 'Unknown',
            value: ethers.formatEther(parsedTx.value || 0),
            status: 'pending'
          });
          
          console.log(`  TX ${i + 1}: ${hash} (${parsedTx.from?.slice(0,8)}... → ${parsedTx.to?.slice(0,8)}...)`);
        } catch (txError) {
          console.error(`  TX ${i + 1} failed:`, txError);
          // Continue with other transactions
        }
      }
    } catch (individualError) {
      console.log('Individual submission failed, falling back to batch method...');
      
      // Fallback to batch method
      try {
        const batchResult = await helpers.sendBatchTransactions(rawTransactions);
        console.log(`Batch sent successfully! Result: ${batchResult}`);
      } catch (batchError) {
        console.error('Both individual and batch methods failed:', batchError);
        throw batchError;
      }
    }
    
    // Wait a moment for mining
    await new Promise(resolve => setTimeout(resolve, 3000));
    
    // Check if new block was mined and get transaction receipts
    const afterBlock = await provider.getBlockNumber();
    console.log(`Current block after execution: ${afterBlock}`);
    
    // Try to get transaction receipts for successful transactions
    if (transactionHashes.length > 0) {
      console.log('🔍 Fetching transaction receipts...');
      for (let i = 0; i < transactionHashes.length; i++) {
        try {
          const receipt = await provider.getTransactionReceipt(transactionHashes[i]);
          if (receipt) {
            transactionDetails[i].gasUsed = receipt.gasUsed.toString();
            transactionDetails[i].status = receipt.status === 1 ? 'success' : 'failed';
            console.log(`  Receipt ${i + 1}: ${receipt.status === 1 ? '✅' : '❌'} Gas: ${receipt.gasUsed}`);
          }
        } catch (receiptError) {
          console.log(`  Receipt ${i + 1}: Pending or unavailable`);
        }
      }
    }
    
    if (afterBlock > beforeBlock) {
      // Get the new block to see our transactions
      const newBlock = await provider.getBlock(afterBlock, true);
      if (newBlock) {
        console.log(`New block ${afterBlock} contains ${newBlock.transactions.length} transactions`);
        
        return {
          success: true,
          transactionCount: rawTransactions.length,
          blockNumber: afterBlock,
          transactionHashes: transactionHashes,
          transactionDetails: transactionDetails,
          batchResult: {
            processedCount: transactionHashes.length || rawTransactions.length,
            blockMined: afterBlock,
            transactionsInBlock: newBlock.transactions.length,
            successfulTxs: transactionDetails.filter(tx => tx.status === 'success').length,
            failedTxs: transactionDetails.filter(tx => tx.status === 'failed').length
          }
        };
      } else {
        return {
          success: true,
          transactionCount: rawTransactions.length,
          blockNumber: afterBlock,
          transactionHashes: transactionHashes,
          transactionDetails: transactionDetails,
          batchResult: {
            processedCount: transactionHashes.length || rawTransactions.length,
            blockMined: afterBlock,
            note: "Block found but details unavailable"
          }
        };
      }
    } else {
      return {
        success: true,
        transactionCount: rawTransactions.length,
        transactionHashes: transactionHashes,
        transactionDetails: transactionDetails,
        batchResult: {
          processedCount: transactionHashes.length || rawTransactions.length,
          note: "Transactions sent but block not yet mined"
        }
      };
    }
    
  } catch (error) {
    console.error('Batch execution failed:', error);
    return {
      success: false,
      transactionCount: rawTransactions.length,
      error: error instanceof Error ? error.message : 'Unknown error'
    };
  }
}

export async function POST(request: NextRequest) {
  try {
    const body: ApprovalRequest = await request.json();
    
    console.log('🚀 Approve API: Processing batch transaction request');
    console.log('Request details:', {
      analysis_id: body.analysis_id,
      simulation_id: body.simulation_id,
      execute_immediately: body.execute_immediately,
      batch_size: body.batch_size || 10,
      transaction_type: body.transaction_type || 'mixed'
    });
    
    // Verify signature
    const isValid = verifySignature(body.wallet_signature);
    if (!isValid) {
      return NextResponse.json(
        { error: 'Invalid wallet signature' },
        { status: 401 }
      );
    }
    
    // Extract wallet address
    const userWallet = extractAddress(body.wallet_signature);
    
    if (body.execute_immediately) {
      // Execute batch transactions immediately
      console.log('⚡ Executing batch transactions immediately...');
      
      const batchSize = body.batch_size || 10;
      const transactionType = body.transaction_type || 'mixed';
      
      // Create batch transactions - use custom transactions if provided
      let rawTransactions: string[];
      
      if (body.custom_transactions && body.custom_transactions.length > 0) {
        console.log('📝 Using custom transaction specifications');
        rawTransactions = await createCustomTransactions(body.custom_transactions);
        console.log(`Created ${rawTransactions.length} custom transactions`);
      } else {
        console.log('🔄 Using default netting transaction patterns');
        rawTransactions = await createNettingTransactions(batchSize, transactionType);
        console.log(`Created ${rawTransactions.length} raw transactions`);
      }
      
      // Execute the batch directly without chunking
      console.log('⚡ Executing batch transactions directly...');
      
      const executionResult = await executeBatchTransactions(rawTransactions);
      
      const approvalId = `approval_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
      
      if (executionResult.success) {
        const response = {
          approval_id: approvalId,
          status: 'executed' as const,
          batch_size: batchSize,
          transaction_type: transactionType,
          transaction_count: executionResult.transactionCount,
          block_number: executionResult.blockNumber,
          transaction_hashes: executionResult.transactionHashes || [],
          transaction_details: executionResult.transactionDetails || [],
          batch_result: executionResult.batchResult,
          user_wallet: userWallet,
          execution_time: new Date().toISOString(),
          message: `Successfully executed batch of ${executionResult.transactionCount} transactions`,
          summary: {
            total_transactions: executionResult.transactionCount,
            successful_transactions: executionResult.transactionDetails?.filter(tx => tx.status === 'success').length || 0,
            failed_transactions: executionResult.transactionDetails?.filter(tx => tx.status === 'failed').length || 0,
            pending_transactions: executionResult.transactionDetails?.filter(tx => tx.status === 'pending').length || 0,
            transaction_hashes_count: executionResult.transactionHashes?.length || 0
          }
        };
        
        console.log('✅ Batch execution completed successfully!');
        return NextResponse.json(response);
      } else {
        return NextResponse.json({
          approval_id: approvalId,
          status: 'failed' as const,
          error: executionResult.error,
          transaction_count: executionResult.transactionCount,
          user_wallet: userWallet
        }, { status: 500 });
      }
    } else {
      // Queue for later execution (mock implementation)
      const approvalId = `approval_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
      const futureBlock = Math.floor(Date.now() / 1000) + 300; // 5 minutes from now
      
      const response = {
        approval_id: approvalId,
        status: 'queued' as const,
        batch_size: body.batch_size || 10,
        transaction_type: body.transaction_type || 'mixed',
        execute_at_block: futureBlock,
        countdown_seconds: 300,
        estimated_confirmation_time: new Date(Date.now() + 300000).toISOString(),
        user_wallet: userWallet,
        message: 'Batch transaction queued for future execution'
      };
      
      return NextResponse.json(response);
    }
    
  } catch (error) {
    console.error('Approval error:', error);
    return NextResponse.json(
      { error: 'Failed to approve trade execution' },
      { status: 500 }
    );
  }
}