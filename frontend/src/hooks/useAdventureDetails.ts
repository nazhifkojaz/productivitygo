import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import type { Adventure } from './useCurrentAdventure';

/**
 * Daily breakdown entry
 */
export interface DailyDamage {
    date: string;
    damage: number;
}

/**
 * Adventure details with daily breakdown
 */
export interface AdventureDetails extends Adventure {
    daily_breakdown: DailyDamage[];
}

/**
 * Hook to fetch adventure details by ID.
 *
 * Used primarily on the AdventureResult page to show:
 * - Final outcome (victory/escaped)
 * - Total damage dealt
 * - XP earned
 * - Daily breakdown
 *
 * Usage:
 * ```tsx
 * const { adventureId } = useParams();
 * const { data: adventure } = useAdventureDetails(adventureId);
 * ```
 */
export function useAdventureDetails(adventureId: string | undefined) {
    const { session } = useAuth();

    return useQuery({
        queryKey: ['adventures', adventureId],
        queryFn: async (): Promise<AdventureDetails> => {
            const { data } = await axios.get<AdventureDetails>(
                `/api/adventures/${adventureId}`,
                {
                    headers: { Authorization: `Bearer ${session?.access_token}` }
                }
            );
            return data;
        },
        enabled: !!session?.access_token && !!adventureId,
    });
}
