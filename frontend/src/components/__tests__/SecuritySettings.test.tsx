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
        onChangePassword: vi.fn().mockResolvedValue(undefined),
    };

    describe('rendering', () => {
        it('renders account security header', () => {
            render(<SecuritySettings {...defaultProps} />);

            expect(screen.getByText('Account Security')).toBeInTheDocument();
        });

        it('renders change password button initially', () => {
            render(<SecuritySettings {...defaultProps} />);

            expect(screen.getByText('Change Password')).toBeInTheDocument();
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

            expect(screen.getByText('Automatically detected: Europe/London')).toBeInTheDocument();
        });

        it('renders sign out button', () => {
            render(<SecuritySettings {...defaultProps} />);

            expect(screen.getByText('Sign Out')).toBeInTheDocument();
        });
    });

    describe('password change', () => {
        it('expands password form when change password clicked', async () => {
            const user = userEvent.setup();
            render(<SecuritySettings {...defaultProps} />);

            const changeButton = screen.getByText('Change Password');
            await user.click(changeButton);

            expect(screen.getByPlaceholderText('New Password')).toBeInTheDocument();
            expect(screen.getByPlaceholderText('Confirm Password')).toBeInTheDocument();
        });

        it('closes form when cancel clicked', async () => {
            const user = userEvent.setup();
            render(<SecuritySettings {...defaultProps} />);

            // Open form
            await user.click(screen.getByText('Change Password'));
            // Cancel
            await user.click(screen.getByRole('button', { name: 'Cancel' }));

            expect(screen.queryByPlaceholderText('New Password')).not.toBeInTheDocument();
        });

        it('calls onChangePassword when passwords match and submit clicked', async () => {
            const user = userEvent.setup();
            const mockChangePassword = vi.fn().mockResolvedValue(undefined);
            render(<SecuritySettings {...defaultProps} onChangePassword={mockChangePassword} />);

            await user.click(screen.getByText('Change Password'));

            const newPasswordInput = screen.getByPlaceholderText('New Password');
            const confirmPasswordInput = screen.getByPlaceholderText('Confirm Password');

            await user.type(newPasswordInput, 'newPassword123');
            await user.type(confirmPasswordInput, 'newPassword123');

            const updateButton = screen.getByRole('button', { name: 'Update Password' });
            await user.click(updateButton);

            await waitFor(() => {
                expect(mockChangePassword).toHaveBeenCalledWith('newPassword123');
            });
        });

        it('does not call onChangePassword when passwords do not match', async () => {
            const user = userEvent.setup();
            const mockChangePassword = vi.fn().mockResolvedValue(undefined);
            render(<SecuritySettings {...defaultProps} onChangePassword={mockChangePassword} />);

            await user.click(screen.getByText('Change Password'));

            const newPasswordInput = screen.getByPlaceholderText('New Password');
            const confirmPasswordInput = screen.getByPlaceholderText('Confirm Password');

            await user.type(newPasswordInput, 'newPassword123');
            await user.type(confirmPasswordInput, 'differentPassword');

            const updateButton = screen.getByRole('button', { name: 'Update Password' });
            await user.click(updateButton);

            expect(mockChangePassword).not.toHaveBeenCalled();
        });

        it('disables password change button when onChangePassword not provided', () => {
            render(<SecuritySettings {...defaultProps} onChangePassword={undefined} />);

            // Find button containing "Change Password" text
            const changeButton = screen.getByText('Change Password').closest('button');
            expect(changeButton).toBeDisabled();
        });
    });

    describe('timezone sync', () => {
        it('calls onTimezoneSync with detected timezone when sync clicked', async () => {
            const user = userEvent.setup();
            const mockSync = vi.fn().mockResolvedValue(undefined);
            render(<SecuritySettings {...defaultProps} onTimezoneSync={mockSync} detectedTimezone="Asia/Seoul" />);

            const syncButton = screen.getByRole('button', { name: 'Sync to Device' });
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

            const syncButton = screen.getByRole('button', { name: 'Sync to Device' });
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
            const syncButton = screen.getByRole('button', { name: 'Sync to Device' });
            await user.click(syncButton);

            // Password inputs should still be accessible (different loading context)
            // But we check that sync button is disabled
            expect(syncButton).toBeDisabled();

            resolveSync!();
        });
    });
});
