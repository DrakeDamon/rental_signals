import { type ClassValue, clsx } from 'clsx';

export function cn(...inputs: ClassValue[]) {
  return clsx(inputs);
}

export function formatCurrency(value: number): string {
  return new Intl.NumberFormat('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: 0,
    maximumFractionDigits: 0,
  }).format(value);
}

export function formatPercent(value: number, includeSign: boolean = false): string {
  const sign = includeSign && value > 0 ? '+' : '';
  return `${sign}${value.toFixed(1)}%`;
}

export function formatDate(dateString: string): string {
  const date = new Date(dateString);
  return new Intl.DateTimeFormat('en-US', {
    month: 'short',
    year: 'numeric',
  }).format(date);
}

export function calculateEffectiveRent(
  baseRent: number,
  concessions: string[] = []
): number {
  // Simple calculation: if "1 month free" or similar, divide by 13 instead of 12
  const hasMonthFree = concessions.some((c) =>
    c.toLowerCase().includes('month free')
  );
  
  if (hasMonthFree) {
    return Math.round((baseRent * 12) / 13);
  }
  
  return baseRent;
}

