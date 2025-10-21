// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@pythnetwork/pyth-sdk-solidity/IPyth.sol";
import "@pythnetwork/pyth-sdk-solidity/PythStructs.sol";
import "@openzeppelin/contracts/access/Ownable.sol";
import "@openzeppelin/contracts/security/ReentrancyGuard.sol";

/**
 * @title PythPriceConsumer
 * @dev Smart contract to consume Pyth Network price feeds using the pull method
 * @notice This contract integrates with Pyth Network to get real-time price data
 */
contract PythPriceConsumer is Ownable, ReentrancyGuard {
    IPyth pyth;
    
    // Mapping of token symbols to their Pyth price feed IDs
    mapping(string => bytes32) public priceIds;
    
    // Events
    event PriceUpdated(string indexed token, int64 price, uint64 timestamp);
    event PriceFeedAdded(string indexed token, bytes32 priceId);
    event PriceFeedRemoved(string indexed token);
    
    // Errors
    error InvalidPriceId();
    error PriceNotFound();
    error StalePrice();
    error InsufficientUpdateFee();
    
    /**
     * @dev Constructor to initialize the Pyth contract
     * @param _pythContract Address of the Pyth contract on the current network
     */
    constructor(address _pythContract) {
        pyth = IPyth(_pythContract);
        
        // Initialize common price feed IDs for Base network
        // ETH/USD
        priceIds["ETH"] = 0xff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace;
        // BTC/USD  
        priceIds["BTC"] = 0xe62df6c8b4a85fe1a67db44dc12de5db330f7ac66b72dc658afedf0f4a415b43;
        // USDC/USD
        priceIds["USDC"] = 0xeaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a;
        // USDT/USD
        priceIds["USDT"] = 0x2b89b9dc8fdf9f34709a5b106b472f0f39bb6ca9ce04b0fd7f2e971688e2e53b;
    }
    
    /**
     * @dev Add a new price feed
     * @param token Token symbol (e.g., "ETH", "BTC")
     * @param priceId Pyth price feed ID for the token
     */
    function addPriceFeed(string calldata token, bytes32 priceId) external onlyOwner {
        if (priceId == bytes32(0)) revert InvalidPriceId();
        
        priceIds[token] = priceId;
        emit PriceFeedAdded(token, priceId);
    }
    
    /**
     * @dev Remove a price feed
     * @param token Token symbol to remove
     */
    function removePriceFeed(string calldata token) external onlyOwner {
        delete priceIds[token];
        emit PriceFeedRemoved(token);
    }
    
    /**
     * @dev Get the latest price for a token (without update)
     * @param token Token symbol
     * @return price Latest price with 8 decimal places
     * @return timestamp Last update timestamp
     */
    function getLatestPrice(string calldata token) 
        external 
        view 
        returns (int64 price, uint64 timestamp) 
    {
        bytes32 priceId = priceIds[token];
        if (priceId == bytes32(0)) revert PriceNotFound();
        
        PythStructs.Price memory priceData = pyth.getPriceUnsafe(priceId);
        
        return (priceData.price, uint64(priceData.publishTime));
    }
    
    /**
     * @dev Get the latest price with confidence interval
     * @param token Token symbol
     * @return price Latest price with 8 decimal places
     * @return conf Confidence interval
     * @return timestamp Last update timestamp
     */
    function getLatestPriceWithConfidence(string calldata token)
        external
        view
        returns (int64 price, uint64 conf, uint64 timestamp)
    {
        bytes32 priceId = priceIds[token];
        if (priceId == bytes32(0)) revert PriceNotFound();
        
        PythStructs.Price memory priceData = pyth.getPriceUnsafe(priceId);
        
        return (priceData.price, priceData.conf, uint64(priceData.publishTime));
    }
    
    /**
     * @dev Update price feeds and get the latest price
     * @param token Token symbol
     * @param priceUpdateData Array of price update data from Pyth
     * @return price Updated price with 8 decimal places
     * @return timestamp Update timestamp
     */
    function updateAndGetPrice(
        string calldata token,
        bytes[] calldata priceUpdateData
    ) 
        external 
        payable 
        nonReentrant
        returns (int64 price, uint64 timestamp) 
    {
        bytes32 priceId = priceIds[token];
        if (priceId == bytes32(0)) revert PriceNotFound();
        
        // Get the required fee for updating the price feeds
        uint fee = pyth.getUpdateFee(priceUpdateData);
        if (msg.value < fee) revert InsufficientUpdateFee();
        
        // Update the price feeds
        pyth.updatePriceFeeds{value: fee}(priceUpdateData);
        
        // Get the updated price
        PythStructs.Price memory priceData = pyth.getPriceUnsafe(priceId);
        
        emit PriceUpdated(token, priceData.price, uint64(priceData.publishTime));
        
        // Refund excess payment
        if (msg.value > fee) {
            payable(msg.sender).transfer(msg.value - fee);
        }
        
        return (priceData.price, uint64(priceData.publishTime));
    }
    
    /**
     * @dev Batch update multiple price feeds
     * @param tokens Array of token symbols
     * @param priceUpdateData Array of price update data from Pyth
     * @return prices Array of updated prices
     * @return timestamps Array of update timestamps
     */
    function batchUpdateAndGetPrices(
        string[] calldata tokens,
        bytes[] calldata priceUpdateData
    )
        external
        payable
        nonReentrant
        returns (int64[] memory prices, uint64[] memory timestamps)
    {
        uint256 tokenCount = tokens.length;
        prices = new int64[](tokenCount);
        timestamps = new uint64[](tokenCount);
        
        // Get the required fee for updating the price feeds
        uint fee = pyth.getUpdateFee(priceUpdateData);
        if (msg.value < fee) revert InsufficientUpdateFee();
        
        // Update the price feeds
        pyth.updatePriceFeeds{value: fee}(priceUpdateData);
        
        // Get updated prices for all tokens
        for (uint256 i = 0; i < tokenCount; i++) {
            bytes32 priceId = priceIds[tokens[i]];
            if (priceId == bytes32(0)) revert PriceNotFound();
            
            PythStructs.Price memory priceData = pyth.getPriceUnsafe(priceId);
            prices[i] = priceData.price;
            timestamps[i] = uint64(priceData.publishTime);
            
            emit PriceUpdated(tokens[i], priceData.price, uint64(priceData.publishTime));
        }
        
        // Refund excess payment
        if (msg.value > fee) {
            payable(msg.sender).transfer(msg.value - fee);
        }
        
        return (prices, timestamps);
    }
    
    /**
     * @dev Get the required fee for updating price feeds
     * @param priceUpdateData Array of price update data
     * @return fee Required fee in wei
     */
    function getUpdateFee(bytes[] calldata priceUpdateData) 
        external 
        view 
        returns (uint fee) 
    {
        return pyth.getUpdateFee(priceUpdateData);
    }
    
    /**
     * @dev Check if a price is stale (older than maxAge seconds)
     * @param token Token symbol
     * @param maxAge Maximum age in seconds
     * @return isStale True if price is stale
     */
    function isPriceStale(string calldata token, uint256 maxAge) 
        external 
        view 
        returns (bool isStale) 
    {
        bytes32 priceId = priceIds[token];
        if (priceId == bytes32(0)) revert PriceNotFound();
        
        PythStructs.Price memory priceData = pyth.getPriceUnsafe(priceId);
        
        return (block.timestamp - priceData.publishTime) > maxAge;
    }
    
    /**
     * @dev Get price feed ID for a token
     * @param token Token symbol
     * @return priceId Pyth price feed ID
     */
    function getPriceFeedId(string calldata token) 
        external 
        view 
        returns (bytes32 priceId) 
    {
        return priceIds[token];
    }
    
    /**
     * @dev Emergency function to withdraw contract balance
     */
    function emergencyWithdraw() external onlyOwner {
        payable(owner()).transfer(address(this).balance);
    }
    
    /**
     * @dev Allow contract to receive ETH
     */
    receive() external payable {}
}
