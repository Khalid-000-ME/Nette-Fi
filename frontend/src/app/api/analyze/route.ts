import { NextRequest, NextResponse } from 'next/server';

interface AnalysisRequest {
  simulations: any[];
  user_priority: "mev_protection" | "profit" | "speed" | "balanced";
  risk_tolerance: "conservative" | "balanced" | "aggressive";
  user_context: {
    trade_size_usd: number;
    is_time_sensitive: boolean;
  };
}

function filterViableSimulations(simulations: any[]): any[] {
  return simulations.filter(sim => 
    sim.mev_risk_score < 80 &&
    parseFloat(sim.price_impact_percent) < 5.0 &&
    parseFloat(sim.gas_cost_usd) < parseFloat(sim.estimated_output_usd) * 0.1 // Gas cost < 10% of output
  );
}

function analyzeWithMEVAgent(simulations: any[]): any {
  // Sort by MEV risk (ascending - lower is better)
  const sorted = [...simulations].sort((a, b) => a.mev_risk_score - b.mev_risk_score);
  const best = sorted[0];
  
  const reasoning = `Option ${best.id} has lowest MEV risk (${best.mev_risk_score}/100). ` +
    `Detected ${best.mempool_snapshot.sandwich_bots_detected} sandwich bots in current block. ` +
    `Waiting ${best.block_offset} blocks reduces exposure by ${Math.max(0, 95 - best.mev_risk_score)}%.`;
  
  const concerns = [];
  if (best.block_offset > 3) {
    concerns.push(`Wait time of ${best.block_offset * 12}s may expose to price movement`);
  }
  
  return {
    recommended_id: best.id,
    score: 100 - best.mev_risk_score,
    reasoning,
    concerns,
    agent: "MEV_Protection"
  };
}

function analyzeWithProfitAgent(simulations: any[]): any {
  // Calculate net profit for each simulation
  const withNetProfit = simulations.map(sim => ({
    ...sim,
    net_profit: parseFloat(sim.estimated_output_usd) - parseFloat(sim.gas_cost_usd) - (sim.mev_risk_score / 100 * parseFloat(sim.estimated_output_usd) * 0.03)
  }));
  
  // Sort by net profit (descending)
  const sorted = withNetProfit.sort((a, b) => b.net_profit - a.net_profit);
  const best = sorted[0];
  const immediate = withNetProfit.find(s => s.block_offset === 0) || sorted[sorted.length - 1];
  
  const profitDiff = best.net_profit - immediate.net_profit;
  
  const reasoning = `Option ${best.id} yields $${best.net_profit.toFixed(2)} net profit, ` +
    `which is $${profitDiff.toFixed(2)} more than immediate execution. ` +
    `This accounts for gas costs and MEV risk.`;
  
  const concerns = [];
  if (best.block_offset > 2) {
    concerns.push("Longer wait time increases price movement risk");
  }
  
  return {
    recommended_id: best.id,
    score: Math.min(100, (profitDiff / immediate.net_profit) * 100 + 70),
    reasoning,
    concerns,
    agent: "Profit_Maximizer"
  };
}

function analyzeWithSpeedAgent(simulations: any[]): any {
  // Sort by execution speed (block offset ascending)
  const sorted = [...simulations].sort((a, b) => a.block_offset - b.block_offset);
  
  // Find fastest option that doesn't sacrifice too much profit
  const fastest = sorted[0];
  const maxProfit = Math.max(...simulations.map(s => parseFloat(s.estimated_output_usd)));
  
  let best = fastest;
  for (const sim of sorted) {
    const profitRatio = parseFloat(sim.estimated_output_usd) / maxProfit;
    if (profitRatio > 0.95) { // Within 5% of max profit
      best = sim;
      break;
    }
  }
  
  const reasoning = `Option ${best.id} executes in ${best.block_offset * 12}s. ` +
    `Minimizes exposure to price volatility while maintaining ` +
    `${((parseFloat(best.estimated_output_usd) / maxProfit) * 100).toFixed(1)}% of maximum profit.`;
  
  return {
    recommended_id: best.id,
    score: 100 - (best.block_offset * 10),
    reasoning,
    concerns: [],
    agent: "Speed_Optimizer"
  };
}

