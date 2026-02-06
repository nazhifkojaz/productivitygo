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
