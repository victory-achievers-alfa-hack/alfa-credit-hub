import { createContext, useCallback, useContext, useEffect, useRef, useState, type ReactNode } from 'react';
import { api, ApiError } from '../services/api';
import { DEMO_USERS } from '../constants';
import { PageSkeleton } from '../components/PageSkeleton';
import type { UserProfile } from '../types/credit';

interface LoginResult { success: boolean; message?: string }
interface AuthContextValue {
  currentUser: UserProfile | null;
  login: (email: string, password: string) => Promise<LoginResult>;
  loginAs: (userId: string) => Promise<LoginResult>;
  logout: () => Promise<boolean>;
}
const AuthContext = createContext<AuthContextValue | undefined>(undefined);
const AUTH_CHANNEL = 'alfa-stream-auth';
const displayUser = (user: UserProfile) => ({ ...user, avatarText: user.name.slice(0, 2).toUpperCase() });
export function AuthProvider({ children }: { children: ReactNode }) {
  const [currentUser, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const signingIn = useRef(false);
  const channel = useRef<BroadcastChannel | null>(null);
  const restoreSession = useCallback(async (signal?: AbortSignal) => {
    try {
      const user = await api<UserProfile>('/me', { signal });
      if (!signal?.aborted) { setUser(displayUser(user)); setError(''); }
    } catch (e) {
      if (signal?.aborted) return;
      if (e instanceof ApiError && e.status === 401) setUser(null);
      else setError('Не удалось проверить сессию. Обновите страницу.');
    }
  }, []);
  useEffect(() => {
    const controller = new AbortController();
    // The effect synchronizes React auth state with the server-side cookie session.
    // oxlint-disable-next-line react/set-state-in-effect
    void restoreSession(controller.signal).finally(() => {
      if (!controller.signal.aborted) setLoading(false);
    });
    if ('BroadcastChannel' in window) {
      channel.current = new BroadcastChannel(AUTH_CHANNEL);
      channel.current.addEventListener('message', () => { void restoreSession(); });
    }
    const expired = () => setUser(null);
    window.addEventListener('session-expired', expired);
    return () => {
      controller.abort();
      channel.current?.close();
      channel.current = null;
      window.removeEventListener('session-expired', expired);
    };
  }, [restoreSession]);
  const login = async (email: string, password: string): Promise<LoginResult> => {
    if (signingIn.current) return { success: false, message: 'Вход уже выполняется' };
    signingIn.current = true;
    try {
      const result = await api<{ user: UserProfile }>('/auth/login', {
        method: 'POST',
        body: { email, password },
      });
      setUser(displayUser(result.user));
      setError('');
      channel.current?.postMessage({ type: 'session-changed' });
      return { success: true };
    } catch (e) { return { success: false, message: e instanceof Error ? e.message : 'Не удалось войти' }; }
    finally { signingIn.current = false; }
  };
  const logout = async (): Promise<boolean> => {
    try {
      await api<void>('/auth/logout', { method: 'POST' });
      setUser(null);
      setError('');
      channel.current?.postMessage({ type: 'session-changed' });
      return true;
    } catch {
      setError('Не удалось завершить сессию. Повторите выход.');
      return false;
    }
  };
  if (loading) return <PageSkeleton label="Проверяем сессию…" />;
  return <AuthContext.Provider value={{ currentUser, login, logout, loginAs: async id => {
    const demo = DEMO_USERS.find(user => user.id === id);
    return demo ? login(demo.email, '123456') : { success: false, message: 'Профиль не найден' };
  } }}>{error && <p role="alert">{error}</p>}{children}</AuthContext.Provider>;
}
// oxlint-disable-next-line react/only-export-components
export function useAuth(): AuthContextValue {
  const value = useContext(AuthContext);
  if (!value) throw new Error('AuthProvider is missing');
  return value;
}
