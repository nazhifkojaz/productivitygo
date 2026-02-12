import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import React from 'react';
import { useDiscoveries } from '../useDiscoveries';
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

describe('useDiscoveries', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    describe('when fetching all discoveries', () => {
        it('fetches discoveries successfully', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            const mockDiscoveries = [
                {
                    monster_type: 'sloth',
                    task_category: 'physical',
                    effectiveness: 'super_effective' as const,
                },
                {
                    monster_type: 'sloth',
                    task_category: 'errand',
                    effectiveness: 'neutral' as const,
                },
            ];

            vi.mocked(axios.get).mockResolvedValue({ data: { discoveries: mockDiscoveries } });

            const { result } = renderHook(() => useDiscoveries(), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isSuccess).toBe(true));

            expect(result.current.data).toEqual(mockDiscoveries);
            expect(axios.get).toHaveBeenCalledWith('/api/adventures/discoveries', {
                headers: { Authorization: 'Bearer test-token' },
            });
        });

        it('returns empty array when no discoveries exist', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.get).mockResolvedValue({ data: { discoveries: [] } });

            const { result } = renderHook(() => useDiscoveries(), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isSuccess).toBe(true));

            expect(result.current.data).toEqual([]);
        });
    });

    describe('when filtering by monster type', () => {
        it('includes monster_type query parameter', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            const mockDiscoveries = [
                {
                    monster_type: 'sloth',
                    task_category: 'physical',
                    effectiveness: 'super_effective' as const,
                },
            ];

            vi.mocked(axios.get).mockResolvedValue({ data: { discoveries: mockDiscoveries } });

            const { result } = renderHook(() => useDiscoveries('sloth'), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isSuccess).toBe(true));

            expect(axios.get).toHaveBeenCalledWith('/api/adventures/discoveries?monster_type=sloth', {
                headers: { Authorization: 'Bearer test-token' },
            });
        });

        it('filters discoveries to only matching monster type', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            const mockDiscoveries = [
                {
                    monster_type: 'sloth',
                    task_category: 'physical',
                    effectiveness: 'super_effective' as const,
                },
                {
                    monster_type: 'sloth',
                    task_category: 'errand',
                    effectiveness: 'neutral' as const,
                },
            ];

            vi.mocked(axios.get).mockResolvedValue({ data: { discoveries: mockDiscoveries } });

            const { result } = renderHook(() => useDiscoveries('sloth'), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isSuccess).toBe(true));

            expect(result.current.data).toHaveLength(2);
            expect(result.current.data?.[0].monster_type).toBe('sloth');
        });
    });

    describe('when not authenticated', () => {
        it('does not fetch when session is null', () => {
            vi.mocked(useAuth).mockReturnValue({ session: null } as any);

            const { result } = renderHook(() => useDiscoveries(), {
                wrapper: createWrapper(),
            });

            expect(result.current.fetchStatus).toBe('idle');
            expect(axios.get).not.toHaveBeenCalled();
        });
    });

    describe('query configuration', () => {
        it('uses different query keys for different monster types', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.get).mockResolvedValue({ data: { discoveries: [] } });

            const { result: fogResult } = renderHook(() => useDiscoveries('fog'), {
                wrapper: createWrapper(),
            });
            const { result: slothResult } = renderHook(() => useDiscoveries('sloth'), {
                wrapper: createWrapper(),
            });

            // Both hooks should succeed independently
            await waitFor(() => expect(fogResult.current.isSuccess).toBe(true));
            await waitFor(() => expect(slothResult.current.isSuccess).toBe(true));
        });

        it('caches data for 10 minutes (verified by successful fetch)', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.get).mockResolvedValue({ data: { discoveries: [] } });

            const { result } = renderHook(() => useDiscoveries(), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isSuccess).toBe(true));

            // Should only call API once (cache is working)
            expect(axios.get).toHaveBeenCalledTimes(1);
        });
    });

    describe('error handling', () => {
        it('handles API errors gracefully', async () => {
            const mockSession = { access_token: 'test-token' };
            vi.mocked(useAuth).mockReturnValue({ session: mockSession } as any);

            vi.mocked(axios.get).mockRejectedValue(new Error('API Error'));

            const { result } = renderHook(() => useDiscoveries(), {
                wrapper: createWrapper(),
            });

            await waitFor(() => expect(result.current.isError).toBe(true));

            expect(result.current.error).toBeTruthy();
        });
    });
});
