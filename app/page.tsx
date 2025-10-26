import Link from 'next/link';
import { SearchBar } from '@/components/SearchBar';
import { DropListingsSection } from '@/components/DropListingsSection';

export default function HomePage() {
  return (
    <div>
      {/* Hero Section */}
      <section className="relative bg-gradient-to-br from-brand/10 via-neutral-50 to-accent/10 dark:from-brand/20 dark:via-neutral-50 dark:to-accent/20">
        <div className="mx-auto max-w-7xl px-4 py-24">
          <div className="max-w-3xl mx-auto text-center">
            <h1 className="text-5xl md:text-6xl font-bold text-neutral-900 mb-6">
              Find Your Perfect
              <span className="text-brand"> Tampa Rental</span>
            </h1>
            <p className="text-xl text-neutral-700 mb-12">
              Track real-time prices, get instant alerts on drops, and discover the best deals in Tampa Bay.
            </p>
            
            {/* Search Bar */}
            <div className="max-w-2xl mx-auto mb-8">
              <SearchBar placeholder="Search neighborhoods, or browse all listings..." />
            </div>
            
            {/* Quick links */}
            <div className="flex flex-wrap justify-center gap-3">
              <Link
                href="/search"
                className="px-6 py-3 bg-brand hover:bg-brand-hover text-white font-semibold rounded-lg transition-colors duration-fast shadow-sm"
              >
                Browse All Listings
              </Link>
              <Link
                href="/drops"
                className="px-6 py-3 bg-neutral-0 hover:bg-neutral-100 text-neutral-900 font-semibold rounded-lg transition-colors duration-fast border-2 border-neutral-300"
              >
                See Price Drops
              </Link>
            </div>
          </div>
        </div>
      </section>
      
      {/* Value Props */}
      <section className="py-16 bg-neutral-0">
        <div className="mx-auto max-w-7xl px-4">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            {/* Real-time tracking */}
            <div className="text-center p-6">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-brand/10 text-brand mb-4">
                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-neutral-900 mb-2">Real-Time Tracking</h3>
              <p className="text-neutral-600">
                Monitor rent prices across all Tampa neighborhoods with up-to-date market data.
              </p>
            </div>
            
            {/* Price alerts */}
            <div className="text-center p-6">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-accent/10 text-accent mb-4">
                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-neutral-900 mb-2">Instant Alerts</h3>
              <p className="text-neutral-600">
                Get notified when prices drop on your saved listings or in your favorite neighborhoods.
              </p>
            </div>
            
            {/* Free to use */}
            <div className="text-center p-6">
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full bg-success/10 text-success mb-4">
                <svg className="w-8 h-8" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="text-xl font-semibold text-neutral-900 mb-2">100% Free</h3>
              <p className="text-neutral-600">
                No subscriptions, no hidden fees. Track as many listings as you want, completely free.
              </p>
            </div>
          </div>
        </div>
      </section>
      
      {/* Featured Price Drops */}
      <section className="py-16 bg-neutral-50 dark:bg-neutral-50">
        <div className="mx-auto max-w-7xl px-4">
          <div className="flex items-center justify-between mb-8">
            <div>
              <h2 className="text-3xl font-bold text-neutral-900 mb-2">Recent Price Drops</h2>
              <p className="text-neutral-600">Catch these deals before they're gone</p>
            </div>
            <Link
              href="/drops"
              className="text-brand hover:text-brand-hover font-semibold transition-colors flex items-center gap-1"
            >
              View all
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
              </svg>
            </Link>
          </div>
          
          <DropListingsSection />
          
          {/* CTA */}
          <div className="mt-12 text-center">
            <Link
              href="/search"
              className="inline-flex items-center gap-2 px-8 py-4 bg-brand hover:bg-brand-hover text-white font-semibold rounded-lg transition-colors duration-fast shadow-md"
            >
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
              </svg>
              Start Searching
            </Link>
          </div>
        </div>
      </section>
      
      {/* How it works */}
      <section className="py-16 bg-neutral-0">
        <div className="mx-auto max-w-7xl px-4">
          <h2 className="text-3xl font-bold text-neutral-900 text-center mb-12">How It Works</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-brand text-white font-bold text-lg mb-4">
                1
              </div>
              <h3 className="font-semibold text-neutral-900 mb-2">Search</h3>
              <p className="text-sm text-neutral-600">Browse Tampa rentals by neighborhood, price, or amenities</p>
            </div>
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-brand text-white font-bold text-lg mb-4">
                2
              </div>
              <h3 className="font-semibold text-neutral-900 mb-2">Save</h3>
              <p className="text-sm text-neutral-600">Add interesting listings to your watchlist</p>
            </div>
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-brand text-white font-bold text-lg mb-4">
                3
              </div>
              <h3 className="font-semibold text-neutral-900 mb-2">Track</h3>
              <p className="text-sm text-neutral-600">Monitor price changes and market trends</p>
            </div>
            <div className="text-center">
              <div className="inline-flex items-center justify-center w-12 h-12 rounded-full bg-brand text-white font-bold text-lg mb-4">
                4
              </div>
              <h3 className="font-semibold text-neutral-900 mb-2">Alert</h3>
              <p className="text-sm text-neutral-600">Get notified when prices drop</p>
            </div>
          </div>
        </div>
      </section>
    </div>
  );
}


