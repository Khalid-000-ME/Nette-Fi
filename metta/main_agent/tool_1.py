#!/usr/bin/env python3
"""
Tool 1: Batch Transaction Approval
Uses frontend API /api/approve to execute batched transactions
"""

import requests
import json
import re
from typing import Dict, Any, Optional, List

# Frontend API configuration
FRONTEND_BASE_URL = "http://192.168.56.1:3000"
APPROVE_ENDPOINT = f"{FRONTEND_BASE_URL}/api/approve"

def parse_transaction_specs(user_input: str) -> List[Dict[str, str]]:
    """
    Parse user input to extract transaction specifications
    
    Examples:
    - "100 USDC to 0x123..., 200 DAI to 0x456..."
    - "Send 50 ETH to 0xabc... and 100 USDT to 0xdef..."
    """
    transactions = []
    
    # Pattern to match: amount + token + to + address
    pattern = r'(\d+(?:\.\d+)?)\s+([A-Z]+)\s+to\s+(0x[a-fA-F0-9]{40})'
    matches = re.findall(pattern, user_input, re.IGNORECASE)
    
    for match in matches:
        amount, token, recipient = match
        transactions.append({
            "token": token.upper(),
            "amount": amount,
            "recipient": recipient
        })
    
    return transactions

def approve_batch_transactions(
    analysis_id: str,
    simulation_id: int,
    wallet_signature: str,
    execute_immediately: bool = True,
    batch_size: int = 5,
    transaction_type: str = "payroll",
    custom_transactions: Optional[str] = None
) -> Dict[str, Any]:
    """
    Execute batch transactions using the frontend approve API
    
    Args:
        analysis_id: ID of the analysis that generated this request
        simulation_id: ID of the simulation to execute
        wallet_signature: User's wallet signature for authorization
        execute_immediately: Whether to execute now or queue for later
        batch_size: Number of transactions in the batch
        transaction_type: Type of transactions ('payroll', 'swap', 'mixed')
        custom_transactions: Custom transaction specifications (e.g., "100 USDC to 0x123..., 200 DAI to 0x456...")
    
    Returns:
        Dict containing execution results
    """
    try:
        print(f"🔧 Tool 1: Executing batch transactions...")
        print(f"   Analysis ID: {analysis_id}")
        print(f"   Simulation ID: {simulation_id}")
        print(f"   Batch Size: {batch_size}")
        print(f"   Type: {transaction_type}")
        print(f"   Execute Immediately: {execute_immediately}")
        
        # Parse custom transactions if provided
        custom_tx_specs = None
        if custom_transactions:
            custom_tx_specs = parse_transaction_specs(custom_transactions)
            if custom_tx_specs:
                print(f"   Custom Transactions: {len(custom_tx_specs)} parsed")
                for i, spec in enumerate(custom_tx_specs):
                    print(f"     TX {i+1}: {spec['amount']} {spec['token']} → {spec['recipient'][:8]}...")
        
        # Prepare request payload
        payload = {
            "analysis_id": analysis_id,
            "simulation_id": simulation_id,
            "wallet_signature": wallet_signature,
            "execute_immediately": execute_immediately,
            "batch_size": batch_size,
            "transaction_type": transaction_type
        }
        
        # Add custom transactions if parsed
        if custom_tx_specs:
            payload["custom_transactions"] = custom_tx_specs
        
        # Make API request
        response = requests.post(
            APPROVE_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Tool 1: Batch execution successful!")
            print(f"   Approval ID: {result.get('approval_id', 'N/A')}")
            print(f"   Status: {result.get('status', 'N/A')}")
            
            if result.get('status') == 'executed':
                print(f"   Transactions: {result.get('transaction_count', 0)}")
                print(f"   Block Number: {result.get('block_number', 'N/A')}")
                
                # Display transaction hashes if available
                tx_hashes = result.get('transaction_hashes', [])
                if tx_hashes:
                    print(f"   Transaction Hashes ({len(tx_hashes)}):")
                    for i, hash_val in enumerate(tx_hashes[:10]):  # Show max 10
                        print(f"     TX {i+1}: {hash_val}")
                    if len(tx_hashes) > 10:
                        print(f"     ... and {len(tx_hashes) - 10} more")
                
                # Display transaction details if available
                tx_details = result.get('transaction_details', [])
                if tx_details:
                    print(f"   Transaction Details:")
                    for i, detail in enumerate(tx_details[:5]):  # Show max 5 details
                        status_icon = "✅" if detail.get('status') == 'success' else "⏳" if detail.get('status') == 'pending' else "❌"
                        print(f"     {status_icon} TX {i+1}: {detail.get('from', 'Unknown')[:8]}... → {detail.get('to', 'Unknown')[:8]}... ({detail.get('value', '0')} ETH)")
                        if detail.get('gasUsed'):
                            print(f"         Gas Used: {detail.get('gasUsed')}")
                
                # Display summary if available
                summary = result.get('summary', {})
                if summary:
                    print(f"   Summary:")
                    print(f"     ✅ Successful: {summary.get('successful_transactions', 0)}")
                    print(f"     ⏳ Pending: {summary.get('pending_transactions', 0)}")
                    print(f"     ❌ Failed: {summary.get('failed_transactions', 0)}")
            
            return {
                "success": True,
                "data": result,
                "transaction_hashes": result.get('transaction_hashes', []),
                "transaction_details": result.get('transaction_details', []),
                "summary": result.get('summary', {}),
                "message": f"Successfully processed {result.get('transaction_count', 0)} transactions",
                "detailed_message": f"Executed {result.get('transaction_count', 0)} transactions in block {result.get('block_number', 'N/A')}. " +
                                  f"Hashes captured: {len(result.get('transaction_hashes', []))}"
            }
        else:
            error_msg = f"API returned status {response.status_code}"
            try:
                error_data = response.json()
                error_msg = error_data.get('error', error_msg)
            except:
                pass
            
            print(f"❌ Tool 1: API error - {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "status_code": response.status_code
            }
            
    except requests.exceptions.ConnectionError:
        error_msg = "Could not connect to frontend server. Make sure it's running on 192.168.56.1:3000"
        print(f"❌ Tool 1: Connection error - {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }
    except requests.exceptions.Timeout:
        error_msg = "Request timed out after 30 seconds"
        print(f"❌ Tool 1: Timeout error - {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ Tool 1: Unexpected error - {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }

# Tool schema for ASI:One
APPROVE_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "approve_batch_transactions",
        "description": "Execute batch transactions for payroll, swaps, or mixed operations using Arcology's parallel processing. This tool submits transactions to the blockchain and returns execution results.",
        "parameters": {
            "type": "object",
            "properties": {
                "analysis_id": {
                    "type": "string",
                    "description": "Unique identifier for the analysis that generated this transaction request"
                },
                "simulation_id": {
                    "type": "integer",
                    "description": "ID of the simulation strategy to execute (1-3, where 1=immediate, 2=delayed, 3=optimized)"
                },
                "wallet_signature": {
                    "type": "string",
                    "description": "User's wallet signature for transaction authorization"
                },
                "execute_immediately": {
                    "type": "boolean",
                    "description": "Whether to execute transactions immediately (true) or queue for later (false)",
                    "default": True
                },
                "batch_size": {
                    "type": "integer",
                    "description": "Number of transactions to include in the batch (minimum 1, recommended: 3-10 for optimal netting)",
                    "minimum": 1,
                    "default": 5
                },
                "transaction_type": {
                    "type": "string",
                    "enum": ["payroll", "swap", "mixed"],
                    "description": "Type of transactions: 'payroll' for employee payments, 'swap' for token exchanges, 'mixed' for combined operations",
                    "default": "payroll"
                },
                "custom_transactions": {
                    "type": "string",
                    "description": "Custom transaction specifications in natural language (e.g., '100 USDC to 0x123..., 200 DAI to 0x456...'). When provided, overrides default transaction patterns."
                }
            },
            "required": ["analysis_id", "simulation_id", "wallet_signature"],
            "additionalProperties": False
        },
        "strict": True
    }
}

if __name__ == "__main__":
    # Test the tool
    test_result = approve_batch_transactions(
        analysis_id="test_analysis_123",
        simulation_id=3,
        wallet_signature="test_signature_abc123",
        execute_immediately=True,
        batch_size=3,
        transaction_type="payroll"
    )
    
    print("\n🧪 Test Result:")
    print(json.dumps(test_result, indent=2))