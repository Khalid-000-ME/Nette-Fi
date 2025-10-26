import { NextRequest, NextResponse } from 'next/server';
import { ethers } from 'ethers';

// Arcology DevNet configuration - matching wallet page exactly
const ARCOLOGY_RPC_URL = "http://192.168.29.121:8545";
const CHAIN_ID = 118;

// Contract addresses - exactly as used in wallet page
const CONTRACTS = {
  NettedAMM: '0x53FA213b0Ef9fA979BD10665742a8D47FE35BCC2',
  USDC: '0x22C3D0cC5CAb74855B991F1Fb7defc8BaC93ca7C',
  WETH: '0x9C7FA77904AB82F0649ca0B73507b6042AAB76Fb',
  DAI: '0x79fb9184DEECCb8bbd2b835B82dc6D67B8aEe185',
  USDT: '0x1a176D63a9250Ab6fAE00E3C0d2D1CEdBB313f6C',
  MATIC: '0x6BE7656dc44F9cBC55942DEED70c200b5a5185C7',
  SOL: '0x747e0f49813fac6D48f2B4A7c41534B7f8E147c0',
  LINK: '0x8660b77CDaF11e330c8b48FE198A87b8dE6C4B13',
  AVAX: '0x510C531eb6f4C4ebC2FBf30EaA7B53B24A1548F2'
};

// Token configurations - exactly as used in wallet page
const TOKENS = {
  USDC: { decimals: 6, symbol: 'USDC' },
  WETH: { decimals: 18, symbol: 'WETH' },
  DAI: { decimals: 18, symbol: 'DAI' },
  USDT: { decimals: 6, symbol: 'USDT' },
  MATIC: { decimals: 18, symbol: 'MATIC' },
  SOL: { decimals: 9, symbol: 'SOL' },
  LINK: { decimals: 18, symbol: 'LINK' },
  AVAX: { decimals: 18, symbol: 'AVAX' }
};

// ERC20 ABI for balance checking
const ERC20_ABI = [
  'function balanceOf(address owner) view returns (uint256)',
  'function decimals() view returns (uint8)',
  'function symbol() view returns (string)',
  'function name() view returns (string)'
];

interface BalanceRequest {
  address?: string;
  private_key?: string;
  tokens?: string[]; // Optional: specific tokens to check
}

interface TokenBalance {
  symbol: string;
  name: string;
  balance: string;
  balance_wei: string;
  decimals: number;
  contract_address: string | null;
  usd_value?: string;
}

interface BalanceResponse {
  address: string;
  chain_id: number;
  network: string;
  balances: TokenBalance[];
  total_usd_value: string;
  timestamp: string;
}

// Load balances exactly like the wallet page does
async function loadBalances(provider: ethers.JsonRpcProvider, signer: ethers.Wallet, address: string): Promise<TokenBalance[]> {
  const balances: TokenBalance[] = [];
  
  try {
    console.log(`🔍 Loading balances for address: ${address}`);
    
    // ETH Balance - exactly like wallet page
    const ethBalance = await provider.getBalance(address);
    const ethFormatted = ethers.formatEther(ethBalance);
    
    balances.push({
      symbol: 'ETH',
      name: 'Ethereum',
      balance: parseFloat(ethFormatted).toFixed(6),
      balance_wei: ethBalance.toString(),
      decimals: 18,
      contract_address: null,
      usd_value: '0.00'
    });
    
    console.log(`✅ ETH balance: ${ethFormatted}`);
    
    // Token Balances - exactly like wallet page
    for (const [symbol, contractAddress] of Object.entries(CONTRACTS)) {
      if (symbol === 'NettedAMM') continue;
      
      try {
        console.log(`🔍 Getting ${symbol} balance from ${contractAddress}`);
        
        const contract = new ethers.Contract(contractAddress, ERC20_ABI, signer);
        const balance = await contract.balanceOf(address);
        const decimals = TOKENS[symbol as keyof typeof TOKENS].decimals;
        const formatted = ethers.formatUnits(balance, decimals);
        
        balances.push({
          symbol: symbol,
          name: symbol, // Will be enhanced if we can get name from contract
          balance: parseFloat(formatted).toFixed(6),
          balance_wei: balance.toString(),
          decimals: decimals,
          contract_address: contractAddress,
          usd_value: '0.00'
        });
        
        console.log(`✅ ${symbol} balance: ${formatted}`);
        
      } catch (error) {
        console.error(`❌ Error getting ${symbol} balance:`, error);
        
        // Add zero balance entry for failed tokens
        const decimals = TOKENS[symbol as keyof typeof TOKENS]?.decimals || 18;
        balances.push({
          symbol: symbol,
          name: symbol + ' (Error)',
          balance: '0.000000',
          balance_wei: '0',
          decimals: decimals,
          contract_address: contractAddress,
          usd_value: '0.00'
        });
      }
    }
    
    return balances;
    
  } catch (error) {
    console.error('❌ Error loading balances:', error);
    throw error;
  }
}

