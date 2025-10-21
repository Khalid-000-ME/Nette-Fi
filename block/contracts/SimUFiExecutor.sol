// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/token/ERC20/IERC20.sol";
import "@openzeppelin/contracts/token/ERC20/utils/SafeERC20.sol";

/**
 * @title SimUFiExecutor
 * @dev Smart contract for executing trades at optimal timing based on AI analysis
 */
contract SimUFiExecutor is ReentrancyGuard, Ownable {
    using SafeERC20 for IERC20;

    struct QueuedTrade {
        address user;
        address tokenIn;
        address tokenOut;
        uint256 amountIn;
        uint256 minAmountOut;
        uint256 executeAtBlock;
        uint256 maxGasPrice;
        bool executed;
        bytes routerCalldata;
    }

    mapping(bytes32 => QueuedTrade) public queuedTrades;
    mapping(address => bool) public authorizedExecutors;
    
    uint256 public executionFee = 0.001 ether; // Fee for execution service
    uint256 public constant MAX_DELAY_BLOCKS = 50; // Maximum blocks to wait
    
    event TradeQueued(
        bytes32 indexed tradeId,
        address indexed user,
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        uint256 executeAtBlock
    );
    
    event TradeExecuted(
        bytes32 indexed tradeId,
        address indexed user,
        uint256 amountOut,
        uint256 gasUsed
    );
    
    event TradeCancelled(
        bytes32 indexed tradeId,
        address indexed user
    );

    modifier onlyAuthorizedExecutor() {
        require(authorizedExecutors[msg.sender] || msg.sender == owner(), "Not authorized");
        _;
    }

    constructor() {}

    /**
     * @dev Queue a trade for execution at optimal block
     */
    function queueTrade(
        address tokenIn,
        address tokenOut,
        uint256 amountIn,
        uint256 minAmountOut,
        uint256 executeAtBlock,
        uint256 maxGasPrice,
        bytes calldata routerCalldata
    ) external payable nonReentrant {
        require(msg.value >= executionFee, "Insufficient execution fee");
        require(executeAtBlock <= block.number + MAX_DELAY_BLOCKS, "Execution too far in future");
        require(executeAtBlock >= block.number, "Cannot execute in past");
        require(amountIn > 0, "Amount must be positive");

        // Transfer tokens to contract
        IERC20(tokenIn).safeTransferFrom(msg.sender, address(this), amountIn);

        // Generate unique trade ID
        bytes32 tradeId = keccak256(
            abi.encodePacked(
                msg.sender,
                tokenIn,
                tokenOut,
                amountIn,
                executeAtBlock,
                block.timestamp
            )
        );

        // Store trade details
        queuedTrades[tradeId] = QueuedTrade({
            user: msg.sender,
            tokenIn: tokenIn,
            tokenOut: tokenOut,
            amountIn: amountIn,
            minAmountOut: minAmountOut,
            executeAtBlock: executeAtBlock,
            maxGasPrice: maxGasPrice,
            executed: false,
            routerCalldata: routerCalldata
        });

        emit TradeQueued(tradeId, msg.sender, tokenIn, tokenOut, amountIn, executeAtBlock);
    }

    /**
     * @dev Execute a queued trade when conditions are met
     */
    function executeTrade(bytes32 tradeId, address router) external onlyAuthorizedExecutor nonReentrant {
        _executeTrade(tradeId, router, true);
    }

    /**
     * @dev Internal function to execute a trade
     */
    function _executeTrade(bytes32 tradeId, address router, bool checkAuthorization) internal {
        QueuedTrade storage trade = queuedTrades[tradeId];
        
        require(!trade.executed, "Trade already executed");
        require(trade.user != address(0), "Trade does not exist");
        require(block.number >= trade.executeAtBlock, "Too early to execute");
        require(tx.gasprice <= trade.maxGasPrice, "Gas price too high");

        uint256 gasStart = gasleft();

        // Mark as executed first to prevent reentrancy
        trade.executed = true;

        // Approve router to spend tokens
        IERC20(trade.tokenIn).safeApprove(router, trade.amountIn);

        // Get initial balance
        uint256 initialBalance = IERC20(trade.tokenOut).balanceOf(address(this));

        // Execute the trade through router
        (bool success, ) = router.call(trade.routerCalldata);
        require(success, "Router call failed");

        // Calculate received amount
        uint256 finalBalance = IERC20(trade.tokenOut).balanceOf(address(this));
        uint256 amountOut = finalBalance - initialBalance;
        
        require(amountOut >= trade.minAmountOut, "Insufficient output amount");

        // Transfer output tokens to user
        IERC20(trade.tokenOut).safeTransfer(trade.user, amountOut);

        uint256 gasUsed = gasStart - gasleft();
        
        emit TradeExecuted(tradeId, trade.user, amountOut, gasUsed);
    }

    /**
     * @dev Cancel a queued trade and refund tokens
     */
    function cancelTrade(bytes32 tradeId) external nonReentrant {
        QueuedTrade storage trade = queuedTrades[tradeId];
        
        require(trade.user == msg.sender, "Not your trade");
        require(!trade.executed, "Trade already executed");
        require(block.number > trade.executeAtBlock + 10, "Cannot cancel yet"); // Grace period

        // Mark as executed to prevent double-spending
        trade.executed = true;

        // Refund tokens
        IERC20(trade.tokenIn).safeTransfer(trade.user, trade.amountIn);

        // Refund execution fee (minus gas costs)
        uint256 refundAmount = executionFee * 90 / 100; // 90% refund
        payable(trade.user).transfer(refundAmount);

        emit TradeCancelled(tradeId, trade.user);
    }

    /**
     * @dev Emergency function to execute trade immediately
     */
    function executeTradeImmediately(bytes32 tradeId, address router) external nonReentrant {
        QueuedTrade storage trade = queuedTrades[tradeId];
        require(trade.user == msg.sender, "Not your trade");
        
        // Allow immediate execution by setting executeAtBlock to current block
        trade.executeAtBlock = block.number;
        
        _executeTrade(tradeId, router, false);
    }

    // Admin functions
    function setAuthorizedExecutor(address executor, bool authorized) external onlyOwner {
        authorizedExecutors[executor] = authorized;
    }

    function setExecutionFee(uint256 newFee) external onlyOwner {
        executionFee = newFee;
    }

    function withdrawFees() external onlyOwner {
        payable(owner()).transfer(address(this).balance);
    }

    function emergencyWithdrawToken(address token, uint256 amount) external onlyOwner {
        IERC20(token).safeTransfer(owner(), amount);
    }

    // View functions
    function getTradeDetails(bytes32 tradeId) external view returns (QueuedTrade memory) {
        return queuedTrades[tradeId];
    }

    function canExecuteTrade(bytes32 tradeId) external view returns (bool) {
        QueuedTrade memory trade = queuedTrades[tradeId];
        return !trade.executed && 
               trade.user != address(0) && 
               block.number >= trade.executeAtBlock &&
               tx.gasprice <= trade.maxGasPrice;
    }
}
