import { RealtimeClient } from './RealtimeClient';

const configuredUrl = import.meta.env.VITE_WS_URL?.trim();
const defaultDevelopmentUrl = import.meta.env.DEV ? 'ws://localhost:8080' : '';

export const realtimeClient = new RealtimeClient(configuredUrl || defaultDevelopmentUrl);
export type { RealtimeEnvelope, RealtimeEvent, RealtimeServerEvent } from './types';
