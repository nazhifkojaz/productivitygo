import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import React from 'react';
import { useProfileMutations } from '../useProfileMutations';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock axios
vi.mock('axios', () => ({
    default: {
        put: vi.fn(),
    },
}));

// Mock AuthContext
vi.mock('../../context/AuthContext', () => ({
    useAuth: vi.fn(),
}));

// Mock supabase
vi.mock('../../lib/supabase', () => ({
    supabase: {
        auth: {
            updateUser: vi.fn(),
        },
    },
}));

// Mock sonner toast
vi.mock('sonner', () => ({
    toast: {
        success: vi.fn(),
        error: vi.fn(),
    },
}));

import axios from 'axios';
import { useAuth } from '../../context/AuthContext';
import { supabase } from '../../lib/supabase';
import { toast } from 'sonner';

const createWrapper = () => {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: {
                retry: false,
            },
            mutations: {
                retry: false,
            },
        },
        logger: {
            log: console.log,
            warn: console.warn,
            error: () => {},
        },
    });
    return ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
};

describe('useProfileMutations', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('updateProfileMutation', () => {
        it('updates profile successfully', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.put).mockResolvedValue({ data: { id: 'user-123' } });

            const queryClient = new QueryClient({
                defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
            });
            const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

            const wrapper = ({ children }: { children: React.ReactNode }) => (
                <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
            );

            const { result } = renderHook(() => useProfileMutations(), { wrapper });

            await result.current.updateProfileMutation.mutateAsync({
                username: 'newuser',
                avatar_emoji: '😎'
            });

            expect(axios.put).toHaveBeenCalledWith(
                '/api/users/profile',
                { username: 'newuser', avatar_emoji: '😎' },
                { headers: { Authorization: 'Bearer test-token' } }
            );

            expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['profile'] });
            expect(toast.success).toHaveBeenCalledWith('Profile updated successfully!');
        });

        it('shows error toast on failure', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.put).mockRejectedValue(new Error('Network error'));

            const { result } = renderHook(() => useProfileMutations(), {
                wrapper: createWrapper(),
            });

            try {
                await result.current.updateProfileMutation.mutateAsync({ username: 'newuser' });
            } catch (e) {
                // Expected
            }

            await waitFor(() => expect(toast.error).toHaveBeenCalled());
            expect(toast.error).toHaveBeenCalledWith('Failed to update profile');
        });
    });

    describe('updateAvatarMutation', () => {
        it('updates avatar successfully', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.put).mockResolvedValue({ data: {} });

            const queryClient = new QueryClient({
                defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
            });
            const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

            const wrapper = ({ children }: { children: React.ReactNode }) => (
                <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
            );

            const { result } = renderHook(() => useProfileMutations(), { wrapper });

            await result.current.updateAvatarMutation.mutateAsync('😎');

            expect(axios.put).toHaveBeenCalledWith(
                '/api/users/profile',
                { avatar_emoji: '😎' },
                { headers: { Authorization: 'Bearer test-token' } }
            );

            expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['profile'] });
            expect(toast.success).toHaveBeenCalledWith('Avatar updated!');
        });

        it('shows error toast on failure', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.put).mockRejectedValue(new Error('Network error'));

            const { result } = renderHook(() => useProfileMutations(), {
                wrapper: createWrapper(),
            });

            try {
                await result.current.updateAvatarMutation.mutateAsync('😎');
            } catch (e) {
                // Expected
            }

            await waitFor(() => expect(toast.error).toHaveBeenCalled());
            expect(toast.error).toHaveBeenCalledWith('Failed to update avatar');
        });
    });

    describe('updateTimezoneMutation', () => {
        it('updates timezone successfully', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.put).mockResolvedValue({ data: {} });

            const queryClient = new QueryClient({
                defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
            });
            const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

            const wrapper = ({ children }: { children: React.ReactNode }) => (
                <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
            );

            const { result } = renderHook(() => useProfileMutations(), { wrapper });

            await result.current.updateTimezoneMutation.mutateAsync('America/New_York');

            expect(axios.put).toHaveBeenCalledWith(
                '/api/users/profile',
                { timezone: 'America/New_York' },
                { headers: { Authorization: 'Bearer test-token' } }
            );

            expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['profile'] });
            expect(toast.success).toHaveBeenCalledWith('Timezone updated to America/New_York');
        });

        it('shows error toast on failure', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.put).mockRejectedValue(new Error('Network error'));

            const { result } = renderHook(() => useProfileMutations(), {
                wrapper: createWrapper(),
            });

            try {
                await result.current.updateTimezoneMutation.mutateAsync('America/New_York');
            } catch (e) {
                // Expected
            }

            await waitFor(() => expect(toast.error).toHaveBeenCalled());
            expect(toast.error).toHaveBeenCalledWith('Failed to update timezone');
        });
    });

    describe('updatePasswordMutation', () => {
        it('updates password successfully', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(supabase.auth.updateUser).mockResolvedValue({ error: null });

            const { result } = renderHook(() => useProfileMutations(), {
                wrapper: createWrapper(),
            });

            await result.current.updatePasswordMutation.mutateAsync('newPassword123');

            expect(supabase.auth.updateUser).toHaveBeenCalledWith({ password: 'newPassword123' });
            expect(toast.success).toHaveBeenCalledWith('Password updated successfully!');
        });

        it('throws error on Supabase failure', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            const mockError = new Error('Invalid password');
            vi.mocked(supabase.auth.updateUser).mockResolvedValue({ error: mockError });

            const { result } = renderHook(() => useProfileMutations(), {
                wrapper: createWrapper(),
            });

            try {
                await result.current.updatePasswordMutation.mutateAsync('weak');
                // Should have thrown
                expect(true).toBe(false);
            } catch (error: any) {
                expect(error.message).toBe('Invalid password');
            }

            await waitFor(() => expect(toast.error).toHaveBeenCalled());
            expect(toast.error).toHaveBeenCalledWith('Invalid password');
        });
    });

    describe('when not authenticated', () => {
        it('mutations still return functions but will fail without token', () => {
            vi.mocked(useAuth).mockReturnValue({ session: null } as any);

            const { result } = renderHook(() => useProfileMutations(), {
                wrapper: createWrapper(),
            });

            expect(result.current.updateProfileMutation).toBeDefined();
            expect(result.current.updateAvatarMutation).toBeDefined();
            expect(result.current.updateTimezoneMutation).toBeDefined();
            expect(result.current.updatePasswordMutation).toBeDefined();
        });
    });
});
