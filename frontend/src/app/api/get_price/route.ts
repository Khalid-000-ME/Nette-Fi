import { NextRequest, NextResponse } from 'next/server';

interface PriceRequest {
  token: string;
  vs_currency: string;
  chain: string;
  useRealData?: boolean;
}

interface PythPriceData {
  id: string;
  price: {
    price: string;
    conf: string;
    expo: number;
    publish_time: number;
  };
  ema_price: {
    price: string;
    conf: string;
    expo: number;
    publish_time: number;
  };
}

// Pyth price feed IDs for major tokens
const PYTH_PRICE_IDS: { [key: string]: string } = {
  'ETH': '0xff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace',
  'BTC': '0xe62df6c8b4a85fe1a67db44dc12de5db330f7ac66b72dc658afedf0f4a415b43',
  'USDC': '0xeaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a',
  'USDT': '0x2b89b9dc8fdf9f34709a5b106b472f0f39bb6ca9ce04b0fd7f2e971688e2e53b',
  'WETH': '0xff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace', // Same as ETH
  'DAI': '0xb0948a5e5313200c632b51bb5ca32f6de0d36e9950a942d19751e833f70dabfd'
};

// Pyth Hermes API endpoints
const PYTH_ENDPOINTS = {
  mainnet: 'https://hermes.pyth.network',
  testnet: 'https://hermes-beta.pyth.network'
};

function calculateVolatility(prices: number[]): string {
  if (prices.length < 2) return "0.0";
  
  const returns = [];
  for (let i = 1; i < prices.length; i++) {
    returns.push((prices[i] - prices[i-1]) / prices[i-1]);
  }
  
  const mean = returns.reduce((sum, ret) => sum + ret, 0) / returns.length;
  const variance = returns.reduce((sum, ret) => sum + Math.pow(ret - mean, 2), 0) / returns.length;
  const volatility = Math.sqrt(variance) * 100;
  
  return volatility.toFixed(1);
}

