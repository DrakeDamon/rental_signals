'use client';

import { useState, useEffect } from 'react';
import { useStore } from '@/lib/store';
import { RangeSlider } from './RangeSlider';
import { neighborhoods } from '@/lib/fixtures';
import { cn } from '@/lib/utils';

interface FilterBarProps {
  sticky?: boolean;
}

export function FilterBar({ sticky = true }: FilterBarProps) {
  const [isScrolled, setIsScrolled] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  
  const filters = useStore((state) => state.filters);
  const updateFilters = useStore((state) => state.updateFilters);
  const resetFilters = useStore((state) => state.resetFilters);
  
  useEffect(() => {
    if (!sticky) return;
    
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 100);
    };
    
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, [sticky]);
  
  const activeFilterCount = [
    filters.beds !== null,
    filters.baths !== null,
    filters.neighborhoods.length > 0,
    filters.hasConcessions,
    filters.priceRange[0] !== 500 || filters.priceRange[1] !== 5000,
  ].filter(Boolean).length;

  return (
    <div
      className={cn(
        'bg-neutral-0 border-b border-neutral-200 dark:border-neutral-100 transition-all duration-medium z-40',
        sticky && 'sticky top-0',
        isScrolled && sticky && 'shadow-md py-2',
        !isScrolled && 'py-4'
      )}
    >
      <div className="mx-auto max-w-7xl px-4">
        {/* Main filter chips */}
        <div className="flex items-center gap-3 overflow-x-auto pb-2 scrollbar-hide">
          {/* Toggle filters button */}
          <button
            onClick={() => setShowFilters(!showFilters)}
            className={cn(
              'flex-shrink-0 px-4 py-2 rounded-lg border-2 font-medium transition-all duration-fast',
              showFilters
                ? 'border-brand bg-brand text-white'
                : 'border-neutral-300 bg-neutral-0 text-neutral-700 hover:border-brand'
            )}
          >
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
              </svg>
              <span>Filters</span>
              {activeFilterCount > 0 && (
                <span className="ml-1 px-1.5 py-0.5 bg-brand-hover text-white rounded-full text-xs font-semibold">
                  {activeFilterCount}
                </span>
              )}
            </div>
          </button>
          
          {/* Beds filter chips */}
          <div className="flex gap-2">
            {[0, 1, 2, 3].map((beds) => (
              <button
                key={beds}
                onClick={() => updateFilters({ beds: filters.beds === beds ? null : beds })}
                className={cn(
                  'flex-shrink-0 px-4 py-2 rounded-lg border-2 font-medium transition-colors duration-fast',
                  filters.beds === beds
                    ? 'border-brand bg-brand text-white'
                    : 'border-neutral-300 bg-neutral-0 text-neutral-700 hover:border-neutral-400'
                )}
              >
                {beds === 0 ? 'Studio' : `${beds} Bed${beds > 1 ? 's' : ''}`}
              </button>
            ))}
          </div>
          
          {/* Concessions toggle */}
          <button
            onClick={() => updateFilters({ hasConcessions: !filters.hasConcessions })}
            className={cn(
              'flex-shrink-0 px-4 py-2 rounded-lg border-2 font-medium transition-colors duration-fast',
              filters.hasConcessions
                ? 'border-accent bg-accent text-white'
                : 'border-neutral-300 bg-neutral-0 text-neutral-700 hover:border-neutral-400'
            )}
          >
            <div className="flex items-center gap-2">
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
              </svg>
              <span>Special Offers</span>
            </div>
          </button>
          
          {/* Reset button */}
          {activeFilterCount > 0 && (
            <button
              onClick={resetFilters}
              className="flex-shrink-0 px-4 py-2 rounded-lg text-neutral-600 hover:text-neutral-900 font-medium transition-colors duration-fast"
            >
              Clear all
            </button>
          )}
        </div>
        
        {/* Expanded filters panel */}
        {showFilters && (
          <div className="mt-4 p-4 bg-neutral-50 dark:bg-neutral-50 rounded-lg space-y-6">
            {/* Price range */}
            <div>
              <RangeSlider
                min={500}
                max={5000}
                step={50}
                value={filters.priceRange}
                onChange={(value) => updateFilters({ priceRange: value })}
                label="Monthly Rent"
              />
            </div>
            
            {/* Bathrooms */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-2">
                Bathrooms (minimum)
              </label>
              <div className="flex gap-2">
                {[null, 1, 1.5, 2, 2.5, 3].map((baths) => (
                  <button
                    key={baths ?? 'any'}
                    onClick={() => updateFilters({ baths })}
                    className={cn(
                      'px-4 py-2 rounded-lg border-2 font-medium transition-colors duration-fast',
                      filters.baths === baths
                        ? 'border-brand bg-brand text-white'
                        : 'border-neutral-300 bg-neutral-0 text-neutral-700 hover:border-neutral-400'
                    )}
                  >
                    {baths === null ? 'Any' : `${baths}+`}
                  </button>
                ))}
              </div>
            </div>
            
            {/* Neighborhoods */}
            <div>
              <label className="block text-sm font-medium text-neutral-700 mb-2">
                Neighborhoods
              </label>
              <div className="flex flex-wrap gap-2">
                {neighborhoods.map((neighborhood) => {
                  const isSelected = filters.neighborhoods.includes(neighborhood);
                  return (
                    <button
                      key={neighborhood}
                      onClick={() => {
                        const newNeighborhoods = isSelected
                          ? filters.neighborhoods.filter((n) => n !== neighborhood)
                          : [...filters.neighborhoods, neighborhood];
                        updateFilters({ neighborhoods: newNeighborhoods });
                      }}
                      className={cn(
                        'px-3 py-1.5 rounded-lg border-2 text-sm font-medium transition-colors duration-fast',
                        isSelected
                          ? 'border-brand bg-brand text-white'
                          : 'border-neutral-300 bg-neutral-0 text-neutral-700 hover:border-neutral-400'
                      )}
                    >
                      {neighborhood}
                    </button>
                  );
                })}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

