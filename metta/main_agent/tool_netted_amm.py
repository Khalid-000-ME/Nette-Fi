#!/usr/bin/env python3
"""
Tool: Netted AMM Status and Analytics
Interfaces with /api/net_status to provide real-time netting information
"""

import requests
import json
from typing import Dict, Any, Optional

# Frontend API configuration
FRONTEND_BASE_URL = "http://localhost:3000"
NET_STATUS_ENDPOINT = f"{FRONTEND_BASE_URL}/api/net_status"

def get_netted_amm_status(detailed: bool = False, action: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """
    Get real-time status and analytics from the Netted AMM system
    
    Args:
        detailed (bool): Whether to include detailed information (recent batches, thread status)
        action (str, optional): Specific action for POST requests ('queue_swap', 'get_status')
        **kwargs: Additional parameters for specific actions
    
    Returns:
        Dict containing netted AMM status, metrics, and analytics
    """
    
    print(f"🔄 Fetching Netted AMM status...")
    print(f"   Detailed: {detailed}")
    if action:
        print(f"   Action: {action}")
    
    try:
        if action and action != 'get_status':
            # POST request for specific actions
            payload = {
                "action": action,
                "data": kwargs
            }
            
            print(f"   Making POST request to {NET_STATUS_ENDPOINT}")
            response = requests.post(
                NET_STATUS_ENDPOINT,
                json=payload,
                timeout=10
            )
        else:
            # GET request for status
            params = {}
            if detailed:
                params['detailed'] = 'true'
            
            print(f"   Making GET request to {NET_STATUS_ENDPOINT}")
            response = requests.get(
                NET_STATUS_ENDPOINT,
                params=params,
                timeout=10
            )
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Netted AMM status retrieved successfully")
            
            # Format the response for better readability
            formatted_response = {
                "success": True,
                "timestamp": data.get("timestamp"),
                "current_batch": data.get("currentBatch", {}),
                "network_status": data.get("network", {}),
                "real_time_metrics": data.get("metrics", {}),
                "contract_stats": data.get("stats", {}),
                "summary": _format_summary(data)
            }
            
            # Add detailed info if available
            if detailed and "detailed" in data:
                formatted_response["detailed_info"] = data["detailed"]
            
            # Add action-specific results
            if action == 'queue_swap' and "swapId" in data:
                formatted_response["swap_result"] = {
                    "swap_id": data.get("swapId"),
                    "batch_id": data.get("batchId"),
                    "queue_position": data.get("position"),
                    "estimated_wait_time": data.get("estimatedWaitTime")
                }
            
            return formatted_response
            
        else:
            error_msg = f"API request failed with status {response.status_code}"
            try:
                error_data = response.json()
                error_msg += f": {error_data.get('error', 'Unknown error')}"
            except:
                error_msg += f": {response.text}"
            
            print(f"❌ {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "status_code": response.status_code
            }
            
    except requests.exceptions.Timeout:
        error_msg = "Request timeout - frontend server may be unavailable"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "fallback_data": _get_fallback_data()
        }
    except requests.exceptions.ConnectionError:
        error_msg = "Connection error - frontend server may be down"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg,
            "fallback_data": _get_fallback_data()
        }
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }

def _format_summary(data: Dict[str, Any]) -> Dict[str, str]:
    """Format key metrics into a readable summary"""
    
    current_batch = data.get("currentBatch", {})
    network = data.get("network", {})
    metrics = data.get("metrics", {})
    stats = data.get("stats", {})
    
    summary = {
        "netting_status": current_batch.get("status", "unknown"),
        "active_requests": str(current_batch.get("activeRequests", 0)),
        "total_swaps_processed": str(stats.get("totalSwaps", 0)),
        "total_gas_saved": str(stats.get("totalGasSaved", 0)),
        "netting_efficiency": stats.get("nettingRate", "0%"),
        "current_block": str(network.get("currentBlock", {}).get("number", "unknown")),
        "parallel_threads": str(network.get("parallelThreads", 0)),
        "requests_per_second": str(metrics.get("requestsPerSecond", 0)),
        "average_gas_savings": metrics.get("averageGasSavings", "0%"),
        "uptime": metrics.get("uptimePercentage", "0%"),
        "contract_address": network.get("contractAddress", stats.get("contractAddress", "unknown"))
    }
    
    return summary

def _get_fallback_data() -> Dict[str, Any]:
    """Provide fallback data when API is unavailable"""
    return {
        "message": "Using cached/fallback data - live API unavailable",
        "current_batch": {
            "status": "unknown",
            "activeRequests": 0
        },
        "network_status": {
            "chainId": 118,
            "isConnected": False
        },
        "metrics": {
            "requestsPerSecond": 0,
            "averageGasSavings": "0%",
            "uptimePercentage": "0%"
        }
    }

# Tool schema for ASI:One agent
NETTED_AMM_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_netted_amm_status",
        "description": "Get real-time status, metrics, and analytics from the Netted AMM system. Shows current netting batch status, gas savings, network statistics, and contract performance metrics. Can also queue new swap requests.",
        "parameters": {
            "type": "object",
            "properties": {
                "detailed": {
                    "type": "boolean",
                    "description": "Whether to include detailed information like recent batches, thread pool status, and current requests. Default: false"
                },
                "action": {
                    "type": "string",
                    "enum": ["get_status", "queue_swap"],
                    "description": "Specific action to perform. 'get_status' for status info, 'queue_swap' to add a new swap request to the netting queue"
                },
                "user": {
                    "type": "string",
                    "description": "User address for queue_swap action (optional, will generate random if not provided)"
                },
                "tokenIn": {
                    "type": "string",
                    "description": "Input token for queue_swap action (e.g., 'ETH', 'USDC')"
                },
                "tokenOut": {
                    "type": "string", 
                    "description": "Output token for queue_swap action (e.g., 'USDC', 'DAI')"
                },
                "amountIn": {
                    "type": "string",
                    "description": "Amount to swap for queue_swap action (e.g., '1.5')"
                }
            },
            "required": []
        }
    }
}

# Test function
if __name__ == "__main__":
    print("Testing Netted AMM Tool...")
    
    # Test basic status
    result = get_netted_amm_status()
    print("Basic Status:", json.dumps(result, indent=2))
    
    # Test detailed status
    result = get_netted_amm_status(detailed=True)
    print("Detailed Status:", json.dumps(result, indent=2))
    
    # Test queue swap
    result = get_netted_amm_status(
        action="queue_swap",
        tokenIn="ETH",
        tokenOut="USDC", 
        amountIn="1.0"
    )
    print("Queue Swap Result:", json.dumps(result, indent=2))