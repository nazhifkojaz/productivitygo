import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import React from 'react';
import { useAdventureMutations } from '../useAdventureMutations';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock axios
vi.mock('axios', () => ({
    default: {
        post: vi.fn(),
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
            mutations: {
                retry: false,
            },
        },
    });
    return ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
};

describe('useAdventureMutations', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('startAdventureMutation', () => {
        it('starts adventure with selected monster', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            const mockAdventure = {
                id: 'adv-123',
                status: 'active',
                monster_max_hp: 200,
                monster: {
                    id: 'monster-123',
                    name: 'Test Monster',
                    emoji: '👹',
                    tier: 'medium',
                    base_hp: 200,
                    description: 'Test',
                },
            };

            vi.mocked(axios.post).mockResolvedValue({ data: mockAdventure });

            const { result } = renderHook(() => useAdventureMutations(), {
                wrapper: createWrapper(),
            });

            await result.current.startAdventureMutation.mutateAsync('monster-123');

            expect(axios.post).toHaveBeenCalledWith(
                '/api/adventures/start',
                { monster_id: 'monster-123' },
                { headers: { Authorization: 'Bearer test-token' } }
            );
        });

        it('invalidates relevant queries on success', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            const mockAdventure = { id: 'adv-123', status: 'active', monster_max_hp: 200 };
            vi.mocked(axios.post).mockResolvedValue({ data: mockAdventure });

            const queryClient = new QueryClient();
            const wrapper = ({ children }: { children: React.ReactNode }) => (
                <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
            );

            // Spy on invalidateQueries
            const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

            const { result } = renderHook(() => useAdventureMutations(), { wrapper });

            await result.current.startAdventureMutation.mutateAsync('monster-123');

            // Check that relevant queries were invalidated
            expect(invalidateSpy).toHaveBeenCalledWith(
                expect.objectContaining({ queryKey: ['adventure'] })
            );
        });
    });

    describe('refreshMonstersMutation', () => {
        it('refreshes monster pool', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            const mockPool = {
                monsters: [
                    {
                        id: 'monster-1',
                        name: 'New Monster',
                        emoji: '👹',
                        tier: 'easy',
                        base_hp: 100,
                        description: 'New',
                    },
                ],
                refreshes_remaining: 2,
                unlocked_tiers: ['easy', 'medium'],
            };

            vi.mocked(axios.post).mockResolvedValue({ data: mockPool });

            const { result } = renderHook(() => useAdventureMutations(), {
                wrapper: createWrapper(),
            });

            await result.current.refreshMonstersMutation.mutateAsync();

            expect(axios.post).toHaveBeenCalledWith(
                '/api/adventures/monsters/refresh',
                {},
                { headers: { Authorization: 'Bearer test-token' } }
            );
        });

        it('updates monster pool cache directly on success', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            const mockPool = {
                monsters: [{ id: '1', name: 'Monster', emoji: '👹', tier: 'easy', base_hp: 100, description: 'Test' }],
                refreshes_remaining: 2,
                unlocked_tiers: ['easy'],
            };

            vi.mocked(axios.post).mockResolvedValue({ data: mockPool });

            const queryClient = new QueryClient();
            const wrapper = ({ children }: { children: React.ReactNode }) => (
                <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
            );

            const setQueryDataSpy = vi.spyOn(queryClient, 'setQueryData');

            const { result } = renderHook(() => useAdventureMutations(), { wrapper });

            await result.current.refreshMonstersMutation.mutateAsync();

            expect(setQueryDataSpy).toHaveBeenCalledWith(['monsters', 'pool'], mockPool);
        });
    });

    describe('abandonAdventureMutation', () => {
        it('abandons adventure with 50% XP', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            const mockResponse = {
                status: 'abandoned',
                xp_earned: 50,
            };

            vi.mocked(axios.post).mockResolvedValue({ data: mockResponse });

            const { result } = renderHook(() => useAdventureMutations(), {
                wrapper: createWrapper(),
            });

            await result.current.abandonAdventureMutation.mutateAsync('adv-123');

            expect(axios.post).toHaveBeenCalledWith(
                '/api/adventures/adv-123/abandon',
                {},
                { headers: { Authorization: 'Bearer test-token' } }
            );
        });
    });

    describe('scheduleBreakMutation', () => {
        it('schedules break day for adventure', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            const mockResponse = {
                status: 'break_scheduled',
                break_date: '2026-02-07',
                new_deadline: '2026-02-08',
                breaks_remaining: 1,
            };

            vi.mocked(axios.post).mockResolvedValue({ data: mockResponse });

            const { result } = renderHook(() => useAdventureMutations(), {
                wrapper: createWrapper(),
            });

            await result.current.scheduleBreakMutation.mutateAsync('adv-123');

            expect(axios.post).toHaveBeenCalledWith(
                '/api/adventures/adv-123/break',
                {},
                { headers: { Authorization: 'Bearer test-token' } }
            );
        });

        it('invalidates current adventure query on success', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            const mockResponse = {
                status: 'break_scheduled',
                break_date: '2026-02-07',
                new_deadline: '2026-02-08',
                breaks_remaining: 1,
            };

            vi.mocked(axios.post).mockResolvedValue({ data: mockResponse });

            const queryClient = new QueryClient();
            const wrapper = ({ children }: { children: React.ReactNode }) => (
                <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
            );

            const invalidateSpy = vi.spyOn(queryClient, 'invalidateQueries');

            const { result } = renderHook(() => useAdventureMutations(), { wrapper });

            await result.current.scheduleBreakMutation.mutateAsync('adv-123');

            expect(invalidateSpy).toHaveBeenCalledWith(
                expect.objectContaining({ queryKey: ['adventure', 'current'] })
            );
        });
    });
});
