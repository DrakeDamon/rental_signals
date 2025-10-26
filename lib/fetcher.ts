export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const base = process.env.NEXT_PUBLIC_API_BASE || '';
  const res = await fetch(`${base}${path}`, {
    ...init,
    headers: {
      'Accept': 'application/json',
      ...(init?.headers || {}),
    },
    // Opt into ISR in RSC when used server-side via next fetch options
    next: { revalidate: 3600 },
  });
  if (!res.ok) {
    const text = await res.text().catch(() => '');
    throw new Error(`Request failed ${res.status}: ${text}`);
  }
  return res.json() as Promise<T>;
}


