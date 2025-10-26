'use client';

import { ResultCard } from '@/components/ResultCard';
import { useDropListings } from '@/lib/store';
import { formatPercent } from '@/lib/utils';

export default function DropsPage() {
  const dropListings = useDropListings();

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-neutral-900 mb-2">Recent Price Drops</h1>
        <p className="text-lg text-neutral-600">
          {dropListings.length} {dropListings.length === 1 ? 'listing' : 'listings'} with recent price reductions
        </p>
      </div>

      {/* Stats cards */}
      {dropListings.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
          <div className="bg-error/10 rounded-lg p-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-full bg-error text-white flex items-center justify-center">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 17h8m0 0V9m0 8l-8-8-4 4-6-6" />
                </svg>
              </div>
              <h3 className="font-semibold text-neutral-900">Biggest Drop</h3>
            </div>
            <p className="text-3xl font-bold text-error">
              {formatPercent(
                ((dropListings[0].lastDrop?.amount || 0) / dropListings[0].currentAsk) * 100
              )}
            </p>
            <p className="text-sm text-neutral-600 mt-1">{dropListings[0].neighborhood}</p>
          </div>

          <div className="bg-accent/10 rounded-lg p-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-full bg-accent text-white flex items-center justify-center">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="font-semibold text-neutral-900">Avg. Savings</h3>
            </div>
            <p className="text-3xl font-bold text-accent">
              $
              {Math.round(
                dropListings.reduce((sum, l) => sum + (l.lastDrop?.amount || 0), 0) /
                  dropListings.length
              )}
            </p>
            <p className="text-sm text-neutral-600 mt-1">per month</p>
          </div>

          <div className="bg-brand/10 rounded-lg p-6">
            <div className="flex items-center gap-3 mb-2">
              <div className="w-10 h-10 rounded-full bg-brand text-white flex items-center justify-center">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="font-semibold text-neutral-900">Most Recent</h3>
            </div>
            <p className="text-3xl font-bold text-brand">
              {Math.min(...dropListings.map((l) => l.lastDrop?.daysAgo || 999))}d
            </p>
            <p className="text-sm text-neutral-600 mt-1">ago</p>
          </div>
        </div>
      )}

      {/* Listings grid */}
      {dropListings.length > 0 ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {dropListings.map((listing) => (
            <ResultCard key={listing.id} listing={listing} />
          ))}
        </div>
      ) : (
        <div className="text-center py-16">
          <svg
            className="w-16 h-16 text-neutral-400 mx-auto mb-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={1.5}
              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
          <h3 className="text-xl font-semibold text-neutral-900 mb-2">No price drops right now</h3>
          <p className="text-neutral-600">Check back soon for new deals</p>
        </div>
      )}
    </div>
  );
}

