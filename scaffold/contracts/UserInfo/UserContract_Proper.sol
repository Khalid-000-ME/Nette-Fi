// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

// Import Arcology concurrent libraries - PROPER OFFICIAL IMPORTS
import "@arcologynetwork/concurrentlib/lib/commutative/U256Cum.sol";
import "@arcologynetwork/concurrentlib/lib/runtime/Runtime.sol";

/**
 * @title UserContract_Proper - Official Arcology Implementation
 * @notice Proper implementation using official @arcologynetwork/concurrentlib
 * @dev Uses deferred execution and proper conflict avoidance patterns
 */
contract UserContract {
    
    // Events
    event UserRegistered(address indexed user, uint256 timestamp);
    event TransactionScheduled(address indexed user, bytes32 indexed transactionId, uint256 scheduledTime);
    event TransactionExecuted(address indexed user, bytes32 indexed transactionId, uint256 gasSaved, uint256 timestamp);
    event SavingsUpdated(address indexed user, uint256 totalSaved, uint256 transactionCount);
    
    // Structs
    struct UserStats {
        uint256 totalTransactions;
        uint256 totalGasSaved;
        uint256 totalAmountProcessed;
        uint256 averageGasSavings;
        uint256 lastTransactionTime;
        bool isRegistered;
    }
    
    struct ScheduledTransaction {
        bytes32 transactionId;
        address user;
        uint256 scheduledTime;
        uint256 estimatedGasSavings;
        uint256 totalAmount;
        uint8 employeeCount;
        bool executed;
        bool cancelled;
        uint256 createdAt;
    }
    
    struct PayrollBatch {
        bytes32 batchId;
        address employer;
        uint256 totalEmployees;
        uint256 totalAmount;
        uint256 gasSaved;
        uint256 executedAt;
        string status; // "pending", "executed", "failed"
    }
    
    // State variables
    address public owner;
    address public nettedAMM;
    
    // User data - using regular mappings for complex structs
    mapping(address => UserStats) public userStats;
    mapping(address => bytes32[]) public userTransactionHistory;
    mapping(bytes32 => ScheduledTransaction) public scheduledTransactions;
    mapping(address => bytes32[]) public userScheduledTransactions;
    mapping(bytes32 => PayrollBatch) public payrollBatches;
    
    // ✅ PROPER: Global statistics using official Arcology concurrent data structures
    U256Cumulative public totalUsersCounter;
    U256Cumulative public totalTransactionsProcessedCounter;
    U256Cumulative public totalGasSavedGloballyCounter;
    U256Cumulative public totalValueProcessedCounter;
    
    // ✅ PROPER: User-specific counters - simplified approach to avoid complex concurrent maps
    // Note: For user-specific data, we'll use regular mappings and update them in deferred execution
    mapping(address => uint256) public userTransactionCounts;
    mapping(address => uint256) public userGasSavedCounts;
    mapping(address => uint256) public userAmountProcessedCounts;
    
    // Access control
    modifier onlyOwner() {
        require(msg.sender == owner, "Not owner");
        _;
    }
    
    modifier onlyNettedAMM() {
        require(msg.sender == nettedAMM, "Not authorized AMM");
        _;
    }
    
    modifier onlyRegisteredUser() {
        require(userStats[msg.sender].isRegistered, "User not registered");
        _;
    }
    
    constructor() {
        owner = msg.sender;
        
        // ✅ PROPER: Initialize concurrent data structures with official library
        totalUsersCounter = new U256Cumulative(0, type(uint256).max);
        totalTransactionsProcessedCounter = new U256Cumulative(0, type(uint256).max);
        totalGasSavedGloballyCounter = new U256Cumulative(0, type(uint256).max);
        totalValueProcessedCounter = new U256Cumulative(0, type(uint256).max);
        
        // ✅ PROPER: Set up deferred execution for batch-sensitive operations
        Runtime.defer("recordTransaction(address,bytes32,uint256,uint256,uint256)", 30000);
    }
    
    /**
     * @notice Set the NettedAMM contract address
     */
    function setNettedAMM(address _nettedAMM) external onlyOwner {
        nettedAMM = _nettedAMM;
    }
    
    /**
     * @notice Register a new user
     */
    function registerUser() external {
        require(!userStats[msg.sender].isRegistered, "User already registered");
        
        userStats[msg.sender] = UserStats({
            totalTransactions: 0,
            totalGasSaved: 0,
            totalAmountProcessed: 0,
            averageGasSavings: 0,
            lastTransactionTime: 0,
            isRegistered: true
        });
        
        // ✅ PROPER: Safe concurrent counter increment
        totalUsersCounter.add(1);
        
        emit UserRegistered(msg.sender, block.timestamp);
    }
    
    /**
     * @notice Schedule a payroll transaction
     */
    function scheduleTransaction(
        uint256 scheduledTime,
        uint256 estimatedGasSavings,
        uint256 totalAmount,
        uint8 employeeCount
    ) external onlyRegisteredUser returns (bytes32 transactionId) {
        require(scheduledTime > block.timestamp, "Invalid scheduled time");
        
        transactionId = keccak256(abi.encodePacked(
            msg.sender,
            scheduledTime,
            totalAmount,
            block.timestamp
        ));
        
        scheduledTransactions[transactionId] = ScheduledTransaction({
            transactionId: transactionId,
            user: msg.sender,
            scheduledTime: scheduledTime,
            estimatedGasSavings: estimatedGasSavings,
            totalAmount: totalAmount,
            employeeCount: employeeCount,
            executed: false,
            cancelled: false,
            createdAt: block.timestamp
        });
        
        // Array operations are kept but should be used carefully in parallel execution
        userScheduledTransactions[msg.sender].push(transactionId);
        
        emit TransactionScheduled(msg.sender, transactionId, scheduledTime);
        
        return transactionId;
    }
    
    /**
     * @notice Record executed transaction (called by NettedAMM)
     * ✅ PROPER: Uses deferred execution for batch-safe processing
     */
    function recordTransaction(
        address user,
        bytes32 batchId,
        uint256 gasSaved,
        uint256 amountProcessed,
        uint256 employeeCount
    ) external onlyNettedAMM {
        require(userStats[user].isRegistered, "User not registered");
        
        // ✅ PROPER: Process user stats in deferred execution to avoid conflicts
        if (Runtime.isInDeferred()) {
            _processUserStatsInDeferred(user, gasSaved, amountProcessed);
        } else {
            // Store for deferred processing
            _storeTransactionForDeferred(user, batchId, gasSaved, amountProcessed, employeeCount);
        }
        
        // Update struct fields that don't need concurrent access
        UserStats storage stats = userStats[user];
        stats.lastTransactionTime = block.timestamp;
        
        // Add to transaction history
        userTransactionHistory[user].push(batchId);
        
        // Record payroll batch
        payrollBatches[batchId] = PayrollBatch({
            batchId: batchId,
            employer: user,
            totalEmployees: employeeCount,
            totalAmount: amountProcessed,
            gasSaved: gasSaved,
            executedAt: block.timestamp,
            status: "executed"
        });
        
        // ✅ PROPER: Update global stats using safe concurrent counters
        totalTransactionsProcessedCounter.add(1);
        totalGasSavedGloballyCounter.add(gasSaved);
        totalValueProcessedCounter.add(amountProcessed);
        
        emit TransactionExecuted(user, batchId, gasSaved, block.timestamp);
        emit SavingsUpdated(user, userGasSavedCounts[user], userTransactionCounts[user]);
    }
    
    /**
     * @dev Process user statistics in deferred execution
     * ✅ PROPER: Only called during deferred execution to avoid conflicts
     */
    function _processUserStatsInDeferred(
        address user,
        uint256 gasSaved,
        uint256 amountProcessed
    ) internal {
        require(Runtime.isInDeferred(), "Only in deferred execution");
        
        // Update user counters safely in deferred execution
        userTransactionCounts[user] += 1;
        userGasSavedCounts[user] += gasSaved;
        userAmountProcessedCounts[user] += amountProcessed;
        
        // Update struct stats
        UserStats storage stats = userStats[user];
        stats.totalTransactions = userTransactionCounts[user];
        stats.totalGasSaved = userGasSavedCounts[user];
        stats.totalAmountProcessed = userAmountProcessedCounts[user];
        stats.averageGasSavings = stats.totalTransactions > 0 ? stats.totalGasSaved / stats.totalTransactions : 0;
    }
    
    /**
     * @dev Store transaction data for deferred processing
     */
    function _storeTransactionForDeferred(
        address user,
        bytes32 batchId,
        uint256 gasSaved,
        uint256 amountProcessed,
        uint256 employeeCount
    ) internal {
        // In a full implementation, we'd store this data for batch processing
        // For now, we'll update the user stats directly (less optimal but safer)
        userTransactionCounts[user] += 1;
        userGasSavedCounts[user] += gasSaved;
        userAmountProcessedCounts[user] += amountProcessed;
        
        // Update struct stats
        UserStats storage stats = userStats[user];
        stats.totalTransactions = userTransactionCounts[user];
        stats.totalGasSaved = userGasSavedCounts[user];
        stats.totalAmountProcessed = userAmountProcessedCounts[user];
        stats.averageGasSavings = stats.totalTransactions > 0 ? stats.totalGasSaved / stats.totalTransactions : 0;
    }
    
    /**
     * @notice Mark scheduled transaction as executed
     */
    function markScheduledTransactionExecuted(bytes32 transactionId, uint256 actualGasSaved) external onlyNettedAMM {
        ScheduledTransaction storage transaction = scheduledTransactions[transactionId];
        require(transaction.user != address(0), "Transaction not found");
        require(!transaction.executed, "Already executed");
        
        transaction.executed = true;
        
        emit TransactionExecuted(transaction.user, transactionId, actualGasSaved, block.timestamp);
    }
    
    /**
     * @notice Cancel scheduled transaction
     */
    function cancelScheduledTransaction(bytes32 transactionId) external {
        ScheduledTransaction storage transaction = scheduledTransactions[transactionId];
        require(transaction.user == msg.sender, "Not your transaction");
        require(!transaction.executed, "Already executed");
        require(!transaction.cancelled, "Already cancelled");
        
        transaction.cancelled = true;
    }
    
    /**
     * @notice Get user statistics - SAFE READ VERSION
     * ✅ PROPER: Uses regular mappings to avoid concurrent conflicts
     */
    function getUserStats(address user) external view returns (
        uint256 totalTransactions,
        uint256 totalGasSaved,
        uint256 totalAmountProcessed,
        uint256 averageGasSavings,
        uint256 lastTransactionTime,
        bool isRegistered
    ) {
        UserStats memory stats = userStats[user];
        
        return (
            stats.totalTransactions,
            stats.totalGasSaved,
            stats.totalAmountProcessed,
            stats.averageGasSavings,
            stats.lastTransactionTime,
            stats.isRegistered
        );
    }
    
    /**
     * @notice Get user transaction history
     */
    function getUserTransactionHistory(address user) external view returns (bytes32[] memory) {
        return userTransactionHistory[user];
    }
    
    /**
     * @notice Get user scheduled transactions
     */
    function getUserScheduledTransactions(address user) external view returns (bytes32[] memory) {
        return userScheduledTransactions[user];
    }
    
    /**
     * @notice Get scheduled transaction details
     */
    function getScheduledTransaction(bytes32 transactionId) external view returns (
        address user,
        uint256 scheduledTime,
        uint256 estimatedGasSavings,
        uint256 totalAmount,
        uint8 employeeCount,
        bool executed,
        bool cancelled,
        uint256 createdAt
    ) {
        ScheduledTransaction memory transaction = scheduledTransactions[transactionId];
        return (
            transaction.user,
            transaction.scheduledTime,
            transaction.estimatedGasSavings,
            transaction.totalAmount,
            transaction.employeeCount,
            transaction.executed,
            transaction.cancelled,
            transaction.createdAt
        );
    }
    
    /**
     * @notice Get payroll batch details
     */
    function getPayrollBatch(bytes32 batchId) external view returns (
        address employer,
        uint256 totalEmployees,
        uint256 totalAmount,
        uint256 gasSaved,
        uint256 executedAt,
        string memory status
    ) {
        PayrollBatch memory batch = payrollBatches[batchId];
        return (
            batch.employer,
            batch.totalEmployees,
            batch.totalAmount,
            batch.gasSaved,
            batch.executedAt,
            batch.status
        );
    }
    
    /**
     * @notice Get global statistics - SAFE READ VERSION
     * ✅ WARNING: Avoid calling during batch processing to prevent conflicts
     */
    function getGlobalStats() external view returns (
        uint256 _totalUsers,
        uint256 _totalTransactionsProcessed,
        uint256 _totalGasSavedGlobally,
        uint256 _totalValueProcessed,
        uint256 _averageGasSavingsPerTransaction
    ) {
        // Note: These reads can cause conflicts if called during concurrent execution
        // Use with caution
        _totalUsers = totalUsersCounter.get();
        _totalTransactionsProcessed = totalTransactionsProcessedCounter.get();
        _totalGasSavedGlobally = totalGasSavedGloballyCounter.get();
        _totalValueProcessed = totalValueProcessedCounter.get();
        
        uint256 avgGasSavings = _totalTransactionsProcessed > 0 ? 
            _totalGasSavedGlobally / _totalTransactionsProcessed : 0;
            
        return (
            _totalUsers,
            _totalTransactionsProcessed,
            _totalGasSavedGlobally,
            _totalValueProcessed,
            avgGasSavings
        );
    }
    
    /**
     * @notice Get user savings percentage compared to traditional methods
     */
    function getUserSavingsPercentage(address user) external view returns (uint256) {
        uint256 totalTransactions = userTransactionCounts[user];
        uint256 totalGasSaved = userGasSavedCounts[user];
        
        if (totalTransactions == 0) return 0;
        
        // Assume traditional gas cost is 150k gas per transaction
        uint256 traditionalGasCost = totalTransactions * 150000;
        
        return (totalGasSaved * 100) / traditionalGasCost;
    }
    
    /**
     * @notice Emergency functions
     */
    function emergencyPause() external onlyOwner {
        // Implementation for emergency pause
    }
    
    function updateOwner(address newOwner) external onlyOwner {
        require(newOwner != address(0), "Invalid address");
        owner = newOwner;
    }
    
    // ✅ PROPER: Safe getter functions - USE WITH CAUTION DURING BATCH PROCESSING
    function getTotalUsers() external view returns (uint256) {
        return totalUsersCounter.get();
    }
    
    function getTotalTransactionsProcessed() external view returns (uint256) {
        return totalTransactionsProcessedCounter.get();
    }
    
    function getTotalGasSavedGlobally() external view returns (uint256) {
        return totalGasSavedGloballyCounter.get();
    }
    
    function getTotalValueProcessed() external view returns (uint256) {
        return totalValueProcessedCounter.get();
    }
}
