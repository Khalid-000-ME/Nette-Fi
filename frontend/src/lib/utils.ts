import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatCurrency(value: number, currency = "USD"): string {
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency,
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(value);
}

export function formatNumber(value: number, decimals = 2): string {
  return new Intl.NumberFormat("en-US", {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  }).format(value);
}

export function formatPercentage(value: number, decimals = 1): string {
  return `${value >= 0 ? "+" : ""}${value.toFixed(decimals)}%`;
}

export function truncateAddress(address: string, start = 6, end = 4): string {
  if (address.length <= start + end) return address;
  return `${address.slice(0, start)}...${address.slice(-end)}`;
}

export function generateId(): string {
  return Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
}

export function calculateTimeRemaining(targetBlock: number, currentBlock: number, blockTime = 12): {
  blocks: number;
  seconds: number;
  minutes: number;
  formatted: string;
} {
  const blocks = Math.max(0, targetBlock - currentBlock);
  const seconds = blocks * blockTime;
  const minutes = Math.floor(seconds / 60);
  
  const formatted = minutes > 0 
    ? `${minutes}m ${seconds % 60}s`
    : `${seconds}s`;
    
  return { blocks, seconds, minutes, formatted };
}

export function getConfidenceColor(confidence: number): string {
  if (confidence >= 90) return "text-green-500";
  if (confidence >= 70) return "text-yellow-500";
  if (confidence >= 50) return "text-orange-500";
  return "text-red-500";
}

export function getMEVRiskColor(risk: number): string {
  if (risk <= 20) return "text-green-500";
  if (risk <= 50) return "text-yellow-500";
  if (risk <= 80) return "text-orange-500";
  return "text-red-500";
}
