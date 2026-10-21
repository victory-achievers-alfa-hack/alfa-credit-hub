import React, { useState } from 'react';
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AutoContext';
import { ProtectedRoute } from './components/ProtectedRoute';
import { Header } from './components/Header/Header';
import { LoginPage } from './pages/LoginPage';
import { ClientDashboard } from './pages/ClientDashboard';
import { NotFoundPage } from './pages/NotFoundPage';
import { INITIAL_APPLICATIONS } from './data/mockData';
import type { CreditApplication } from './types/credit';

const AppRoutes: React.FC = () => {
  const { currentUser, login, logout } = useAuth();
  const [applications, setApplications] = useState<CreditApplication[]>(INITIAL_APPLICATIONS);

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Шапка отображается только авторизованным */}
      {currentUser && <Header currentUser={currentUser} onLogout={logout} />}

      <main style={{ flex: 1 }}>
        <Routes>
          {/* Публичный вход */}
          <Route path="/login" element={<LoginPage onLogin={login} />} />

          {/* Корень: редирект по роли или на /login */}
          <Route
            path="/"
            element={
              <Navigate
                to={currentUser ? (currentUser.role === 'bank' ? '/bank' : '/client') : '/login'}
                replace
              />
            }
          />

          {/* ================= КОНТУР КЛИЕНТА ================= */}
          {/* /client — витрина и калькулятор */}
          <Route
            path="/client"
            element={
              <ProtectedRoute requiredRole="client">
                <ClientDashboard applications={applications} />
              </ProtectedRoute>
            }
          />

          {/* /client/apply — подача заявки */}
          <Route
            path="/client/apply"
            element={
              <ProtectedRoute requiredRole="client">
                <div style={{ padding: '60px', textAlign: 'center' }}>
                  <h2>Форма подачи заявки (/client/apply)</h2>
                  <p style={{ color: '#6F7985' }}>Тут будет ввод ИНН и автоподтягивание данных</p>
                </div>
              </ProtectedRoute>
            }
          />

          {/* /client/applications — список всех заявок пользователя */}
          <Route
            path="/client/applications"
            element={
              <ProtectedRoute requiredRole="client">
                <ClientDashboard applications={applications} />
              </ProtectedRoute>
            }
          />

          {/* /client/applications/:id — трекер статуса, оффер, подписание */}
          <Route
            path="/client/applications/:id"
            element={
              <ProtectedRoute requiredRole="client">
                <div style={{ padding: '60px', textAlign: 'center' }}>
                  <h2>Трекер статуса заявки (/client/applications/:id)</h2>
                  <p style={{ color: '#6F7985' }}>Таймлайн статусов, оффер банка и подписание</p>
                </div>
              </ProtectedRoute>
            }
          />

          {/* ================= КОНТУР БАНКА ================= */}
          {/* /bank — дашборд кредитного инспектора */}
          <Route
            path="/bank"
            element={
              <ProtectedRoute requiredRole="bank">
                <div style={{ padding: '60px', textAlign: 'center' }}>
                  <h2>Рабочее место банка (/bank)</h2>
                  <p style={{ color: '#6F7985' }}>Таблица всех входящих заявок бизнеса</p>
                </div>
              </ProtectedRoute>
            }
          />

          {/* /bank/applications/:id — детальная карточка разбора */}
          <Route
            path="/bank/applications/:id"
            element={
              <ProtectedRoute requiredRole="bank">
                <div style={{ padding: '60px', textAlign: 'center' }}>
                  <h2>Карточка разбора заявки андеррайтером (/bank/applications/:id)</h2>
                  <p style={{ color: '#6F7985' }}>Скоринг, ФНС, БКИ, AI-резюме и кнопки решений</p>
                </div>
              </ProtectedRoute>
            }
          />

          {/* 404 */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </main>
    </div>
  );
};

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRoutes />
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
