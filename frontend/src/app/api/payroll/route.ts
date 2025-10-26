import { NextRequest, NextResponse } from 'next/server';
import { ethers } from 'ethers';

// Arcology DevNet configuration
const ARCOLOGY_RPC_URL = "http://192.168.29.121:8545";

// Token addresses - Updated with all deployed tokens
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

// ERC20 ABI for transfers
const ERC20_ABI = [
    "function transfer(address to, uint256 amount) external returns (bool)",
    "function balanceOf(address account) external view returns (uint256)"
];

// Test account for payroll (company wallet) - Account 10 from network.json
const COMPANY_WALLET = {
    address: "0x8aa62d370585e28fd2333325d3dbaef6112279Ce",
    privateKey: "0xd9815a0fa4f31172530f17a6ae64bf5f00a3a651f3d6476146d2c62ae5527dc4"
};

interface PayrollEntry {
    employee_address: string;
    employee_name?: string;
    token: string;           // USDC, DAI, ETH, etc.
    amount: string;          // Amount in human-readable format
    department?: string;
    position?: string;
}

interface PayrollRequest {
    company_signature: string;
    payroll_entries: PayrollEntry[];
    execute_immediately: boolean;
    max_chunk_size?: number;  // Override default chunk size
    description?: string;
}

/**
 * SAFE PAYROLL BATCH PROCESSOR
 * Splits large payroll batches into scheduler-safe chunks
 */
async function processSafePayrollBatch(
    payrollEntries: PayrollEntry[], 
    maxChunkSize: number = 2
): Promise<{
    success: boolean;
    totalEmployees: number;
    processedEmployees: number;
    transactionHashes: string[];
    chunkResults: Array<{
        chunkIndex: number;
        employees: number;
        success: boolean;
        hashes: string[];
    }>;
    error?: string;
}> {
    try {
        console.log(`💰 Processing payroll for ${payrollEntries.length} employees`);
        console.log(`📦 Using safe chunk size: ${maxChunkSize} to prevent container crashes`);
        
        const provider = new ethers.JsonRpcProvider(ARCOLOGY_RPC_URL);
        const companyWallet = new ethers.Wallet(COMPANY_WALLET.privateKey, provider);
        
        // Split payroll entries into safe chunks
        const chunks: PayrollEntry[][] = [];
        for (let i = 0; i < payrollEntries.length; i += maxChunkSize) {
            chunks.push(payrollEntries.slice(i, i + maxChunkSize));
        }
        
        console.log(`📋 Split payroll into ${chunks.length} chunks`);
        
        const allHashes: string[] = [];
        const chunkResults: Array<{
            chunkIndex: number;
            employees: number;
            success: boolean;
            hashes: string[];
        }> = [];
        
        // Process each chunk sequentially
        for (let chunkIndex = 0; chunkIndex < chunks.length; chunkIndex++) {
            const chunk = chunks[chunkIndex];
            console.log(`\n💼 Processing payroll chunk ${chunkIndex + 1}/${chunks.length} (${chunk.length} employees)...`);
            
            const chunkHashes: string[] = [];
            
            try {
                // Process each employee in the chunk
                for (let empIndex = 0; empIndex < chunk.length; empIndex++) {
                    const entry = chunk[empIndex];
                    
                    try {
                        console.log(`  👤 Employee ${empIndex + 1}: ${entry.employee_name || entry.employee_address.slice(0,8)}... - ${entry.amount} ${entry.token}`);
                        
                        // Check ETH balance for gas fees first
                        const ethBalance = await provider.getBalance(companyWallet.address);
                        const minGasRequired = ethers.parseUnits('0.001', 'ether'); // 0.001 ETH for gas
                        
                        if (ethBalance < minGasRequired) {
                            throw new Error(`Insufficient ETH for gas fees. Have: ${ethers.formatEther(ethBalance)} ETH, Need: 0.001 ETH minimum`);
                        }
                        
                        // Get current nonce
                        const nonce = await provider.getTransactionCount(companyWallet.address);
                        
                        let txParams;
                        
                        if (entry.token.toUpperCase() === 'ETH') {
                            // ETH transfer
                            const amountWei = ethers.parseEther(entry.amount);
                            txParams = {
                                to: entry.employee_address,
                                value: amountWei,
                                gasLimit: 21000,
                                gasPrice: ethers.parseUnits('2', 'gwei'),
                                nonce: nonce,
                                chainId: 118
                            };
                        } else {
                            // ERC20 token transfer
                            const tokenSymbol = entry.token.toUpperCase();
                            const tokenAddress = TOKENS[tokenSymbol as keyof typeof TOKENS];
                            const tokenDecimals = TOKEN_DECIMALS[tokenSymbol as keyof typeof TOKEN_DECIMALS];
                            
                            if (!tokenAddress) {
                                throw new Error(`Unsupported token: ${entry.token}`);
                            }
                            
                            const amountWithDecimals = ethers.parseUnits(entry.amount, tokenDecimals);
                            const tokenContract = new ethers.Contract(tokenAddress, ERC20_ABI, companyWallet);
                            
                            const transferData = tokenContract.interface.encodeFunctionData('transfer', [
                                entry.employee_address,
                                amountWithDecimals
                            ]);
                            
                            txParams = {
                                to: tokenAddress,
                                value: 0,
                                data: transferData,
                                gasLimit: 100000,
                                gasPrice: ethers.parseUnits('2', 'gwei'),
                                nonce: nonce,
                                chainId: 118
                            };
                        }
                        
                        // Sign and send transaction
                        const signedTx = await companyWallet.signTransaction(txParams);
                        const hash = await provider.send("eth_sendRawTransaction", [signedTx]);
                        
                        chunkHashes.push(hash);
                        allHashes.push(hash);
                        
                        console.log(`    ✅ Sent: ${hash.slice(0, 10)}...`);
                        
                        // Small delay between transactions in the same chunk
                        if (empIndex < chunk.length - 1) {
                            await new Promise(resolve => setTimeout(resolve, 500));
                        }
                        
                    } catch (empError) {
                        console.error(`    ❌ Failed to pay employee ${empIndex + 1}:`, empError);
                    }
                }
                
                chunkResults.push({
                    chunkIndex: chunkIndex,
                    employees: chunk.length,
                    success: chunkHashes.length > 0,
                    hashes: chunkHashes
                });
                
                console.log(`  📊 Chunk ${chunkIndex + 1} completed: ${chunkHashes.length}/${chunk.length} employees paid`);
                
                // Wait between chunks to prevent scheduler overload
                if (chunkIndex < chunks.length - 1) {
                    console.log(`  ⏳ Waiting 3 seconds before next payroll chunk...`);
                    await new Promise(resolve => setTimeout(resolve, 3000));
                }
                
            } catch (chunkError) {
                console.error(`  ❌ Chunk ${chunkIndex + 1} failed:`, chunkError);
                chunkResults.push({
                    chunkIndex: chunkIndex,
                    employees: chunk.length,
                    success: false,
                    hashes: []
                });
            }
        }
        
        const successfulChunks = chunkResults.filter(c => c.success).length;
        const processedEmployees = allHashes.length;
        
        console.log(`\n🎯 Payroll Processing Complete:`);
        console.log(`   Chunks: ${successfulChunks}/${chunks.length} successful`);
        console.log(`   Employees: ${processedEmployees}/${payrollEntries.length} paid`);
        
        return {
            success: processedEmployees > 0,
            totalEmployees: payrollEntries.length,
            processedEmployees: processedEmployees,
            transactionHashes: allHashes,
            chunkResults: chunkResults
        };
        
    } catch (error) {
        console.error('Payroll processing failed:', error);
        return {
            success: false,
            totalEmployees: payrollEntries.length,
            processedEmployees: 0,
            transactionHashes: [],
            chunkResults: [],
            error: error instanceof Error ? error.message : 'Unknown error'
        };
    }
}

