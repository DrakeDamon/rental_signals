import { cn } from '@/lib/utils';

interface SkeletonProps {
  className?: string;
  variant?: 'card' | 'text' | 'circle' | 'chart' | 'map';
}

export function Skeleton({ className, variant = 'text' }: SkeletonProps) {
  const baseClasses = 'skeleton rounded-md';
  
  const variantClasses = {
    card: 'h-80 w-full',
    text: 'h-4 w-full',
    circle: 'h-12 w-12 rounded-full',
    chart: 'h-64 w-full',
    map: 'h-96 w-full',
  };

  return (
    <div
      className={cn(baseClasses, variantClasses[variant], className)}
      role="status"
      aria-label="Loading..."
    />
  );
}

export function CardSkeleton() {
  return (
    <div className="border border-neutral-200 dark:border-neutral-100 rounded-lg overflow-hidden">
      <Skeleton variant="card" className="rounded-none" />
      <div className="p-4 space-y-3">
        <Skeleton className="h-6 w-3/4" />
        <Skeleton className="h-4 w-1/2" />
        <div className="flex gap-2 pt-2">
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-4 w-16" />
          <Skeleton className="h-4 w-16" />
        </div>
        <Skeleton className="h-6 w-24" />
      </div>
    </div>
  );
}

export function ChartSkeleton() {
  return (
    <div className="space-y-4">
      <div className="flex justify-between items-center">
        <Skeleton className="h-6 w-40" />
        <Skeleton className="h-8 w-32" />
      </div>
      <Skeleton variant="chart" />
    </div>
  );
}

export function ListSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <CardSkeleton key={i} />
      ))}
    </div>
  );
}

