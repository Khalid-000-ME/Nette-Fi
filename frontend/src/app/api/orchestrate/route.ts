import { NextRequest, NextResponse } from 'next/server';

interface OrchestrationRequest {
  wallet_address: string;
  trade: {
    from_token: string;
    to_token: string;
    amount: string;
    chain: string;
  };
  user_priority: "mev_protection" | "profit" | "speed" | "balanced";
  risk_tolerance: "conservative" | "balanced" | "aggressive";
  max_wait_blocks: number;
  auto_execute: boolean;
}

export async function POST(request: NextRequest) {
  try {
    const body: OrchestrationRequest = await request.json();
    
    // Generate unique request ID
    const requestId = `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    
    // 1. Fetch mempool data
    const mempoolResponse = await fetch(`${request.nextUrl.origin}/api/mempool?chain=${body.trade.chain}`);
    const mempoolData = await mempoolResponse.json();
    
    // 2. Get current prices
    const priceResponse = await fetch(`${request.nextUrl.origin}/api/get_price`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ 
        token: body.trade.from_token,
        vs_currency: "USD",
        chain: body.trade.chain
      })
    });
    const priceData = await priceResponse.json();
    
    // 3. Trigger parallel simulations
    const simulationResponse = await fetch(`${request.nextUrl.origin}/api/simulate`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        ...body.trade,
        wallet: body.wallet_address,
        mempool_state: mempoolData,
        current_price: priceData,
        simulation_params: {
          block_offsets: [0, 1, 2, 3, 5],
          gas_prices: [50, 100, 150, 200]
        }
      })
    });
    const simulationData = await simulationResponse.json();
    
    // 4. Send to AI analysis
    const analysisResponse = await fetch(`${request.nextUrl.origin}/api/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        simulations: simulationData.results,
        user_priority: body.user_priority,
        risk_tolerance: body.risk_tolerance,
        user_context: {
          trade_size_usd: parseFloat(body.trade.amount) * parseFloat(priceData.price_usd),
          is_time_sensitive: body.user_priority === "speed"
        }
      })
    });
    const analysisData = await analysisResponse.json();
    
    // Store the analysis result (in production, use a database)
    // For now, we'll return the analysis directly
    
    return NextResponse.json({
      request_id: requestId,
      status: "ready",
      simulations_count: simulationData.total_simulations,
      estimated_time_seconds: 0, // Already completed
      ...analysisData
    });
    
  } catch (error) {
    console.error('Orchestration error:', error);
    return NextResponse.json(
      { error: 'Failed to orchestrate trade analysis' },
      { status: 500 }
    );
  }
}