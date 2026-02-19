/**
 * Types for Arena (Dashboard) component and sub-components.
 *
 * REFACTOR-005: Phase 5 - Week 3 - Arena.tsx Refactoring
 */

import type { Adventure, AdventureAppState } from './adventure';
import type { Task } from './task';

/**
 * Rival information from battle API
 */
export interface RivalInfo {
    username?: string;
    avatar_emoji?: string;
    level?: number;
    rank?: string;
    tasks_completed?: number;
    tasks_total?: number;
}

/**
 * Battle app states from backend
 */
export type BattleAppState =
    | 'IN_BATTLE'
    | 'PRE_BATTLE'
    | 'PENDING_ACCEPTANCE'
    | 'LAST_BATTLE_DAY';

/**
 * Battle data structure from API
 */
export interface BattleData {
    id: string;
    user1_id?: string;
    user1?: {
        id?: string;
        username?: string;
        avatar_emoji?: string;
    };
    user2?: {
        id?: string;
        username?: string;
        avatar_emoji?: string;
    };
    rival?: RivalInfo;
    app_state?: BattleAppState;
    start_date?: string;
    current_day?: number;
    duration?: number;
    rounds_played?: number;
    status?: string;
}

/**
 * Combined arena game mode
 */
export type ArenaMode = 'battle' | 'adventure';

/**
 * Combined app state for arena UI
 */
export type ArenaAppState =
    | BattleAppState
    | AdventureAppState
    | 'ACTIVE'; // Fallback for adventure

/**
 * Arena scores for PVP mode
 */
export interface ArenaScores {
    myScore: number;
    rivalScore: number;
    isLeading: boolean;
}

/**
 * Pre-battle countdown display format
 */
export interface CountdownDisplay {
    timeRemaining: string;
    isStartingNow: boolean;
}

/**
 * Round info display
 */
export interface RoundInfo {
    label: string;
    currentDay: number;
    totalDays: number;
    roundsPlayed?: number;
    totalRounds?: number;
}

/**
 * Arena state computed from battle/adventure data
 */
export interface ArenaState {
    mode: ArenaMode;
    appState: ArenaAppState;
    isPreBattle: boolean;
    isLastDay: boolean;
    isPending: boolean;
    shouldShowTasks: boolean;
    roundInfo: RoundInfo | null;
}

/**
 * Props for task completion handler
 */
export interface TaskCompletionHandler {
    onToggleTask: (taskId: string, complete: boolean) => void;
}

/**
 * Props for action buttons (forfeit/retreat, accept invite)
 */
export interface ArenaActionHandlers {
    onAcceptInvite?: () => void;
    onForfeit?: () => void;
    onRetreat?: () => void;
    onScheduleBreak?: () => void;
    onPlanTomorrow?: () => void;
}

// Re-export commonly used types
export type { Adventure, Task };
