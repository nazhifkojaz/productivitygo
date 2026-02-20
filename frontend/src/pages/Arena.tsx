/**
 * Arena Page (Dashboard)
 *
 * Main game view for active battles and adventures.
 * Displays scores, tasks, countdown, and action buttons.
 *
 * REFACTOR-005: Phase 5 - Week 3 - Refactored from 405 to ~200 lines
 */

import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';
import { useCurrentBattle } from '../hooks/useCurrentBattle';
import { useProfile } from '../hooks/useProfile';
import { useCurrentAdventure } from '../hooks/useCurrentAdventure';
import { useAdventureMutations } from '../hooks/useAdventureMutations';
import { useTodayTasks } from '../hooks/useTodayTasks';
import { useTaskMutations } from '../hooks/useTaskMutations';
import { useMidnightCountdown } from '../hooks/useMidnightCountdown';
import { useBattleCountdown, useBattleScores } from '../hooks';
import RivalRadar from '../components/RivalRadar';
import MonsterCard from '../components/MonsterCard';
import {
    ArenaHeader,
    PreBattleCountdown,
    PendingAcceptanceBanner,
    BattleScoreboard,
    ActiveTasksList,
    ArenaActions,
} from '../components/arena';
import type {
    ArenaMode,
    ArenaAppState,
    RoundInfo,
} from '../types';

/**
 * Computes the arena state from battle and adventure data
 */
function computeArenaState(
    battle: any,
    adventure: any
): {
    mode: ArenaMode;
    appState: ArenaAppState;
    isPreBattle: boolean;
    isLastDay: boolean;
    isPending: boolean;
    shouldShowTasks: boolean;
    roundInfo: RoundInfo | null;
} {
    // Adventure takes priority if both exist
    const mode: ArenaMode = !!adventure && !battle ? 'adventure' : 'battle';

    // Get app state based on mode
    const appState: ArenaAppState = mode === 'adventure'
        ? (adventure?.app_state || 'ACTIVE')
        : (battle?.app_state || 'IN_BATTLE');

    const isPreBattle = appState === 'PRE_BATTLE' || appState === 'PRE_ADVENTURE';
    const isLastDay = appState === 'LAST_BATTLE_DAY' || appState === 'LAST_DAY';
    const isPending = appState === 'PENDING_ACCEPTANCE';
    const shouldShowTasks = !isPreBattle && !isPending;

    // Build round info
    let roundInfo: RoundInfo | null = null;
    if (mode === 'adventure' && adventure) {
        roundInfo = {
            label: '',
            currentDay: adventure.current_round || 1,
            totalDays: adventure.duration || 5,
        };
    } else if (battle) {
        roundInfo = {
            label: `ROUND ${battle.rounds_played || 1}/5 · DAY ${battle.current_day || 1} OF ${battle.duration || 5}`,
            currentDay: battle.current_day || 1,
            totalDays: battle.duration || 5,
            roundsPlayed: battle.rounds_played || 1,
            totalRounds: 5,
        };
    }

    return { mode, appState, isPreBattle, isLastDay, isPending, shouldShowTasks, roundInfo };
}

/**
 * Main Arena/Dashboard component
 */