// Create a dummy private key for signer (wallet page uses actual user's private key)
// We'll use the first test account's private key as a dummy signer
const DUMMY_PRIVATE_KEY = "0x2289ae919f03075448d567c9c4a22846ce3711731c895f1bea572cef25bb346f";

async function getAllTokenBalances(
  provider: ethers.JsonRpcProvider,
  address: string,
  requestedTokens?: string[]
): Promise<TokenBalance[]> {
  try {
    // Create signer exactly like wallet page does
    const signer = new ethers.Wallet(DUMMY_PRIVATE_KEY, provider);
    
    // Load balances using the same method as wallet page
    const allBalances = await loadBalances(provider, signer, address);
    
    // Filter to requested tokens if specified
    if (requestedTokens && requestedTokens.length > 0) {
      return allBalances.filter(balance => 
        requestedTokens.includes(balance.symbol)
      );
    }
    
    return allBalances;
    
  } catch (error) {
    console.error('❌ Failed to get all token balances:', error);
    throw error;
  }
}

export async function POST(request: NextRequest) {
  try {
    let body: BalanceRequest;
    
    try {
      body = await request.json();
    } catch (jsonError) {
      return NextResponse.json(
        { error: 'Invalid JSON in request body' },
        { status: 400 }
      );
    }
    
    console.log('🔍 Balance request:', {
      hasAddress: !!body.address,
      hasPrivateKey: !!body.private_key,
      requestedTokens: body.tokens?.length || 'all'
    });
    
    let userAddress: string;
    
    // Determine user address
    if (body.address) {
      userAddress = body.address;
    } else if (body.private_key) {
      try {
        const wallet = new ethers.Wallet(body.private_key);
        userAddress = wallet.address;
      } catch (error) {
        return NextResponse.json(
          { error: 'Invalid private key format' },
          { status: 400 }
        );
      }
    } else {
      return NextResponse.json(
        { error: 'Either address or private_key must be provided' },
        { status: 400 }
      );
    }
    
    // Validate address format
    if (!ethers.isAddress(userAddress)) {
      return NextResponse.json(
        { error: 'Invalid Ethereum address format' },
        { status: 400 }
      );
    }
    
    // Initialize provider
    let provider: ethers.JsonRpcProvider;
    try {
      provider = new ethers.JsonRpcProvider(ARCOLOGY_RPC_URL);
      
      // Test connection
      await provider.getBlockNumber();
    } catch (error) {
      console.error('Failed to connect to Arcology RPC:', error);
      return NextResponse.json(
        { error: 'Failed to connect to blockchain network' },
        { status: 503 }
      );
    }
    
    // Get all token balances
    const balances = await getAllTokenBalances(provider, userAddress, body.tokens);
    
    // Calculate total USD value (would need real price feeds)
    const totalUsdValue = balances.reduce((sum, token) => {
      return sum + parseFloat(token.usd_value || '0');
    }, 0);
    
    const response: BalanceResponse = {
      address: userAddress,
      chain_id: CHAIN_ID,
      network: 'Arcology DevNet',
      balances: balances,
      total_usd_value: totalUsdValue.toFixed(2),
      timestamp: new Date().toISOString()
    };
    
    console.log(`✅ Retrieved balances for ${balances.length} tokens`);
    console.log(`   Address: ${userAddress}`);
    console.log(`   Non-zero balances: ${balances.filter(b => parseFloat(b.balance) > 0).length}`);
    
    return NextResponse.json(response);
    
  } catch (error) {
    console.error('❌ Balance API error:', error);
    return NextResponse.json(
      { 
        error: 'Failed to retrieve balances',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const address = searchParams.get('address');
    const tokens = searchParams.get('tokens')?.split(',');
    
    if (!address) {
      return NextResponse.json(
        { error: 'Address parameter is required' },
        { status: 400 }
      );
    }
    
    // Validate address
    if (!ethers.isAddress(address)) {
      return NextResponse.json(
        { error: 'Invalid Ethereum address format' },
        { status: 400 }
      );
    }
    
    // Initialize provider
    let provider: ethers.JsonRpcProvider;
    try {
      provider = new ethers.JsonRpcProvider(ARCOLOGY_RPC_URL);
      await provider.getBlockNumber();
    } catch (error) {
      return NextResponse.json(
        { error: 'Failed to connect to blockchain network' },
        { status: 503 }
      );
    }
    
    // Get balances
    const balances = await getAllTokenBalances(provider, address, tokens);
    
    const response: BalanceResponse = {
      address: address,
      chain_id: CHAIN_ID,
      network: 'Arcology DevNet',
      balances: balances,
      total_usd_value: '0.00',
      timestamp: new Date().toISOString()
    };
    
    return NextResponse.json(response);
    
  } catch (error) {
    console.error('❌ Balance GET API error:', error);
    return NextResponse.json(
      { 
        error: 'Failed to retrieve balances',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}