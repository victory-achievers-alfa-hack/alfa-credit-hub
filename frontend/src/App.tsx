import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { Header } from './components/Header';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AuthProvider, useAuth } from './context/AutoContext';
import { CreditProvider } from './context/CreditContext';
import { ApplicationFormPage } from './pages/ApplicationFormPage';
import { BankApplicationPage } from './pages/BankApplicationPage';
import { BankDashboardPage } from './pages/BankDashboardPage';
import { BusinessPage } from './pages/BusinessPage';
import { ClientApplicationPage } from './pages/ClientApplicationPage';
import { ClientApplicationsPage } from './pages/ClientApplicationsPage';
import { ClientDashboard } from './pages/ClientDashboard';
import { FinancingPage } from './pages/FinancingPage';
import { LoginPage } from './pages/LoginPage';
import { NotFoundPage } from './pages/NotFoundPage';

function AppRoutes() {
  const { currentUser } = useAuth();

  return (
    <div className="app">
      {currentUser && <Header />}
      <div className="app__content">
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route
            path="/"
            element={<Navigate to={!currentUser ? '/login' : currentUser.role === 'bank' ? '/bank' : '/client'} replace />}
          />

          <Route path="/client" element={<ProtectedRoute requiredRole="client"><ClientDashboard /></ProtectedRoute>} />
          <Route path="/client/business" element={<ProtectedRoute requiredRole="client"><BusinessPage /></ProtectedRoute>} />
          <Route path="/client/financing" element={<ProtectedRoute requiredRole="client"><FinancingPage /></ProtectedRoute>} />
          <Route path="/client/apply" element={<ProtectedRoute requiredRole="client"><ApplicationFormPage /></ProtectedRoute>} />
          <Route path="/client/applications" element={<ProtectedRoute requiredRole="client"><ClientApplicationsPage /></ProtectedRoute>} />
          <Route path="/client/applications/:id" element={<ProtectedRoute requiredRole="client"><ClientApplicationPage /></ProtectedRoute>} />

          <Route path="/bank" element={<ProtectedRoute requiredRole="bank"><BankDashboardPage /></ProtectedRoute>} />
          <Route path="/bank/applications/:id" element={<ProtectedRoute requiredRole="bank"><BankApplicationPage /></ProtectedRoute>} />

          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </div>
    </div>
  );
}

export function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <CreditProvider>
          <AppRoutes />
        </CreditProvider>
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
