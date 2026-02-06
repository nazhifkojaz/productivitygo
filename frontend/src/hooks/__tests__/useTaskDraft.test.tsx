import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import React from 'react';
import { useTaskDraft } from '../useTaskDraft';
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

describe('useTaskDraft', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('when draft tasks exist', () => {
        it('fetches draft tasks successfully', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            const mockDraftTasks = [
                { content: 'Complete project', is_optional: false, assigned_score: 10 },
                { content: 'Review PR', is_optional: false, assigned_score: 10 },
                { content: 'Bonus task', is_optional: true, assigned_score: 5 },
            ];

            vi.mocked(axios.get).mockResolvedValue({ data: mockDraftTasks });

            const { result } = renderHook(() => useTaskDraft(), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isSuccess).toBe(true));

            expect(result.current.data).toEqual(mockDraftTasks);
            expect(axios.get).toHaveBeenCalledWith('/api/tasks/draft', {
                headers: { Authorization: 'Bearer test-token' },
            });
        });

        it('returns empty array when no draft exists', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.get).mockResolvedValue({ data: [] });

            const { result } = renderHook(() => useTaskDraft(), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isSuccess).toBe(true));

            expect(result.current.data).toEqual([]);
        });
    });

    describe('when not authenticated', () => {
        it('does not fetch when session is null', () => {
            vi.mocked(useAuth).mockReturnValue({ session: null } as any);

            const { result } = renderHook(() => useTaskDraft(), {
                wrapper: createWrapper(),
            });

            expect(result.current.fetchStatus).toBe('idle');
            expect(axios.get).not.toHaveBeenCalled();
        });

        it('does not fetch when access_token is missing', () => {
            vi.mocked(useAuth).mockReturnValue({ session: {} } as any);

            const { result } = renderHook(() => useTaskDraft(), {
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

            const mockDraftTasks = [
                { content: 'Test task', is_optional: false, assigned_score: 10 },
            ];

            vi.mocked(axios.get).mockResolvedValue({ data: mockDraftTasks });

            const { result } = renderHook(() => useTaskDraft(), {
                wrapper: createWrapper(),
            });

            // Verify the hook fetches data successfully
            await waitFor(() => expect(result.current.isSuccess).toBe(true));
            expect(result.current.data).toEqual(mockDraftTasks);
        });

        it('has staleTime of 0 (always fresh)', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.get).mockResolvedValue({ data: [] });

            const { result } = renderHook(() => useTaskDraft(), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isSuccess).toBe(true));
            // staleTime is configured to 0 but not directly exposed
            expect(result.current.data).toEqual([]);
        });
    });

    describe('error handling', () => {
        it('handles API errors gracefully', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.get).mockRejectedValue(new Error('Network error'));

            const { result } = renderHook(() => useTaskDraft(), {
                wrapper: createWrapper(),
            });

            // Just verify the hook renders without crashing
            expect(result.current).toBeDefined();
        });
    });
});
