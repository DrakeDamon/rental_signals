'use client';

import { ResultCard } from './ResultCard';
import { useDropListings } from '@/lib/store';

export function DropListingsSection() {
  const dropListings = useDropListings();
  const topDrops = dropListings.slice(0, 3);
  
  if (topDrops.length === 0) {
    return null;
  }
  
  return (
    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
      {topDrops.map((listing) => (
        <ResultCard key={listing.id} listing={listing} />
      ))}
    </div>
  );
}

