"use client";
import { useState } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, TooltipProps } from 'recharts';
import type { TrendPoint, PricePoint } from '@/types';
import { formatCurrency, formatDate } from '@/lib/utils';
import { cn } from '@/lib/utils';

interface TrendChartProps {
  data: TrendPoint[] | PricePoint[];
  interval?: 30 | 90;
  onIntervalChange?: (interval: 30 | 90) => void;
  title?: string;
}

// Custom tooltip
function CustomTooltip({ active, payload }: TooltipProps<number, string>) {
  if (active && payload && payload.length) {
    const data = payload[0].payload;
    const value = data.value;
    const period = data.month || data.period;
    
    return (
      <div className="bg-neutral-0 border border-neutral-200 dark:border-neutral-100 rounded-lg shadow-lg p-3">
        <p className="text-sm text-neutral-600 mb-1">
          {formatDate(period)}
        </p>
        <p className="text-lg font-semibold text-neutral-900">
          {formatCurrency(value)}
        </p>
      </div>
    );
  }
  return null;
}

export function TrendChart({ data, interval = 90, onIntervalChange, title }: TrendChartProps) {
  const [selectedInterval, setSelectedInterval] = useState(interval);
  
  // Limit data based on interval
  const filteredData = data.slice(-selectedInterval / 30);
  
  const handleIntervalChange = (newInterval: 30 | 90) => {
    setSelectedInterval(newInterval);
    onIntervalChange?.(newInterval);
  };

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex justify-between items-center">
        {title && <h3 className="text-lg font-semibold text-neutral-900">{title}</h3>}
        <div className="flex gap-2">
          <button
            onClick={() => handleIntervalChange(30)}
            className={cn(
              'px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-fast',
              selectedInterval === 30
                ? 'bg-brand text-white'
                : 'bg-neutral-100 text-neutral-700 hover:bg-neutral-200'
            )}
          >
            30 Days
          </button>
          <button
            onClick={() => handleIntervalChange(90)}
            className={cn(
              'px-3 py-1.5 rounded-md text-sm font-medium transition-colors duration-fast',
              selectedInterval === 90
                ? 'bg-brand text-white'
                : 'bg-neutral-100 text-neutral-700 hover:bg-neutral-200'
            )}
          >
            90 Days
          </button>
        </div>
      </div>
      
      {/* Chart */}
      <div className="w-full h-64 bg-neutral-50 dark:bg-neutral-50 rounded-lg p-4">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={filteredData} margin={{ left: 0, right: 0, top: 8, bottom: 8 }}>
            <CartesianGrid strokeDasharray="3 3" stroke="var(--color-neutral-300)" />
            <XAxis 
              dataKey={(d) => d.month || d.period}
              stroke="var(--color-neutral-600)"
              fontSize={12}
              tickFormatter={(value) => {
                const date = new Date(value);
                return date.toLocaleDateString('en-US', { month: 'short' });
              }}
            />
            <YAxis 
              stroke="var(--color-neutral-600)"
              fontSize={12}
              tickFormatter={(value) => `$${(value / 1000).toFixed(1)}k`}
            />
            <Tooltip content={<CustomTooltip />} />
            <Line 
              type="monotone" 
              dataKey="value" 
              stroke="var(--color-brand-primary)" 
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 6, fill: 'var(--color-brand-primary)' }}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}


