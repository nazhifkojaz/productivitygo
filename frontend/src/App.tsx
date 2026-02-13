import React, { useEffect, useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import Login from './pages/Login';
import Arena from './pages/Arena';
import Lobby from './pages/Lobby';
import axios from 'axios';
import PlanTasks from './pages/PlanTasks';
import Profile from './pages/Profile';
import PublicProfile from './pages/PublicProfile';
import BattleResult from './pages/BattleResult';
import AdventureResult from './pages/AdventureResult';
import { OpenAPI } from './api';
import { Toaster } from 'sonner';
import { useProfile } from './hooks/useProfile';
import TimezoneSync from './components/TimezoneSync';
import LandingOrLobby from './components/LandingOrLobby';

// Landing Page Design
import ExperimentPage from './pages/landing/experiment';
import Design1 from './pages/landing/design1';
import Design2 from './pages/landing/design2';
import Design3 from './pages/landing/design3';
import Design4 from './pages/landing/design4';
import Design5 from './pages/landing/design5';

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

// Game Session Router - handles both battles and adventures
type GameSessionState = 'loading' | 'idle' | 'in_battle' | 'battle_completed' | 'in_adventure' | 'adventure_completed';

const GameRouter = () => {
  const { session } = useAuth();
  const { data: profile, isLoading: profileLoading } = useProfile();
  const [gameState, setGameState] = useState<GameSessionState>('loading');
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkGameSession = async () => {
      if (!profile || profileLoading) return;

      try {
        const currentBattleId = profile.current_battle;
        const currentAdventureId = profile.current_adventure;

        // No active session
        if (!currentBattleId && !currentAdventureId) {
          setGameState('idle');
          setLoading(false);
          return;
        }

        // Check adventure first (if exists) - adventures take priority
        if (currentAdventureId) {
          const adventureResponse = await axios.get(`/api/adventures/${currentAdventureId}`, {
            headers: { Authorization: `Bearer ${session?.access_token}` }
          });

          setSessionId(currentAdventureId);

          if (['completed', 'escaped', 'abandoned'].includes(adventureResponse.data.status)) {
            setGameState('adventure_completed');
          } else {
            setGameState('in_adventure');
          }
          setLoading(false);
          return;
        }

        // Check battle
        if (currentBattleId) {
          const battleResponse = await axios.get(`/api/battles/${currentBattleId}`, {
            headers: { Authorization: `Bearer ${session?.access_token}` }
          });

          setSessionId(currentBattleId);

          if (battleResponse.data.status === 'completed') {
            setGameState('battle_completed');
          } else {
            setGameState('in_battle');
          }
        }
      } catch (error) {
        console.error('Failed to check game state:', error);
        setGameState('idle');
      } finally {
        setLoading(false);
      }
    };

    checkGameSession();
  }, [session, profile, profileLoading]);

  if (loading) return <div className="h-screen flex items-center justify-center font-black text-2xl">SYNCING...</div>;

  // Completed states -> redirect to result pages
  if (gameState === 'battle_completed' && sessionId) {
    return <Navigate to={`/battle-result/${sessionId}`} replace />;
  }

  if (gameState === 'adventure_completed' && sessionId) {
    return <Navigate to={`/adventure-result/${sessionId}`} replace />;
  }

  // Active states -> show arena
  if (gameState === 'in_battle' || gameState === 'in_adventure') {
    return <Arena />;
  }

  // Lobby state
  return <Lobby />;
};

function App() {
  return (
    <Router basename={import.meta.env.BASE_URL}>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
          {/* Smart game router - handles routing based on game state */}
          <Route path="/lobby" element={<ProtectedRoute><GameRouter /></ProtectedRoute>} />
          {/* Direct arena access (when user knows they have an active game) */}
          <Route path="/arena" element={<ProtectedRoute><Arena /></ProtectedRoute>} />
          {/* Legacy route - redirect to lobby for backwards compatibility */}
          <Route path="/dashboard" element={<Navigate to="/lobby" replace />} />
          <Route path="/plan" element={<ProtectedRoute><PlanTasks /></ProtectedRoute>} />
          <Route path="/battle-result/:battleId" element={<ProtectedRoute><BattleResult /></ProtectedRoute>} />
          <Route path="/adventure-result/:adventureId" element={<ProtectedRoute><AdventureResult /></ProtectedRoute>} />
          <Route path="/user/:userId" element={<ProtectedRoute><PublicProfile /></ProtectedRoute>} />
          {/* Landing Page Design */}
          <Route path="/exp" element={<ExperimentPage />} />
          <Route path="/1" element={<Design1 />} />
          <Route path="/2" element={<Design2 />} />
          <Route path="/3" element={<Design3 />} />
          <Route path="/4" element={<Design4 />} />
          <Route path="/5" element={<Design5 />} />
          {/* Root redirect - auth-aware: landing for visitors, lobby for authenticated */}
          <Route path="/" element={<LandingOrLobby />} />
        </Routes>
        <Toaster position="top-right" richColors closeButton />
      </AuthProvider>
    </Router>
  );
}

export default App;
