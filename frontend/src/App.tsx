import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import { AppLayout } from './layouts/AppLayout';
import { Login } from './pages/Login';
import { Register } from './pages/Register';
import { Dashboard } from './pages/Dashboard';
import { Documents } from './pages/Documents';
import { UploadDocument } from './pages/UploadDocument';
import { RagChat } from './pages/RagChat';
import { HallucinationAnalysis } from './pages/HallucinationAnalysis';
import { EvaluationHistory } from './pages/EvaluationHistory';
import { Analytics } from './pages/Analytics';
import { Settings } from './pages/Settings';

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          {/* Public Authentication routes */}
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />

          {/* Authenticated Workspace routes */}
          <Route element={<AppLayout />}>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/documents" element={<Documents />} />
            <Route path="/documents/upload" element={<UploadDocument />} />
            <Route path="/chat" element={<RagChat />} />
            <Route path="/analysis/:id" element={<HallucinationAnalysis />} />
            <Route path="/history" element={<EvaluationHistory />} />
            <Route path="/analytics" element={<Analytics />} />
            <Route path="/settings" element={<Settings />} />
          </Route>

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/dashboard" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
