import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import type { TypeDiscovery, MonsterType } from '../types';

/**
 * Hook to fetch the user's discovered type effectiveness entries.
 *
 * Features:
 * - Optionally filter by monster_type
 * - 10-minute stale time (discoveries change infrequently)
 * - Only fetches when authenticated
 *
 * Usage:
 * ```tsx
 * // Get all discoveries
 * const { data: discoveries, isLoading } = useDiscoveries();
 *
 * // Filter by monster type
 * const { data: slothDiscoveries } = useDiscoveries('sloth');
 * ```
 */
export function useDiscoveries(monsterType?: MonsterType) {
    const { session } = useAuth();

    return useQuery({
        queryKey: ['discoveries', monsterType],
        queryFn: async (): Promise<TypeDiscovery[]> => {
            const params = monsterType ? `?monster_type=${monsterType}` : '';
            const { data } = await axios.get<{ discoveries: TypeDiscovery[] }>(
                `/api/adventures/discoveries${params}`,
                {
                    headers: { Authorization: `Bearer ${session?.access_token}` }
                }
            );
            return data.discoveries;
        },
        enabled: !!session?.access_token,
        staleTime: 10 * 60 * 1000, // 10 minutes
        refetchOnWindowFocus: false,
    });
}

// Re-export TypeDiscovery from centralized location for convenience
export type { TypeDiscovery } from '../types';
