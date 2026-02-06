import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import type { Adventure } from '../types';

/**
 * Hook to fetch the user's active adventure.
 *
 * Returns null (via error) if no active adventure exists.
 * Use this to check if user is in adventure mode.
 *
 * Usage:
 * ```tsx
 * const { data: adventure, isLoading, error } = useCurrentAdventure();
 *
 * if (error?.response?.status === 404) {
 *   // No active adventure, show lobby
 * }
 * ```
 */
export function useCurrentAdventure() {
    const { session } = useAuth();

    return useQuery({
        queryKey: ['adventures', 'current'],
        queryFn: async (): Promise<Adventure> => {
            const { data } = await axios.get<Adventure>(
                '/api/adventures/current',
                {
                    headers: { Authorization: `Bearer ${session?.access_token}` }
                }
            );
            return data;
        },
        enabled: !!session?.access_token,
        retry: false, // Don't retry on 404 (no active adventure)
        throwOnError: false,
    });
}

// Re-export types from centralized location for backward compatibility
export type { Adventure, AdventureAppState, AdventureDetails } from '../types';
