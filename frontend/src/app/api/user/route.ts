import { NextRequest, NextResponse } from 'next/server';
import { ethers } from 'ethers';

// UserContract ABI (matching deployed Arcology-compatible contract)
// NOTE: Some functions are non-view due to Arcology concurrent counter access tracking
const USER_CONTRACT_ABI = [
    "function registerUser() external",
    "function getUserStats(address user) external returns (uint256 totalTransactions, uint256 totalGasSaved, uint256 totalAmountProcessed, uint256 averageGasSavings, uint256 lastTransactionTime, bool isRegistered)",
    "function getUserTransactionHistory(address user) external view returns (bytes32[] memory)",
    "function getUserScheduledTransactions(address user) external view returns (bytes32[] memory)",
    "function scheduleTransaction(uint256 scheduledTime, uint256 estimatedGasSavings, uint256 totalAmount, uint8 employeeCount) external returns (bytes32 transactionId)",
    "function getScheduledTransaction(bytes32 transactionId) external view returns (address user, uint256 scheduledTime, uint256 estimatedGasSavings, uint256 totalAmount, uint8 employeeCount, bool executed, bool cancelled, uint256 createdAt)",
    "function getPayrollBatch(bytes32 batchId) external view returns (address employer, uint256 totalEmployees, uint256 totalAmount, uint256 gasSaved, uint256 executedAt, string memory status)",
    "function getGlobalStats() external returns (uint256 _totalUsers, uint256 _totalTransactionsProcessed, uint256 _totalGasSavedGlobally, uint256 _totalValueProcessed, uint256 _averageGasSavingsPerTransaction)",
    "function getUserSavingsPercentage(address user) external returns (uint256)",
    "function getTotalUsers() external returns (uint256)",
    "function getTotalTransactionsProcessed() external returns (uint256)",
    "function getTotalGasSavedGlobally() external returns (uint256)",
    "function getTotalValueProcessed() external returns (uint256)"
];

// Contract configuration
const ARCOLOGY_RPC_URL = "http://192.168.29.121:8545";
const USER_CONTRACT_ADDRESS = "0x6999E8Ed409926A3A75aa594E8af136beFc31C3e";
const CHAIN_ID = 118;

// Initialize provider and contract
let provider: ethers.JsonRpcProvider;
let userContract: ethers.Contract | null = null;

try {
    provider = new ethers.JsonRpcProvider(ARCOLOGY_RPC_URL);
    
    // Create a dummy signer for read-only operations (Arcology concurrent counters require signer)
    const dummyPrivateKey = "0xd9815a0fa4f31172530f17a6ae64bf5f00a3a651f3d6476146d2c62ae5527dc4"; // Account 10
    const signer = new ethers.Wallet(dummyPrivateKey, provider);
    
    userContract = new ethers.Contract(USER_CONTRACT_ADDRESS, USER_CONTRACT_ABI, signer);
    console.log('📊 User API: Connected to deployed UserContract at', USER_CONTRACT_ADDRESS);
    
    // Test if contract exists by checking code
    provider.getCode(USER_CONTRACT_ADDRESS).then(code => {
        if (code === '0x') {
            console.error('❌ No contract deployed at', USER_CONTRACT_ADDRESS);
        } else {
            console.log('✅ Contract code found at', USER_CONTRACT_ADDRESS, 'Length:', code.length);
        }
    }).catch(err => {
        console.error('❌ Failed to check contract code:', err);
    });
} catch (error) {
    console.warn('Failed to initialize blockchain connection:', error);
}

interface UserRequest {
    action: string;
    userAddress?: string;
    transactionId?: string;
    batchId?: string;
    scheduledTime?: number;
    estimatedGasSavings?: number;
    totalAmount?: number;
    employeeCount?: number;
}

