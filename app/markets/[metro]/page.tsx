import { fetchJson } from '@/lib/fetcher';
import type { MarketSummary, TrendPoint } from '@/types';
import { TrendChart } from '@/components/TrendChart';

interface Params { params: { metro: string } }

async function getData(metro: string) {
  const [summary, series] = await Promise.all([
    fetchJson<MarketSummary>(`/v1/markets/${metro}`),
    fetchJson<TrendPoint[]>(`/v1/markets/${metro}/trends`),
  ]);
  return { summary, series };
}

export default async function MetroPage({ params }: Params) {
  const { metro } = params;
  const { summary, series } = await getData(metro);
  return (
    <div className="mx-auto max-w-7xl px-4 py-8">
      <h1 className="text-2xl font-semibold mb-2">{summary.name}, {summary.state}</h1>
      <p className="text-gray-600 mb-6">{summary.metro}</p>
      <TrendChart data={series} />
    </div>
  );
}

export const revalidate = 3600;


