'use client';

import { useEffect, useRef, useState } from 'react';
import type { Listing } from '@/types';
import { useStore } from '@/lib/store';
import { formatCurrency } from '@/lib/utils';

interface MapProps {
  listings: Listing[];
  onMarkerClick?: (id: string) => void;
}

export function Map({ listings, onMarkerClick }: MapProps) {
  const mapContainer = useRef<HTMLDivElement>(null);
  const [isClient, setIsClient] = useState(false);
  const highlightedId = useStore((state) => state.highlightedListingId);
  const mapView = useStore((state) => state.mapView);

  useEffect(() => {
    setIsClient(true);
  }, []);

  // For now, render a placeholder with listing markers
  // In a full implementation, this would use react-map-gl + maplibre-gl
  return (
    <div
      ref={mapContainer}
      className="w-full h-full bg-neutral-100 dark:bg-neutral-100 rounded-lg relative overflow-hidden"
      style={{
        backgroundImage: `url("data:image/svg+xml,%3Csvg width='60' height='60' viewBox='0 0 60 60' xmlns='http://www.w3.org/2000/svg'%3E%3Cg fill='none' fill-rule='evenodd'%3E%3Cg fill='%23cbd5e1' fill-opacity='0.4'%3E%3Cpath d='M36 34v-4h-2v4h-4v2h4v4h2v-4h4v-2h-4zm0-30V0h-2v4h-4v2h4v4h2V6h4V4h-4zM6 34v-4H4v4H0v2h4v4h2v-4h4v-2H6zM6 4V0H4v4H0v2h4v4h2V6h4V4H6z'/%3E%3C/g%3E%3C/g%3E%3C/svg%3E")`,
      }}
    >
      {/* Map overlay */}
      <div className="absolute inset-0 bg-gradient-to-br from-blue-100/30 to-teal-100/30" />
      
      {/* Pseudo markers */}
      <div className="absolute inset-0 flex items-center justify-center">
        <div className="relative w-full h-full max-w-4xl max-h-96">
          {listings.slice(0, 10).map((listing, index) => {
            const isHighlighted = highlightedId === listing.id;
            // Pseudo-random positioning for demo
            const left = 10 + (index * 17) % 80;
            const top = 15 + (index * 23) % 70;
            
            return (
              <button
                key={listing.id}
                onClick={() => onMarkerClick?.(listing.id)}
                className={`absolute transform -translate-x-1/2 -translate-y-full transition-all duration-fast ${
                  isHighlighted ? 'scale-125 z-10' : 'scale-100 z-0'
                }`}
                style={{ left: `${left}%`, top: `${top}%` }}
                title={listing.title}
              >
                {/* Pin */}
                <div className={`relative ${isHighlighted ? 'animate-bounce' : ''}`}>
                  {/* Price bubble */}
                  <div
                    className={`px-3 py-1.5 rounded-lg font-semibold text-sm shadow-md transition-colors ${
                      isHighlighted
                        ? 'bg-brand text-white'
                        : listing.lastDrop
                        ? 'bg-error text-white'
                        : 'bg-neutral-0 text-neutral-900'
                    }`}
                  >
                    {formatCurrency(listing.currentAsk)}
                  </div>
                  {/* Pointer */}
                  <div
                    className={`absolute left-1/2 -translate-x-1/2 w-0 h-0 border-l-4 border-r-4 border-t-8 border-transparent ${
                      isHighlighted
                        ? 'border-t-brand'
                        : listing.lastDrop
                        ? 'border-t-error'
                        : 'border-t-neutral-0'
                    }`}
                  />
                </div>
              </button>
            );
          })}
        </div>
      </div>
      
      {/* Map controls placeholder */}
      <div className="absolute top-4 right-4 flex flex-col gap-2">
        <button className="w-10 h-10 bg-neutral-0 rounded-lg shadow-md flex items-center justify-center hover:bg-neutral-100 transition-colors">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
          </svg>
        </button>
        <button className="w-10 h-10 bg-neutral-0 rounded-lg shadow-md flex items-center justify-center hover:bg-neutral-100 transition-colors">
          <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20 12H4" />
          </svg>
        </button>
      </div>
      
      {/* Attribution */}
      <div className="absolute bottom-2 left-2 text-xs text-neutral-600 bg-neutral-0/75 px-2 py-1 rounded">
        Map placeholder - MapLibre GL integration pending
      </div>
    </div>
  );
}