export async function GET(request: NextRequest) {
    try {
        const { searchParams } = new URL(request.url);
        const action = searchParams.get('action') || 'get_stats';
        const userAddress = searchParams.get('userAddress');
        const transactionId = searchParams.get('transactionId');
        const batchId = searchParams.get('batchId');

        console.log(`📊 User API request: ${action} for ${userAddress}`);

        if (!userContract) {
            return NextResponse.json({
                error: 'Blockchain connection not available',
                fallback: true,
                mockData: getMockUserData(action, userAddress || undefined)
            });
        }

        switch (action) {
            case 'get_stats':
                if (!userAddress) {
                    return NextResponse.json({ error: 'User address required' }, { status: 400 });
                }

                try {
                    // Check if contract exists first
                    if (!userContract) {
                        throw new Error('UserContract not initialized');
                    }
                    
                    console.log('🔍 Calling getUserStats for:', userAddress);
                    const stats = await userContract.getUserStats(userAddress);
                    console.log('✅ getUserStats result:', stats);
                    
                    console.log('🔍 Calling getUserSavingsPercentage for:', userAddress);
                    const savingsPercentage = await userContract.getUserSavingsPercentage(userAddress);
                    console.log('✅ getUserSavingsPercentage result:', savingsPercentage);
                    
                    return NextResponse.json({
                        success: true,
                        userAddress,
                        stats: {
                            totalTransactions: stats.totalTransactions.toString(),
                            totalGasSaved: stats.totalGasSaved.toString(),
                            totalAmountProcessed: ethers.formatEther(stats.totalAmountProcessed),
                            averageGasSavings: stats.averageGasSavings.toString(),
                            lastTransactionTime: stats.lastTransactionTime.toString(),
                            isRegistered: stats.isRegistered,
                            savingsPercentage: savingsPercentage.toString()
                        }
                    });
                } catch (error) {
                    console.error('Error fetching user stats:', error);
                    return NextResponse.json({
                        error: 'Failed to fetch user stats',
                        fallback: true,
                        mockData: getMockUserData('get_stats', userAddress)
                    });
                }

            case 'get_history':
                if (!userAddress) {
                    return NextResponse.json({ error: 'User address required' }, { status: 400 });
                }

                try {
                    const history = await userContract.getUserTransactionHistory(userAddress);
                    const scheduledTxs = await userContract.getUserScheduledTransactions(userAddress);
                    
                    return NextResponse.json({
                        success: true,
                        userAddress,
                        transactionHistory: history,
                        scheduledTransactions: scheduledTxs
                    });
                } catch (error) {
                    console.error('Error fetching user history:', error);
                    return NextResponse.json({
                        error: 'Failed to fetch user history',
                        fallback: true,
                        mockData: getMockUserData('get_history', userAddress)
                    });
                }

            case 'get_scheduled_transaction':
                if (!transactionId) {
                    return NextResponse.json({ error: 'Transaction ID required' }, { status: 400 });
                }

                try {
                    const transaction = await userContract.getScheduledTransaction(transactionId);
                    
                    return NextResponse.json({
                        success: true,
                        transactionId,
                        transaction: {
                            user: transaction.user,
                            scheduledTime: transaction.scheduledTime.toString(),
                            estimatedGasSavings: transaction.estimatedGasSavings.toString(),
                            totalAmount: ethers.formatEther(transaction.totalAmount),
                            employeeCount: transaction.employeeCount,
                            executed: transaction.executed,
                            cancelled: transaction.cancelled,
                            createdAt: transaction.createdAt.toString()
                        }
                    });
                } catch (error) {
                    console.error('Error fetching scheduled transaction:', error);
                    return NextResponse.json({ error: 'Failed to fetch scheduled transaction' }, { status: 500 });
                }

            case 'get_payroll_batch':
                if (!batchId) {
                    return NextResponse.json({ error: 'Batch ID required' }, { status: 400 });
                }

                try {
                    const batch = await userContract.getPayrollBatch(batchId);
                    
                    return NextResponse.json({
                        success: true,
                        batchId,
                        batch: {
                            employer: batch.employer,
                            totalEmployees: batch.totalEmployees.toString(),
                            totalAmount: ethers.formatEther(batch.totalAmount),
                            gasSaved: batch.gasSaved.toString(),
                            executedAt: batch.executedAt.toString(),
                            status: batch.status
                        }
                    });
                } catch (error) {
                    console.error('Error fetching payroll batch:', error);
                    return NextResponse.json({ error: 'Failed to fetch payroll batch' }, { status: 500 });
                }

            case 'get_global_stats':
                try {
                    // Check if contract exists first
                    if (!userContract) {
                        throw new Error('UserContract not initialized');
                    }
                    
                    console.log('🔍 Calling getGlobalStats...');
                    const globalStats = await userContract.getGlobalStats();
                    console.log('✅ getGlobalStats result:', globalStats);
                    
                    return NextResponse.json({
                        success: true,
                        globalStats: {
                            totalUsers: globalStats._totalUsers.toString(),
                            totalTransactionsProcessed: globalStats._totalTransactionsProcessed.toString(),
                            totalGasSavedGlobally: globalStats._totalGasSavedGlobally.toString(),
                            totalValueProcessed: ethers.formatEther(globalStats._totalValueProcessed),
                            averageGasSavingsPerTransaction: globalStats._averageGasSavingsPerTransaction.toString()
                        }
                    });
                } catch (error) {
                    console.error('Error fetching global stats:', error);
                    return NextResponse.json({
                        error: 'Failed to fetch global stats',
                        fallback: true,
                        mockData: getMockUserData('get_global_stats')
                    });
                }

            default:
                return NextResponse.json({ error: 'Invalid action' }, { status: 400 });
        }

    } catch (error) {
        console.error('❌ User API error:', error);
        return NextResponse.json(
            { 
                error: 'Failed to process user request',
                details: error instanceof Error ? error.message : 'Unknown error'
            },
            { status: 500 }
        );
    }
}

