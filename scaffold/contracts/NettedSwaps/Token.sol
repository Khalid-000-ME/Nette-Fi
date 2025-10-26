// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

import "@openzeppelin/contracts/token/ERC20/ERC20.sol";
import "@openzeppelin/contracts/access/Ownable.sol";

/**
 * @title Token
 * @dev ERC20 token updated to Solidity ^0.8.19 using OpenZeppelin contracts
 * Simplified version that maintains core functionality while being compatible
 * with the latest OpenZeppelin library version.
 */
contract Token is ERC20, Ownable {
    
    event BalanceQuery(uint256 val);

    /**
     * @dev Constructor that initializes the token with OpenZeppelin ERC20
     * @param name_ The name of the token
     * @param symbol_ The symbol of the token
     */
    constructor(string memory name_, string memory symbol_) 
        ERC20(name_, symbol_) 
        Ownable()
    {
        // Mint initial supply to deployer
        _mint(msg.sender, 1000000 * 10**decimals());
    }

    /**
     * @dev Mints tokens to a specified address. Only owner can mint.
     * @param to The address to mint tokens to
     * @param amount The amount of tokens to mint
     */
    function mint(address to, uint256 amount) external onlyOwner {
        _mint(to, amount);
    }

    /**
     * @dev Burns tokens from a specified address. Only owner can burn.
     * @param from The address to burn tokens from
     * @param amount The amount of tokens to burn
     */
    function burn(address from, uint256 amount) external onlyOwner {
        _burn(from, amount);
    }

    /**
     * @dev Gets the balance and emits an event for tracking
     * @param account The account to query
     * @return The balance
     */
    function getBalanceWithEvent(address account) external returns (uint256) {
        uint256 balance = balanceOf(account);
        emit BalanceQuery(balance);
        return balance;
    }

    /**
     * @dev Batch transfer function for efficiency
     * @param recipients Array of recipient addresses
     * @param amounts Array of amounts to transfer
     */
    function batchTransfer(address[] calldata recipients, uint256[] calldata amounts) external {
        require(recipients.length == amounts.length, "Arrays length mismatch");
        
        for (uint256 i = 0; i < recipients.length; i++) {
            transfer(recipients[i], amounts[i]);
        }
    }

    /**
     * @dev Batch approve function for efficiency
     * @param spenders Array of spender addresses
     * @param amounts Array of amounts to approve
     */
    function batchApprove(address[] calldata spenders, uint256[] calldata amounts) external {
        require(spenders.length == amounts.length, "Arrays length mismatch");
        
        for (uint256 i = 0; i < spenders.length; i++) {
            approve(spenders[i], amounts[i]);
        }
    }
}
