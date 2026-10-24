import { createContext, useContext, useMemo, useState, type ReactNode } from 'react';
import { DEMO_USERS } from '../data/mockData';
import type { UserProfile } from '../types/credit';

interface LoginResult {
  success: boolean;
  message?: string;
}

interface AuthContextValue {
  currentUser: UserProfile | null;
  login: (email: string, password: string) => LoginResult;
  loginAs: (userId: string) => void;
  logout: () => void;
}

const USER_STORAGE_KEY = 'alfa_stream_user_v2';
const AuthContext = createContext<AuthContextValue | undefined>(undefined);

function getSavedUser(): UserProfile | null {
  const userId = sessionStorage.getItem(USER_STORAGE_KEY);
  return DEMO_USERS.find((user) => user.id === userId) ?? null;
}

export function AuthProvider({ children }: { children: ReactNode }) {
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(getSavedUser);

  const value = useMemo<AuthContextValue>(() => ({
    currentUser,
    login: (email, password) => {
      const user = DEMO_USERS.find(
        (candidate) => candidate.email.toLowerCase() === email.trim().toLowerCase() && candidate.password === password,
      );

      if (!user) {
        return { success: false, message: 'Проверьте логин и пароль. Для демо используется пароль 123456.' };
      }

      setCurrentUser(user);
      sessionStorage.setItem(USER_STORAGE_KEY, user.id);
      return { success: true };
    },
    loginAs: (userId) => {
      const user = DEMO_USERS.find((candidate) => candidate.id === userId);
      if (!user) return;
      setCurrentUser(user);
      sessionStorage.setItem(USER_STORAGE_KEY, user.id);
    },
    logout: () => {
      setCurrentUser(null);
      sessionStorage.removeItem(USER_STORAGE_KEY);
    },
  }), [currentUser]);

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

// oxlint-disable-next-line react/only-export-components -- Provider and hook intentionally share one context module.
export function useAuth(): AuthContextValue {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within AuthProvider');
  return context;
}
