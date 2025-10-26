"use client";

import { ResultCard } from '@/components/ResultCard';
import { useStore } from '@/lib/store';
import { useState } from 'react';
import { cn } from '@/lib/utils';

type SortBy = 'price-asc' | 'price-desc' | 'name' | 'neighborhood';

export default function MarketsPage() {
  const listings = useStore((state) => state.listings);
  const [sortBy, setSortBy] = useState<SortBy>('price-asc');
  
  // Sort listings
  const sortedListings = [...listings].sort((a, b) => {
    switch (sortBy) {
      case 'price-asc':
        return a.currentAsk - b.currentAsk;
      case 'price-desc':
        return b.currentAsk - a.currentAsk;
      case 'name':
        return a.title.localeCompare(b.title);
      case 'neighborhood':
        return a.neighborhood.localeCompare(b.neighborhood);
      default:
        return 0;
    }
  });

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-neutral-900 mb-2">All Markets</h1>
        <p className="text-lg text-neutral-600">
          Browse {listings.length} available rental listings in Tampa
        </p>
      </div>
      
      {/* Sort controls */}
      <div className="mb-6 flex items-center justify-between">
        <div className="text-sm text-neutral-600">
          Showing {sortedListings.length} {sortedListings.length === 1 ? 'listing' : 'listings'}
        </div>
        <div className="flex items-center gap-2">
          <label className="text-sm font-medium text-neutral-700">Sort by:</label>
          <select
            value={sortBy}
            onChange={(e) => setSortBy(e.target.value as SortBy)}
            className="px-3 py-2 bg-neutral-0 border-2 border-neutral-300 rounded-lg text-sm font-medium text-neutral-900 focus:outline-none focus:border-brand transition-colors"
          >
            <option value="price-asc">Price: Low to High</option>
            <option value="price-desc">Price: High to Low</option>
            <option value="name">Name</option>
            <option value="neighborhood">Neighborhood</option>
          </select>
        </div>
      </div>

      {/* Listings grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {sortedListings.map((listing) => (
          <ResultCard key={listing.id} listing={listing} />
        ))}
      </div>
    </div>
  );
}

