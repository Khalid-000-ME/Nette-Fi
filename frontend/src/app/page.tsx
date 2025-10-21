'use client';

import Link from "next/link";
import Image from "next/image";
import { useState } from "react";

// Extend Window interface to include ethereum
interface EthereumProvider {
  request: (args: { method: string; params?: any[] }) => Promise<any>;
  isMetaMask?: boolean;
}

declare global {
  interface Window {
    ethereum?: EthereumProvider;
  }
}

export default function Home() {
  const [isConnecting, setIsConnecting] = useState(false);

  const handleConnectWallet = async () => {
    setIsConnecting(true);
    
    try {
      // Check if MetaMask is installed
      if (typeof window !== 'undefined' && window.ethereum) {
        // Request account access
        await window.ethereum.request({ method: 'eth_requestAccounts' });
        
        // Redirect to trading page after successful connection
        window.location.href = '/trade';
      } else {
        // Redirect to MetaMask installation
        window.open('https://metamask.io/download/', '_blank');
      }
    } catch (error) {
      console.error('Failed to connect wallet:', error);
      // Reset connecting state on error
      setIsConnecting(false);
    }
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
      
      {/* Main Content Container */}
      <div className="relative z-10 w-full max-w-md mx-auto px-6">
        {/* Transparent Container */}
        <div className="bg-white/10 backdrop-blur-md border border-white/20 rounded-3xl p-8 shadow-2xl">
          
          {/* Logo */}
          <div className="flex justify-center mb-6">
            <div className="relative w-24 h-24 rounded-full overflow-hidden border-4 border-white/30 shadow-lg">
              <Image
                src="/logo.png"
                alt="Sim-U-Fi Logo"
                fill
                className="object-cover"
                priority
              />
            </div>
          </div>
          
          {/* Project Name */}
          <h1 className="text-center text-4xl font-bold text-white mb-4 font-heading">
            Sim-U-Fi
          </h1>
          
          {/* Catchy Tagline */}
          <p className="text-center text-lg text-white/90 mb-8 font-subheading leading-relaxed">
            <span className="block text-xl font-semibold mb-3">
              One trade. Infinite simulations. Zero regrets.
            </span>
            <span className="block text-sm text-white/80 leading-relaxed">
              AI-powered MEV protection using parallel simulations, real-time price feeds, 
              and consensus-driven trade optimization.
            </span>
          </p>
          
          {/* Connect Wallet Button */}
          <button
            onClick={handleConnectWallet}
            disabled={isConnecting}
            className="w-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 text-white font-semibold py-4 px-6 rounded-xl transition-all duration-300 shadow-lg hover:shadow-xl transform hover:scale-[1.02] disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
          >
            {isConnecting ? (
              <div className="flex items-center justify-center space-x-2">
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin"></div>
                <span>Connecting...</span>
              </div>
            ) : (
              'Connect Wallet'
            )}
          </button>
          
          {/* Additional Info */}
          <div className="mt-6 text-center">
            <p className="text-white/70 text-sm mb-3">
              Powered by Arcology Network, ASI:One, Blockscout & Pyth Oracle
            </p>
            
            {/* Quick Stats */}
            <div className="flex justify-center space-x-6 text-white/80 text-xs">
              <div className="text-center">
                <div className="font-bold">100+</div>
                <div>Simulations</div>
              </div>
              <div className="text-center">
                <div className="font-bold">&lt;10s</div>
                <div>Analysis</div>
              </div>
              <div className="text-center">
                <div className="font-bold">AI</div>
                <div>Powered</div>
              </div>
            </div>
          </div>
          
          {/* Learn More Link */}
          <div className="mt-6 text-center">
            <Link 
              href="#"
              className="text-white/80 hover:text-white text-sm underline transition-colors"
            >
              Learn more about MEV protection
            </Link>
          </div>
        </div>
      </div>
      
      {/* Bottom Attribution */}
      <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 text-white/60 text-xs text-center">
        Built for ETHOnline 2025
      </div>
    </div>
  );
}
