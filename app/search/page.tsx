'use client';

import { useState } from 'react';
import { FilterBar } from '@/components/FilterBar';
import { ResultCard } from '@/components/ResultCard';
import { useFilteredListings, useStore } from '@/lib/store';
import { CardSkeleton } from '@/components/Skeleton';
import dynamic from 'next/dynamic';

// Dynamically import Map to avoid SSR issues
const Map = dynamic(() => import('@/components/Map').then(mod => mod.Map), {
  ssr: false,
  loading: () => (
    <div className="w-full h-full bg-neutral-100 rounded-lg flex items-center justify-center">
      <div className="text-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-brand mx-auto mb-4"></div>
        <p className="text-neutral-600">Loading map...</p>
      </div>
    </div>
  ),
});

export default function SearchPage() {
  const [showMap, setShowMap] = useState(true);
  const listings = useFilteredListings();
  const setHighlightedListing = useStore((state) => state.setHighlightedListing);
  
  const handleCardHover = (id: string | null) => {
    setHighlightedListing(id);
  };

  return (
    <div className="flex flex-col h-screen">
      {/* Filter bar */}
      <FilterBar sticky />
      
      {/* Main content */}
      <div className="flex-1 flex overflow-hidden">
        {/* Map - hidden on mobile, toggle-able */}
        <div className={`${showMap ? 'w-full lg:w-1/2' : 'w-0'} transition-all duration-medium overflow-hidden`}>
          <div className="h-full p-4">
            <Map
              listings={listings}
              onMarkerClick={(id) => {
                setHighlightedListing(id);
                // Scroll to listing in list
                const element = document.getElementById(`listing-${id}`);
                element?.scrollIntoView({ behavior: 'smooth', block: 'center' });
              }}
            />
          </div>
        </div>
        
        {/* Listings list */}
        <div className={`${showMap ? 'hidden lg:block lg:w-1/2' : 'w-full'} overflow-y-auto`}>
          <div className="p-4 space-y-4">
            {/* Results header */}
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-2xl font-bold text-neutral-900">
                {listings.length} {listings.length === 1 ? 'Listing' : 'Listings'}
              </h2>
              
              {/* Toggle map button (mobile) */}
              <button
                onClick={() => setShowMap(!showMap)}
                className="lg:hidden px-4 py-2 bg-brand text-white rounded-lg font-medium hover:bg-brand-hover transition-colors"
              >
                {showMap ? 'Show List' : 'Show Map'}
              </button>
            </div>
            
            {/* Listings */}
            {listings.length > 0 ? (
              listings.map((listing) => (
                <div key={listing.id} id={`listing-${listing.id}`}>
                  <ResultCard
                    listing={listing}
                    onHover={handleCardHover}
                  />
                </div>
              ))
            ) : (
              <div className="text-center py-16">
                <svg className="w-16 h-16 text-neutral-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <h3 className="text-xl font-semibold text-neutral-900 mb-2">No listings found</h3>
                <p className="text-neutral-600 mb-4">Try adjusting your filters to see more results</p>
                <button
                  onClick={() => useStore.getState().resetFilters()}
                  className="px-6 py-2 bg-brand text-white rounded-lg font-medium hover:bg-brand-hover transition-colors"
                >
                  Clear Filters
                </button>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

