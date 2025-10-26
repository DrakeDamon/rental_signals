'use client';

import { useState } from 'react';
import { ResultCard } from '@/components/ResultCard';
import { useWatchlistListings, useStore } from '@/lib/store';
import Link from 'next/link';

export default function WatchlistPage() {
  const [activeTab, setActiveTab] = useState<'saved' | 'alerts'>('saved');
  const watchlistListings = useWatchlistListings();
  const alerts = useStore((state) => state.alerts);
  const removeAlert = useStore((state) => state.removeAlert);
  const toggleAlert = useStore((state) => state.toggleAlert);

  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-neutral-900 mb-2">My Watchlist</h1>
        <p className="text-lg text-neutral-600">Track your favorite listings and price alerts</p>
      </div>

      {/* Tabs */}
      <div className="flex gap-4 border-b border-neutral-200 dark:border-neutral-100 mb-8">
        <button
          onClick={() => setActiveTab('saved')}
          className={`pb-3 px-1 font-semibold transition-colors relative ${
            activeTab === 'saved'
              ? 'text-brand border-b-2 border-brand'
              : 'text-neutral-600 hover:text-neutral-900'
          }`}
        >
          Saved Listings
          {watchlistListings.length > 0 && (
            <span className="ml-2 px-2 py-0.5 bg-neutral-200 text-neutral-700 text-xs font-bold rounded-full">
              {watchlistListings.length}
            </span>
          )}
        </button>
        <button
          onClick={() => setActiveTab('alerts')}
          className={`pb-3 px-1 font-semibold transition-colors relative ${
            activeTab === 'alerts'
              ? 'text-brand border-b-2 border-brand'
              : 'text-neutral-600 hover:text-neutral-900'
          }`}
        >
          Price Alerts
          {alerts.length > 0 && (
            <span className="ml-2 px-2 py-0.5 bg-neutral-200 text-neutral-700 text-xs font-bold rounded-full">
              {alerts.length}
            </span>
          )}
        </button>
      </div>

      {/* Saved Listings Tab */}
      {activeTab === 'saved' && (
        <div>
          {watchlistListings.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {watchlistListings.map((listing) => (
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
                  d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
                />
              </svg>
              <h3 className="text-xl font-semibold text-neutral-900 mb-2">
                No saved listings yet
              </h3>
              <p className="text-neutral-600 mb-6">
                Start building your watchlist by saving listings you're interested in
              </p>
              <Link
                href="/search"
                className="inline-flex items-center gap-2 px-6 py-3 bg-brand hover:bg-brand-hover text-white font-semibold rounded-lg transition-colors"
              >
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
                Browse Listings
              </Link>
            </div>
          )}
        </div>
      )}

      {/* Alerts Tab */}
      {activeTab === 'alerts' && (
        <div>
          {alerts.length > 0 ? (
            <div className="space-y-4">
              {alerts.map((alert) => {
                const listing = watchlistListings.find((l) => l.id === alert.listingId);
                return (
                  <div
                    key={alert.id}
                    className="bg-neutral-50 dark:bg-neutral-50 rounded-lg p-6 flex items-center justify-between"
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-3 mb-2">
                        <h3 className="font-semibold text-neutral-900">
                          {listing ? listing.title : alert.neighborhood || 'Price Alert'}
                        </h3>
                        <span
                          className={`px-2 py-0.5 rounded-full text-xs font-medium ${
                            alert.active
                              ? 'bg-success text-white'
                              : 'bg-neutral-300 text-neutral-700'
                          }`}
                        >
                          {alert.active ? 'Active' : 'Paused'}
                        </span>
                      </div>
                      <p className="text-sm text-neutral-600 mb-1">{alert.condition}</p>
                      <div className="flex items-center gap-4 text-xs text-neutral-500">
                        <span className="flex items-center gap-1">
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                            />
                          </svg>
                          {alert.channel}
                        </span>
                        <span className="flex items-center gap-1">
                          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
                            />
                          </svg>
                          {alert.cadence}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <button
                        onClick={() => toggleAlert(alert.id)}
                        className="px-4 py-2 rounded-lg border-2 border-neutral-300 text-neutral-700 hover:border-brand hover:text-brand font-medium transition-colors"
                      >
                        {alert.active ? 'Pause' : 'Resume'}
                      </button>
                      <button
                        onClick={() => removeAlert(alert.id)}
                        className="px-4 py-2 rounded-lg bg-error hover:bg-error-hover text-white font-medium transition-colors"
                      >
                        Delete
                      </button>
                    </div>
                  </div>
                );
              })}
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
                  d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
                />
              </svg>
              <h3 className="text-xl font-semibold text-neutral-900 mb-2">No alerts set up</h3>
              <p className="text-neutral-600 mb-6">
                Create alerts to get notified when prices drop on your favorite listings
              </p>
              <button className="inline-flex items-center gap-2 px-6 py-3 bg-brand hover:bg-brand-hover text-white font-semibold rounded-lg transition-colors">
                <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 4v16m8-8H4"
                  />
                </svg>
                Create Alert
              </button>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

