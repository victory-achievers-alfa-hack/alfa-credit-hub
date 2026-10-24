const base = (import.meta.env.VITE_API_URL ?? '/api/v1').replace(/\/$/, '');

export class ApiError extends Error {
  status: number;
  constructor(status: number, message: string) { super(message); this.status = status; }
}

export async function api<T>(path: string, body?: unknown, signal?: AbortSignal): Promise<T> {
  const response = await fetch(`${base}${path}`, {
    method: body === undefined ? 'GET' : 'POST', credentials: 'include', signal,
    headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401) window.dispatchEvent(new Event('session-expired'));
    throw new ApiError(response.status, data?.message ?? data?.detail?.message ?? `Ошибка запроса (${response.status})`);
  }
  return data as T;
}

export async function allItems<T>(path: string, signal?: AbortSignal): Promise<T[]> {
  const items: T[] = [];
  for (;;) {
    const page = await api<{ items: T[]; total: number }>(`${path}?limit=100&offset=${items.length}`, undefined, signal);
    items.push(...page.items);
    if (!page.items.length || items.length >= page.total) return items;
  }
}

export function realtimeUrl(): string {
  const url = new URL(`${base}/realtime`, window.location.origin);
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  return url.toString();
}
