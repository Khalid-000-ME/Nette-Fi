// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/security/ReentrancyGuard.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title MEVProtection
 * @dev Contract for detecting and preventing MEV attacks
 */
contract MEVProtection is ReentrancyGuard, Ownable {
    
    struct TransactionPattern {
        address sender;
        uint256 gasPrice;
        uint256 blockNumber;
        bytes32 txHash;
        bool isSuspicious;
    }
    
    struct MEVBot {
        address botAddress;
        uint256 suspiciousTransactions;
        uint256 lastActiveBlock;
        bool isBlacklisted;
    }
    
    mapping(address => MEVBot) public detectedBots;
    mapping(bytes32 => TransactionPattern) public transactionPatterns;
    mapping(address => uint256) public userProtectionLevel;
    
    uint256 public constant HIGH_GAS_THRESHOLD = 200 gwei;
    uint256 public constant SUSPICIOUS_TX_THRESHOLD = 5;
    uint256 public maxProtectedSlippage = 300; // 3% in basis points
    
    event MEVBotDetected(address indexed bot, uint256 suspiciousCount);
    event MEVAttackPrevented(address indexed attacker, address indexed victim, uint256 savedAmount);
    event ProtectionLevelUpdated(address indexed user, uint256 newLevel);
    
    /**
     * @dev Analyze transaction for MEV patterns
     */
    function analyzeMEVRisk(
        address sender,
        uint256 gasPrice,
        uint256 tradeAmount,
        address tokenPair
    ) external returns (uint256 riskScore) {
        // Check if sender is known MEV bot
        if (detectedBots[sender].isBlacklisted) {
            return 100; // Maximum risk
        }
        
        riskScore = 0;
        
        // High gas price indicates potential MEV
        if (gasPrice > HIGH_GAS_THRESHOLD) {
            riskScore += 30;
        }
        
        // Check for sandwich attack patterns
        if (isSandwichAttackPattern(sender, tokenPair)) {
            riskScore += 40;
            _updateBotSuspicion(sender);
        }
        
        // Large trade amounts are more attractive to MEV
        if (tradeAmount > 10 ether) {
            riskScore += 15;
        }
        
        // Check transaction frequency
        if (isHighFrequencyTrader(sender)) {
            riskScore += 15;
        }
        
        return riskScore > 100 ? 100 : riskScore;
    }
    
    /**
     * @dev Check if transaction pattern indicates sandwich attack
     */
    function isSandwichAttackPattern(address sender, address tokenPair) internal view returns (bool) {
        // Look for pattern: high gas tx -> normal tx -> high gas tx from same sender
        // This is a simplified heuristic
        
        MEVBot memory bot = detectedBots[sender];
        
        // If sender has history of suspicious activity
        if (bot.suspiciousTransactions > 2) {
            return true;
        }
        
        // Check if sender is making multiple transactions in short time
        if (bot.lastActiveBlock > 0 && block.number - bot.lastActiveBlock < 3) {
            return true;
        }
        
        return false;
    }
    
    /**
     * @dev Check if address shows high-frequency trading patterns
     */
    function isHighFrequencyTrader(address trader) internal view returns (bool) {
        MEVBot memory bot = detectedBots[trader];
        
        // If more than 10 transactions in last 100 blocks
        return bot.lastActiveBlock > 0 && 
               block.number - bot.lastActiveBlock < 100 && 
               bot.suspiciousTransactions > 10;
    }
    
    /**
     * @dev Update bot suspicion level
     */
    function _updateBotSuspicion(address bot) internal {
        MEVBot storage botData = detectedBots[bot];
        botData.suspiciousTransactions++;
        botData.lastActiveBlock = block.number;
        
        // Blacklist if too many suspicious transactions
        if (botData.suspiciousTransactions >= SUSPICIOUS_TX_THRESHOLD) {
            botData.isBlacklisted = true;
            emit MEVBotDetected(bot, botData.suspiciousTransactions);
        }
    }
    
    /**
     * @dev Calculate optimal gas price to avoid MEV
     */
    function getOptimalGasPrice(uint256 currentGasPrice, uint256 mevRisk) external pure returns (uint256) {
        if (mevRisk < 30) {
            return currentGasPrice; // No adjustment needed
        } else if (mevRisk < 60) {
            return currentGasPrice * 110 / 100; // 10% increase
        } else if (mevRisk < 80) {
            return currentGasPrice * 125 / 100; // 25% increase
        } else {
            return currentGasPrice * 150 / 100; // 50% increase
        }
    }
    
    /**
     * @dev Calculate recommended delay blocks to avoid MEV
     */
    function getRecommendedDelay(uint256 mevRisk, uint256 tradeSize) external pure returns (uint256) {
        if (mevRisk < 30) {
            return 0; // Execute immediately
        } else if (mevRisk < 60) {
            return 1; // Wait 1 block
        } else if (mevRisk < 80) {
            return 2; // Wait 2 blocks
        } else {
            // High risk - wait longer for large trades
            return tradeSize > 5 ether ? 5 : 3;
        }
    }
    
    /**
     * @dev Set user protection level
     */
    function setProtectionLevel(uint256 level) external {
        require(level <= 3, "Invalid protection level");
        userProtectionLevel[msg.sender] = level;
        emit ProtectionLevelUpdated(msg.sender, level);
    }
    
    /**
     * @dev Get protection recommendations for user
     */
    function getProtectionRecommendations(
        address user,
        uint256 mevRisk,
        uint256 tradeAmount
    ) external view returns (
        uint256 recommendedGasPrice,
        uint256 recommendedDelay,
        bool shouldExecute
    ) {
        uint256 protectionLevel = userProtectionLevel[user];
        
        // Adjust recommendations based on user's protection level
        if (protectionLevel == 0) {
            // No protection - user accepts MEV risk
            return (tx.gasprice, 0, true);
        } else if (protectionLevel == 1) {
            // Basic protection
            recommendedGasPrice = this.getOptimalGasPrice(tx.gasprice, mevRisk);
            recommendedDelay = mevRisk > 70 ? 1 : 0;
            shouldExecute = mevRisk < 90;
        } else if (protectionLevel == 2) {
            // Standard protection
            recommendedGasPrice = this.getOptimalGasPrice(tx.gasprice, mevRisk);
            recommendedDelay = this.getRecommendedDelay(mevRisk, tradeAmount);
            shouldExecute = mevRisk < 80;
        } else {
            // Maximum protection
            recommendedGasPrice = this.getOptimalGasPrice(tx.gasprice, mevRisk) * 120 / 100;
            recommendedDelay = this.getRecommendedDelay(mevRisk, tradeAmount) + 1;
            shouldExecute = mevRisk < 60;
        }
    }
    
    // Admin functions
    function blacklistBot(address bot) external onlyOwner {
        detectedBots[bot].isBlacklisted = true;
        emit MEVBotDetected(bot, detectedBots[bot].suspiciousTransactions);
    }
    
    function removeFromBlacklist(address bot) external onlyOwner {
        detectedBots[bot].isBlacklisted = false;
    }
    
    function setMaxProtectedSlippage(uint256 newSlippage) external onlyOwner {
        require(newSlippage <= 1000, "Slippage too high"); // Max 10%
        maxProtectedSlippage = newSlippage;
    }
    
    // View functions
    function isBotBlacklisted(address bot) external view returns (bool) {
        return detectedBots[bot].isBlacklisted;
    }
    
    function getBotSuspicionLevel(address bot) external view returns (uint256) {
        return detectedBots[bot].suspiciousTransactions;
    }
}
