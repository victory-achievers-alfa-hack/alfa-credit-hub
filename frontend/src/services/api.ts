const base = (import.meta.env.VITE_API_URL ?? '/api/v1').replace(/\/$/, '');
const DEFAULT_TIMEOUT_MS = 20_000;

type HttpMethod = 'GET' | 'POST';

interface ApiErrorPayload {
  code?: string;
  message?: string;
  fieldErrors?: Record<string, string> | null;
  detail?: { code?: string; message?: string } | string;
}

export interface ApiRequestOptions {
  method?: HttpMethod;
  body?: unknown;
  signal?: AbortSignal;
  timeoutMs?: number;
}

export class ApiError extends Error {
  readonly status: number;
  readonly code?: string;
  readonly fieldErrors: Record<string, string>;

  constructor(
    status: number,
    message: string,
    code?: string,
    fieldErrors?: Record<string, string> | null,
  ) {
    super(message);
    this.name = 'ApiError';
    this.status = status;
    this.code = code;
    this.fieldErrors = fieldErrors ?? {};
  }
}

function parsePayload(text: string): unknown {
  if (!text) return undefined;
  try {
    return JSON.parse(text);
  } catch {
    return undefined;
  }
}

export async function api<T>(path: string, options: ApiRequestOptions = {}): Promise<T> {
  const controller = new AbortController();
  const { method = 'GET', body, signal, timeoutMs = DEFAULT_TIMEOUT_MS } = options;
  const abortFromCaller = () => controller.abort(signal?.reason);
  if (signal?.aborted) abortFromCaller();
  else signal?.addEventListener('abort', abortFromCaller, { once: true });
  const timeout = window.setTimeout(() => controller.abort('timeout'), timeoutMs);

  try {
    const response = await fetch(`${base}${path}`, {
      method,
      credentials: 'include',
      signal: controller.signal,
      headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    });
    const text = response.status === 204 ? '' : await response.text();
    const data = parsePayload(text) as ApiErrorPayload | undefined;

    if (!response.ok) {
      if (response.status === 401) window.dispatchEvent(new Event('session-expired'));
      const detail = typeof data?.detail === 'object' ? data.detail : undefined;
      throw new ApiError(
        response.status,
        data?.message ?? detail?.message ?? (typeof data?.detail === 'string' ? data.detail : `Ошибка запроса (${response.status})`),
        data?.code ?? detail?.code,
        data?.fieldErrors,
      );
    }

    if (!text) return undefined as T;
    if (!response.headers.get('content-type')?.toLowerCase().includes('application/json') || data === undefined) {
      throw new ApiError(response.status, 'Сервер вернул ответ в неожиданном формате', 'INVALID_RESPONSE');
    }
    return data as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (controller.signal.aborted && !signal?.aborted) {
      throw new ApiError(0, 'Сервер не ответил вовремя', 'REQUEST_TIMEOUT');
    }
    throw error;
  } finally {
    window.clearTimeout(timeout);
    signal?.removeEventListener('abort', abortFromCaller);
  }
}

export async function allItems<T>(path: string, signal?: AbortSignal): Promise<T[]> {
  const items: T[] = [];
  for (;;) {
    const separator = path.includes('?') ? '&' : '?';
    const page = await api<{ items: T[]; total: number }>(
      `${path}${separator}limit=100&offset=${items.length}`,
      { signal },
    );
    items.push(...page.items);
    if (!page.items.length || items.length >= page.total) return items;
  }
}

export function realtimeUrl(): string {
  const configured = import.meta.env.VITE_WS_URL?.trim();
  if (configured) return configured;
  const url = new URL(`${base}/realtime`, window.location.origin);
  url.protocol = url.protocol === 'https:' ? 'wss:' : 'ws:';
  return url.toString();
}
