import { NextRequest, NextResponse } from 'next/server';

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url);
    const requestId = searchParams.get('request_id');
    
    if (!requestId) {
      return NextResponse.json(
        { error: 'request_id parameter is required' },
        { status: 400 }
      );
    }
    
    // In production, fetch from database using requestId
    // For demo purposes, return mock data
    const mockResponse = {
      request_id: requestId,
      status: "ready" as const,
      recommendation: {
        execute_at_block: 19234567,
        blocks_to_wait: 3,
        seconds_to_wait: 36,
        expected_output: "15120.45",
        expected_output_usd: "15120.45",
        confidence: 92,
        savings_vs_immediate: "124.00"
      },
      top_simulations: [
        {
          id: 1,
          block_offset: 0,
          gas_gwei: 50,
          output_usd: "15000.00",
          mev_risk: 95,
          gas_cost_usd: "15.00",
          status: "rejected" as const,
          rejection_reason: "High MEV risk"
        },
        {
          id: 2,
          block_offset: 3,
          gas_gwei: 100,
          output_usd: "15120.45",
          mev_risk: 12,
          gas_cost_usd: "30.00",
          status: "recommended" as const,
          agent_scores: {
            mev_agent: 95,
            profit_agent: 88,
            speed_agent: 65,
            consensus: 92
          }
        }
      ],
      agent_reasoning: {
        mev_agent: "Option 2 avoids 3 detected sandwich bots in current mempool",
        profit_agent: "Option 2 yields $120 more than immediate execution",
        speed_agent: "36s wait acceptable given profit improvement",
        consensus: "Recommended option balances MEV safety (95/100) with strong profit (+$124)"
      }
    };
    
    return NextResponse.json(mockResponse);
    
  } catch (error) {
    console.error('Get trade error:', error);
    return NextResponse.json(
      { error: 'Failed to fetch trade status' },
      { status: 500 }
    );
  }
}