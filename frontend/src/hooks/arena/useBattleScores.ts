/**
 * Custom hook for calculating battle scores.
 *
 * Computes the user's score from completed tasks and the rival's
 * score from battle data. Used for the PVP scoreboard display.
 *
 * REFACTOR-005: Phase 5 - Week 3 - Arena.tsx Refactoring
 */

import { useMemo } from 'react';
import type { Task } from '../../types/task';
import type { BattleData, ArenaScores } from '../../types/arena';

export interface UseBattleScoresProps {
    tasks: Task[];
    battle?: BattleData | null;
}

/**
 * Hook that calculates scores for PVP battles
 * @returns ArenaScores with myScore, rivalScore, and isLeading flag
 */
export function useBattleScores({ tasks, battle }: UseBattleScoresProps): ArenaScores | null {
    return useMemo(() => {
        if (!battle) return null;

        // Calculate my score from completed tasks
        const myScore = tasks.reduce((sum, task) => {
            if (task.is_completed) {
                return sum + (task.is_optional ? 5 : 10);
            }
            return sum;
        }, 0);

        // Calculate rival score from their completed tasks
        const rivalScore = battle?.rival?.tasks_completed
            ? battle.rival.tasks_completed * 10
            : 0;

        return {
            myScore,
            rivalScore,
            isLeading: myScore >= rivalScore,
        };
    }, [tasks, battle]);
}
