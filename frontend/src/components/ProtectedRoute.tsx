import React from 'react';
import { Navigate, useLocation } from 'react-router-dom';
import { useAuth } from '../context/AutoContext';

interface ProtectedRouteProps {
  children: React.ReactElement;
  requiredRole?: 'client' | 'bank';
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ children, requiredRole }) => {
  const { currentUser } = useAuth();
  const location = useLocation();

  // Если не авторизован -> на страницу входа
  if (!currentUser) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Если зашел клиент на адрес банка -> в /client
  if (requiredRole && currentUser.role !== requiredRole) {
    return <Navigate to={currentUser.role === 'bank' ? '/bank' : '/client'} replace />;
  }

  return children;
};