async function fetchPythPrice(token: string, chain: string): Promise<any> {
  const priceId = PYTH_PRICE_IDS[token.toUpperCase()];
  
  if (!priceId) {
    throw new Error(`Price feed not available for token: ${token}`);
  }
  
  // Use mainnet for production chains, testnet for testnets
  const isTestnet = chain.includes('sepolia') || chain.includes('testnet') || chain.includes('goerli');
  const endpoint = isTestnet ? PYTH_ENDPOINTS.testnet : PYTH_ENDPOINTS.mainnet;
  
  try {
    console.log(`🔮 Fetching Pyth price for ${token} (${priceId})`);
    
    // Fetch latest price data
    const response = await fetch(`${endpoint}/api/latest_price_feeds?ids[]=${priceId}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      },
      next: { revalidate: 10 } // Cache for 10 seconds
    });
    
    if (!response.ok) {
      throw new Error(`Pyth API error: ${response.status} ${response.statusText}`);
    }
    
    const data = await response.json();
    
    if (!data || data.length === 0) {
      throw new Error(`No price data found for ${token}`);
    }
    
    const priceData: PythPriceData = data[0];
    
    // Convert price from Pyth format (price * 10^expo) to USD
    const price = parseFloat(priceData.price.price) * Math.pow(10, priceData.price.expo);
    const confidence = parseFloat(priceData.price.conf) * Math.pow(10, priceData.price.expo);
    const publishTime = priceData.price.publish_time;
    
    console.log(`✅ Pyth price for ${token}: $${price.toFixed(2)} (confidence: ±$${confidence.toFixed(2)})`);
    
    return {
      price: price,
      confidence: confidence,
      publishTime: publishTime,
      priceId: priceId
    };
    
  } catch (error) {
    console.error(`❌ Failed to fetch Pyth price for ${token}:`, error);
    throw error;
  }
}

async function fetchHistoricalPrices(token: string, chain: string): Promise<number[]> {
  const priceId = PYTH_PRICE_IDS[token.toUpperCase()];
  
  if (!priceId) {
    return [];
  }
  
  const isTestnet = chain.includes('sepolia') || chain.includes('testnet') || chain.includes('goerli');
  const endpoint = isTestnet ? PYTH_ENDPOINTS.testnet : PYTH_ENDPOINTS.mainnet;
  
  try {
    // Fetch historical data for the last hour (for volatility calculation)
    const endTime = Math.floor(Date.now() / 1000);
    const startTime = endTime - 3600; // 1 hour ago
    
    const response = await fetch(
      `${endpoint}/api/get_price_feed?id=${priceId}&start_time=${startTime}&end_time=${endTime}`,
      {
        method: 'GET',
        headers: { 'Accept': 'application/json' },
        next: { revalidate: 300 } // Cache for 5 minutes
      }
    );
    
    if (!response.ok) {
      return [];
    }
    
    const data = await response.json();
    
    if (!data || !data.length) {
      return [];
    }
    
    // Extract prices and convert from Pyth format
    const prices = data.slice(-60).map((item: any) => {
      return parseFloat(item.price.price) * Math.pow(10, item.price.expo);
    });
    
    return prices;
    
  } catch (error) {
    console.error(`⚠️ Failed to fetch historical prices for ${token}:`, error);
    return [];
  }
}

export async function POST(request: NextRequest) {
  try {
    const { token, vs_currency, chain, useRealData = true }: PriceRequest = await request.json();
    
    console.log(`📊 Price request: ${token}/${vs_currency} on ${chain} (real data: ${useRealData})`);
    
    let priceData;
    let historicalPrices: number[] = [];
    let usingRealData = useRealData;
    
    if (usingRealData) {
      try {
        // Fetch real Pyth price data
        priceData = await fetchPythPrice(token, chain);
        
        // Fetch historical prices for volatility calculation
        historicalPrices = await fetchHistoricalPrices(token, chain);
        
      } catch (error) {
        console.warn(`⚠️ Falling back to mock data due to Pyth error:`, error);
        usingRealData = false;
      }
    }
    
    // Fallback to mock data if real data fails or is disabled
    if (!usingRealData || !priceData) {
      console.log(`🎭 Using mock price data for ${token}`);
      
      const mockPrices: { [key: string]: number } = {
        'ETH': 3000.45,
        'WETH': 3000.45,
        'USDC': 1.00,
        'USDT': 0.999,
        'DAI': 1.001,
        'BTC': 65000.00
      };
      
      const basePrice = mockPrices[token.toUpperCase()] || 1.0;
      
      priceData = {
        price: basePrice,
        confidence: basePrice * 0.001, // 0.1% confidence interval
        publishTime: Math.floor(Date.now() / 1000),
        priceId: PYTH_PRICE_IDS[token.toUpperCase()] || 'mock'
      };
      
      // Generate mock historical prices
      historicalPrices = Array.from({ length: 60 }, (_, i) => {
        const variation = (Math.random() - 0.5) * 0.02; // ±1% variation
        return basePrice * (1 + variation);
      });
    }
    
    // Calculate volatility
    const volatility = calculateVolatility(historicalPrices);
    
    // Calculate price changes (mock for now, would need more historical data)
    const priceChange1h = (Math.random() - 0.5) * 2; // ±1%
    const priceChange24h = (Math.random() - 0.5) * 10; // ±5%
    
    // Calculate confidence as percentage
    const confidencePercent = ((priceData.confidence / priceData.price) * 100).toFixed(3);
    
    const response = {
      token: token.toUpperCase(),
      price_usd: priceData.price.toFixed(2),
      price_change_1h: `${priceChange1h >= 0 ? '+' : ''}${priceChange1h.toFixed(1)}%`,
      price_change_24h: `${priceChange24h >= 0 ? '+' : ''}${priceChange24h.toFixed(1)}%`,
      volatility_1h: `${volatility}%`,
      confidence_interval: `±${confidencePercent}%`,
      confidence_usd: `±$${priceData.confidence.toFixed(4)}`,
      liquidity_usd: token === 'ETH' ? "45000000" : "12000000",
      volume_24h: token === 'ETH' ? "12000000" : "8000000",
      last_updated: new Date(priceData.publishTime * 1000).toISOString(),
      publish_time: priceData.publishTime,
      price_feed_id: priceData.priceId,
      source: usingRealData ? "pyth_network" : "mock_data",
      chain: chain
    };
    
    console.log(`✅ Price response for ${token}: $${response.price_usd} (${response.source})`);
    
    return NextResponse.json(response);
    
  } catch (error) {
    console.error('❌ Price fetch error:', error);
    return NextResponse.json(
      { 
        error: 'Failed to fetch price data',
        details: error instanceof Error ? error.message : 'Unknown error'
      },
      { status: 500 }
    );
  }
}