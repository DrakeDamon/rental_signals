'use client';

import { useState } from 'react';
import Image from 'next/image';
import Link from 'next/link';
import type { Listing } from '@/types';
import { cn, formatCurrency, formatPercent } from '@/lib/utils';
import { useStore } from '@/lib/store';

interface ResultCardProps {
  listing: Listing;
  onHover?: (id: string | null) => void;
  compact?: boolean;
}

export function ResultCard({ listing, onHover, compact = false }: ResultCardProps) {
  const [imageError, setImageError] = useState(false);
  const isInWatchlist = useStore((state) => state.isInWatchlist(listing.id));
  const addToWatchlist = useStore((state) => state.addToWatchlist);
  const removeFromWatchlist = useStore((state) => state.removeFromWatchlist);
  const highlightedId = useStore((state) => state.highlightedListingId);
  
  const isHighlighted = highlightedId === listing.id;
  
  const handleWatchlistToggle = (e: React.MouseEvent) => {
    e.preventDefault();
    e.stopPropagation();
    
    if (isInWatchlist) {
      removeFromWatchlist(listing.id);
    } else {
      addToWatchlist(listing.id);
    }
  };
  
  const changeColor = listing.yoyPct && listing.yoyPct >= 0 ? 'text-success' : 'text-error';
  const dropPercent = listing.lastDrop 
    ? ((listing.lastDrop.amount / listing.currentAsk) * 100).toFixed(1)
    : null;

  return (
    <Link
      href={`/listing/${listing.id}`}
      className={cn(
        'block border rounded-lg overflow-hidden card-lift bg-neutral-0',
        'hover:shadow-md transition-all duration-fast',
        isHighlighted && 'ring-2 ring-brand shadow-md'
      )}
      onMouseEnter={() => onHover?.(listing.id)}
      onMouseLeave={() => onHover?.(null)}
    >
      {/* Image */}
      <div className="relative aspect-video bg-neutral-100">
        {!imageError ? (
          <Image
            src={listing.images[0]}
            alt={listing.title}
            fill
            className="object-cover"
            sizes="(max-width: 768px) 100vw, (max-width: 1024px) 50vw, 33vw"
            onError={() => setImageError(true)}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-neutral-400">
            <svg className="w-16 h-16" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
          </div>
        )}
        
        {/* Badges overlay */}
        <div className="absolute top-2 left-2 flex flex-col gap-1">
          {listing.lastDrop && (
            <span className="px-2 py-1 bg-error text-white text-xs font-medium rounded-md shadow-sm">
              -{dropPercent}% Drop
            </span>
          )}
          {listing.concessions && listing.concessions.length > 0 && (
            <span className="px-2 py-1 bg-accent text-white text-xs font-medium rounded-md shadow-sm">
              Special Offer
            </span>
          )}
        </div>
        
        {/* Save button */}
        <button
          onClick={handleWatchlistToggle}
          className="absolute top-2 right-2 w-8 h-8 rounded-full bg-white/90 hover:bg-white backdrop-blur-sm flex items-center justify-center transition-colors duration-fast shadow-sm focus-visible"
          aria-label={isInWatchlist ? 'Remove from watchlist' : 'Add to watchlist'}
        >
          <svg
            className={cn(
              'w-5 h-5 transition-colors',
              isInWatchlist ? 'fill-error text-error' : 'fill-none text-neutral-600'
            )}
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={2}
          >
            <path strokeLinecap="round" strokeLinejoin="round" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
          </svg>
        </button>
        
        {/* Neighborhood badge */}
        <div className="absolute bottom-2 left-2">
          <span className="px-2 py-1 bg-neutral-900/75 text-white text-xs font-medium rounded-md backdrop-blur-sm">
            {listing.neighborhood}
          </span>
        </div>
      </div>
      
      {/* Content */}
      <div className={cn('p-4', compact && 'p-3')}>
        <h3 className={cn('font-semibold text-neutral-900 line-clamp-1', compact ? 'text-sm' : 'text-base')}>
          {listing.title}
        </h3>
        <p className="text-sm text-neutral-600 mt-1 line-clamp-1">{listing.address}</p>
        
        {/* Meta chips */}
        <div className="flex gap-3 mt-3 text-sm text-neutral-700">
          <div className="flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
            <span>{listing.beds} bd</span>
          </div>
          <div className="flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
            </svg>
            <span>{listing.baths} ba</span>
          </div>
          <div className="flex items-center gap-1">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
            <span>{listing.sqft.toLocaleString()} sqft</span>
          </div>
        </div>
        
        {/* Price and change */}
        <div className="flex items-baseline justify-between mt-4">
          <div>
            <span className="text-2xl font-bold text-neutral-900">
              {formatCurrency(listing.currentAsk)}
            </span>
            <span className="text-sm text-neutral-600 ml-1">/mo</span>
          </div>
          {listing.yoyPct !== undefined && (
            <div className={cn('text-sm font-medium', changeColor)}>
              {formatPercent(listing.yoyPct, true)} YoY
            </div>
          )}
        </div>
        
        {/* Concessions note */}
        {listing.concessions && listing.concessions.length > 0 && (
          <div className="mt-2 text-xs text-accent font-medium">
            {listing.concessions[0]}
          </div>
        )}
      </div>
    </Link>
  );
}

