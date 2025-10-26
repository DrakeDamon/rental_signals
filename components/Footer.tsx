import Link from 'next/link';

export function Footer() {
  return (
    <footer className="border-t border-neutral-200 dark:border-neutral-100 bg-neutral-50 dark:bg-neutral-50">
      <div className="mx-auto max-w-7xl px-4 py-8">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
          {/* Brand */}
          <div>
            <div className="flex items-center gap-2 font-bold text-lg text-neutral-900 mb-3">
              <svg className="w-5 h-5 text-brand" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
              </svg>
              <span>LeaseRadar</span>
            </div>
            <p className="text-sm text-neutral-600">
              Real-time Tampa rental market tracking and price drop alerts.
            </p>
          </div>
          
          {/* Navigation */}
          <div>
            <h4 className="font-semibold text-neutral-900 mb-3">Navigate</h4>
            <ul className="space-y-2 text-sm">
              <li><Link href="/search" className="text-neutral-600 hover:text-brand transition-colors">Search</Link></li>
              <li><Link href="/markets" className="text-neutral-600 hover:text-brand transition-colors">Markets</Link></li>
              <li><Link href="/drops" className="text-neutral-600 hover:text-brand transition-colors">Price Drops</Link></li>
              <li><Link href="/watchlist" className="text-neutral-600 hover:text-brand transition-colors">Watchlist</Link></li>
            </ul>
          </div>
          
          {/* Resources */}
          <div>
            <h4 className="font-semibold text-neutral-900 mb-3">Resources</h4>
            <ul className="space-y-2 text-sm">
              <li><a href="#" className="text-neutral-600 hover:text-brand transition-colors">About</a></li>
              <li><a href="#" className="text-neutral-600 hover:text-brand transition-colors">API</a></li>
              <li><a href="#" className="text-neutral-600 hover:text-brand transition-colors">Blog</a></li>
              <li><a href="#" className="text-neutral-600 hover:text-brand transition-colors">Contact</a></li>
            </ul>
          </div>
          
          {/* Legal */}
          <div>
            <h4 className="font-semibold text-neutral-900 mb-3">Legal</h4>
            <ul className="space-y-2 text-sm">
              <li><a href="#" className="text-neutral-600 hover:text-brand transition-colors">Privacy</a></li>
              <li><a href="#" className="text-neutral-600 hover:text-brand transition-colors">Terms</a></li>
              <li><a href="#" className="text-neutral-600 hover:text-brand transition-colors">Data Sources</a></li>
            </ul>
          </div>
        </div>
        
        <div className="mt-8 pt-6 border-t border-neutral-200 dark:border-neutral-100 text-sm text-neutral-600 text-center">
          © {new Date().getFullYear()} LeaseRadar. Built with data from Zillow, ApartmentList, and FRED.
        </div>
      </div>
    </footer>
  );
}


