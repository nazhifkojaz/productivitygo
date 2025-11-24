import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import UserDashboard from './pages/UserDashboard';
import axios from 'axios';
import PlanTasks from './pages/PlanTasks';
import Profile from './pages/Profile';
import PublicProfile from './pages/PublicProfile';
import { OpenAPI } from './api';
import { Toaster } from 'sonner';

// Protected Route Wrapper
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const { session, loading } = useAuth();

  useEffect(() => {
    // Set API Base URL to relative path (proxied by Vite)
    OpenAPI.BASE = "/api";
    if (session?.access_token) {
      OpenAPI.TOKEN = session.access_token;
    }
  }, [session]);

  if (loading) return <div className="h-screen flex items-center justify-center font-black text-2xl">LOADING...</div>;
  if (!session) return <Navigate to="/login" />;
  return <>{children}</>;
};

// Battle Router Wrapper
const BattleRouter = () => {
  const { session } = useAuth();
  const [hasActiveBattle, setHasActiveBattle] = useState<boolean | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkBattle = async () => {
      if (session?.access_token) {
        OpenAPI.TOKEN = session.access_token;
        try {
          await axios.get('/api/battles/current', {
            headers: { Authorization: `Bearer ${session.access_token}` }
          });
          setHasActiveBattle(true);
        } catch (error) {
          setHasActiveBattle(false);
        } finally {
          setLoading(false);
        }
      }
    };
    checkBattle();
  }, [session]);

  if (loading) return <div className="h-screen flex items-center justify-center font-black text-2xl">SYNCING...</div>;

  // If active battle -> Go to Arena (Dashboard)
  // If no active battle -> Go to Lobby (UserDashboard)
  return hasActiveBattle ? <Dashboard /> : <UserDashboard />;
};

import BattleResult from './pages/BattleResult';
// import EditProfile from './pages/EditProfile';

function App() {
  return (
    <Router>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
          {/* <Route path="/profile/edit" element={<ProtectedRoute><EditProfile /></ProtectedRoute>} /> */}
          <Route path="/dashboard" element={<ProtectedRoute><BattleRouter /></ProtectedRoute>} />
          <Route path="/plan" element={<ProtectedRoute><PlanTasks /></ProtectedRoute>} />
          <Route path="/battle-result/:battleId" element={<ProtectedRoute><BattleResult /></ProtectedRoute>} />
          <Route path="/user/:userId" element={<ProtectedRoute><PublicProfile /></ProtectedRoute>} />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
        </Routes>
        <Toaster position="top-right" richColors closeButton />
      </AuthProvider>
    </Router>
  );
}

export default App;
