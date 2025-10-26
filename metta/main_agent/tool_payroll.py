#!/usr/bin/env python3
"""
Tool Payroll: Safe Batch Payroll Processing
Uses frontend API /api/payroll to execute large payroll batches safely
Prevents Arcology scheduler crashes by using smart chunking
"""

import requests
import json
import re
from typing import Dict, Any, Optional, List

# Frontend API configuration
FRONTEND_BASE_URL = "http://192.168.56.1:3000"
PAYROLL_ENDPOINT = f"{FRONTEND_BASE_URL}/api/payroll"

def parse_payroll_entries(payroll_data: str) -> List[Dict[str, str]]:
    """
    Parse payroll data from various formats
    
    Supported formats:
    1. "Alice:100 USDC:0x123..., Bob:200 DAI:0x456..."
    2. "Employee1,0x123...,100,USDC|Employee2,0x456...,200,DAI"
    3. JSON-like: "[{'name':'Alice','address':'0x123...','amount':'100','token':'USDC'}]"
    """
    entries = []
    
    try:
        # Try JSON format first
        if payroll_data.strip().startswith('['):
            json_data = json.loads(payroll_data)
            for item in json_data:
                entries.append({
                    "employee_name": item.get('name', ''),
                    "employee_address": item.get('address', ''),
                    "amount": str(item.get('amount', '')),
                    "token": item.get('token', 'USDC').upper(),
                    "department": item.get('department', ''),
                    "position": item.get('position', '')
                })
            return entries
    except:
        pass
    
    # Try colon-separated format: "Alice:100 USDC:0x123..."
    colon_pattern = r'([^:,]+):(\d+(?:\.\d+)?)\s+([A-Z]+):(0x[a-fA-F0-9]{40})'
    colon_matches = re.findall(colon_pattern, payroll_data, re.IGNORECASE)
    
    if colon_matches:
        for match in colon_matches:
            name, amount, token, address = match
            entries.append({
                "employee_name": name.strip(),
                "employee_address": address,
                "amount": amount,
                "token": token.upper(),
                "department": "",
                "position": ""
            })
        return entries
    
    # Try pipe-separated format: "Employee1,0x123...,100,USDC|Employee2,0x456...,200,DAI"
    if '|' in payroll_data:
        employee_entries = payroll_data.split('|')
        for entry in employee_entries:
            parts = entry.strip().split(',')
            if len(parts) >= 4:
                entries.append({
                    "employee_name": parts[0].strip(),
                    "employee_address": parts[1].strip(),
                    "amount": parts[2].strip(),
                    "token": parts[3].strip().upper(),
                    "department": parts[4].strip() if len(parts) > 4 else "",
                    "position": parts[5].strip() if len(parts) > 5 else ""
                })
        return entries
    
    # Try simple format: "100 USDC to 0x123... for Alice, 200 DAI to 0x456... for Bob"
    simple_pattern = r'(\d+(?:\.\d+)?)\s+([A-Z]+)\s+to\s+(0x[a-fA-F0-9]{40})(?:\s+for\s+([^,]+))?'
    simple_matches = re.findall(simple_pattern, payroll_data, re.IGNORECASE)
    
    if simple_matches:
        for i, match in enumerate(simple_matches):
            amount, token, address, name = match
            entries.append({
                "employee_name": name.strip() if name else f"Employee_{i+1}",
                "employee_address": address,
                "amount": amount,
                "token": token.upper(),
                "department": "",
                "position": ""
            })
        return entries
    
    return entries

