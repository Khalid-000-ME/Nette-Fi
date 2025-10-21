#!/usr/bin/env node

/**
 * Pyth Network Integration Test Script
 * Tests both the API route and direct Pyth Network integration
 */

const fetch = require('node-fetch');

// Configuration
const API_BASE_URL = 'http://localhost:3000'; // Adjust for your Next.js app
const PYTH_HERMES_URL = 'https://hermes.pyth.network';

// Test tokens
const TEST_TOKENS = ['ETH', 'BTC', 'USDC', 'USDT'];

// Colors for console output
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m',
  cyan: '\x1b[36m'
};

function log(color, message) {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function logSection(title) {
  console.log('\n' + '='.repeat(60));
  log('cyan', `🧪 ${title}`);
  console.log('='.repeat(60));
}

function logSuccess(message) {
  log('green', `✅ ${message}`);
}

function logError(message) {
  log('red', `❌ ${message}`);
}

function logWarning(message) {
  log('yellow', `⚠️  ${message}`);
}

function logInfo(message) {
  log('blue', `ℹ️  ${message}`);
}

/**
 * Test direct Pyth Hermes API
 */
async function testPythDirectAPI() {
  logSection('Testing Direct Pyth Hermes API');
  
  // Pyth price feed IDs
  const priceIds = {
    'ETH': '0xff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace',
    'BTC': '0xe62df6c8b4a85fe1a67db44dc12de5db330f7ac66b72dc658afedf0f4a415b43',
    'USDC': '0xeaa020c61cc479712813461ce153894a96a6c00b21ed0cfc2798d1f9a9e9c94a'
  };
  
  for (const [token, priceId] of Object.entries(priceIds)) {
    try {
      logInfo(`Fetching ${token} price from Pyth Hermes...`);
      
      const response = await fetch(`${PYTH_HERMES_URL}/api/latest_price_feeds?ids[]=${priceId}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (!data || data.length === 0) {
        throw new Error('No price data returned');
      }
      
      const priceData = data[0];
      const price = parseFloat(priceData.price.price) * Math.pow(10, priceData.price.expo);
      const confidence = parseFloat(priceData.price.conf) * Math.pow(10, priceData.price.expo);
      const publishTime = new Date(priceData.price.publish_time * 1000);
      
      logSuccess(`${token}: $${price.toFixed(2)} ±$${confidence.toFixed(4)} (${publishTime.toISOString()})`);
      
    } catch (error) {
      logError(`Failed to fetch ${token} price: ${error.message}`);
    }
  }
}

/**
 * Test the Next.js API route with real Pyth data
 */
async function testAPIRouteWithRealData() {
  logSection('Testing API Route with Real Pyth Data');
  
  for (const token of TEST_TOKENS) {
    try {
      logInfo(`Testing ${token} price via API route...`);
      
      const response = await fetch(`${API_BASE_URL}/api/get_price`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token: token,
          vs_currency: 'usd',
          chain: 'base',
          useRealData: true
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.error) {
        throw new Error(data.error);
      }
      
      logSuccess(`${data.token}: $${data.price_usd} (${data.source})`);
      logInfo(`  Confidence: ${data.confidence_interval} (${data.confidence_usd})`);
      logInfo(`  Volatility: ${data.volatility_1h}`);
      logInfo(`  Last Updated: ${data.last_updated}`);
      logInfo(`  Price Feed ID: ${data.price_feed_id}`);
      
    } catch (error) {
      logError(`Failed to test ${token}: ${error.message}`);
    }
  }
}

/**
 * Test the API route with mock data fallback
 */
async function testAPIRouteWithMockData() {
  logSection('Testing API Route with Mock Data Fallback');
  
  for (const token of TEST_TOKENS) {
    try {
      logInfo(`Testing ${token} price with mock data...`);
      
      const response = await fetch(`${API_BASE_URL}/api/get_price`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token: token,
          vs_currency: 'usd',
          chain: 'base',
          useRealData: false
        })
      });
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      const data = await response.json();
      
      if (data.error) {
        throw new Error(data.error);
      }
      
      logSuccess(`${data.token}: $${data.price_usd} (${data.source})`);
      logInfo(`  Source: ${data.source}`);
      logInfo(`  Volatility: ${data.volatility_1h}`);
      
    } catch (error) {
      logError(`Failed to test ${token} with mock data: ${error.message}`);
    }
  }
}

/**
 * Test price feed update data retrieval
 */
async function testPriceUpdateData() {
  logSection('Testing Price Update Data Retrieval');
  
  const priceIds = [
    '0xff61491a931112ddf1bd8147cd1b641375f79f5825126d665480874634fd0ace', // ETH
    '0xe62df6c8b4a85fe1a67db44dc12de5db330f7ac66b72dc658afedf0f4a415b43'  // BTC
  ];
  
  try {
    logInfo('Fetching price update data for ETH and BTC...');
    
    const idsParam = priceIds.map(id => `ids[]=${id}`).join('&');
    const response = await fetch(`${PYTH_HERMES_URL}/api/latest_vaas?${idsParam}`);
    
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }
    
    const data = await response.json();
    
    if (!data || data.length === 0) {
      throw new Error('No price update data returned');
    }
    
    logSuccess(`Retrieved ${data.length} price update VAAs`);
    
    data.forEach((vaa, index) => {
      logInfo(`  VAA ${index + 1}: ${vaa.slice(0, 20)}... (${vaa.length} bytes)`);
    });
    
  } catch (error) {
    logError(`Failed to fetch price update data: ${error.message}`);
  }
}

/**
 * Test error handling
 */
async function testErrorHandling() {
  logSection('Testing Error Handling');
  
  // Test invalid token
  try {
    logInfo('Testing invalid token...');
    
    const response = await fetch(`${API_BASE_URL}/api/get_price`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        token: 'INVALID_TOKEN',
        vs_currency: 'usd',
        chain: 'base',
        useRealData: true
      })
    });
    
    const data = await response.json();
    
    if (data.error) {
      logSuccess('Error handling works: Invalid token properly rejected');
    } else {
      logWarning('Expected error for invalid token, but got success response');
    }
    
  } catch (error) {
    logError(`Unexpected error during invalid token test: ${error.message}`);
  }
  
  // Test malformed request
  try {
    logInfo('Testing malformed request...');
    
    const response = await fetch(`${API_BASE_URL}/api/get_price`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        // Missing required fields
        invalid: 'request'
      })
    });
    
    const data = await response.json();
    
    if (data.error) {
      logSuccess('Error handling works: Malformed request properly rejected');
    } else {
      logWarning('Expected error for malformed request, but got success response');
    }
    
  } catch (error) {
    logError(`Unexpected error during malformed request test: ${error.message}`);
  }
}

/**
 * Performance test
 */
async function testPerformance() {
  logSection('Performance Testing');
  
  const startTime = Date.now();
  const promises = [];
  
  // Test concurrent requests
  for (let i = 0; i < 5; i++) {
    const promise = fetch(`${API_BASE_URL}/api/get_price`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        token: 'ETH',
        vs_currency: 'usd',
        chain: 'base',
        useRealData: true
      })
    });
    promises.push(promise);
  }
  
  try {
    logInfo('Running 5 concurrent price requests...');
    
    const responses = await Promise.all(promises);
    const endTime = Date.now();
    
    const successCount = responses.filter(r => r.ok).length;
    const totalTime = endTime - startTime;
    
    logSuccess(`${successCount}/5 requests succeeded in ${totalTime}ms`);
    logInfo(`Average response time: ${(totalTime / 5).toFixed(2)}ms`);
    
  } catch (error) {
    logError(`Performance test failed: ${error.message}`);
  }
}

/**
 * Main test runner
 */
async function runTests() {
  log('bright', '🚀 Starting Pyth Network Integration Tests\n');
  
  try {
    // Test direct Pyth API
    await testPythDirectAPI();
    
    // Test API route with real data
    await testAPIRouteWithRealData();
    
    // Test API route with mock data
    await testAPIRouteWithMockData();
    
    // Test price update data
    await testPriceUpdateData();
    
    // Test error handling
    await testErrorHandling();
    
    // Performance test
    await testPerformance();
    
    logSection('Test Summary');
    logSuccess('All tests completed! 🎉');
    logInfo('Check the logs above for any failures or warnings.');
    
  } catch (error) {
    logError(`Test suite failed: ${error.message}`);
    process.exit(1);
  }
}

// Handle command line arguments
const args = process.argv.slice(2);

if (args.includes('--help') || args.includes('-h')) {
  console.log(`
Pyth Network Integration Test Script

Usage: node Pyth.js [options]

Options:
  --api-only     Test only the API route (skip direct Pyth tests)
  --pyth-only    Test only direct Pyth integration (skip API tests)
  --mock-only    Test only mock data functionality
  --help, -h     Show this help message

Examples:
  node Pyth.js                    # Run all tests
  node Pyth.js --api-only         # Test only API route
  node Pyth.js --pyth-only        # Test only direct Pyth integration
  node Pyth.js --mock-only        # Test only mock data
  `);
  process.exit(0);
}

// Run specific tests based on arguments
if (args.includes('--api-only')) {
  testAPIRouteWithRealData().then(() => testAPIRouteWithMockData());
} else if (args.includes('--pyth-only')) {
  testPythDirectAPI().then(() => testPriceUpdateData());
} else if (args.includes('--mock-only')) {
  testAPIRouteWithMockData();
} else {
  // Run all tests
  runTests();
}