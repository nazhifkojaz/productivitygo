import { useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';

/**
 * Response from start adventure
 */
interface StartAdventureResponse {
    id: string;
    status: string;
    monster_max_hp: number;
    // ... other adventure fields
}

/**
 * Response from refresh monsters
 */
interface RefreshMonstersResponse {
    monsters: Array<{
        id: string;
        name: string;
        emoji: string;
        tier: string;
        base_hp: number;
        description: string;
    }>;
    refreshes_remaining: number;
    unlocked_tiers: string[];
}

/**
 * Response from abandon adventure
 */
interface AbandonResponse {
    status: string;
    xp_earned: number;
}

/**
 * Response from schedule break
 */
interface BreakResponse {
    status: string;
    break_date: string;
    new_deadline: string;
    breaks_remaining: number;
}

/**
 * Hook with all adventure mutations.
 *
 * Provides:
 * - startAdventureMutation: Start new adventure
 * - refreshMonstersMutation: Refresh monster pool
 * - abandonAdventureMutation: Abandon with 50% XP
 * - scheduleBreakMutation: Schedule break day
 *
 * Usage:
 * ```tsx
 * const { startAdventureMutation } = useAdventureMutations();
 *
 * const handleStart = async (monsterId: string) => {
 *   await startAdventureMutation.mutateAsync(monsterId);
 * };
 * ```
 */
export function useAdventureMutations() {
    const { session } = useAuth();
    const queryClient = useQueryClient();

    /**
     * Start a new adventure with selected monster
     */
    const startAdventureMutation = useMutation({
        mutationFn: async (monsterId: string): Promise<StartAdventureResponse> => {
            const { data } = await axios.post(
                '/api/adventures/start',
                { monster_id: monsterId },
                { headers: { Authorization: `Bearer ${session?.access_token}` } }
            );
            return data;
        },
        onSuccess: () => {
            // Invalidate queries that depend on adventure state
            queryClient.invalidateQueries({ queryKey: ['adventure'] });
            queryClient.invalidateQueries({ queryKey: ['profile'] });
            queryClient.invalidateQueries({ queryKey: ['monsters'] });
        },
    });

    /**
     * Refresh monster pool (max 3 times)
     */
    const refreshMonstersMutation = useMutation({
        mutationFn: async (): Promise<RefreshMonstersResponse> => {
            const { data } = await axios.post(
                '/api/adventures/monsters/refresh',
                {},
                { headers: { Authorization: `Bearer ${session?.access_token}` } }
            );
            return data;
        },
        onSuccess: (data) => {
            // Update the monster pool cache directly
            queryClient.setQueryData(['monsters', 'pool'], data);
        },
    });

    /**
     * Abandon adventure early (50% XP)
     */
    const abandonAdventureMutation = useMutation({
        mutationFn: async (adventureId: string): Promise<AbandonResponse> => {
            const { data } = await axios.post(
                `/api/adventures/${adventureId}/abandon`,
                {},
                { headers: { Authorization: `Bearer ${session?.access_token}` } }
            );
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['adventure'] });
            queryClient.invalidateQueries({ queryKey: ['profile'] });
        },
    });

    /**
     * Schedule tomorrow as a break day
     */
    const scheduleBreakMutation = useMutation({
        mutationFn: async (adventureId: string): Promise<BreakResponse> => {
            const { data } = await axios.post(
                `/api/adventures/${adventureId}/break`,
                {},
                { headers: { Authorization: `Bearer ${session?.access_token}` } }
            );
            return data;
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['adventure', 'current'] });
        },
    });

    return {
        startAdventureMutation,
        refreshMonstersMutation,
        abandonAdventureMutation,
        scheduleBreakMutation,
    };
}
