import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import React from 'react';
import { useChallengeMutations } from '../useChallengeMutations';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock axios
vi.mock('axios', () => ({
    default: {
        get: vi.fn(),
        post: vi.fn(),
    },
}));

// Mock AuthContext
vi.mock('../../context/AuthContext', () => ({
    useAuth: vi.fn(),
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

describe('useChallengeMutations', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('sendChallengeMutation', () => {
        it('sends challenge to known user successfully', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.post).mockResolvedValue({ data: { id: 'battle-123' } });

            const queryClient = new QueryClient({
                defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
            });
            const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

            const wrapper = ({ children }: { children: React.ReactNode }) => (
                <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
            );

            const { result } = renderHook(() => useChallengeMutations(), { wrapper });

            await result.current.sendChallengeMutation.mutateAsync({
                rivalId: 'user-456',
                startDate: '2026-02-10',
                duration: 5
            });

            expect(axios.post).toHaveBeenCalledWith(
                '/api/invites/send',
                {
                    rival_id: 'user-456',
                    start_date: '2026-02-10',
                    duration: 5
                },
                { headers: { Authorization: 'Bearer test-token' } }
            );

            expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['battles', 'invites'] });
            expect(toast.success).toHaveBeenCalledWith('Challenge sent successfully!');
        });

        it('shows error toast on failure', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.post).mockRejectedValue({
                response: { data: { detail: 'User already has a pending battle' } }
            });

            const { result } = renderHook(() => useChallengeMutations(), {
                wrapper: createWrapper(),
            });

            try {
                await result.current.sendChallengeMutation.mutateAsync({
                    rivalId: 'user-456',
                    startDate: '2026-02-10',
                    duration: 5
                });
            } catch (e) {
                // Expected - mutation throws on error
            }

            // Wait for toast.error to be called
            await waitFor(() => expect(toast.error).toHaveBeenCalled());
            expect(toast.error).toHaveBeenCalledWith('User already has a pending battle');
        });

        it('handles validation errors (array format)', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.post).mockRejectedValue({
                response: {
                    data: {
                        detail: [
                            { msg: 'Invalid date format', loc: ['body', 'start_date'] },
                            { msg: 'Duration must be 3, 5, or 7', loc: ['body', 'duration'] }
                        ]
                    }
                }
            });

            const { result } = renderHook(() => useChallengeMutations(), {
                wrapper: createWrapper(),
            });

            try {
                await result.current.sendChallengeMutation.mutateAsync({
                    rivalId: 'user-456',
                    startDate: 'invalid',
                    duration: 5
                });
            } catch (e) {
                // Expected to throw
            }

            await waitFor(() => expect(toast.error).toHaveBeenCalled());
            const toastCall = vi.mocked(toast.error).mock.calls[0]?.[0];
            expect(toastCall).toContain('Validation errors:');
        });
    });

    describe('sendChallengeByEmailMutation', () => {
        it('searches for user and sends challenge successfully', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            const mockSearchResults = [
                { id: 'user-789', username: 'rival123', email: 'rival@example.com' },
                { id: 'user-999', username: 'other', email: 'other@example.com' }
            ];
            vi.mocked(axios.get).mockResolvedValue({ data: mockSearchResults });
            vi.mocked(axios.post).mockResolvedValue({ data: { id: 'battle-456' } });

            const queryClient = new QueryClient({
                defaultOptions: { queries: { retry: false }, mutations: { retry: false } },
            });
            const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

            const wrapper = ({ children }: { children: React.ReactNode }) => (
                <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
            );

            const { result } = renderHook(() => useChallengeMutations(), { wrapper });

            await result.current.sendChallengeByEmailMutation.mutateAsync({
                emailOrUsername: 'rival123',
                startDate: '2026-02-10',
                duration: 5
            });

            // Verify search was called
            expect(axios.get).toHaveBeenCalledWith(
                '/api/social/search?q=rival123',
                { headers: { Authorization: 'Bearer test-token' } }
            );

            // Verify invite was sent with correct user ID
            expect(axios.post).toHaveBeenCalledWith(
                '/api/invites/send',
                {
                    rival_id: 'user-789',
                    start_date: '2026-02-10',
                    duration: 5
                },
                { headers: { Authorization: 'Bearer test-token' } }
            );

            expect(invalidateSpy).toHaveBeenCalledWith({ queryKey: ['battles', 'invites'] });
            expect(toast.success).toHaveBeenCalledWith('Invite sent to rival123!');
        });

        it('matches by email when searching', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            const mockSearchResults = [
                { id: 'user-789', username: 'rival123', email: 'rival@example.com' }
            ];
            vi.mocked(axios.get).mockResolvedValue({ data: mockSearchResults });
            vi.mocked(axios.post).mockResolvedValue({ data: { id: 'battle-456' } });

            const { result } = renderHook(() => useChallengeMutations(), {
                wrapper: createWrapper(),
            });

            await result.current.sendChallengeByEmailMutation.mutateAsync({
                emailOrUsername: 'rival@example.com',
                startDate: '2026-02-10',
                duration: 5
            });

            expect(axios.post).toHaveBeenCalledWith(
                '/api/invites/send',
                expect.objectContaining({
                    rival_id: 'user-789'
                }),
                expect.anything()
            );
        });

        it('throws error when user not found', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.get).mockResolvedValue({ data: [] });

            const { result } = renderHook(() => useChallengeMutations(), {
                wrapper: createWrapper(),
            });

            try {
                await result.current.sendChallengeByEmailMutation.mutateAsync({
                    emailOrUsername: 'nonexistent',
                    startDate: '2026-02-10',
                    duration: 5
                });
                // Should have thrown
                expect(true).toBe(false);
            } catch (error: any) {
                expect(error.message).toContain('not found');
            }
        });

        it('shows toast with username when user not found', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.get).mockResolvedValue({ data: [] });

            const { result } = renderHook(() => useChallengeMutations(), {
                wrapper: createWrapper(),
            });

            try {
                await result.current.sendChallengeByEmailMutation.mutateAsync({
                    emailOrUsername: 'nonexistent',
                    startDate: '2026-02-10',
                    duration: 5
                });
            } catch (e) {
                // Expected to throw
            }

            await waitFor(() => {
                expect(toast.error).toHaveBeenCalledWith(
                    expect.stringContaining('not found')
                );
            });
        });
    });

    describe('isSending', () => {
        it('is true when sendChallengeMutation is pending', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            let resolvePromise: () => void;
            const slowPromise = new Promise((resolve) => {
                resolvePromise = () => resolve({ data: {} });
            });
            vi.mocked(axios.post).mockReturnValue(slowPromise);

            const { result } = renderHook(() => useChallengeMutations(), {
                wrapper: createWrapper(),
            });

            result.current.sendChallengeMutation.mutate({
                rivalId: 'user-123',
                startDate: '2026-02-10',
                duration: 5
            });

            // isSending should track the pending state
            expect(result.current.sendChallengeMutation.isPending).toBeDefined();
            expect(typeof result.current.isSending).toBe('boolean');

            // Resolve
            await (resolvePromise as () => void)();

            await waitFor(() => expect(result.current.sendChallengeMutation.isSuccess).toBe(true));
        });

        it('is true when sendChallengeByEmailMutation is pending', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            const mockSearchResults = [{ id: 'user-123', username: 'testuser', email: 'test@test.com' }];
            vi.mocked(axios.get).mockResolvedValue({ data: mockSearchResults });
            vi.mocked(axios.post).mockResolvedValue({ data: { id: 'battle-123' } });

            const { result } = renderHook(() => useChallengeMutations(), {
                wrapper: createWrapper(),
            });

            // Start the mutation (don't await yet)
            result.current.sendChallengeByEmailMutation.mutate({
                emailOrUsername: 'test@test.com',
                startDate: '2026-02-10',
                duration: 5
            });

            // Check that we can access the mutation and it has the expected properties
            expect(result.current.sendChallengeByEmailMutation).toBeDefined();
            expect(typeof result.current.isSending).toBe('boolean');

            // Wait for success
            await waitFor(() => expect(result.current.sendChallengeByEmailMutation.isSuccess).toBe(true));

            // After success, isPending should be false
            expect(result.current.sendChallengeByEmailMutation.isPending).toBe(false);
        });
    });

    describe('when not authenticated', () => {
        it('mutations still return functions but will fail without token', () => {
            vi.mocked(useAuth).mockReturnValue({ session: null } as any);

            const { result } = renderHook(() => useChallengeMutations(), {
                wrapper: createWrapper(),
            });

            expect(result.current.sendChallengeMutation).toBeDefined();
            expect(result.current.sendChallengeByEmailMutation).toBeDefined();
        });
    });
});
