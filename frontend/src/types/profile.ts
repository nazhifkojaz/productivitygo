/**
 * Profile stats from the backend
 */
export interface ProfileStats {
    battle_wins: number;
    total_xp: number;
    battle_fought: number;
    win_rate: string;
    tasks_completed: number;
    current_streak?: number;
}

/**
 * Match history entry (includes both battles and adventures)
 */
export interface MatchHistory {
    id: string;
    date: string;
    rival: string;
    result: 'WIN' | 'LOSS' | 'DRAW' | 'ESCAPED' | 'COMPLETED';
    duration: number;
    type: 'battle' | 'adventure';
    emoji?: string;  // For adventures
    xp_earned?: number;  // For adventures
}

/**
 * User shape from social API endpoints (search, following, followers)
 */
export interface SocialUser {
    id: string;
    username: string;
    avatar_emoji?: string;
    level?: number;
    rank?: string;
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
    match_history?: MatchHistory[];
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
    match_history?: MatchHistory[];
}
