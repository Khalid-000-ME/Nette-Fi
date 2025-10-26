#!/usr/bin/env python3
"""
Tool 3: Balance Checker Tool
Uses the /api/get_balance endpoint to fetch user's token balances
"""

import requests
import json
from typing import Dict, Any, Optional, List

# Frontend API configuration
FRONTEND_BASE_URL = "http://192.168.56.1:3000"
BALANCE_API_URL = f"{FRONTEND_BASE_URL}/api/get_balance"

def get_user_balances(
    wallet_signature: Optional[str] = None,
    wallet_address: Optional[str] = None,
    specific_tokens: Optional[List[str]] = None,
    timeout: int = 15
) -> Dict[str, Any]:
    """
    Get user's token balances using the balance API
    
    Args:
        wallet_signature: Private key or wallet signature (optional)
        wallet_address: Wallet address (optional, used if no signature provided)
        specific_tokens: List of specific tokens to check (optional)
        timeout: Request timeout in seconds
    
    Returns:
        Dict containing balance information and success status
    """
    
    print(f"🔍 Tool 3: Getting user balances...")
    
    try:
        # Prepare request payload
        payload = {}
        
        if wallet_signature:
            # Use private key if provided
            payload["private_key"] = wallet_signature
            print(f"   Using wallet signature for balance lookup")
        elif wallet_address:
            # Use address if provided
            payload["address"] = wallet_address
            print(f"   Using wallet address: {wallet_address}")
        else:
            return {
                "success": False,
                "error": "Either wallet_signature or wallet_address must be provided",
                "balances": [],
                "recommendations": [
                    "Provide your wallet private key for secure balance checking",
                    "Alternatively, provide your wallet address for read-only balance lookup",
                    "Private key format: 0x followed by 64 hexadecimal characters"
                ]
            }
        
        # Add specific tokens filter if requested
        if specific_tokens:
            payload["tokens"] = specific_tokens
            print(f"   Filtering for specific tokens: {', '.join(specific_tokens)}")
        
        # Make API request
        print(f"🌐 Calling balance API: {BALANCE_API_URL}")
        response = requests.post(
            BALANCE_API_URL,
            json=payload,
            headers={'Content-Type': 'application/json'},
            timeout=timeout
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Process balance data
            balances = data.get("balances", [])
            total_tokens = len(balances)
            non_zero_balances = [b for b in balances if float(b.get("balance", "0")) > 0]
            
            print(f"✅ Successfully retrieved balances!")
            print(f"   Address: {data.get('address', 'Unknown')}")
            print(f"   Network: {data.get('network', 'Unknown')}")
            print(f"   Total tokens: {total_tokens}")
            print(f"   Non-zero balances: {len(non_zero_balances)}")
            
            # Create summary for each token
            balance_summary = []
            for token in balances:
                balance_value = float(token.get("balance", "0"))
                balance_summary.append({
                    "token": token.get("symbol", "Unknown"),
                    "balance": token.get("balance", "0"),
                    "balance_formatted": f"{balance_value:,.6f}",
                    "has_balance": balance_value > 0,
                    "contract_address": token.get("contract_address"),
                    "decimals": token.get("decimals", 18)
                })
            
            return {
                "success": True,
                "address": data.get("address"),
                "network": data.get("network", "Arcology DevNet"),
                "chain_id": data.get("chain_id", 118),
                "total_tokens": total_tokens,
                "tokens_with_balance": len(non_zero_balances),
                "balances": balance_summary,
                "raw_data": data,
                "timestamp": data.get("timestamp"),
                "recommendations": [
                    f"You have balances in {len(non_zero_balances)} out of {total_tokens} supported tokens",
                    "Use these balances for payroll transactions or token swaps",
                    "Consider the gas costs (ETH) when planning transactions"
                ]
            }
        
        else:
            error_data = {}
            try:
                error_data = response.json()
            except:
                pass
            
            error_msg = error_data.get("error", f"HTTP {response.status_code}")
            print(f"❌ Balance API error: {error_msg}")
            
            return {
                "success": False,
                "error": error_msg,
                "status_code": response.status_code,
                "balances": [],
                "recommendations": [
                    "Check if the frontend server is running (npm run dev)",
                    "Verify your wallet signature or address format",
                    "Ensure the Arcology DevNet is accessible"
                ]
            }
    
    except requests.exceptions.Timeout:
        print(f"❌ Balance API timeout after {timeout}s")
        return {
            "success": False,
            "error": f"Request timeout after {timeout} seconds",
            "balances": [],
            "recommendations": [
                "The balance API is taking too long to respond",
                "Check network connectivity to the frontend server",
                "Try again with a longer timeout"
            ]
        }
    
    except requests.exceptions.ConnectionError:
        print(f"❌ Cannot connect to balance API")
        return {
            "success": False,
            "error": "Cannot connect to frontend server",
            "balances": [],
            "recommendations": [
                "Make sure the frontend server is running: npm run dev",
                "Check if the server is accessible at http://192.168.56.1:3000",
                "Verify network connectivity"
            ]
        }
    
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "balances": [],
            "recommendations": [
                "This appears to be an unexpected error",
                "Check the error details and try again",
                "Contact support if the issue persists"
            ]
        }

# Tool schema for ASI:One integration
BALANCE_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_user_balances",
        "description": "Get user's token balances for all supported tokens (ETH, USDC, WETH, DAI, USDT, MATIC) using their wallet signature or address. Shows real-time balances from Arcology DevNet.",
        "parameters": {
            "type": "object",
            "properties": {
                "wallet_signature": {
                    "type": "string",
                    "description": "User's wallet private key (64-character hex string starting with 0x). Preferred method for secure balance checking."
                },
                "wallet_address": {
                    "type": "string", 
                    "description": "User's wallet address (42-character hex string starting with 0x). Alternative to private key for read-only balance lookup."
                },
                "specific_tokens": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Optional list of specific tokens to check. Available: ETH, USDC, WETH, DAI, USDT, MATIC. If not provided, checks all tokens."
                }
            },
            "required": [],
            "additionalProperties": False
        }
    }
}

def main():
    """Test the balance tool directly"""
    print("🧪 Testing Balance Tool")
    print("=" * 50)
    
    # Test with known account
    test_address = "0x8aa62d370585e28fd2333325d3dbaef6112279Ce"
    
    print("Test 1: Get all balances by address")
    result1 = get_user_balances(wallet_address=test_address)
    print(f"Success: {result1['success']}")
    if result1['success']:
        print(f"Tokens with balance: {result1['tokens_with_balance']}")
        for balance in result1['balances']:
            if balance['has_balance']:
                print(f"  {balance['token']}: {balance['balance_formatted']}")
    
    print("\nTest 2: Get specific tokens only")
    result2 = get_user_balances(
        wallet_address=test_address,
        specific_tokens=["ETH", "USDC", "DAI"]
    )
    print(f"Success: {result2['success']}")
    if result2['success']:
        print(f"Filtered tokens: {len(result2['balances'])}")
    
    print("\nTest 3: Error handling - no credentials")
    result3 = get_user_balances()
    print(f"Success: {result3['success']}")
    print(f"Error: {result3.get('error', 'None')}")

if __name__ == "__main__":
    main()