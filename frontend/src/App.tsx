import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AuthProvider } from './auth/AuthContext';
import { ProtectedRoute } from './auth/ProtectedRoute';
import { RootLayout, AuthLayout, MotherLayout, AshaLayout } from './layouts';
import {
  HomePage,
  NotFoundPage,
  LoginPage,
  RegisterPage,
  MotherDashboardPage,
  HealthRecordEntryPage,
  RiskTimelinePage,
  AiAssistantPage,
  AshaDashboardPage,
  AlertsQueuePage,
  AssignedMothersPage,
} from './pages';
import './index.css';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Main App Shell */}
          <Route path="/" element={<RootLayout />}>
            <Route index element={<HomePage />} />

            {/* Authentication Sub-routes */}
            <Route path="auth" element={<AuthLayout />}>
              <Route path="login" element={<LoginPage />} />
              <Route path="register" element={<RegisterPage />} />
            </Route>

            {/* Mother Portal (Protected: MOTHER role) */}
            <Route
              path="mother"
              element={
                <ProtectedRoute allowedRoles={['MOTHER']}>
                  <MotherLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<MotherDashboardPage />} />
              <Route path="health-entry" element={<HealthRecordEntryPage />} />
              <Route path="risk-timeline" element={<RiskTimelinePage />} />
              <Route path="ai-assistant" element={<AiAssistantPage />} />
            </Route>

            {/* ASHA Portal (Protected: ASHA role) */}
            <Route
              path="asha"
              element={
                <ProtectedRoute allowedRoles={['ASHA']}>
                  <AshaLayout />
                </ProtectedRoute>
              }
            >
              <Route index element={<AshaDashboardPage />} />
              <Route path="alerts" element={<AlertsQueuePage />} />
              <Route path="mothers" element={<AssignedMothersPage />} />
              <Route path="mothers/:motherId/timeline" element={<RiskTimelinePage />} />
              <Route path="mothers/:motherId/assistant" element={<AiAssistantPage />} />
            </Route>

            {/* Catch-all 404 */}
            <Route path="*" element={<NotFoundPage />} />
          </Route>
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
