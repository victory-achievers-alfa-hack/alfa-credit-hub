import type { RealtimeEnvelope, RealtimeEvent, RealtimeServerEvent } from './types';

type RealtimeListener = (message: RealtimeEnvelope<RealtimeServerEvent>) => void;

const MAX_QUEUE_SIZE = 50;
const MAX_RECONNECT_DELAY = 10_000;

function createMessageId(): string {
  return typeof crypto.randomUUID === 'function'
    ? crypto.randomUUID()
    : `ws-${Date.now()}-${Math.random().toString(16).slice(2)}`;
}

export class RealtimeClient {
  private socket: WebSocket | null = null;
  private reconnectTimer: number | null = null;
  private reconnectAttempt = 0;
  private stopped = false;
  private readonly listeners = new Set<RealtimeListener>();
  private readonly queue: RealtimeEnvelope<RealtimeEvent>[] = [];
  private readonly url: string;

  constructor(url: string) {
    this.url = url;
  }

  connect(): void {
    if (!this.url || typeof window === 'undefined') return;
    if (this.socket?.readyState === WebSocket.OPEN || this.socket?.readyState === WebSocket.CONNECTING) return;

    this.stopped = false;
    this.socket = new WebSocket(this.url);

    this.socket.addEventListener('open', () => {
      this.reconnectAttempt = 0;
      this.flushQueue();
    });

    this.socket.addEventListener('message', (event) => {
      if (typeof event.data !== 'string') return;

      try {
        const message = JSON.parse(event.data) as RealtimeEnvelope<RealtimeServerEvent>;
        if (!message || typeof message.type !== 'string' || typeof message.id !== 'string') return;
        this.listeners.forEach((listener) => listener(message));
      } catch {
        // Ignore malformed realtime messages without breaking the main application flow.
      }
    });

    this.socket.addEventListener('close', () => {
      this.socket = null;
      if (!this.stopped) this.scheduleReconnect();
    });
  }

  publish(event: RealtimeEvent): void {
    if (!this.url) return;

    const message: RealtimeEnvelope<RealtimeEvent> = {
      ...event,
      id: createMessageId(),
      sentAt: new Date().toISOString(),
    };

    if (this.socket?.readyState === WebSocket.OPEN) {
      this.socket.send(JSON.stringify(message));
      return;
    }

    if (this.queue.length >= MAX_QUEUE_SIZE) this.queue.shift();
    this.queue.push(message);
    this.connect();
  }

  subscribe(listener: RealtimeListener): () => void {
    this.listeners.add(listener);
    return () => this.listeners.delete(listener);
  }

  disconnect(): void {
    this.stopped = true;
    if (this.reconnectTimer !== null) window.clearTimeout(this.reconnectTimer);
    this.reconnectTimer = null;
    this.socket?.close();
    this.socket = null;
  }

  private flushQueue(): void {
    if (this.socket?.readyState !== WebSocket.OPEN) return;
    while (this.queue.length > 0) {
      const message = this.queue.shift();
      if (message) this.socket.send(JSON.stringify(message));
    }
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer !== null) return;
    const delay = Math.min(1_000 * 2 ** this.reconnectAttempt, MAX_RECONNECT_DELAY);
    this.reconnectAttempt += 1;
    this.reconnectTimer = window.setTimeout(() => {
      this.reconnectTimer = null;
      this.connect();
    }, delay);
  }
}
