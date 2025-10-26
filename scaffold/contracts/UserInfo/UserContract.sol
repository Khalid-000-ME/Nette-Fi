// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title UserContract - DeFi Payroll Manager User Statistics
 * @notice Stores user statistics, scheduled transactions, and savings data
 * @dev Tracks all user interactions with the payroll system
 */
contract UserContract_Comp {
    
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
    
    // User data
    mapping(address => UserStats) public userStats;
    mapping(address => bytes32[]) public userTransactionHistory;
    mapping(bytes32 => ScheduledTransaction) public scheduledTransactions;
    mapping(address => bytes32[]) public userScheduledTransactions;
    mapping(bytes32 => PayrollBatch) public payrollBatches;
    
    // Global statistics
    uint256 public totalUsers;
    uint256 public totalTransactionsProcessed;
    uint256 public totalGasSavedGlobally;
    uint256 public totalValueProcessed;
    
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
        
        totalUsers++;
        
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
        
        userScheduledTransactions[msg.sender].push(transactionId);
        
        emit TransactionScheduled(msg.sender, transactionId, scheduledTime);
        
        return transactionId;
    }
    
    /**
     * @notice Record executed transaction (called by NettedAMM)
     */
    function recordTransaction(
        address user,
        bytes32 batchId,
        uint256 gasSaved,
        uint256 amountProcessed,
        uint256 employeeCount
    ) external onlyNettedAMM {
        require(userStats[user].isRegistered, "User not registered");
        
        // Update user stats
        UserStats storage stats = userStats[user];
        stats.totalTransactions++;
        stats.totalGasSaved += gasSaved;
        stats.totalAmountProcessed += amountProcessed;
        stats.averageGasSavings = stats.totalGasSaved / stats.totalTransactions;
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
        
        // Update global stats
        totalTransactionsProcessed++;
        totalGasSavedGlobally += gasSaved;
        totalValueProcessed += amountProcessed;
        
        emit TransactionExecuted(user, batchId, gasSaved, block.timestamp);
        emit SavingsUpdated(user, stats.totalGasSaved, stats.totalTransactions);
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
     * @notice Get user statistics
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
     * @notice Get global statistics
     */
    function getGlobalStats() external view returns (
        uint256 _totalUsers,
        uint256 _totalTransactionsProcessed,
        uint256 _totalGasSavedGlobally,
        uint256 _totalValueProcessed,
        uint256 _averageGasSavingsPerTransaction
    ) {
        uint256 avgGasSavings = totalTransactionsProcessed > 0 ? 
            totalGasSavedGlobally / totalTransactionsProcessed : 0;
            
        return (
            totalUsers,
            totalTransactionsProcessed,
            totalGasSavedGlobally,
            totalValueProcessed,
            avgGasSavings
        );
    }
    
    /**
     * @notice Get user savings percentage compared to traditional methods
     */
    function getUserSavingsPercentage(address user) external view returns (uint256) {
        UserStats memory stats = userStats[user];
        if (stats.totalTransactions == 0) return 0;
        
        // Assume traditional gas cost is 150k gas per transaction
        uint256 traditionalGasCost = stats.totalTransactions * 150000;
        uint256 actualGasCost = traditionalGasCost - stats.totalGasSaved;
        
        return (stats.totalGasSaved * 100) / traditionalGasCost;
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
}