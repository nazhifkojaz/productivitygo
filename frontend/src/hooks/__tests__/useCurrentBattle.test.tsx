import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import React from 'react';
import { useCurrentBattle } from '../useCurrentBattle';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock axios
vi.mock('axios', () => ({
    default: {
        get: vi.fn(),
    },
}));

// Mock AuthContext
vi.mock('../../context/AuthContext', () => ({
    useAuth: vi.fn(),
}));

import axios from 'axios';
import { useAuth } from '../../context/AuthContext';

const createWrapper = () => {
    const queryClient = new QueryClient({
        defaultOptions: {
            queries: {
                retry: false,
            },
        },
    });
    return ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
};

describe('useCurrentBattle', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('when user has active battle', () => {
        it('fetches current battle successfully with /api/ prefix', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            const mockBattle = {
                id: 'battle-123',
                user1_id: 'user-1',
                user2_id: 'user-2',
                start_date: '2026-02-01',
                end_date: '2026-02-05',
                status: 'active',
                current_round: 2,
                duration: 5,
                created_at: '2026-02-01T00:00:00',
                user1: {
                    username: 'Player1',
                    level: 5,
                    timezone: 'Asia/Jakarta',
                    battle_win_count: 3,
                    battle_count: 5,
                    total_xp_earned: 500,
                    completed_tasks: 10,
                },
                user2: {
                    username: 'Player2',
                    level: 4,
                    timezone: 'Asia/Jakarta',
                    battle_win_count: 2,
                    battle_count: 4,
                    total_xp_earned: 400,
                    completed_tasks: 8,
                },
            };

            vi.mocked(axios.get).mockResolvedValue({ data: mockBattle });

            const { result } = renderHook(() => useCurrentBattle(), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isSuccess).toBe(true));

            expect(result.current.data).toEqual(mockBattle);
            expect(axios.get).toHaveBeenCalledWith('/api/battles/current', {
                headers: { Authorization: 'Bearer test-token' },
            });
        });

        it('includes user profiles in response', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            const mockBattle = {
                id: 'battle-123',
                status: 'active',
                user1: {
                    username: 'Rival1',
                    level: 10,
                    timezone: 'America/New_York',
                    battle_win_count: 5,
                    battle_count: 8,
                    total_xp_earned: 1000,
                    completed_tasks: 20,
                },
                user2: {
                    username: 'Rival2',
                    level: 8,
                    timezone: 'Europe/London',
                    battle_win_count: 3,
                    battle_count: 7,
                    total_xp_earned: 800,
                    completed_tasks: 15,
                },
            };

            vi.mocked(axios.get).mockResolvedValue({ data: mockBattle });

            const { result } = renderHook(() => useCurrentBattle(), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isSuccess).toBe(true));

            expect(result.current.data?.user1).toBeDefined();
            expect(result.current.data?.user2).toBeDefined();
            expect(result.current.data?.user1.username).toBe('Rival1');
        });
    });

    describe('when user has no active battle', () => {
        it('handles 404 gracefully with throwOnError: false', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            const error = {
                response: { status: 404 },
                message: 'No active battle found',
            };
            vi.mocked(axios.get).mockRejectedValue(error);

            const { result } = renderHook(() => useCurrentBattle(), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isError).toBe(true));

            // With throwOnError: false, we should get error state but not throw
            expect(result.current.error).toBeTruthy();
        });

        it('does not retry on 404 (no active battle is expected state)', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.get).mockRejectedValue({
                response: { status: 404 },
            });

            renderHook(() => useCurrentBattle(), {
                wrapper: createWrapper(),
            });

            // Should only be called once (no retry due to retry: false)
            await waitFor(() => expect(axios.get).toHaveBeenCalledTimes(1));
        });
    });

    describe('when not authenticated', () => {
        it('does not fetch when session is null', () => {
            vi.mocked(useAuth).mockReturnValue({ session: null } as any);

            const { result } = renderHook(() => useCurrentBattle(), {
                wrapper: createWrapper(),
            });

            expect(result.current.fetchStatus).toBe('idle');
            expect(axios.get).not.toHaveBeenCalled();
        });

        it('does not fetch when access_token is missing', () => {
            vi.mocked(useAuth).mockReturnValue({ session: {} } as any);

            const { result } = renderHook(() => useCurrentBattle(), {
                wrapper: createWrapper(),
            });

            expect(result.current.fetchStatus).toBe('idle');
            expect(axios.get).not.toHaveBeenCalled();
        });
    });

    describe('query configuration', () => {
        it('uses correct query key for cache invalidation', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            const mockBattle = {
                id: 'battle-456',
                status: 'active',
                user1: { username: 'User1', level: 1, timezone: 'UTC', battle_win_count: 0, battle_count: 0, total_xp_earned: 0, completed_tasks: 0 },
                user2: { username: 'User2', level: 1, timezone: 'UTC', battle_win_count: 0, battle_count: 0, total_xp_earned: 0, completed_tasks: 0 },
            };

            vi.mocked(axios.get).mockResolvedValue({ data: mockBattle });

            const { result } = renderHook(() => useCurrentBattle(), {
                wrapper: createWrapper(),
            });

            // Query key should be ['battle', 'current']
            await waitFor(() => expect(result.current.isSuccess).toBe(true));
        });
    });

    describe('error handling', () => {
        it('handles server errors (500)', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.get).mockRejectedValue({
                response: { status: 500 },
                message: 'Internal server error',
            });

            const { result } = renderHook(() => useCurrentBattle(), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isError).toBe(true));
            expect(result.current.error).toBeTruthy();
        });
    });
});
