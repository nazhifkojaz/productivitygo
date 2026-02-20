import React, { useEffect, lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import axios from 'axios';
import { OpenAPI } from './api';
import { Toaster } from 'sonner';
import TimezoneSync from './components/TimezoneSync';
import LandingOrLobby from './components/LandingOrLobby';
import LoadingFallback from './components/LoadingFallback';

// Lazy load authenticated pages for code splitting
const Login = lazy(() => import('./pages/Login'));
const Arena = lazy(() => import('./pages/Arena'));
const Lobby = lazy(() => import('./pages/Lobby'));
const PlanTasks = lazy(() => import('./pages/PlanTasks'));
const Profile = lazy(() => import('./pages/Profile'));
const PublicProfile = lazy(() => import('./pages/PublicProfile'));
const BattleResult = lazy(() => import('./pages/BattleResult'));
const AdventureResult = lazy(() => import('./pages/AdventureResult'));

// Protected Route Wrapper
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { session, loading } = useAuth();

  useEffect(() => {
    if (session?.access_token) {
      OpenAPI.TOKEN = session.access_token;
      // Also update axios for manual calls
      axios.defaults.headers.common['Authorization'] = `Bearer ${session.access_token}`;
    }
  }, [session]);

  if (loading) return <div className="h-screen flex items-center justify-center font-black text-2xl">LOADING...</div>;
  if (!session) return <Navigate to="/login" />;
  return (
    <>
      <TimezoneSync />
      {children}
    </>
  );
};

function App() {
  return (
    <Router basename={import.meta.env.BASE_URL}>
      <AuthProvider>
        <Suspense fallback={<LoadingFallback message="LOADING..." />}>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
            {/* Lobby - session-aware rendering handled in Lobby.tsx */}
            <Route path="/lobby" element={<ProtectedRoute><Lobby /></ProtectedRoute>} />
            {/* Direct arena access - user can navigate freely between lobby and arena */}
            <Route path="/arena" element={<ProtectedRoute><Arena /></ProtectedRoute>} />
            {/* Legacy route - redirect to lobby for backwards compatibility */}
            <Route path="/dashboard" element={<Navigate to="/lobby" replace />} />
            <Route path="/plan" element={<ProtectedRoute><PlanTasks /></ProtectedRoute>} />
            <Route path="/battle-result/:battleId" element={<ProtectedRoute><BattleResult /></ProtectedRoute>} />
            <Route path="/adventure-result/:adventureId" element={<ProtectedRoute><AdventureResult /></ProtectedRoute>} />
            <Route path="/user/:userId" element={<ProtectedRoute><PublicProfile /></ProtectedRoute>} />
            {/* Root redirect - auth-aware: landing for visitors, lobby for authenticated */}
            <Route path="/" element={<LandingOrLobby />} />
          </Routes>
        </Suspense>
        <Toaster position="top-right" richColors closeButton />
      </AuthProvider>
    </Router>
  );
}

export default App;
