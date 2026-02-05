import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import type { Monster } from './useMonsters';

/**
 * Adventure app states
 */
export type AdventureAppState =
    | 'ACTIVE'
    | 'ON_BREAK'
    | 'LAST_DAY'
    | 'PRE_ADVENTURE'
    | 'DEADLINE_PASSED'
    | 'COMPLETED'
    | 'ESCAPED';

/**
 * Adventure type definition
 */
export interface Adventure {
    id: string;
    user_id: string;
    monster_id: string;

    // Timing
    duration: number;
    start_date: string;
    deadline: string;

    // Monster state
    monster_max_hp: number;
    monster_current_hp: number;

    // Progress
    status: 'active' | 'completed' | 'escaped' | 'abandoned';
    current_round: number;
    total_damage_dealt: number;
    xp_earned: number;

    // Breaks
    break_days_used: number;
    max_break_days: number;
    is_on_break: boolean;
    break_end_date: string | null;

    // Embedded monster data
    monster?: Monster;

    // Computed fields (from API)
    app_state?: AdventureAppState;
    days_remaining?: number;
}

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