function generateConsensus(
  mevAnalysis: any,
  profitAnalysis: any,
  speedAnalysis: any,
  userPriority: string,
  riskTolerance: string
): any {
  // Weight agents based on user priority
  const weights = {
    mev_protection: { mev: 0.6, profit: 0.3, speed: 0.1 },
    profit: { mev: 0.2, profit: 0.6, speed: 0.2 },
    speed: { mev: 0.2, profit: 0.2, speed: 0.6 },
    balanced: { mev: 0.4, profit: 0.4, speed: 0.2 }
  };
  
  const weight = weights[userPriority as keyof typeof weights];
  
  // Calculate weighted scores for each recommendation
  const candidates = [
    { id: mevAnalysis.recommended_id, score: mevAnalysis.score * weight.mev, source: 'mev' },
    { id: profitAnalysis.recommended_id, score: profitAnalysis.score * weight.profit, source: 'profit' },
    { id: speedAnalysis.recommended_id, score: speedAnalysis.score * weight.speed, source: 'speed' }
  ];
  
  // Group by ID and sum scores
  const scoreMap = new Map();
  candidates.forEach(c => {
    const current = scoreMap.get(c.id) || { score: 0, sources: [] };
    scoreMap.set(c.id, {
      score: current.score + c.score,
      sources: [...current.sources, c.source]
    });
  });
  
  // Find highest scoring option
  let bestId = 0;
  let bestScore = 0;
  let bestSources: string[] = [];
  
  for (const [id, data] of scoreMap.entries()) {
    if (data.score > bestScore) {
      bestScore = data.score;
      bestId = id;
      bestSources = data.sources;
    }
  }
  
  const confidence = Math.min(95, Math.max(70, bestScore));
  
  const agentAgreement = bestSources.length > 1 
    ? `${bestSources.length}/3 agents agree (${bestSources.join(' + ')})`
    : `Primary recommendation from ${bestSources[0]} agent`;
  
  const reasoning = `Given user priority '${userPriority}' and '${riskTolerance}' risk tolerance, ` +
    `option ${bestId} provides optimal balance. ${agentAgreement}.`;
  
  return {
    recommended_id: bestId,
    confidence: Math.round(confidence),
    reasoning,
    agent_agreement: agentAgreement,
    key_tradeoff: "Balancing MEV safety, profit optimization, and execution speed"
  };
}

export async function POST(request: NextRequest) {
  try {
    const body: AnalysisRequest = await request.json();
    
    // Filter obviously bad options
    const viableSimulations = filterViableSimulations(body.simulations);
    
    if (viableSimulations.length === 0) {
      return NextResponse.json({
        error: "No viable simulations found",
        message: "All simulations have high MEV risk or excessive costs"
      }, { status: 400 });
    }
    
    // Run agent analyses
    const mevAnalysis = analyzeWithMEVAgent(viableSimulations);
    const profitAnalysis = analyzeWithProfitAgent(viableSimulations);
    const speedAnalysis = analyzeWithSpeedAgent(viableSimulations);
    
    // Generate consensus
    const consensus = generateConsensus(
      mevAnalysis,
      profitAnalysis,
      speedAnalysis,
      body.user_priority,
      body.risk_tolerance
    );
    
    // Find the recommended simulation
    const recommendedSim = viableSimulations.find(s => s.id === consensus.recommended_id);
    
    // Generate alternatives
    const alternatives = [];
    
    if (mevAnalysis.recommended_id !== consensus.recommended_id) {
      alternatives.push({
        id: mevAnalysis.recommended_id,
        reason: "Safest option if MEV protection is top priority",
        tradeoff: "May sacrifice some profit for safety"
      });
    }
    
    if (profitAnalysis.recommended_id !== consensus.recommended_id && alternatives.length < 2) {
      alternatives.push({
        id: profitAnalysis.recommended_id,
        reason: "Highest profit if willing to take more risk",
        tradeoff: "Higher potential returns with elevated MEV exposure"
      });
    }
    
    const response = {
      analysis_id: `analysis_${Date.now()}_${Math.random().toString(36).substr(2, 6)}`,
      recommended_simulation: {
        id: recommendedSim.id,
        execute_at_block: 19234564 + recommendedSim.block_offset,
        blocks_to_wait: recommendedSim.block_offset,
        expected_output_usd: recommendedSim.estimated_output_usd,
        confidence: consensus.confidence
      },
      agent_analyses: {
        mev_protection_agent: mevAnalysis,
        profit_maximizer_agent: profitAnalysis,
        speed_optimizer_agent: speedAnalysis,
        consensus_agent: consensus
      },
      alternative_options: alternatives
    };
    
    return NextResponse.json(response);
    
  } catch (error) {
    console.error('Analysis error:', error);
    return NextResponse.json(
      { error: 'Failed to analyze simulations' },
      { status: 500 }
    );
  }
}