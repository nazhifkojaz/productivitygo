/**
 * Profile stats from the backend
 */
export interface ProfileStats {
    battle_wins: number;
    total_xp: number;
    battle_fought: number;
    win_rate: string;
    tasks_completed: number;
}

/**
 * Full profile data
 */
export interface ProfileData {
    id: string;
    username: string;
    avatar_emoji: string;
    timezone: string;
    level: number;
    rank: string;
    stats: ProfileStats;
    email: string;
}

/**
 * Public profile data (excluding email)
 */
export interface PublicProfileData {
    id: string;
    username: string;
    avatar_emoji: string;
    timezone: string;
    level: number;
    rank: string;
    stats: ProfileStats;
}
