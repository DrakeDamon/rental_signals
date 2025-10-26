export interface MarketSummary {
  metro: string;
  name: string;
  state: string;
  latestRent: number;
  yoyPct: number;
  heatScore?: number;
}

export interface TrendPoint {
  month: string;
  value: number;
  yoyPct?: number;
  momPct?: number;
}

export interface CompareResult {
  metro: string;
  series: TrendPoint[];
}

// LeaseRadar types
export interface Listing {
  id: string;
  title: string;
  address: string;
  neighborhood: string;
  beds: number;
  baths: number;
  sqft: number;
  currentAsk: number;
  lastDrop?: {
    amount: number;
    daysAgo: number;
  };
  concessions?: string[];
  priceSeries: PricePoint[];
  images: string[];
  amenities?: string[];
  lat: number;
  lng: number;
  yoyPct?: number;
  momPct?: number;
}

export interface PricePoint {
  period: string; // YYYY-MM format
  value: number;
}

export interface Alert {
  id: string;
  listingId?: string;
  neighborhood?: string;
  condition: string;
  threshold?: number;
  channel: 'email' | 'sms';
  cadence: 'immediate' | 'daily' | 'weekly';
  active: boolean;
  createdAt: string;
}

export interface FilterState {
  priceRange: [number, number];
  beds: number | null;
  baths: number | null;
  neighborhoods: string[];
  hasConcessions: boolean;
}

export interface MapViewState {
  latitude: number;
  longitude: number;
  zoom: number;
}


