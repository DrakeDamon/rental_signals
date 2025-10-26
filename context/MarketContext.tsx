"use client";
import { createContext, useContext, useReducer, ReactNode } from 'react';

type Timeframe = '1Y' | '3Y' | '5Y' | 'MAX';

export interface MarketFilters {
  state?: string;
  dropThreshold?: number;
  timeframe?: Timeframe;
}

interface MarketState {
  selectedMarkets: string[];
  filters: MarketFilters;
}

type Action =
  | { type: 'setFilters'; filters: Partial<MarketFilters> }
  | { type: 'addMarket'; metro: string }
  | { type: 'removeMarket'; metro: string }
  | { type: 'clearSelection' };

function reducer(state: MarketState, action: Action): MarketState {
  switch (action.type) {
    case 'setFilters':
      return { ...state, filters: { ...state.filters, ...action.filters } };
    case 'addMarket':
      if (state.selectedMarkets.includes(action.metro)) return state;
      return { ...state, selectedMarkets: [...state.selectedMarkets, action.metro] };
    case 'removeMarket':
      return { ...state, selectedMarkets: state.selectedMarkets.filter(m => m !== action.metro) };
    case 'clearSelection':
      return { ...state, selectedMarkets: [] };
    default:
      return state;
  }
}

const MarketContext = createContext<{
  state: MarketState;
  dispatch: React.Dispatch<Action>;
} | null>(null);

export function MarketProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, {
    selectedMarkets: [],
    filters: { timeframe: '1Y' },
  });
  return <MarketContext.Provider value={{ state, dispatch }}>{children}</MarketContext.Provider>;
}

export function useMarket() {
  const ctx = useContext(MarketContext);
  if (!ctx) throw new Error('useMarket must be used within MarketProvider');
  return ctx;
}


