/**
 * App Component - Root application with ALL routing centralized here
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import DashboardLayout from './components/layout/DashboardLayout';
import Login from './pages/Login';
import Register from './pages/Register';
import Agents from './pages/Agents';
import TestCall from './pages/TestCall';
import Calls from './pages/Calls';

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return user ? <>{children}</> : <Navigate to="/login" />;
}

function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Protected Routes - All dashboard pages */}
          <Route
            path="/dashboard"
            element={
              <PrivateRoute>
                <DashboardLayout />
              </PrivateRoute>
            }
          >
            {/* Nested routes - rendered inside DashboardLayout's <Outlet /> */}
            <Route index element={<Navigate to="/dashboard/agents" replace />} />
            <Route path="agents" element={<Agents />} />
            <Route path="test-call" element={<TestCall />} />
            <Route path="calls" element={<Calls />} />
          </Route>

          {/* Root redirect and 404 catch all */}
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}

export default App;
