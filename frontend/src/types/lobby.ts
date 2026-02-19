/**
 * Types for Lobby component and sub-components.
 *
 * REFACTOR-005: Phase 5 - Item 6.2
 */

import type { MatchHistory, SocialUser } from './profile';

export interface LobbyProfileData {
    username: string;
    avatar_emoji: string;
    level: number;
    rank?: string;
    stats?: {
        battle_wins: number;
        battle_fought: number;
        tasks_completed: number;
        total_xp: number;
        current_streak: number;
    };
    match_history?: MatchHistory[];
    current_battle?: string | null;
    current_adventure?: string | null;
}

export interface ActiveSessionData {
    sessionType: 'battle' | 'adventure';
    opponentName: string;
    opponentEmoji?: string;
    currentDay: number;
    totalDays: number;
}

export interface BattleInviteData {
    id: string;
    user1?: {
        username?: string;
    };
    duration: number;
    start_date: string;
}

export type SocialTab = {
    following: 'following' | 'followers' | 'search';
};

// Re-export types from profile for convenience
export type { SocialUser, MatchHistory };
