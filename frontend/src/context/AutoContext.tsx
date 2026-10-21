import React, { createContext, useContext, useState, useEffect } from 'react';
import type { UserProfile } from '../data/mockData';

interface AuthContextType {
  currentUser: UserProfile | null;
  login: (user: UserProfile) => void;
  logout: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(() => {
    const saved = localStorage.getItem('alfa_user');
    return saved ? JSON.parse(saved) : null;
  });

  const login = (user: UserProfile) => {
    setCurrentUser(user);
    localStorage.setItem('alfa_user', JSON.stringify(user));
  };

  const logout = () => {
    setCurrentUser(null);
    localStorage.removeItem('alfa_user');
  };

  return (
    <AuthContext.Provider value={{ currentUser, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) throw new Error('useAuth must be used within an AuthProvider');
  return context;
};
