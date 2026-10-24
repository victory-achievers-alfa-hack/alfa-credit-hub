import { createContext, useContext, useEffect, useRef, useState, type ReactNode } from 'react';
import { api, ApiError } from '../services/api';
import { DEMO_USERS } from '../data/mockData';
import type { UserProfile } from '../types/credit';

interface LoginResult { success: boolean; message?: string }
interface AuthContextValue {
  currentUser: UserProfile | null;
  login: (email: string, password: string) => Promise<LoginResult>;
  loginAs: (userId: string) => Promise<LoginResult>;
  logout: () => Promise<void>;
}
const AuthContext = createContext<AuthContextValue | undefined>(undefined);
const displayUser = (user: UserProfile) => ({ ...user, avatarText: user.name.slice(0, 2).toUpperCase() });
export function AuthProvider({ children }: { children: ReactNode }) {
  const [currentUser, setUser] = useState<UserProfile | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const signingIn = useRef(false);
  useEffect(() => {
    const controller = new AbortController();
    api<UserProfile>('/me', undefined, controller.signal).then(u => setUser(displayUser(u))).catch(e => {
      if (!controller.signal.aborted && !(e instanceof ApiError && e.status === 401)) setError('Не удалось проверить сессию. Обновите страницу.');
    }).finally(() => { if (!controller.signal.aborted) setLoading(false); });
    const expired = () => setUser(null);
    window.addEventListener('session-expired', expired);
    return () => { controller.abort(); window.removeEventListener('session-expired', expired); };
  }, []);
  const login = async (email: string, password: string): Promise<LoginResult> => {
    if (signingIn.current) return { success: false, message: 'Вход уже выполняется' };
    signingIn.current = true;
    try {
      const result = await api<{ user: UserProfile }>('/auth/login', { email, password });
      setUser(displayUser(result.user)); setError(''); return { success: true };
    } catch (e) { return { success: false, message: e instanceof Error ? e.message : 'Не удалось войти' }; }
    finally { signingIn.current = false; }
  };
  const logout = async () => {
    try { await api('/auth/logout', {}); setUser(null); setError(''); }
    catch { setError('Не удалось завершить сессию. Повторите выход.'); }
  };
  if (loading) return <p role="status">Проверяем сессию…</p>;
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
