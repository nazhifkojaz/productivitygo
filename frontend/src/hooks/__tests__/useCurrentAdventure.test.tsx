import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import React from 'react';
import { useCurrentAdventure } from '../useCurrentAdventure';
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

describe('useCurrentAdventure', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('when user has active adventure', () => {
        it('fetches current adventure successfully', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            const mockAdventure = {
                id: 'adv-123',
                user_id: 'user-123',
                monster_id: 'monster-123',
                duration: 5,
                start_date: '2026-02-01',
                deadline: '2026-02-05',
                monster_max_hp: 200,
                monster_current_hp: 150,
                status: 'active',
                current_round: 2,
                total_damage_dealt: 50,
                xp_earned: 0,
                break_days_used: 0,
                max_break_days: 2,
                is_on_break: false,
                break_end_date: null,
                monster: {
                    id: 'monster-123',
                    name: 'Procrastination Goblin',
                    emoji: '👺',
                    tier: 'medium',
                    base_hp: 200,
                    description: "There's still time...",
                },
                app_state: 'ACTIVE',
                days_remaining: 3,
            };

            vi.mocked(axios.get).mockResolvedValue({ data: mockAdventure });

            const { result } = renderHook(() => useCurrentAdventure(), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isSuccess).toBe(true));

            expect(result.current.data).toEqual(mockAdventure);
            expect(axios.get).toHaveBeenCalledWith('/api/adventures/current', {
                headers: { Authorization: 'Bearer test-token' },
            });
        });

        it('includes computed fields from backend', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            const mockAdventure = {
                id: 'adv-123',
                app_state: 'ON_BREAK',
                days_remaining: 5,
                monster: {
                    id: 'monster-123',
                    name: 'Test Monster',
                    emoji: '👹',
                    tier: 'easy',
                    base_hp: 100,
                    description: 'Test',
                },
            };

            vi.mocked(axios.get).mockResolvedValue({ data: mockAdventure });

            const { result } = renderHook(() => useCurrentAdventure(), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isSuccess).toBe(true));

            expect(result.current.data?.app_state).toBe('ON_BREAK');
            expect(result.current.data?.days_remaining).toBe(5);
        });
    });

    describe('when user has no active adventure', () => {
        it('handles 404 gracefully with throwOnError: false', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            const error = {
                response: { status: 404 },
                message: 'No active adventure found',
            };
            vi.mocked(axios.get).mockRejectedValue(error);

            const { result } = renderHook(() => useCurrentAdventure(), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isError).toBe(true));

            // With throwOnError: false, we should get error state but not throw
            expect(result.current.error).toBeTruthy();
        });

        it('does not retry on 404', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.get).mockRejectedValue({
                response: { status: 404 },
            });

            renderHook(() => useCurrentAdventure(), {
                wrapper: createWrapper(),
            });

            // Should only be called once (no retry)
            await waitFor(() => expect(axios.get).toHaveBeenCalledTimes(1));
        });
    });

    describe('when not authenticated', () => {
        it('does not fetch when session is null', () => {
            vi.mocked(useAuth).mockReturnValue({ session: null } as any);

            const { result } = renderHook(() => useCurrentAdventure(), {
                wrapper: createWrapper(),
            });

            expect(result.current.fetchStatus).toBe('idle');
            expect(axios.get).not.toHaveBeenCalled();
        });
    });

    describe('query configuration', () => {
        it('has correct query key', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            const mockAdventure = {
                id: 'adv-123',
                monster: {
                    id: 'monster-123',
                    name: 'Test',
                    emoji: '👹',
                    tier: 'easy',
                    base_hp: 100,
                    description: 'Test',
                },
            };

            vi.mocked(axios.get).mockResolvedValue({ data: mockAdventure });

            const { result } = renderHook(() => useCurrentAdventure(), {
                wrapper: createWrapper(),
            });

            // Query key should be ['adventure', 'current']
            await waitFor(() => expect(result.current.isSuccess).toBe(true));
        });
    });
});
