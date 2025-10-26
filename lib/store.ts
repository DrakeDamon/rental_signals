import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import type { Listing, Alert, FilterState, MapViewState } from '@/types';
import { fixtureListings, defaultMapCenter } from './fixtures';

interface StoreState {
  // Listings
  listings: Listing[];
  selectedListingId: string | null;
  setSelectedListing: (id: string | null) => void;
  
  // Watchlist
  watchlist: string[]; // listing IDs
  addToWatchlist: (id: string) => void;
  removeFromWatchlist: (id: string) => void;
  isInWatchlist: (id: string) => boolean;
  
  // Alerts
  alerts: Alert[];
  addAlert: (alert: Omit<Alert, 'id' | 'createdAt'>) => void;
  removeAlert: (id: string) => void;
  toggleAlert: (id: string) => void;
  
  // Filters
  filters: FilterState;
  updateFilters: (filters: Partial<FilterState>) => void;
  resetFilters: () => void;
  
  // Map view
  mapView: MapViewState;
  setMapView: (view: Partial<MapViewState>) => void;
  
  // Highlighted listing (for map/list sync)
  highlightedListingId: string | null;
  setHighlightedListing: (id: string | null) => void;
}

const defaultFilters: FilterState = {
  priceRange: [500, 5000],
  beds: null,
  baths: null,
  neighborhoods: [],
  hasConcessions: false,
};

// Store with persistence for watchlist and alerts
export const useStore = create<StoreState>()(
  persist(
    (set, get) => ({
      // Listings
      listings: fixtureListings,
      selectedListingId: null,
      setSelectedListing: (id) => set({ selectedListingId: id }),
      
      // Watchlist
      watchlist: [],
      addToWatchlist: (id) => {
        const { watchlist } = get();
        if (!watchlist.includes(id)) {
          set({ watchlist: [...watchlist, id] });
        }
      },
      removeFromWatchlist: (id) => {
        const { watchlist } = get();
        set({ watchlist: watchlist.filter((item) => item !== id) });
      },
      isInWatchlist: (id) => {
        return get().watchlist.includes(id);
      },
      
      // Alerts
      alerts: [],
      addAlert: (alert) => {
        const newAlert: Alert = {
          ...alert,
          id: `alert-${Date.now()}`,
          createdAt: new Date().toISOString(),
          active: true,
        };
        set({ alerts: [...get().alerts, newAlert] });
      },
      removeAlert: (id) => {
        set({ alerts: get().alerts.filter((alert) => alert.id !== id) });
      },
      toggleAlert: (id) => {
        set({
          alerts: get().alerts.map((alert) =>
            alert.id === id ? { ...alert, active: !alert.active } : alert
          ),
        });
      },
      
      // Filters
      filters: defaultFilters,
      updateFilters: (newFilters) => {
        set({ filters: { ...get().filters, ...newFilters } });
      },
      resetFilters: () => {
        set({ filters: defaultFilters });
      },
      
      // Map view
      mapView: defaultMapCenter,
      setMapView: (view) => {
        set({ mapView: { ...get().mapView, ...view } });
      },
      
      // Highlighted listing
      highlightedListingId: null,
      setHighlightedListing: (id) => {
        set({ highlightedListingId: id });
      },
    }),
    {
      name: 'leaseradar-storage',
      partialize: (state) => ({
        watchlist: state.watchlist,
        alerts: state.alerts,
      }),
    }
  )
);

// Filtered listings selector
export const useFilteredListings = () => {
  const listings = useStore((state) => state.listings);
  const filters = useStore((state) => state.filters);
  
  return listings.filter((listing) => {
    // Price range filter
    if (
      listing.currentAsk < filters.priceRange[0] ||
      listing.currentAsk > filters.priceRange[1]
    ) {
      return false;
    }
    
    // Beds filter
    if (filters.beds !== null && listing.beds !== filters.beds) {
      return false;
    }
    
    // Baths filter
    if (filters.baths !== null && listing.baths < filters.baths) {
      return false;
    }
    
    // Neighborhoods filter
    if (
      filters.neighborhoods.length > 0 &&
      !filters.neighborhoods.includes(listing.neighborhood)
    ) {
      return false;
    }
    
    // Concessions filter
    if (
      filters.hasConcessions &&
      (!listing.concessions || listing.concessions.length === 0)
    ) {
      return false;
    }
    
    return true;
  });
};

// Watchlist listings selector
export const useWatchlistListings = () => {
  const listings = useStore((state) => state.listings);
  const watchlist = useStore((state) => state.watchlist);
  
  return listings.filter((listing) => watchlist.includes(listing.id));
};

// Listings with recent drops
export const useDropListings = () => {
  const listings = useStore((state) => state.listings);
  
  return listings
    .filter((listing) => listing.lastDrop)
    .sort((a, b) => {
      const aPercent = a.lastDrop
        ? (a.lastDrop.amount / a.currentAsk) * 100
        : 0;
      const bPercent = b.lastDrop
        ? (b.lastDrop.amount / b.currentAsk) * 100
        : 0;
      return bPercent - aPercent;
    });
};