export default function Dashboard() {
    const { session, user } = useAuth();
    const navigate = useNavigate();
    const { data: battle, isLoading: battleLoading } = useCurrentBattle();
    const { data: profile } = useProfile();
    const { data: adventure, isLoading: adventureLoading } = useCurrentAdventure();
    const { abandonAdventureMutation, scheduleBreakMutation } = useAdventureMutations();
    const { completeTaskMutation } = useTaskMutations();

    // Timezone-based countdowns
    const timeLeft = useMidnightCountdown(profile?.timezone);

    // Compute arena state
    const arenaState = computeArenaState(battle, adventure);
    const { mode, isPreBattle, isLastDay, isPending, shouldShowTasks, roundInfo } = arenaState;

    // Pre-battle countdown
    const timeUntilBattle = useBattleCountdown({
        battle,
        adventure,
        isAdventureMode: mode === 'adventure',
        isPreBattle,
        profile,
    });

    // Fetch today's tasks
    const { data: tasks = [] } = useTodayTasks({
        enabled: shouldShowTasks && (!!battle || !!adventure)
    });

    // Calculate scores for PVP mode
    const scores = useBattleScores({ tasks, battle });

    // Loading state
    if (battleLoading || adventureLoading) {
        return (
            <div className="min-h-screen bg-[#E8E4D9] neo-grid-bg flex items-center justify-center font-black">
                INITIALIZING BATTLEFIELD...
            </div>
        );
    }

    // Determine if current user is the battle creator
    const isCreator = battle?.user1_id === user?.id;

    // Event handlers
    const toggleTask = async (taskId: string, isCompleted: boolean) => {
        if (isCompleted) {
            await completeTaskMutation.mutateAsync(taskId);
        } else {
            toast.error('Undoing tasks is not yet supported by the protocol.');
        }
    };

    const handleAcceptInvite = async () => {
        try {
            await axios.post(
                `/api/battles/${battle.id}/accept`,
                {},
                { headers: { Authorization: `Bearer ${session?.access_token}` } }
            );
            window.location.reload();
        } catch {
            toast.error('Failed to accept invite.');
        }
    };

    const handleForfeit = async () => {
        if (!confirm('Are you sure you want to surrender? This will end the battle immediately and count as a loss.')) {
            return;
        }

        try {
            await axios.post(
                `/api/battles/${battle.id}/forfeit`,
                {},
                { headers: { Authorization: `Bearer ${session?.access_token}` } }
            );
            toast.success('Battle forfeited.');
            navigate(`/battle-result/${battle.id}`);
        } catch {
            toast.error('Failed to forfeit battle.');
        }
    };

    const handleRetreat = async () => {
        if (!adventure) return;
        if (!confirm('Retreat from adventure? You\'ll receive 50% of earned XP.')) {
            return;
        }

        try {
            await abandonAdventureMutation.mutateAsync(adventure.id);
            toast.success('Retreated from adventure');
            navigate(`/adventure-result/${adventure.id}`);
        } catch {
            toast.error('Failed to retreat from adventure');
        }
    };

    const handleScheduleBreak = async () => {
        if (!adventure) return;
        if (adventure.break_days_used >= 2) {
            toast.error('No break days remaining');
            return;
        }
        if (!confirm('Schedule a break day for tomorrow? The deadline will extend by 1 day.')) {
            return;
        }

        try {
            await scheduleBreakMutation.mutateAsync(adventure.id);
            toast.success('Break day scheduled for tomorrow!');
        } catch (error: any) {
            toast.error(error.response?.data?.detail || 'Failed to schedule break');
        }
    };

    const handleForfeitOrRetreat = mode === 'adventure' ? handleRetreat : handleForfeit;

    return (
        <main className="min-h-screen bg-[#E8E4D9] neo-grid-bg p-4 md:p-8">
            {/* Header */}
            <ArenaHeader
                mode={mode}
                roundInfo={roundInfo}
                appState={arenaState.appState}
                timeLeft={timeLeft}
                onNavigateToLobby={() => navigate('/lobby')}
                onNavigateToProfile={() => navigate('/profile')}
            />

            <div className="max-w-4xl mx-auto space-y-6">
                {/* Pre-Battle Banner */}
                {isPreBattle && (
                    <PreBattleCountdown mode={mode} timeUntilBattle={timeUntilBattle} />
                )}

                {/* Pending Acceptance Banner */}
                {isPending && battle && (
                    <PendingAcceptanceBanner
                        isCreator={isCreator}
                        onAcceptInvite={handleAcceptInvite}
                    />
                )}

                {/* Scoreboard for PVP mode */}
                {mode === 'battle' && battle && !isPreBattle && !isPending && scores && (
                    <BattleScoreboard scores={scores} battle={battle} />
                )}

                {/* Opponent Display */}
                {mode === 'adventure' ? (
                    adventure ? <MonsterCard adventure={adventure} /> : null
                ) : (
                    battle && <RivalRadar battle={battle} />
                )}

                {/* Active Tasks */}
                {!isPreBattle && !isPending && (
                    <ActiveTasksList tasks={tasks} onToggleTask={toggleTask} />
                )}

                {/* Action Buttons */}
                <ArenaActions
                    mode={mode}
                    isLastDay={isLastDay}
                    isPending={isPending}
                    adventure={adventure}
                    onPlanTomorrow={() => navigate('/plan')}
                    onScheduleBreak={handleScheduleBreak}
                    onForfeitOrRetreat={handleForfeitOrRetreat}
                />
            </div>
        </main>
    );
}
