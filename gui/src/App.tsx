import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { ApiKeys } from './pages/ApiKeys';
import { ApiKeyDetail } from './pages/ApiKeyDetail';
import { Repositories } from './pages/Repositories';
import { ChangePassword } from './pages/ChangePassword';
import { Inspector } from './pages/Inspector';
import { Layout } from './components/layout/Layout';

// Protected route component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-900">
        <div className="text-gray-500 dark:text-gray-400">Loading...</div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return <Layout>{children}</Layout>;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route
          path="/dashboard"
          element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          }
        />
        <Route
          path="/api-keys"
          element={
            <ProtectedRoute>
              <ApiKeys />
            </ProtectedRoute>
          }
        />
        <Route
          path="/api-keys/:id"
          element={
            <ProtectedRoute>
              <ApiKeyDetail />
            </ProtectedRoute>
          }
        />
        <Route
          path="/repositories"
          element={
            <ProtectedRoute>
              <Repositories />
            </ProtectedRoute>
          }
        />
        <Route
          path="/inspector"
          element={
            <ProtectedRoute>
              <Inspector />
            </ProtectedRoute>
          }
        />
        <Route
          path="/change-password"
          element={
            <ProtectedRoute>
              <ChangePassword />
            </ProtectedRoute>
          }
        />
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