export async function POST(request: NextRequest) {
    try {
        const body: UserRequest = await request.json();
        const { action, userAddress, scheduledTime, estimatedGasSavings, totalAmount, employeeCount } = body;

        console.log(`📝 User API POST request: ${action}`);

        if (!userContract) {
            return NextResponse.json({
                error: 'Blockchain connection not available',
                message: 'Contract interaction requires blockchain connection'
            }, { status: 503 });
        }

        switch (action) {
            case 'register_user':
                // Note: This would require a wallet connection in the frontend
                return NextResponse.json({
                    success: false,
                    message: 'User registration requires wallet connection from frontend',
                    instructions: 'Use web3 wallet to call registerUser() function'
                });

            case 'schedule_transaction':
                if (!userAddress || !scheduledTime || !estimatedGasSavings || !totalAmount || !employeeCount) {
                    return NextResponse.json({ error: 'Missing required parameters' }, { status: 400 });
                }

                // Note: This would also require wallet connection for transaction signing
                return NextResponse.json({
                    success: false,
                    message: 'Transaction scheduling requires wallet connection from frontend',
                    instructions: 'Use web3 wallet to call scheduleTransaction() function',
                    parameters: {
                        scheduledTime,
                        estimatedGasSavings,
                        totalAmount: ethers.parseEther(totalAmount.toString()),
                        employeeCount
                    }
                });

            default:
                return NextResponse.json({ error: 'Invalid action' }, { status: 400 });
        }

    } catch (error) {
        console.error('❌ User API POST error:', error);
        return NextResponse.json(
            { 
                error: 'Failed to process user request',
                details: error instanceof Error ? error.message : 'Unknown error'
            },
            { status: 500 }
        );
    }
}

function getMockUserData(action: string, userAddress?: string) {
    switch (action) {
        case 'get_stats':
            return {
                userAddress,
                stats: {
                    totalTransactions: "15",
                    totalGasSaved: "2450000",
                    totalAmountProcessed: "45000.0",
                    averageGasSavings: "163333",
                    lastTransactionTime: Math.floor(Date.now() / 1000).toString(),
                    isRegistered: true,
                    savingsPercentage: "68"
                }
            };
        
        case 'get_history':
            return {
                userAddress,
                transactionHistory: [
                    "0x1234567890abcdef1234567890abcdef12345678",
                    "0x2345678901bcdef12345678901bcdef123456789",
                    "0x3456789012cdef123456789012cdef1234567890"
                ],
                scheduledTransactions: [
                    "0x4567890123def1234567890123def12345678901"
                ]
            };
        
        case 'get_global_stats':
            return {
                globalStats: {
                    totalUsers: "1247",
                    totalTransactionsProcessed: "18653",
                    totalGasSavedGlobally: "45678900",
                    totalValueProcessed: "12450000.0",
                    averageGasSavingsPerTransaction: "2449"
                }
            };
        
        default:
            return { message: 'Mock data not available for this action' };
    }
}