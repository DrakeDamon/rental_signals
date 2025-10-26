'use client';

import { useState } from 'react';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { ThemeToggle } from './ThemeToggle';
import { useStore } from '@/lib/store';
import { cn } from '@/lib/utils';

export function Navbar() {
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const pathname = usePathname();
  const watchlistCount = useStore((state) => state.watchlist.length);
  
  const navLinks = [
    { href: '/search', label: 'Search' },
    { href: '/markets', label: 'Markets' },
    { href: '/drops', label: 'Drops' },
    { href: '/watchlist', label: 'Watchlist' },
  ];
  
  const isActive = (href: string) => pathname?.startsWith(href);

  return (
    <header className="sticky top-0 z-50 border-b border-neutral-200 dark:border-neutral-100 bg-neutral-0/90 backdrop-blur-sm">
      <div className="mx-auto max-w-7xl px-4">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <Link href="/" className="flex items-center gap-2 font-bold text-xl text-neutral-900 hover:text-brand transition-colors">
            <svg className="w-6 h-6 text-brand" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
            <span>LeaseRadar</span>
          </Link>
          
          {/* Desktop navigation */}
          <nav className="hidden md:flex items-center gap-6">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                className={cn(
                  'text-sm font-medium transition-colors duration-fast relative',
                  isActive(link.href)
                    ? 'text-brand'
                    : 'text-neutral-700 hover:text-brand'
                )}
              >
                {link.label}
                {link.label === 'Watchlist' && watchlistCount > 0 && (
                  <span className="absolute -top-2 -right-4 w-5 h-5 bg-error text-white text-xs font-bold rounded-full flex items-center justify-center">
                    {watchlistCount}
                  </span>
                )}
              </Link>
            ))}
          </nav>
          
          {/* Right side actions */}
          <div className="flex items-center gap-3">
            <ThemeToggle />
            
            {/* Mobile menu button */}
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="md:hidden w-10 h-10 rounded-md bg-neutral-100 hover:bg-neutral-200 transition-colors flex items-center justify-center focus-visible"
              aria-label="Toggle menu"
              aria-expanded={mobileMenuOpen}
            >
              {mobileMenuOpen ? (
                <svg className="w-5 h-5 text-neutral-900" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              ) : (
                <svg className="w-5 h-5 text-neutral-900" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              )}
            </button>
          </div>
        </div>
        
        {/* Mobile navigation */}
        {mobileMenuOpen && (
          <nav className="md:hidden py-4 space-y-2 border-t border-neutral-200 dark:border-neutral-100">
            {navLinks.map((link) => (
              <Link
                key={link.href}
                href={link.href}
                onClick={() => setMobileMenuOpen(false)}
                className={cn(
                  'block px-4 py-2 rounded-md text-sm font-medium transition-colors',
                  isActive(link.href)
                    ? 'bg-brand text-white'
                    : 'text-neutral-700 hover:bg-neutral-100'
                )}
              >
                <div className="flex items-center justify-between">
                  <span>{link.label}</span>
                  {link.label === 'Watchlist' && watchlistCount > 0 && (
                    <span className="px-2 py-0.5 bg-error text-white text-xs font-bold rounded-full">
                      {watchlistCount}
                    </span>
                  )}
                </div>
              </Link>
            ))}
          </nav>
        )}
      </div>
    </header>
  );
}


