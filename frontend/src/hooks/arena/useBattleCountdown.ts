/**
 * Custom hook for pre-battle/adventure countdown timer.
 *
 * Calculates the time remaining until a battle or adventure starts
 * based on the user's timezone and the start date.
 *
 * REFACTOR-005: Phase 5 - Week 3 - Arena.tsx Refactoring
 */

import { useState, useEffect } from 'react';
import type { BattleData, Adventure } from '../../types/arena';

interface Profile {
    timezone?: string;
}

export interface UseBattleCountdownProps {
    battle?: BattleData | null;
    adventure?: Adventure | null;
    isAdventureMode: boolean;
    isPreBattle: boolean;
    profile?: Profile | null;
}

/**
 * Hook that computes the countdown to battle/adventure start
 * @returns Formatted countdown string or empty string if not applicable
 */
export function useBattleCountdown({
    battle,
    adventure,
    isAdventureMode,
    isPreBattle,
    profile,
}: UseBattleCountdownProps): string {
    const [timeUntilBattle, setTimeUntilBattle] = useState<string>('');

    useEffect(() => {
        if (!isPreBattle || !profile?.timezone) {
            setTimeUntilBattle('');
            return;
        }

        const session = isAdventureMode ? adventure : battle;
        const startDateStr = session?.start_date;
        if (!startDateStr) return;

        const updateCountdown = () => {
            const now = new Date();
            const userTimezone = profile.timezone;

            // Parse start date (format: YYYY-MM-DD)
            const [year, month, day] = startDateStr.split('-').map(Number);

            // Get current time in user's timezone
            const nowInUserTz = new Date(now.toLocaleString('en-US', { timeZone: userTimezone }));
            const localOffset = now.getTime() - new Date(now.toLocaleString('en-US')).getTime();
            const userOffset = now.getTime() - nowInUserTz.getTime();
            const offsetDiff = userOffset - localOffset;

            // Create start date in user's timezone
            const startDateObj = new Date(year, month - 1, day, 0, 0, 0);
            const startDateInUserTz = new Date(startDateObj.getTime() - offsetDiff);

            const diff = startDateInUserTz.getTime() - now.getTime();

            if (diff <= 0) {
                setTimeUntilBattle('Starting now!');
                return;
            }

            const days = Math.floor(diff / (1000 * 60 * 60 * 24));
            const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((diff % (1000 * 60)) / 1000);

            if (days > 0) {
                setTimeUntilBattle(`${days}d ${hours}h ${minutes}m`);
            } else if (hours > 0) {
                setTimeUntilBattle(`${hours}h ${minutes}m ${seconds}s`);
            } else {
                setTimeUntilBattle(`${minutes}m ${seconds}s`);
            }
        };

        updateCountdown();
        const interval = setInterval(updateCountdown, 1000);

        return () => clearInterval(interval);
    }, [battle, adventure, isAdventureMode, isPreBattle, profile]);

    return timeUntilBattle;
}
