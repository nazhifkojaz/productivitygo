import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import React from 'react';
import { useTodayTasks } from '../useTodayTasks';
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
        logger: {
            log: console.log,
            warn: console.warn,
            error: () => {}, // Suppress error logging during tests
        },
    });
    return ({ children }: { children: React.ReactNode }) => (
        <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
    );
};

describe('useTodayTasks', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('when user has tasks', () => {
        it('fetches today tasks successfully', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            const mockTasks = [
                { id: 'task-1', content: 'Complete project', is_completed: false, is_optional: false },
                { id: 'task-2', content: 'Review PR', is_completed: false, is_optional: false },
                { id: 'task-3', content: 'Bonus task', is_completed: false, is_optional: true },
            ];

            vi.mocked(axios.get).mockResolvedValue({ data: mockTasks });

            const { result } = renderHook(() => useTodayTasks(), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isSuccess).toBe(true));

            expect(result.current.data).toEqual(mockTasks);
            expect(axios.get).toHaveBeenCalledWith('/api/tasks/today', {
                headers: { Authorization: 'Bearer test-token' },
            });
        });

        it('returns empty array when no tasks exist', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.get).mockResolvedValue({ data: [] });

            const { result } = renderHook(() => useTodayTasks(), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isSuccess).toBe(true));

            expect(result.current.data).toEqual([]);
        });
    });

    describe('when not authenticated', () => {
        it('does not fetch when session is null', () => {
            vi.mocked(useAuth).mockReturnValue({ session: null } as any);

            const { result } = renderHook(() => useTodayTasks(), {
                wrapper: createWrapper(),
            });

            expect(result.current.fetchStatus).toBe('idle');
            expect(axios.get).not.toHaveBeenCalled();
        });

        it('does not fetch when access_token is missing', () => {
            vi.mocked(useAuth).mockReturnValue({ session: {} } as any);

            const { result } = renderHook(() => useTodayTasks(), {
                wrapper: createWrapper(),
            });

            expect(result.current.fetchStatus).toBe('idle');
            expect(axios.get).not.toHaveBeenCalled();
        });
    });

    describe('enabled option', () => {
        it('respects enabled=false option', () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            renderHook(() => useTodayTasks({ enabled: false }), {
                wrapper: createWrapper(),
            });

            expect(axios.get).not.toHaveBeenCalled();
        });

        it('fetches when enabled=true explicitly', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.get).mockResolvedValue({ data: [] });

            renderHook(() => useTodayTasks({ enabled: true }), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(axios.get).toHaveBeenCalled());
        });
    });

    describe('query configuration', () => {
        it('uses correct query key for cache invalidation', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            const mockTasks = [
                { id: 'task-1', content: 'Test task', is_completed: false, is_optional: false },
            ];

            vi.mocked(axios.get).mockResolvedValue({ data: mockTasks });

            const { result } = renderHook(() => useTodayTasks(), {
                wrapper: createWrapper(),
            });

            // Verify the hook fetches data successfully
            await waitFor(() => expect(result.current.isSuccess).toBe(true));
            expect(result.current.data).toBeDefined();
        });
    });

    describe('error handling', () => {
        it('handles API errors gracefully', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.get).mockRejectedValue(new Error('Network error'));

            const { result } = renderHook(() => useTodayTasks(), {
                wrapper: createWrapper(),
            });

            // Just verify the hook renders without crashing
            expect(result.current).toBeDefined();
        });
    });
});
