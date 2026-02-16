import { describe, it, expect, vi } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import SecuritySettings from '../SecuritySettings';

describe('SecuritySettings', () => {
    const defaultProps = {
        currentTimezone: 'America/New_York',
        detectedTimezone: 'America/New_York',
        onTimezoneSync: vi.fn().mockResolvedValue(undefined),
        onSignOut: vi.fn(),
    };

    describe('rendering', () => {
        it('renders settings header', () => {
            render(<SecuritySettings {...defaultProps} />);

            expect(screen.getByText('Settings')).toBeInTheDocument();
        });

        it('displays current timezone', () => {
            render(<SecuritySettings {...defaultProps} currentTimezone="Asia/Tokyo" />);

            expect(screen.getByText('Asia/Tokyo')).toBeInTheDocument();
        });

        it('defaults to UTC when timezone is undefined', () => {
            render(<SecuritySettings {...defaultProps} currentTimezone={undefined} />);

            expect(screen.getByText('UTC')).toBeInTheDocument();
        });

        it('displays detected timezone', () => {
            render(<SecuritySettings {...defaultProps} detectedTimezone="Europe/London" />);

            expect(screen.getByText('Detected: Europe/London')).toBeInTheDocument();
        });

        it('renders sign out button', () => {
            render(<SecuritySettings {...defaultProps} />);

            expect(screen.getByText('Sign Out')).toBeInTheDocument();
        });
    });

    describe('timezone sync', () => {
        it('calls onTimezoneSync with detected timezone when sync clicked', async () => {
            const user = userEvent.setup();
            const mockSync = vi.fn().mockResolvedValue(undefined);
            render(<SecuritySettings {...defaultProps} onTimezoneSync={mockSync} detectedTimezone="Asia/Seoul" />);

            const syncButton = screen.getByRole('button', { name: 'Sync' });
            await user.click(syncButton);

            await waitFor(() => {
                expect(mockSync).toHaveBeenCalledWith('Asia/Seoul');
            });
        });

        it('shows loading state while syncing', async () => {
            const user = userEvent.setup();
            let resolvePromise: (value: void) => void;
            const mockSync = vi.fn(() => new Promise((resolve) => {
                resolvePromise = resolve;
            }));
            render(<SecuritySettings {...defaultProps} onTimezoneSync={mockSync} />);

            const syncButton = screen.getByRole('button', { name: 'Sync' });
            await user.click(syncButton);

            // Button should be disabled during loading
            expect(syncButton).toBeDisabled();

            resolvePromise!();
        });
    });

    describe('sign out', () => {
        it('calls onSignOut when sign out button clicked', async () => {
            const user = userEvent.setup();
            const mockSignOut = vi.fn();
            render(<SecuritySettings {...defaultProps} onSignOut={mockSignOut} />);

            const signOutButton = screen.getByRole('button', { name: /sign out/i });
            await user.click(signOutButton);

            expect(mockSignOut).toHaveBeenCalledTimes(1);
        });
    });

    describe('loading states', () => {
        it('disables inputs while loading', async () => {
            const user = userEvent.setup();
            let resolveSync: () => void;
            const mockSync = vi.fn(() => new Promise((resolve) => {
                resolveSync = resolve as () => void;
            }));

            render(<SecuritySettings {...defaultProps} onTimezoneSync={mockSync} />);

            // Start loading
            const syncButton = screen.getByRole('button', { name: 'Sync' });
            await user.click(syncButton);

            // Sync button should be disabled during loading
            expect(syncButton).toBeDisabled();

            resolveSync!();
        });
    });
});
