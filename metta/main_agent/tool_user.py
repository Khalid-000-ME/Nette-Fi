#!/usr/bin/env python3
"""
Tool 4: User Details and Statistics
Uses frontend API /api/user to fetch user statistics, history, and global data
"""

import requests
import json
from typing import Dict, Any, Optional, List

# Frontend API configuration
FRONTEND_BASE_URL = "http://192.168.56.1:3000"
USER_ENDPOINT = f"{FRONTEND_BASE_URL}/api/user"

def get_user_details(
    action: str = "get_stats",
    wallet_signature: Optional[str] = None,
    wallet_address: Optional[str] = None,
    transaction_id: Optional[str] = None,
    batch_id: Optional[str] = None
) -> Dict[str, Any]:
    """
    Fetch user details and statistics using the frontend user API
    
    Args:
        action: Action to perform ('get_stats', 'get_history', 'get_scheduled_transaction', 'get_payroll_batch', 'get_global_stats')
        wallet_signature: User's wallet signature for address derivation (optional)
        wallet_address: Direct wallet address (optional, used if signature not provided)
        transaction_id: Transaction ID for scheduled transaction queries
        batch_id: Batch ID for payroll batch queries
    
    Returns:
        Dict containing user details and statistics
    """
    try:
        print(f"🔍 Tool 4: Getting user details...")
        print(f"   Action: {action}")
        
        # Derive address from signature if provided
        user_address = wallet_address
        if wallet_signature and not user_address:
            try:
                # For demo purposes, we'll use a simple derivation
                # In production, you'd use proper cryptographic derivation
                user_address = f"0x{wallet_signature[2:42]}"  # Simplified derivation
                print(f"   Derived address from signature: {user_address}")
            except Exception as e:
                print(f"   ⚠️ Could not derive address from signature: {e}")
        
        if wallet_address:
            print(f"   Using wallet address: {wallet_address}")
        
        # Prepare query parameters
        params = {"action": action}
        
        if user_address:
            params["userAddress"] = user_address
        if transaction_id:
            params["transactionId"] = transaction_id
        if batch_id:
            params["batchId"] = batch_id
        
        print(f"🌐 Calling user API: {USER_ENDPOINT}")
        
        # Make API request
        response = requests.get(
            USER_ENDPOINT,
            params=params,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Successfully retrieved user details!")
            
            # Process different action types
            if action == "get_stats" and result.get('success'):
                stats = result.get('stats', {})
                print(f"   User Address: {result.get('userAddress', 'N/A')}")
                print(f"   Total Transactions: {stats.get('totalTransactions', '0')}")
                print(f"   Total Gas Saved: {stats.get('totalGasSaved', '0')}")
                print(f"   Total Amount Processed: {stats.get('totalAmountProcessed', '0')} ETH")
                print(f"   Average Gas Savings: {stats.get('averageGasSavings', '0')}")
                print(f"   Savings Percentage: {stats.get('savingsPercentage', '0')}%")
                print(f"   Registered: {stats.get('isRegistered', False)}")
                
            elif action == "get_history" and result.get('success'):
                tx_history = result.get('transactionHistory', [])
                scheduled_txs = result.get('scheduledTransactions', [])
                print(f"   Transaction History: {len(tx_history)} transactions")
                print(f"   Scheduled Transactions: {len(scheduled_txs)} pending")
                
            elif action == "get_global_stats" and result.get('success'):
                global_stats = result.get('globalStats', {})
                print(f"   Total Users: {global_stats.get('totalUsers', '0')}")
                print(f"   Total Transactions Processed: {global_stats.get('totalTransactionsProcessed', '0')}")
                print(f"   Total Gas Saved Globally: {global_stats.get('totalGasSavedGlobally', '0')}")
                print(f"   Total Value Processed: {global_stats.get('totalValueProcessed', '0')} ETH")
            
            # Check if fallback/mock data was used
            if result.get('fallback'):
                print(f"   ⚠️ Using fallback/mock data (blockchain connection unavailable)")
            
            return {
                "success": True,
                "action": action,
                "data": result,
                "user_address": user_address,
                "message": f"Successfully retrieved {action.replace('_', ' ')} data"
            }
        else:
            error_msg = f"API returned status {response.status_code}"
            try:
                error_data = response.json()
                error_msg = error_data.get('error', error_msg)
            except:
                pass
            
            print(f"❌ Tool 4: API error - {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "status_code": response.status_code
            }
            
    except requests.exceptions.ConnectionError:
        error_msg = "Could not connect to frontend server. Make sure it's running on 192.168.56.1:3000"
        print(f"❌ Tool 4: Connection error - {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }
    except requests.exceptions.Timeout:
        error_msg = "Request timed out after 30 seconds"
        print(f"❌ Tool 4: Timeout error - {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ Tool 4: Unexpected error - {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }

# Tool schema for ASI:One
USER_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_user_details",
        "description": "Fetch user statistics, transaction history, and global platform data from the DeFi Payroll Manager. Provides comprehensive user analytics including gas savings, transaction counts, and platform-wide statistics.",
        "parameters": {
            "type": "object",
            "properties": {
                "action": {
                    "type": "string",
                    "enum": ["get_stats", "get_history", "get_scheduled_transaction", "get_payroll_batch", "get_global_stats"],
                    "description": "Action to perform: 'get_stats' for user statistics, 'get_history' for transaction history, 'get_scheduled_transaction' for specific scheduled transaction, 'get_payroll_batch' for batch details, 'get_global_stats' for platform-wide statistics",
                    "default": "get_stats"
                },
                "wallet_signature": {
                    "type": "string",
                    "description": "User's wallet signature for address derivation (optional, will derive address automatically)"
                },
                "wallet_address": {
                    "type": "string",
                    "description": "Direct wallet address (optional, used if signature not provided)"
                },
                "transaction_id": {
                    "type": "string",
                    "description": "Transaction ID for scheduled transaction queries (required for get_scheduled_transaction action)"
                },
                "batch_id": {
                    "type": "string",
                    "description": "Batch ID for payroll batch queries (required for get_payroll_batch action)"
                }
            },
            "required": ["action"],
            "additionalProperties": False
        },
        "strict": True
    }
}

if __name__ == "__main__":
    # Test the tool with different actions
    print("🧪 Testing User Details Tool")
    print("=" * 50)
    
    # Test 1: Get user stats
    print("Test 1: Get user statistics")
    result1 = get_user_details(
        action="get_stats",
        wallet_address="0x8aa62d370585e28fd2333325d3dbaef6112279Ce"
    )
    print(f"Success: {result1.get('success')}")
    
    # Test 2: Get global stats
    print("\nTest 2: Get global statistics")
    result2 = get_user_details(action="get_global_stats")
    print(f"Success: {result2.get('success')}")
    
    # Test 3: Get user history
    print("\nTest 3: Get user history")
    result3 = get_user_details(
        action="get_history",
        wallet_address="0x8aa62d370585e28fd2333325d3dbaef6112279Ce"
    )
    print(f"Success: {result3.get('success')}")
    
    print("\n📊 Test Summary:")
    print(f"✅ User Stats: {'Working' if result1.get('success') else 'Failed'}")
    print(f"✅ Global Stats: {'Working' if result2.get('success') else 'Failed'}")
    print(f"✅ User History: {'Working' if result3.get('success') else 'Failed'}")