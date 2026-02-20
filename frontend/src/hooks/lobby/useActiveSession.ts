/**
 * Custom hook for detecting active battle/adventure sessions.
 *
 * REFACTOR-005: Phase 5 - Item 6.2
 */

import { useEffect, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCurrentBattle } from '../useCurrentBattle';
import { useCurrentAdventure } from '../useCurrentAdventure';
import type { ActiveSessionData } from '../../types/lobby';

interface Profile {
    id?: string;
    current_battle?: string | null;
    current_adventure?: string | null;
}

export function useActiveSession(profile: Profile | null) {
    const navigate = useNavigate();
    const { data: activeBattle } = useCurrentBattle();
    const { data: activeAdventure } = useCurrentAdventure();

    const hasActiveBattle = !!profile?.current_battle;
    const hasActiveAdventure = !!profile?.current_adventure;
    const showBanner = hasActiveBattle || hasActiveAdventure;

    // Redirect to result page if session is completed
    useEffect(() => {
        if (activeBattle?.status === 'completed') {
            navigate(`/battle-result/${activeBattle.id}`, { replace: true });
        }
        if (activeAdventure?.status === 'completed' || activeAdventure?.status === 'escaped') {
            navigate(`/adventure-result/${activeAdventure.id}`, { replace: true });
        }
    }, [activeBattle, activeAdventure, navigate]);

    const bannerProps = useMemo((): ActiveSessionData | null => {
        if (hasActiveAdventure && activeAdventure) {
            const monster = activeAdventure.monster;
            return {
                sessionType: 'adventure',
                opponentName: monster?.name || 'Unknown Monster',
                opponentEmoji: monster?.emoji,
                currentDay: activeAdventure.current_round || 1,
                totalDays: activeAdventure.duration || 5,
            };
        }
        if (hasActiveBattle && activeBattle && profile) {
            const rival = activeBattle.user1?.id === profile?.id ? activeBattle.user2 : activeBattle.user1;
            return {
                sessionType: 'battle',
                opponentName: rival?.username || 'Rival',
                opponentEmoji: rival?.avatar_emoji,
                currentDay: activeBattle.current_round || 1,
                totalDays: activeBattle.duration || 5,
            };
        }
        return null;
    }, [hasActiveAdventure, hasActiveBattle, activeAdventure, activeBattle, profile]);

    return {
        showBanner,
        bannerProps,
    };
}