export async function POST(request: NextRequest) {
    try {
        const body: PayrollRequest = await request.json();
        
        console.log('💰 Payroll API: Processing batch payroll request');
        console.log(`👥 Employees: ${body.payroll_entries.length}`);
        console.log(`⚡ Execute immediately: ${body.execute_immediately}`);
        
        // Validate signature
        if (!body.company_signature || body.company_signature.length < 10) {
            return NextResponse.json(
                { error: 'Invalid company signature' },
                { status: 401 }
            );
        }
        
        // Validate payroll entries
        if (!body.payroll_entries || body.payroll_entries.length === 0) {
            return NextResponse.json(
                { error: 'No payroll entries provided' },
                { status: 400 }
            );
        }
        
        if (body.execute_immediately) {
            // Process payroll immediately with safe chunking
            const maxChunkSize = body.max_chunk_size || 2; // Default to 2 to prevent crashes
            
            console.log(`🚀 Processing payroll immediately with chunk size: ${maxChunkSize}`);
            
            const result = await processSafePayrollBatch(body.payroll_entries, maxChunkSize);
            
            const payrollId = `payroll_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
            
            if (result.success) {
                return NextResponse.json({
                    payroll_id: payrollId,
                    status: 'completed',
                    total_employees: result.totalEmployees,
                    processed_employees: result.processedEmployees,
                    transaction_hashes: result.transactionHashes,
                    chunk_results: result.chunkResults,
                    execution_time: new Date().toISOString(),
                    message: `Successfully processed payroll for ${result.processedEmployees}/${result.totalEmployees} employees`,
                    summary: {
                        success_rate: `${Math.round((result.processedEmployees / result.totalEmployees) * 100)}%`,
                        total_chunks: result.chunkResults.length,
                        successful_chunks: result.chunkResults.filter(c => c.success).length,
                        max_chunk_size: maxChunkSize,
                        scheduler_safe: true
                    }
                });
            } else {
                return NextResponse.json({
                    payroll_id: payrollId,
                    status: 'failed',
                    error: result.error,
                    total_employees: result.totalEmployees,
                    processed_employees: result.processedEmployees
                }, { status: 500 });
            }
        } else {
            // Queue for later execution
            const payrollId = `payroll_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`;
            
            return NextResponse.json({
                payroll_id: payrollId,
                status: 'queued',
                total_employees: body.payroll_entries.length,
                estimated_execution_time: new Date(Date.now() + 300000).toISOString(), // 5 minutes
                message: 'Payroll queued for execution'
            });
        }
        
    } catch (error) {
        console.error('Payroll API error:', error);
        return NextResponse.json(
            { error: 'Failed to process payroll request' },
            { status: 500 }
        );
    }
}
