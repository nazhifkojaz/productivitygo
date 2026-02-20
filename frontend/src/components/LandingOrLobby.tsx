import { useAuth } from '../context/AuthContext';
import { Navigate } from 'react-router-dom';
import LandingPage from '../pages/landing/LandingPage';

/**
 * Auth-aware root route component
 * - Shows landing page to unauthenticated visitors
 * - Redirects authenticated users to /lobby
 * - Handles loading state during auth check
 */
export default function LandingOrLobby() {
  const { session, loading } = useAuth();

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center font-black text-2xl">
        LOADING...
      </div>
    );
  }

  // Authenticated users go straight to lobby
  if (session) {
    return <Navigate to="/lobby" replace />;
  }

  // Unauthenticated visitors see landing page
  return <LandingPage />;
}
