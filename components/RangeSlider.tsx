'use client';

import * as Slider from '@radix-ui/react-slider';
import { formatCurrency } from '@/lib/utils';

interface RangeSliderProps {
  min: number;
  max: number;
  step?: number;
  value: [number, number];
  onChange: (value: [number, number]) => void;
  label?: string;
  formatValue?: (value: number) => string;
}

export function RangeSlider({
  min,
  max,
  step = 1,
  value,
  onChange,
  label,
  formatValue = formatCurrency,
}: RangeSliderProps) {
  return (
    <div className="space-y-2">
      {label && (
        <div className="flex justify-between items-center">
          <label className="text-sm font-medium text-neutral-700">{label}</label>
          <span className="text-sm text-neutral-600">
            {formatValue(value[0])} - {formatValue(value[1])}
          </span>
        </div>
      )}
      <Slider.Root
        className="relative flex items-center select-none touch-none w-full h-5"
        value={value}
        onValueChange={onChange}
        min={min}
        max={max}
        step={step}
        minStepsBetweenThumbs={1}
        aria-label={label}
      >
        <Slider.Track className="bg-neutral-200 dark:bg-neutral-100 relative grow rounded-full h-1">
          <Slider.Range className="absolute bg-brand rounded-full h-full" />
        </Slider.Track>
        <Slider.Thumb
          className="block w-4 h-4 bg-neutral-0 border-2 border-brand rounded-full hover:bg-neutral-50 focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2 transition-colors cursor-grab active:cursor-grabbing"
          aria-label="Minimum value"
        />
        <Slider.Thumb
          className="block w-4 h-4 bg-neutral-0 border-2 border-brand rounded-full hover:bg-neutral-50 focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2 transition-colors cursor-grab active:cursor-grabbing"
          aria-label="Maximum value"
        />
      </Slider.Root>
    </div>
  );
}

