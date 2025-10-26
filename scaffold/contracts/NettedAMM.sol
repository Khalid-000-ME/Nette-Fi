// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

/**
 * @title Simple NettedAMM
 * @dev Real-time netting contract that processes parallel transactions as they come
 * No complex authorization - just pure netting logic
 */
contract NettedAMM_Comp {
    
    // Events for tracking
    event SwapRequested(address indexed user, address tokenA, address tokenB, uint256 amountA, uint256 timestamp);
    event SwapNetted(address indexed userA, address indexed userB, address tokenA, address tokenB, uint256 nettedAmount, bytes32 txHash);
    event SwapExecuted(address indexed user, address tokenA, address tokenB, uint256 amountA, uint256 amountB, bytes32 txHash);
    event PriceUpdated(address indexed tokenA, address indexed tokenB, uint256 newPrice, uint256 timestamp);
    
    // Swap request structure
    struct SwapRequest {
        address user;
        address tokenA;
        address tokenB;
        uint256 amountA;
        uint256 minAmountB;
        uint256 timestamp;
        bool isActive;
    }
    
    // Storage
    mapping(bytes32 => SwapRequest) public swapRequests;
    mapping(address => mapping(address => uint256)) public tokenPrices; // tokenA -> tokenB -> price
    mapping(address => mapping(address => uint256)) public liquidityPool;
    
    bytes32[] public activeRequests;
    uint256 public totalSwaps;
    uint256 public totalNetted;
    uint256 public gasSaved;
    
    // Simple price oracle (for demo purposes)
    uint256 constant PRICE_PRECISION = 1e18;
    
    constructor() {
        // Initialize some basic token prices (demo values)
        // USDC -> ETH price (1 USDC = 0.0003 ETH approximately)
        tokenPrices[0x1642dD5c38642f91E4aa0025978b572fe30Ed89d][address(0)] = 3e14; // 0.0003 ETH per USDC
        tokenPrices[address(0)][0x1642dD5c38642f91E4aa0025978b572fe30Ed89d] = 3333e18; // 3333 USDC per ETH
        
        // Add more price pairs as needed
        tokenPrices[0x1642dD5c38642f91E4aa0025978b572fe30Ed89d][0x2249977665260A63307Cf72a4D65385cC0817CB5] = 1e18; // USDC -> DAI 1:1
        tokenPrices[0x2249977665260A63307Cf72a4D65385cC0817CB5][0x1642dD5c38642f91E4aa0025978b572fe30Ed89d] = 1e18; // DAI -> USDC 1:1
    }
    
    /**
     * @dev Request a swap - this is where the magic happens
     * Automatically tries to net with existing requests
     */
    function requestSwap(
        address tokenA,
        address tokenB,
        uint256 amountA,
        uint256 minAmountB
    ) external payable returns (bytes32 requestId, bool wasNetted) {
        
        require(tokenA != tokenB, "Same token");
        require(amountA > 0, "Invalid amount");
        
        // Handle ETH deposits
        if (tokenA == address(0)) {
            require(msg.value == amountA, "ETH amount mismatch");
        }
        
        // Generate unique request ID
        requestId = keccak256(abi.encodePacked(
            msg.sender,
            tokenA,
            tokenB,
            amountA,
            block.timestamp,
            totalSwaps
        ));
        
        totalSwaps++;
        
        emit SwapRequested(msg.sender, tokenA, tokenB, amountA, block.timestamp);
        
        // Try to find a matching request for netting
        bytes32 matchedRequestId = findMatchingRequest(tokenA, tokenB, amountA);
        
        if (matchedRequestId != bytes32(0)) {
            // Found a match! Execute netting
            wasNetted = true;
            executeNetting(requestId, matchedRequestId, tokenA, tokenB, amountA);
            totalNetted++;
            gasSaved += 21000; // Estimate gas saved per netted transaction
            
        } else {
            // No match found, store the request
            wasNetted = false;
            SwapRequest memory newRequest = SwapRequest({
                user: msg.sender,
                tokenA: tokenA,
                tokenB: tokenB,
                amountA: amountA,
                minAmountB: minAmountB,
                timestamp: block.timestamp,
                isActive: true
            });
            
            swapRequests[requestId] = newRequest;
            activeRequests.push(requestId);
        }
        
        // Update price based on this transaction
        updatePrice(tokenA, tokenB, amountA);
        
        return (requestId, wasNetted);
    }
    
    /**
     * @dev Find a matching request for netting
     */
    function findMatchingRequest(
        address tokenA,
        address tokenB,
        uint256 amountA
    ) internal view returns (bytes32) {
        
        for (uint256 i = 0; i < activeRequests.length; i++) {
            bytes32 requestId = activeRequests[i];
            SwapRequest memory request = swapRequests[requestId];
            
            if (!request.isActive) continue;
            
            // Check if this is an opposite swap (A->B vs B->A)
            if (request.tokenA == tokenB && request.tokenB == tokenA) {
                // Check if amounts are compatible for netting
                uint256 expectedAmountB = getExpectedAmount(tokenA, tokenB, amountA);
                
                if (request.amountA >= expectedAmountB) {
                    return requestId;
                }
            }
        }
        
        return bytes32(0);
    }
    
    /**
     * @dev Execute netting between two requests
     */
    function executeNetting(
        bytes32 requestId1,
        bytes32 requestId2,
        address tokenA,
        address tokenB,
        uint256 amountA
    ) internal {
        
        SwapRequest storage request2 = swapRequests[requestId2];
        
        // Calculate netted amounts
        uint256 expectedAmountB = getExpectedAmount(tokenA, tokenB, amountA);
        uint256 nettedAmount = expectedAmountB;
        
        // Mark the matched request as inactive
        request2.isActive = false;
        
        // Remove from active requests
        removeFromActiveRequests(requestId2);
        
        // Generate transaction hash for this netting operation
        bytes32 nettingTxHash = keccak256(abi.encodePacked(
            requestId1,
            requestId2,
            block.timestamp,
            "NETTED"
        ));
        
        emit SwapNetted(msg.sender, request2.user, tokenA, tokenB, nettedAmount, nettingTxHash);
        
        // In a real implementation, you would transfer the netted amounts
        // For demo purposes, we just emit events
    }
    
    /**
     * @dev Execute individual swap (when no netting possible)
     */
    function executeIndividualSwap(bytes32 requestId) external {
        SwapRequest storage request = swapRequests[requestId];
        require(request.isActive, "Request not active");
        require(request.user == msg.sender, "Not your request");
        
        uint256 amountB = getExpectedAmount(request.tokenA, request.tokenB, request.amountA);
        require(amountB >= request.minAmountB, "Insufficient output");
        
        request.isActive = false;
        removeFromActiveRequests(requestId);
        
        bytes32 swapTxHash = keccak256(abi.encodePacked(
            requestId,
            block.timestamp,
            "INDIVIDUAL"
        ));
        
        emit SwapExecuted(request.user, request.tokenA, request.tokenB, request.amountA, amountB, swapTxHash);
    }
    
    /**
     * @dev Update token price based on swap activity
     */
    function updatePrice(address tokenA, address tokenB, uint256 amountA) internal {
        // Simple price update mechanism
        uint256 currentPrice = tokenPrices[tokenA][tokenB];
        
        if (currentPrice == 0) {
            // Set default price if not exists
            tokenPrices[tokenA][tokenB] = PRICE_PRECISION;
            currentPrice = PRICE_PRECISION;
        }
        
        // Adjust price based on volume (simple mechanism)
        uint256 priceImpact = (amountA * 1e15) / (1e18 + amountA); // Small price impact
        uint256 newPrice = currentPrice + priceImpact;
        
        tokenPrices[tokenA][tokenB] = newPrice;
        
        emit PriceUpdated(tokenA, tokenB, newPrice, block.timestamp);
    }
    
    /**
     * @dev Get expected output amount for a swap
     */
    function getExpectedAmount(address tokenA, address tokenB, uint256 amountA) public view returns (uint256) {
        uint256 price = tokenPrices[tokenA][tokenB];
        if (price == 0) return 0;
        
        return (amountA * price) / PRICE_PRECISION;
    }
    
    /**
     * @dev Remove request from active list
     */
    function removeFromActiveRequests(bytes32 requestId) internal {
        for (uint256 i = 0; i < activeRequests.length; i++) {
            if (activeRequests[i] == requestId) {
                activeRequests[i] = activeRequests[activeRequests.length - 1];
                activeRequests.pop();
                break;
            }
        }
    }
    
    /**
     * @dev Get contract statistics
     */
    function getStats() external view returns (
        uint256 _totalSwaps,
        uint256 _totalNetted,
        uint256 _gasSaved,
        uint256 _activeRequestsCount
    ) {
        return (totalSwaps, totalNetted, gasSaved, activeRequests.length);
    }
    
    /**
     * @dev Get active requests count
     */
    function getActiveRequestsCount() external view returns (uint256) {
        return activeRequests.length;
    }
    
    /**
     * @dev Get token price
     */
    function getPrice(address tokenA, address tokenB) external view returns (uint256) {
        return tokenPrices[tokenA][tokenB];
    }
    
    // Fallback to receive ETH
    receive() external payable {}
}