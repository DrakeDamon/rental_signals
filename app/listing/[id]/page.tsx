'use client';

import { use } from 'react';
import { useStore } from '@/lib/store';
import { TrendChart } from '@/components/TrendChart';
import { ResultCard } from '@/components/ResultCard';
import { notFound } from 'next/navigation';
import Image from 'next/image';
import { useState } from 'react';
import { formatCurrency, calculateEffectiveRent, formatPercent } from '@/lib/utils';

export default function ListingPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const listings = useStore((state) => state.listings);
  const isInWatchlist = useStore((state) => state.isInWatchlist(id));
  const addToWatchlist = useStore((state) => state.addToWatchlist);
  const removeFromWatchlist = useStore((state) => state.removeFromWatchlist);
  
  const [activeImageIndex, setActiveImageIndex] = useState(0);
  const [imageError, setImageError] = useState(false);

  const listing = listings.find((l) => l.id === id);

  if (!listing) {
    notFound();
  }

  const effectiveRent = calculateEffectiveRent(listing.currentAsk, listing.concessions);
  const savings = listing.currentAsk - effectiveRent;
  
  // Find similar listings (same neighborhood or similar price)
  const similarListings = listings
    .filter(
      (l) =>
        l.id !== listing.id &&
        (l.neighborhood === listing.neighborhood ||
          Math.abs(l.currentAsk - listing.currentAsk) < 300)
    )
    .slice(0, 3);

  const handleWatchlistToggle = () => {
    if (isInWatchlist) {
      removeFromWatchlist(id);
    } else {
      addToWatchlist(id);
    }
  };

  return (
    <div className="bg-neutral-50 dark:bg-neutral-50 min-h-screen">
      {/* Gallery */}
      <div className="bg-neutral-900 relative h-96">
        {!imageError ? (
          <Image
            src={listing.images[activeImageIndex]}
            alt={listing.title}
            fill
            className="object-cover"
            sizes="100vw"
            priority
            onError={() => setImageError(true)}
          />
        ) : (
          <div className="w-full h-full flex items-center justify-center text-neutral-400">
            <svg className="w-32 h-32" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={1}
                d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
              />
            </svg>
          </div>
        )}
        
        {/* Image thumbnails */}
        {listing.images.length > 1 && !imageError && (
          <div className="absolute bottom-4 left-1/2 -translate-x-1/2 flex gap-2">
            {listing.images.map((_, index) => (
              <button
                key={index}
                onClick={() => setActiveImageIndex(index)}
                className={`w-3 h-3 rounded-full transition-colors ${
                  index === activeImageIndex ? 'bg-white' : 'bg-white/50 hover:bg-white/75'
                }`}
                aria-label={`View image ${index + 1}`}
              />
            ))}
          </div>
        )}
      </div>

      <div className="mx-auto max-w-7xl px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main content */}
          <div className="lg:col-span-2 space-y-8">
            {/* Header */}
            <div className="bg-neutral-0 rounded-lg p-6">
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h1 className="text-3xl font-bold text-neutral-900 mb-2">{listing.title}</h1>
                  <p className="text-lg text-neutral-600 flex items-center gap-2">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                      />
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                      />
                    </svg>
                    {listing.address}
                  </p>
                </div>
                <button
                  onClick={handleWatchlistToggle}
                  className={`px-6 py-3 rounded-lg font-semibold transition-colors flex items-center gap-2 ${
                    isInWatchlist
                      ? 'bg-error text-white hover:bg-error-hover'
                      : 'bg-brand text-white hover:bg-brand-hover'
                  }`}
                >
                  <svg className="w-5 h-5" fill={isInWatchlist ? 'currentColor' : 'none'} viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                    />
                  </svg>
                  {isInWatchlist ? 'Saved' : 'Save'}
                </button>
              </div>

              {/* Meta chips */}
              <div className="flex flex-wrap gap-4 text-neutral-700">
                <div className="flex items-center gap-2 px-4 py-2 bg-neutral-100 rounded-lg">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
                    />
                  </svg>
                  <span className="font-medium">{listing.beds} Bedrooms</span>
                </div>
                <div className="flex items-center gap-2 px-4 py-2 bg-neutral-100 rounded-lg">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"
                    />
                  </svg>
                  <span className="font-medium">{listing.baths} Bathrooms</span>
                </div>
                <div className="flex items-center gap-2 px-4 py-2 bg-neutral-100 rounded-lg">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4"
                    />
                  </svg>
                  <span className="font-medium">{listing.sqft.toLocaleString()} sqft</span>
                </div>
                <div className="flex items-center gap-2 px-4 py-2 bg-brand/10 text-brand rounded-lg">
                  <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z"
                    />
                    <path
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      strokeWidth={2}
                      d="M15 11a3 3 0 11-6 0 3 3 0 016 0z"
                    />
                  </svg>
                  <span className="font-medium">{listing.neighborhood}</span>
                </div>
              </div>
            </div>

            {/* Price History Chart */}
            <div className="bg-neutral-0 rounded-lg p-6">
              <TrendChart
                data={listing.priceSeries}
                title="Price History"
                interval={90}
              />
            </div>

            {/* Amenities */}
            {listing.amenities && listing.amenities.length > 0 && (
              <div className="bg-neutral-0 rounded-lg p-6">
                <h2 className="text-2xl font-bold text-neutral-900 mb-4">Amenities</h2>
                <div className="grid grid-cols-2 gap-3">
                  {listing.amenities.map((amenity) => (
                    <div key={amenity} className="flex items-center gap-2 text-neutral-700">
                      <svg className="w-5 h-5 text-success" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth={2}
                          d="M5 13l4 4L19 7"
                        />
                      </svg>
                      <span>{amenity}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Similar Listings */}
            {similarListings.length > 0 && (
              <div className="bg-neutral-0 rounded-lg p-6">
                <h2 className="text-2xl font-bold text-neutral-900 mb-4">Similar Listings</h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {similarListings.map((similar) => (
                    <ResultCard key={similar.id} listing={similar} compact />
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Sidebar */}
          <div className="space-y-6">
            {/* Price card - sticky */}
            <div className="bg-neutral-0 rounded-lg p-6 sticky top-20">
              <div className="mb-4">
                <div className="text-4xl font-bold text-neutral-900 mb-1">
                  {formatCurrency(listing.currentAsk)}
                  <span className="text-xl text-neutral-600 font-normal">/mo</span>
                </div>
                {listing.yoyPct !== undefined && (
                  <div className={`text-sm font-medium ${listing.yoyPct >= 0 ? 'text-success' : 'text-error'}`}>
                    {formatPercent(listing.yoyPct, true)} from last year
                  </div>
                )}
              </div>

              {/* Concessions */}
              {listing.concessions && listing.concessions.length > 0 && (
                <div className="mb-4 p-4 bg-accent/10 border border-accent rounded-lg">
                  <div className="flex items-center gap-2 mb-2">
                    <svg className="w-5 h-5 text-accent" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z"
                      />
                    </svg>
                    <span className="font-semibold text-accent">Special Offer</span>
                  </div>
                  {listing.concessions.map((concession) => (
                    <p key={concession} className="text-sm text-neutral-900 mb-1">
                      {concession}
                    </p>
                  ))}
                  <div className="mt-3 pt-3 border-t border-accent/30">
                    <p className="text-sm text-neutral-600">Effective rent:</p>
                    <p className="text-2xl font-bold text-accent">
                      {formatCurrency(effectiveRent)}/mo
                    </p>
                    <p className="text-xs text-neutral-600 mt-1">
                      Save {formatCurrency(savings)}/month
                    </p>
                  </div>
                </div>
              )}

              {/* Last price drop */}
              {listing.lastDrop && (
                <div className="mb-4 p-4 bg-error/10 border border-error rounded-lg">
                  <div className="flex items-center gap-2 mb-1">
                    <svg className="w-5 h-5 text-error" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path
                        strokeLinecap="round"
                        strokeLinejoin="round"
                        strokeWidth={2}
                        d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6"
                      />
                    </svg>
                    <span className="font-semibold text-error">Recent Price Drop</span>
                  </div>
                  <p className="text-2xl font-bold text-error">
                    -{formatCurrency(listing.lastDrop.amount)}
                  </p>
                  <p className="text-xs text-neutral-600 mt-1">
                    {listing.lastDrop.daysAgo} days ago
                  </p>
                </div>
              )}

              <button
                onClick={handleWatchlistToggle}
                className={`w-full py-3 rounded-lg font-semibold transition-colors ${
                  isInWatchlist
                    ? 'bg-neutral-200 text-neutral-900 hover:bg-neutral-300'
                    : 'bg-brand text-white hover:bg-brand-hover'
                }`}
              >
                {isInWatchlist ? 'Remove from Watchlist' : 'Add to Watchlist'}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

