"use client";

import { useState, useEffect } from "react";
import Image from "next/image";
import { ArrowUpDown, Wallet, RefreshCw, Loader2 } from "lucide-react";

interface TokenInfo {
  symbol: string;
  name: string;
  price: string;
  change24h: string;
  icon: string;
}

interface PriceData {
  token: string;
  price_usd: string;
  price_change_1h: string;
  price_change_24h: string;
  volatility_1h: string;
  confidence_interval: string;
  confidence_usd: string;
  last_updated: string;
  source: string;
}

const TOKENS: TokenInfo[] = [
  { symbol: "ETH", name: "Ethereum", price: "0.00", change24h: "0.0%", icon: "🔷" },
  { symbol: "USDC", name: "USD Coin", price: "0.00", change24h: "0.0%", icon: "💵" },
  { symbol: "USDT", name: "Tether", price: "0.00", change24h: "0.0%", icon: "💰" },
  { symbol: "DAI", name: "Dai", price: "0.00", change24h: "0.0%", icon: "🟡" },
  { symbol: "WETH", name: "Wrapped ETH", price: "0.00", change24h: "0.0%", icon: "🔶" },
  { symbol: "BTC", name: "Bitcoin", price: "0.00", change24h: "0.0%", icon: "₿" }
];

export default function TradePage() {
  const [fromToken, setFromToken] = useState("ETH");
  const [toToken, setToToken] = useState("USDC");
  const [amount, setAmount] = useState("");
  const [fromPriceData, setFromPriceData] = useState<PriceData | null>(null);
  const [toPriceData, setToPriceData] = useState<PriceData | null>(null);
  const [isLoadingPrices, setIsLoadingPrices] = useState(false);
  const [walletAddress] = useState("0x742d...5bEb");

  // Fetch price data when tokens change
  const fetchPriceData = async (token: string): Promise<PriceData | null> => {
    try {
      const response = await fetch('/api/get_price', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          token: token,
          vs_currency: 'USD',
          chain: 'base',
          useRealData: true
        })
      });
      
      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
      console.error('Failed to fetch price:', error);
    }
    return null;
  };

  useEffect(() => {
    const loadPrices = async () => {
      setIsLoadingPrices(true);
      const [fromPrice, toPrice] = await Promise.all([
        fetchPriceData(fromToken),
        fetchPriceData(toToken)
      ]);
      setFromPriceData(fromPrice);
      setToPriceData(toPrice);
      setIsLoadingPrices(false);
    };

    loadPrices();
  }, [fromToken, toToken]);

  const swapTokens = () => {
    const temp = fromToken;
    setFromToken(toToken);
    setToToken(temp);
  };

  const handleAnalyze = () => {
    if (!amount || parseFloat(amount) <= 0) {
      alert("Please enter a valid amount");
      return;
    }
    // Navigate to analysis or trigger simulation
    alert("Analysis feature coming soon!");
  };

  return (
    <div 
      className="min-h-screen relative flex items-center justify-center"
      style={{
        backgroundImage: 'url(/bg-enter-full.png)',
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat'
      }}
    >
      {/* Background Overlay */}
      <div className="absolute inset-0 bg-black/30 backdrop-blur-[1px]"></div>
      
      {/* Wallet Address - Top Right */}
      <div className="absolute top-6 right-6 z-20">
        <div className="flex items-center space-x-2 bg-white/10 backdrop-blur-md border border-white/20 rounded-full px-4 py-2">
          <Wallet className="w-4 h-4 text-white/80" />
          <span className="text-white/90 text-sm font-medium">{walletAddress}</span>
        </div>
      </div>

      {/* Main Swap Container */}
      <div className="relative z-10 w-full max-w-md mx-auto px-6">
        <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-3xl p-8 shadow-2xl">
          
          {/* Logo */}
          <div className="flex justify-center mb-6">
            <div className="relative w-16 h-16 rounded-full overflow-hidden border-4 border-white/30 shadow-lg">
              <Image
                src="/logo.png"
                alt="Sim-U-Fi Logo"
                fill
                className="object-cover"
                priority
              />
            </div>
          </div>

          {/* From Token */}
          <div className="mb-4">
            <label className="block text-white/80 text-sm font-medium mb-2">From</label>
            <div className="bg-white/5 border border-white/20 rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <select 
                  value={fromToken}
                  onChange={(e) => setFromToken(e.target.value)}
                  className="bg-transparent text-white text-lg font-semibold border-none outline-none cursor-pointer"
                >
                  {TOKENS.map((token) => (
                    <option key={token.symbol} value={token.symbol} className="bg-gray-800 text-white">
                      {token.icon} {token.symbol}
                    </option>
                  ))}
                </select>
                {isLoadingPrices ? (
                  <Loader2 className="w-4 h-4 text-white/60 animate-spin" />
                ) : (
                  <RefreshCw className="w-4 h-4 text-white/60" />
                )}
              </div>
              <input
                type="number"
                value={amount}
                onChange={(e) => setAmount(e.target.value)}
                placeholder="0.0"
                className="w-full bg-transparent text-white text-2xl font-bold placeholder-white/40 border-none outline-none"
              />
              {fromPriceData && (
                <div className="mt-2 text-white/60 text-sm">
                  ${fromPriceData.price_usd} {fromPriceData.price_change_24h}
                  <span className="ml-2 text-xs">via {fromPriceData.source}</span>
                </div>
              )}
            </div>
          </div>

          {/* Swap Button */}
          <div className="flex justify-center my-4">
            <button
              onClick={swapTokens}
              className="bg-white/10 hover:bg-white/20 border border-white/20 rounded-full p-3 transition-all duration-200"
            >
              <ArrowUpDown className="w-5 h-5 text-white" />
            </button>
          </div>

          {/* To Token */}
          <div className="mb-6">
            <label className="block text-white/80 text-sm font-medium mb-2">To</label>
            <div className="bg-white/5 border border-white/20 rounded-xl p-4">
              <div className="flex items-center justify-between mb-3">
                <select 
                  value={toToken}
                  onChange={(e) => setToToken(e.target.value)}
                  className="bg-transparent text-white text-lg font-semibold border-none outline-none cursor-pointer"
                >
                  {TOKENS.map((token) => (
                    <option key={token.symbol} value={token.symbol} className="bg-gray-800 text-white">
                      {token.icon} {token.symbol}
                    </option>
                  ))}
                </select>
              </div>
              <div className="text-white/60 text-2xl font-bold">
                {amount && fromPriceData && toPriceData ? 
                  (parseFloat(amount) * parseFloat(fromPriceData.price_usd) / parseFloat(toPriceData.price_usd)).toFixed(6)
                  : "0.0"
                }
              </div>
              {toPriceData && (
                <div className="mt-2 text-white/60 text-sm">
                  ${toPriceData.price_usd} {toPriceData.price_change_24h}
                  <span className="ml-2 text-xs">via {toPriceData.source}</span>
                </div>
              )}
            </div>
          </div>

          {/* Analyze Trade Button */}
          <button
            onClick={handleAnalyze}
            disabled={!amount || parseFloat(amount) <= 0 || isLoadingPrices}
            className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-semibold py-4 px-6 rounded-xl transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
          >
            {isLoadingPrices ? (
              <div className="flex items-center justify-center space-x-2">
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Loading Prices...</span>
              </div>
            ) : (
              'Analyze Trade'
            )}
          </button>

          {/* Price Info */}
          {(fromPriceData || toPriceData) && (
            <div className="mt-4 text-center">
              <p className="text-white/70 text-xs">
                Real-time prices from Pyth Network
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}