import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';

/**
 * Monster type definition
 */
export interface Monster {
    id: string;
    name: string;
    emoji: string;
    tier: 'easy' | 'medium' | 'hard' | 'expert' | 'boss';
    base_hp: number;
    description: string;
}

/**
 * Response from /adventures/monsters endpoint
 */
export interface MonsterPoolResponse {
    monsters: Monster[];
    refreshes_remaining: number;
    unlocked_tiers: string[];
    current_rating: number;
}

/**
 * Hook to fetch weighted monster pool for adventure selection.
 *
 * Features:
 * - Returns 4 monsters weighted by user's rating
 * - Includes refresh count (max 3)
 * - Shows which tiers are unlocked
 *
 * Usage:
 * ```tsx
 * const { data: pool, isLoading } = useMonsters();
 * pool?.monsters.map(m => <MonsterCard monster={m} />)
 * ```
 */
export function useMonsters() {
    const { session } = useAuth();

    return useQuery({
        queryKey: ['monsters', 'pool'],
        queryFn: async (): Promise<MonsterPoolResponse> => {
            const { data } = await axios.get<MonsterPoolResponse>(
                '/api/adventures/monsters',
                {
                    headers: { Authorization: `Bearer ${session?.access_token}` }
                }
            );
            return data;
        },
        enabled: !!session?.access_token,
        // Don't refetch on window focus (pool should stay stable)
        refetchOnWindowFocus: false,
    });
}
