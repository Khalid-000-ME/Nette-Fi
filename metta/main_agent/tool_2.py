#!/usr/bin/env python3
"""
Tool 2: Live Price Feed
Uses frontend API /api/get_price to get real-time price data
"""

import requests
import json
from typing import Dict, Any, Optional

# Frontend API configuration
FRONTEND_BASE_URL = "http://192.168.56.1:3000"
GET_PRICE_ENDPOINT = f"{FRONTEND_BASE_URL}/api/get_price"

def get_live_price(
    token: str,
    vs_currency: str = "usd",
    chain: str = "base",
    use_real_data: bool = True
) -> Dict[str, Any]:
    """
    Get live price data for a token using the frontend price API
    
    Args:
        token: Token symbol (e.g., 'ETH', 'USDC', 'DAI', 'BTC')
        vs_currency: Currency to price against (default: 'usd')
        chain: Blockchain network (default: 'base')
        use_real_data: Whether to use real Pyth data or mock data
    
    Returns:
        Dict containing price data and market metrics
    """
    try:
        print(f"📊 Tool 2: Fetching live price data...")
        print(f"   Token: {token.upper()}")
        print(f"   VS Currency: {vs_currency.upper()}")
        print(f"   Chain: {chain}")
        print(f"   Use Real Data: {use_real_data}")
        
        # Prepare request payload
        payload = {
            "token": token.upper(),
            "vs_currency": vs_currency.lower(),
            "chain": chain.lower(),
            "useRealData": use_real_data
        }
        
        # Make API request
        response = requests.post(
            GET_PRICE_ENDPOINT,
            json=payload,
            headers={"Content-Type": "application/json"},
            timeout=15
        )
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Tool 2: Price data retrieved successfully!")
            print(f"   Price: ${result.get('price_usd', 'N/A')}")
            print(f"   Source: {result.get('source', 'N/A')}")
            print(f"   24h Change: {result.get('price_change_24h', 'N/A')}")
            
            return {
                "success": True,
                "data": result,
                "message": f"Current {token.upper()} price: ${result.get('price_usd', 'N/A')} from {result.get('source', 'unknown source')}"
            }
        else:
            error_msg = f"API returned status {response.status_code}"
            try:
                error_data = response.json()
                error_msg = error_data.get('error', error_msg)
            except:
                pass
            
            print(f"❌ Tool 2: API error - {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "status_code": response.status_code
            }
            
    except requests.exceptions.ConnectionError:
        error_msg = "Could not connect to frontend server. Make sure it's running on 192.168.56.1:3000"
        print(f"❌ Tool 2: Connection error - {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }
    except requests.exceptions.Timeout:
        error_msg = "Request timed out after 15 seconds"
        print(f"❌ Tool 2: Timeout error - {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        print(f"❌ Tool 2: Unexpected error - {error_msg}")
        return {
            "success": False,
            "error": error_msg
        }

# Tool schema for ASI:One
PRICE_TOOL_SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_live_price",
        "description": "Get real-time price data for cryptocurrencies and tokens using Pyth Network price feeds. Returns current price, market metrics, volatility, and confidence intervals.",
        "parameters": {
            "type": "object",
            "properties": {
                "token": {
                    "type": "string",
                    "description": "Token symbol to get price for (e.g., 'ETH', 'BTC', 'USDC', 'DAI', 'USDT', 'WETH', 'SOL', 'AVAX', 'LINK', 'MATIC')"
                },
                "vs_currency": {
                    "type": "string",
                    "description": "Currency to price against",
                    "enum": ["usd", "eur", "btc", "eth"],
                    "default": "usd"
                },
                "chain": {
                    "type": "string",
                    "description": "Blockchain network for context",
                    "enum": ["ethereum", "base", "polygon", "arbitrum", "optimism", "bsc"],
                    "default": "base"
                },
                "use_real_data": {
                    "type": "boolean",
                    "description": "Whether to use real Pyth Network data (true) or mock data for testing (false)",
                    "default": True
                }
            },
            "required": ["token"],
            "additionalProperties": False
        },
        "strict": True
    }
}

if __name__ == "__main__":
    # Test the tool
    test_result = get_live_price(
        token="ETH",
        vs_currency="usd",
        chain="base",
        use_real_data=True
    )
    
    print("\n🧪 Test Result:")
    print(json.dumps(test_result, indent=2))