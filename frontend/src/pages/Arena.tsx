import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';
import {
    Shield, Zap, Check, Plus,
    User, AlertTriangle, Flag, Coffee
} from 'lucide-react';
import RivalRadar from '../components/RivalRadar';
import MonsterCard from '../components/MonsterCard';
import { useCurrentBattle } from '../hooks/useCurrentBattle';
import { useProfile } from '../hooks/useProfile';
import { useCurrentAdventure } from '../hooks/useCurrentAdventure';
import { useAdventureMutations } from '../hooks/useAdventureMutations';
import { useTodayTasks } from '../hooks/useTodayTasks';
import { useTaskMutations } from '../hooks/useTaskMutations';
import { getTaskCategoryMeta } from '../types/task';

export default function Dashboard() {
    const { session, user } = useAuth();
    const navigate = useNavigate();
    const { data: battle, isLoading: battleLoading } = useCurrentBattle();
    const { data: profile } = useProfile();
    const { data: adventure, isLoading: adventureLoading } = useCurrentAdventure();
    const { abandonAdventureMutation, scheduleBreakMutation } = useAdventureMutations();
    const [timeLeft, setTimeLeft] = useState<string>('');

    // Determine game mode - adventure takes priority if both exist
    const isAdventureMode = !!adventure && !battle;
    const isLoading = battleLoading || adventureLoading;

    // Determine if we should show tasks
    const appState = isAdventureMode
        ? (adventure?.app_state || 'ACTIVE')
        : (battle?.app_state || 'IN_BATTLE');
    const isPreBattle = appState === 'PRE_BATTLE' || appState === 'PRE_ADVENTURE';
    const isLastDay = appState === 'LAST_BATTLE_DAY' || appState === 'LAST_DAY';
    const isPending = appState === 'PENDING_ACCEPTANCE';
    const shouldShowTasks = !isPreBattle && !isPending;

    // Fetch today's tasks
    const { data: tasks = [] } = useTodayTasks({
        enabled: shouldShowTasks && (!!battle || !!adventure)
    });

    const { completeTaskMutation } = useTaskMutations();

    // Countdown timer for end of day
    useEffect(() => {
        if (!profile?.timezone) return;

        const updateCountdown = () => {
            const now = new Date();

            // Calculate midnight in user's timezone
            const userNowStr = now.toLocaleString('en-US', { timeZone: profile.timezone });
            const userNow = new Date(userNowStr);

            // Calculate tomorrow midnight in user's timezone
            const tomorrowMidnight = new Date(userNow);
            tomorrowMidnight.setDate(tomorrowMidnight.getDate() + 1);
            tomorrowMidnight.setHours(0, 0, 0, 0);

            // Calculate difference
            const diff = tomorrowMidnight.getTime() - userNow.getTime();
            const hours = Math.floor(diff / (1000 * 60 * 60));
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((diff % (1000 * 60)) / 1000);

            setTimeLeft(`${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`);
        };

        updateCountdown();
        const interval = setInterval(updateCountdown, 1000);

        return () => clearInterval(interval);
    }, [profile]);

    // Countdown timer for pre-battle/adventure start
    const [timeUntilBattle, setTimeUntilBattle] = useState<string>('');
    useEffect(() => {
        if (!isPreBattle || !profile?.timezone) return;

        const updateCountdown = () => {
            const now = new Date();
            const userTimezone = profile.timezone;
            const startDateStr = isAdventureMode ? adventure!.start_date : battle!.start_date;

            const [year, month, day] = startDateStr.split('-').map(Number);
            const nowInUserTz = new Date(now.toLocaleString('en-US', { timeZone: userTimezone }));
            const localOffset = now.getTime() - new Date(now.toLocaleString('en-US')).getTime();
            const userOffset = now.getTime() - nowInUserTz.getTime();
            const offsetDiff = userOffset - localOffset;

            const startDate = new Date(year, month - 1, day, 0, 0, 0);
            const startDateInUserTz = new Date(startDate.getTime() - offsetDiff);

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

    const toggleTask = async (taskId: string, isCompleted: boolean) => {
        if (isCompleted) {
            await completeTaskMutation.mutateAsync(taskId);
        } else {
            toast.error("Undoing tasks is not yet supported by the protocol.");
        }
    };

    if (isLoading) return <div className="min-h-screen bg-[#E8E4D9] neo-grid-bg flex items-center justify-center font-black">INITIALIZING BATTLEFIELD...</div>;

    const isCreator = battle?.user1_id === user?.id;

    const handleAcceptInvite = async () => {
        try {
            await axios.post(`/api/battles/${battle.id}/accept`, {}, {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
            window.location.reload();
        } catch (error) {
            toast.error("Failed to accept invite.");
        }
    };

    const handleForfeit = async () => {
        if (!confirm("Are you sure you want to surrender? This will end the battle immediately and count as a loss.")) return;

        try {
            await axios.post(`/api/battles/${battle.id}/forfeit`, {}, {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
            toast.success("Battle forfeited.");
            navigate(`/battle-result/${battle.id}`);
        } catch (error) {
            console.error("Failed to forfeit", error);
            toast.error("Failed to forfeit battle.");
        }
    };

    const handleRetreat = async () => {
        if (!adventure) return;
        if (!confirm("Retreat from adventure? You'll receive 50% of earned XP.")) return;

        try {
            await abandonAdventureMutation.mutateAsync(adventure.id);
            toast.success("Retreated from adventure");
            navigate(`/adventure-result/${adventure.id}`);
        } catch (error) {
            console.error("Failed to retreat", error);
            toast.error("Failed to retreat from adventure");
        }
    };

    const handleScheduleBreak = async () => {
        if (!adventure) return;
        if (adventure.break_days_used >= 2) {
            toast.error("No break days remaining");
            return;
        }
        if (!confirm("Schedule a break day for tomorrow? The deadline will extend by 1 day.")) return;

        try {
            await scheduleBreakMutation.mutateAsync(adventure.id);
            toast.success("Break day scheduled for tomorrow!");
        } catch (error: any) {
            console.error("Failed to schedule break", error);
            toast.error(error.response?.data?.detail || "Failed to schedule break");
        }
    };

    // Calculate scores for scoreboard
    const myScore = tasks.reduce((sum, t) => sum + (t.is_completed ? t.assigned_score : 0), 0);
    const rivalScore = battle?.rival?.tasks_completed ? (battle?.rival?.tasks_completed * 10) : 0;
    const roundInfo = battle ? `ROUND ${battle?.rounds_played || 1}/5 · DAY ${battle?.current_day || 1} OF ${battle?.duration || 5}` : null;

    return (
        <main className="min-h-screen bg-[#E8E4D9] neo-grid-bg p-4 md:p-8">
            {/* Header */}
            <div className="max-w-4xl mx-auto mb-6">
                <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000] p-4 flex items-center justify-between">
                    <div>
                        <h1 className="text-2xl font-black uppercase">Battle Arena</h1>
                        <p className="text-xs font-mono text-gray-500">
                            {isAdventureMode
                                ? isPreBattle
                                    ? '[ PREPARING FOR ADVENTURE ]'
                                    : `[ DAY ${adventure?.current_round || 1} OF ${adventure?.duration || 5} ]`
                                : isPreBattle
                                    ? '[ PREPARING FOR BATTLE ]'
                                    : isPending
                                        ? '[ AWAITING RIVAL ]'
                                        : `[ ${roundInfo} ]`
                            }
                        </p>
                    </div>
                    <div className="flex items-center gap-2">
                        <div className="text-right">
                            <div className="text-xs font-mono font-bold text-gray-500">TIME REMAINING</div>
                            <div className="font-mono font-black text-lg">{timeLeft}</div>
                        </div>
                        <button
                            onClick={() => navigate('/profile')}
                            className="p-3 bg-white border-3 border-black shadow-[3px_3px_0_0_#000] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0_0_#000] transition-all"
                        >
                            <User className="w-5 h-5" />
                        </button>
                    </div>
                </div>
            </div>

            {/* Pre-Battle Banner */}
            {isPreBattle && (
                <div className="max-w-4xl mx-auto mb-6">
                    <div className="bg-[#F4A261] border-4 border-black shadow-[6px_6px_0_0_#000] p-8 text-center">
                        <h2 className="text-2xl font-black uppercase mb-2 flex items-center justify-center gap-2">
                            <AlertTriangle className="w-8 h-8" /> {isAdventureMode ? 'Adventure Pending' : 'Battle Pending'}
                        </h2>
                        <p className="font-bold mb-1">
                            {isAdventureMode ? 'The hunt begins in' : 'The battle begins in'}
                        </p>
                        <div className="text-3xl font-black mb-2">
                            {timeUntilBattle || 'Loading...'}
                        </div>
                        <p className="font-bold text-sm">
                            {isAdventureMode ? 'Plan your first day of tasks.' : 'Prepare your protocols.'}
                        </p>
                    </div>
                </div>
            )}

            {/* Pending Acceptance Banner */}
            {isPending && (
                <div className="max-w-4xl mx-auto mb-6">
                    <div className="bg-[#2A9D8F] border-4 border-black shadow-[6px_6px_0_0_#000] p-8 text-center">
                        <h2 className="text-2xl font-black uppercase mb-2 flex items-center justify-center gap-2 text-white">
                            <Shield className="w-8 h-8" /> Rematch Invite
                        </h2>
                        {isCreator ? (
                            <p className="font-bold text-white">Waiting for your rival to accept the challenge.</p>
                        ) : (
                            <div className="flex flex-col items-center gap-4">
                                <p className="font-bold text-white">You have been challenged to a rematch!</p>
                                <button
                                    onClick={handleAcceptInvite}
                                    className="bg-white border-3 border-black px-6 py-3 font-black uppercase shadow-[4px_4px_0_0_#000] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0_0_#000] transition-all"
                                >
                                    Accept Challenge
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            )}

            <div className="max-w-4xl mx-auto space-y-6">
                {/* Scoreboard for PVP mode */}
                {!isAdventureMode && battle && !isPreBattle && !isPending && (
                    <div className="grid grid-cols-2 gap-4">
                        <div className={`border-4 border-black p-6 text-center ${myScore >= rivalScore ? 'bg-[#2A9D8F] text-white' : 'bg-white'}`}>
                            <div className="text-xs font-black uppercase font-mono mb-2">YOUR SCORE</div>
                            <div className="text-5xl font-black">{myScore}</div>
                            <div className="text-sm font-bold mt-2">XP EARNED</div>
                            {myScore >= rivalScore && (
                                <div className="mt-2 inline-block bg-white text-black px-3 py-1 text-xs font-black border-2 border-black">
                                    LEADING
                                </div>
                            )}
                        </div>

                        <div className={`border-4 border-black p-6 text-center ${rivalScore > myScore ? 'bg-[#E63946] text-white' : 'bg-white'}`}>
                            <div className="text-xs font-black uppercase font-mono mb-2">{battle.rival?.username?.toUpperCase() || 'RIVAL'}</div>
                            <div className="text-5xl font-black">{rivalScore}</div>
                            <div className="text-sm font-bold mt-2">XP EARNED</div>
                            {rivalScore > myScore && (
                                <div className="mt-2 inline-block bg-white text-black px-3 py-1 text-xs font-black border-2 border-black">
                                    LEADING
                                </div>
                            )}
                        </div>
                    </div>
                )}

                {/* Opponent Display */}
                {isAdventureMode ? (
                    <MonsterCard adventure={adventure} />
                ) : (
                    <RivalRadar battle={battle} />
                )}

                {/* Active Tasks */}
                {!isPreBattle && !isPending && (
                    <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000]">
                        <div className="bg-black text-white p-4 border-b-4 border-black flex items-center justify-between">
                            <h2 className="text-xl font-black uppercase flex items-center gap-2">
                                <Zap className="w-6 h-6" /> Active Protocols
                            </h2>
                            <span className="font-mono text-sm">{tasks.filter(t => t.is_completed).length}/{tasks.length} COMPLETE</span>
                        </div>

                        <div className="p-4 space-y-3">
                            {tasks.length === 0 ? (
                                <div className="text-center py-8 border-2 border-dashed border-gray-300">
                                    <p className="font-bold text-gray-400">NO TASKS ASSIGNED</p>
                                    <p className="text-xs text-gray-400 mt-1">Did you forget to plan yesterday?</p>
                                </div>
                            ) : (
                                <AnimatePresence>
                                    {tasks.map((task, index) => (
                                        <motion.div
                                            key={task.id}
                                            layout
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            exit={{ opacity: 0, scale: 0.9 }}
                                            whileHover={{ x: 2 }}
                                            className={`flex items-center gap-4 p-4 border-3 border-black transition-all cursor-pointer ${
                                                task.is_completed
                                                    ? 'bg-gray-200 opacity-60'
                                                    : 'bg-white shadow-[3px_3px_0_0_#000] hover:shadow-[4px_4px_0_0_#000]'
                                            }`}
                                            onClick={() => toggleTask(task.id, !task.is_completed)}
                                        >
                                            <span className="font-mono text-xl font-black text-gray-400 w-6">0{index + 1}</span>

                                            <span
                                                className="text-lg"
                                                title={getTaskCategoryMeta(task.category || 'errand').label}
                                            >
                                                {getTaskCategoryMeta(task.category || 'errand').emoji}
                                            </span>

                                            <button
                                                className={`w-8 h-8 border-2 border-black flex items-center justify-center transition-all ${
                                                    task.is_completed ? 'bg-[#2A9D8F]' : 'bg-white'
                                                }`}
                                            >
                                                {task.is_completed && <Check className="w-5 h-5 text-white" />}
                                            </button>

                                            <span className={`flex-1 font-bold ${task.is_completed ? 'line-through text-gray-500' : ''}`}>
                                                {task.content}
                                            </span>

                                            <span className={`px-2 py-1 text-xs font-black border-2 border-black ${
                                                task.is_optional ? 'bg-[#F4A261]' : 'bg-[#E63946] text-white'
                                            }`}>
                                                {task.is_optional ? '+5 BONUS' : '+10'}
                                            </span>
                                        </motion.div>
                                    ))}
                                </AnimatePresence>
                            )}
                        </div>
                    </div>
                )}

                {/* Planning Button */}
                {!isLastDay && !isPending && (
                    <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => navigate('/plan')}
                        className="w-full bg-[#2A9D8F] border-4 border-black p-6 text-2xl font-black uppercase text-white shadow-[6px_6px_0_0_#000] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[4px_4px_0_0_#000] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none transition-all flex items-center justify-center gap-3"
                    >
                        <Plus className="w-8 h-8" />
                        Plan Tomorrow
                    </motion.button>
                )}

                {isLastDay && (
                    <div className="w-full bg-[#E63946] border-4 border-black p-4 text-center font-bold text-white shadow-[4px_4px_0_0_#000]">
                        ⚠️ FINAL DAY - NO PLANNING REQUIRED
                    </div>
                )}

                {/* Break Day Button (Adventure only) */}
                {isAdventureMode && adventure && !isPreBattle && adventure.break_days_used < 2 && (
                    <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={handleScheduleBreak}
                        className="w-full bg-yellow-300 border-3 border-black p-4 text-lg font-black uppercase shadow-[4px_4px_0_0_#000] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0_0_#000] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none transition-all flex items-center justify-center gap-2"
                    >
                        <Coffee className="w-5 h-5" />
                        Schedule Break ({2 - adventure.break_days_used} remaining)
                    </motion.button>
                )}

                {/* Forfeit/Retreat Button */}
                {!isPending && (
                    <button
                        onClick={isAdventureMode ? handleRetreat : handleForfeit}
                        className="w-full bg-[#E63946] border-3 border-black p-4 font-bold uppercase text-white shadow-[4px_4px_0_0_#000] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0_0_#000] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none transition-all flex items-center justify-center gap-2"
                    >
                        <Flag className="w-5 h-5" /> {isAdventureMode ? 'RETREAT' : 'SURRENDER BATTLE'}
                    </button>
                )}
            </div>
        </main>
    );
}
