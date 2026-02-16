import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import LandingOrLobby from '../LandingOrLobby';

// Mock the auth context
vi.mock('../../context/AuthContext', () => ({
  AuthProvider: ({ children }: { children: React.ReactNode }) => <>{children}</>,
  useAuth: vi.fn()
}));

// Mock LandingPage to avoid rendering the full landing page
vi.mock('../../pages/landing/LandingPage', () => ({
  default: () => <div data-testid="landing-page">Landing Page</div>
}));

import { useAuth } from '../../context/AuthContext';

const mockUseAuth = useAuth as unknown as ReturnType<typeof vi.fn>;

describe('LandingOrLobby', () => {
  it('shows loading UI when auth is loading', () => {
    vi.mocked(mockUseAuth)!.mockReturnValue({
      session: null,
      user: null,
      loading: true,
      signOut: vi.fn()
    });

    render(
      <BrowserRouter>
        <LandingOrLobby />
      </BrowserRouter>
    );

    expect(screen.getByText('LOADING...')).toBeInTheDocument();
  });

  it('redirects to /lobby when user is authenticated', () => {
    const mockSession = {
      access_token: 'mock-token',
      user: { id: '123', email: 'test@example.com' }
    };

    vi.mocked(mockUseAuth)!.mockReturnValue({
      session: mockSession,
      user: mockSession.user,
      loading: false,
      signOut: vi.fn()
    });

    render(
      <BrowserRouter>
        <LandingOrLobby />
      </BrowserRouter>
    );

    // Navigate component renders a redirect - should not show loading UI or landing page
    expect(screen.queryByText('LOADING...')).not.toBeInTheDocument();
    expect(screen.queryByTestId('landing-page')).not.toBeInTheDocument();
  });

  it('renders landing page when user is not authenticated', () => {
    vi.mocked(mockUseAuth)!.mockReturnValue({
      session: null,
      user: null,
      loading: false,
      signOut: vi.fn()
    });

    render(
      <BrowserRouter>
        <LandingOrLobby />
      </BrowserRouter>
    );

    expect(screen.getByTestId('landing-page')).toBeInTheDocument();
    expect(screen.queryByText('LOADING...')).not.toBeInTheDocument();
  });
});