def process_safe_payroll(
    company_signature: str,
    payroll_data: str,
    execute_immediately: bool = True,
    max_chunk_size: int = 2,
    description: str = ""
) -> Dict[str, Any]:
    """
    Process payroll batch safely using smart chunking to prevent container crashes
    
    Args:
        company_signature: Company's authorization signature
        payroll_data: Payroll entries in supported format
        execute_immediately: Whether to execute now or queue for later
        max_chunk_size: Maximum transactions per chunk (default 2 for safety)
        description: Optional description for the payroll batch
    
    Returns:
        Dict containing payroll processing results
    """
    try:
        print(f"💰 Tool Payroll: Processing safe payroll batch...")
        print(f"   Execute Immediately: {execute_immediately}")
        print(f"   Max Chunk Size: {max_chunk_size} (scheduler-safe)")
        
        # Parse payroll entries
        payroll_entries = parse_payroll_entries(payroll_data)
        
        if not payroll_entries:
            print("❌ No valid payroll entries found in the provided data")
            return {
                "success": False,
                "error": "No valid payroll entries could be parsed from the input"
            }
        
        print(f"   Parsed Entries: {len(payroll_entries)}")
        for i, entry in enumerate(payroll_entries[:5]):  # Show first 5
            print(f"     {i+1}. {entry['employee_name']}: {entry['amount']} {entry['token']} → {entry['employee_address'][:8]}...")
        if len(payroll_entries) > 5:
            print(f"     ... and {len(payroll_entries) - 5} more employees")
        
        # Prepare request payload
        payload = {
            "company_signature": company_signature,
            "payroll_entries": payroll_entries,
            "execute_immediately": execute_immediately,
            "max_chunk_size": max_chunk_size,
            "description": description
        }
        
        # Make API request
        response = requests.post(
            PAYROLL_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=60  # Longer timeout for large payrolls
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Tool Payroll: Processing successful!")
            print(f"   Payroll ID: {result.get('payroll_id', 'N/A')}")
            print(f"   Status: {result.get('status', 'N/A')}")
            
            if result.get('status') == 'completed':
                total_employees = result.get('total_employees', 0)
                processed_employees = result.get('processed_employees', 0)
                
                print(f"   Employees: {processed_employees}/{total_employees} paid")
                
                # Display transaction hashes
                tx_hashes = result.get('transaction_hashes', [])
                if tx_hashes:
                    print(f"   Transaction Hashes ({len(tx_hashes)}):")
                    for i, hash_val in enumerate(tx_hashes[:10]):  # Show max 10
                        print(f"     TX {i+1}: {hash_val}")
                    if len(tx_hashes) > 10:
                        print(f"     ... and {len(tx_hashes) - 10} more")
                
                # Display chunk results
                chunk_results = result.get('chunk_results', [])
                if chunk_results:
                    print(f"   Chunk Processing:")
                    successful_chunks = sum(1 for c in chunk_results if c.get('success'))
                    print(f"     Chunks: {successful_chunks}/{len(chunk_results)} successful")
                    for i, chunk in enumerate(chunk_results[:3]):  # Show first 3 chunks
                        status_icon = "✅" if chunk.get('success') else "❌"
                        print(f"     {status_icon} Chunk {i+1}: {len(chunk.get('hashes', []))}/{chunk.get('employees', 0)} employees paid")
                
                # Display summary
                summary = result.get('summary', {})
                if summary:
                    print(f"   Summary:")
                    print(f"     Success Rate: {summary.get('success_rate', 'N/A')}")
                    print(f"     Total Chunks: {summary.get('total_chunks', 0)}")
                    print(f"     Scheduler Safe: {summary.get('scheduler_safe', False)}")
            
            return {
                "success": True,
                "data": result,
                "payroll_id": result.get('payroll_id'),
                "total_employees": result.get('total_employees', 0),
                "processed_employees": result.get('processed_employees', 0),
                "transaction_hashes": result.get('transaction_hashes', []),
                "chunk_results": result.get('chunk_results', []),
                "summary": result.get('summary', {}),
                "message": f"Successfully processed payroll for {result.get('processed_employees', 0)}/{result.get('total_employees', 0)} employees",
                "scheduler_safe": True
            }
        else:
            error_msg = f"API returned status {response.status_code}"
            try:
                error_data = response.json()
                error_msg = error_data.get('error', error_msg)
            except:
                pass
            
            print(f"❌ Tool Payroll: API error - {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "status_code": response.status_code
            }
            
    except requests.exceptions.ConnectionError:
        error_msg = "Could not connect to frontend server. Make sure it's running on 192.168.56.1:3000"
        print(f"❌ Tool Payroll: Connection error - {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }
    except requests.exceptions.Timeout:
        error_msg = "Request timed out after 60 seconds"
        print(f"❌ Tool Payroll: Timeout error - {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ Tool Payroll: Unexpected error - {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }

# Tool schema for ASI:One
PAYROLL_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "process_safe_payroll",
        "description": "Process large payroll batches safely using smart chunking to prevent Arcology scheduler crashes. Ideal for paying multiple employees with different tokens. Uses chunk size of 2 transactions to ensure container stability.",
        "parameters": {
            "type": "object",
            "properties": {
                "company_signature": {
                    "type": "string",
                    "description": "Company's authorization signature for payroll processing"
                },
                "payroll_data": {
                    "type": "string",
                    "description": "Payroll entries in supported formats: 'Alice:100 USDC:0x123..., Bob:200 DAI:0x456...' or 'Employee1,0x123...,100,USDC|Employee2,0x456...,200,DAI' or JSON array"
                },
                "execute_immediately": {
                    "type": "boolean",
                    "description": "Whether to execute payroll immediately (true) or queue for later (false)",
                    "default": True
                },
                "max_chunk_size": {
                    "type": "integer",
                    "description": "Maximum transactions per chunk (default 2 for scheduler safety, max 2 recommended)",
                    "minimum": 1,
                    "maximum": 2,
                    "default": 2
                },
                "description": {
                    "type": "string",
                    "description": "Optional description for the payroll batch (e.g., 'Monthly salary payments - October 2024')",
                    "default": ""
                }
            },
            "required": ["company_signature", "payroll_data"],
            "additionalProperties": False
        },
        "strict": True
    }
}

if __name__ == "__main__":
    # Test the tool with sample payroll data
    test_payroll = "Alice:1000 USDC:0x21522c86A586e696961b68aa39632948D9F11170, Bob:1500 DAI:0xa75Cd05BF16BbeA1759DE2A66c0472131BC5Bd8D, Charlie:800 USDT:0x2c7161284197e40E83B1b657e98B3bb8FF3C90ed"
    
    test_result = process_safe_payroll(
        company_signature="test_company_signature_abc123",
        payroll_data=test_payroll,
        execute_immediately=True,
        max_chunk_size=2,
        description="Test payroll batch - October 2024"
    )
    
    print("\n🧪 Test Result:")
    print(json.dumps(test_result, indent=2))
