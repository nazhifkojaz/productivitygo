import type { Monster, TypeDiscovery } from './monster';

/**
 * Adventure app states computed by the backend
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

    // Discovered type effectiveness for current monster
    discoveries?: TypeDiscovery[];

    // Computed fields (from API)
    app_state?: AdventureAppState;
    days_remaining?: number;
}

/**
 * Daily breakdown entry for adventure details
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
