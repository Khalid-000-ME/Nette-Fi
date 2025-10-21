import { NextResponse } from 'next/server';

export async function GET() {
  try {
    // Check if MeTTa service is available
    const mettaUrl = process.env.NEXT_PUBLIC_METTA_SERVICE_URL || 'http://localhost:8000';
    
    let mettaStatus = 'unknown';
    try {
      const response = await fetch(`${mettaUrl}/health`, { 
        method: 'GET',
        headers: { 'Content-Type': 'application/json' },
        signal: AbortSignal.timeout(5000) // 5 second timeout
      });
      mettaStatus = response.ok ? 'healthy' : 'unhealthy';
    } catch (error) {
      mettaStatus = 'unreachable';
    }

    return NextResponse.json({
      status: 'healthy',
      timestamp: new Date().toISOString(),
      version: '1.0.0',
      services: {
        frontend: 'healthy',
        metta_service: mettaStatus
      },
      environment: process.env.NODE_ENV || 'development'
    });
  } catch (error) {
    return NextResponse.json(
      { 
        status: 'unhealthy', 
        error: 'Health check failed',
        timestamp: new Date().toISOString()
      },
      { status: 500 }
    );
  }
}
