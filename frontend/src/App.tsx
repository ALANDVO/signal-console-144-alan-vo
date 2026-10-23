import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { useEffect } from 'react';
import { useAuthStore } from './hooks/useAuth';
import { Layout } from './components/Layout';
import { LoginPage } from './components/LoginPage';
import { SkillTable } from './components/SkillTable';
import { EvaluationTable } from './components/EvaluationTable';
import { DriftTable } from './components/DriftTable';
import { AuditTable } from './components/AuditTable';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading, checkAuth } = useAuthStore();
  const location = useLocation();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  if (isLoading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '300px' }}>
        <div className="spinner" />
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  return <>{children}</>;
}

function PublicRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, isLoading } = useAuthStore();

  if (isLoading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '300px' }}>
        <div className="spinner" />
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/skills" replace />;
  }

  return <>{children}</>;
}

export default function App() {
  const { checkAuth } = useAuthStore();

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  return (
    <Routes>
      <Route path="/login" element={
        <PublicRoute>
          <LoginPage />
        </PublicRoute>
      } />
      
      <Route element={
        <ProtectedRoute>
          <Layout />
        </ProtectedRoute>
      }>
        <Route path="/" element={<Navigate to="/skills" replace />} />
        <Route path="/skills" element={<SkillTable />} />
        <Route path="/evaluations" element={<EvaluationTable />} />
        <Route path="/evaluations/:skillId" element={<EvaluationTable />} />
        <Route path="/drift" element={<DriftTable />} />
        <Route path="/audit" element={<AuditTable />} />
      </Route>
      
      <Route path="*" element={<Navigate to="/skills" replace />} />
    </Routes>
  );
}