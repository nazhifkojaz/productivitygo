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

export default function Dashboard() {
    const { session, user } = useAuth();
    const navigate = useNavigate();
    const { data: battle, isLoading: battleLoading } = useCurrentBattle();
    const { data: profile } = useProfile();
    const { data: adventure, isLoading: adventureLoading } = useCurrentAdventure();
    const { abandonAdventureMutation, scheduleBreakMutation } = useAdventureMutations();
    const [timeUntilBattle, setTimeUntilBattle] = useState<string>('');

    // Determine game mode - adventure takes priority if both exist
    const isAdventureMode = !!adventure && !battle;
    const isLoading = battleLoading || adventureLoading;

    // Determine if we should show tasks (only during active battle/adventure days)
    // Derive app_state from adventure when in adventure mode, from battle when in PVP mode
    const appState = isAdventureMode
        ? (adventure?.app_state || 'ACTIVE')
        : (battle?.app_state || 'IN_BATTLE');
    const isPreBattle = appState === 'PRE_BATTLE' || appState === 'PRE_ADVENTURE';
    const isLastDay = appState === 'LAST_BATTLE_DAY' || appState === 'LAST_DAY';
    const isPending = appState === 'PENDING_ACCEPTANCE';
    const shouldShowTasks = !isPreBattle && !isPending;

    // Fetch today's tasks using React Query hook
    const { data: tasks = [] } = useTodayTasks({
        enabled: shouldShowTasks && (!!battle || !!adventure)
    });

    // Task mutations
    const { completeTaskMutation } = useTaskMutations();

    // Countdown timer for pre-battle and pre-adventure
    useEffect(() => {
        if (!isPreBattle || !profile?.timezone) return;

        const updateCountdown = () => {
            const now = new Date();

            // Parse the start date (YYYY-MM-DD) as midnight in the user's timezone
            const userTimezone = profile.timezone;
            const startDateStr = isAdventureMode ? adventure!.start_date : battle!.start_date;

            // Create a date string at midnight in the user's timezone
            const [year, month, day] = startDateStr.split('-').map(Number);

            // Get current time in user's timezone to extract offset
            const nowInUserTz = new Date(now.toLocaleString('en-US', { timeZone: userTimezone }));

            // Calculate the offset difference between user's timezone and local timezone
            const localOffset = now.getTime() - new Date(now.toLocaleString('en-US')).getTime();
            const userOffset = now.getTime() - nowInUserTz.getTime();
            const offsetDiff = userOffset - localOffset;

            // Create the start date at midnight in user's timezone
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
            // React Query handles optimistic updates internally if configured
            // For now, the mutation will invalidate and refetch
            await completeTaskMutation.mutateAsync(taskId);
        } else {
            // Undo completion (if supported API-wise, currently only complete endpoint exists)
            toast.error("Undoing tasks is not yet supported by the protocol.");
        }
    };

    if (isLoading) return <div className="min-h-screen bg-neo-bg flex items-center justify-center font-black">INITIALIZING BATTLEFIELD...</div>;

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

    return (
        <main className="min-h-screen bg-neo-bg p-4 md:p-8 pb-48 flex flex-col items-center">
            {/* Header */}
            <header className="w-full max-w-3xl flex justify-between items-center mb-8">
                <div className="bg-neo-white border-3 border-black p-4 shadow-neo-sm">
                    <h1 className="text-2xl font-black italic uppercase">Battle <span className="text-neo-primary">Dashboard</span></h1>
                    <div className="text-xs font-bold text-gray-500">
                        {isAdventureMode
                            ? (isPreBattle
                                ? 'PREPARING FOR ADVENTURE'
                                : `DAY ${adventure?.current_round || 1} • ${adventure?.days_remaining || 0} DAYS LEFT`)
                            : isPreBattle
                                ? 'PREPARING FOR BATTLE'
                                : isPending
                                    ? 'AWAITING RIVAL'
                                    : `ROUND ${battle?.rounds_played || 1} / 5`
                        }
                    </div>
                </div>
                <div className="flex gap-2">
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => navigate('/profile')}
                        className="w-12 h-12 bg-white border-3 border-black shadow-neo flex items-center justify-center"
                        title="My Profile"
                    >
                        <User className="w-6 h-6" />
                    </motion.button>


                </div>
            </header>

            {/* Pre-Battle Banner */}
            {isPreBattle && (
                <div className="w-full max-w-3xl bg-yellow-300 border-3 border-black p-6 shadow-neo mb-8 text-center">
                    <h2 className="text-2xl font-black uppercase mb-2 flex items-center justify-center gap-2">
                        <AlertTriangle className="w-8 h-8" /> {isAdventureMode ? 'Adventure Pending' : 'Battle Pending'}
                    </h2>
                    <p className="font-bold mb-1">
                        {isAdventureMode ? 'The hunt begins in' : 'The battle begins in'}
                    </p>
                    <div className="text-3xl font-black text-neo-primary mb-2">
                        {timeUntilBattle || 'Loading...'}
                    </div>
                    <p className="font-bold text-sm">
                        {isAdventureMode ? 'Plan your first day of tasks.' : 'Prepare your protocols.'}
                    </p>
                </div>
            )}

            {/* Pending Acceptance Banner */}
            {isPending && (
                <div className="w-full max-w-3xl bg-blue-300 border-3 border-black p-6 shadow-neo mb-8 text-center">
                    <h2 className="text-2xl font-black uppercase mb-2 flex items-center justify-center gap-2">
                        <Shield className="w-8 h-8" /> Rematch Invite
                    </h2>
                    {isCreator ? (
                        <p className="font-bold">Waiting for your rival to accept the challenge.</p>
                    ) : (
                        <div className="flex flex-col items-center gap-4">
                            <p className="font-bold">You have been challenged to a rematch!</p>
                            <button
                                onClick={handleAcceptInvite}
                                className="btn-neo bg-neo-primary text-white px-6 py-2 font-black uppercase"
                            >
                                Accept Challenge
                            </button>
                        </div>
                    )}
                </div>
            )}

            <div className="w-full max-w-3xl space-y-8">
                {/* Opponent Display - RivalRadar for PVP, MonsterCard for Adventure */}
                {isAdventureMode ? (
                    <MonsterCard adventure={adventure} />
                ) : (
                    <RivalRadar battle={battle} />
                )}

                {/* Active Tasks (Hide if Pre-Battle or Pending) */}
                {!isPreBattle && !isPending && (
                    <section className="bg-neo-white border-3 border-black p-6 md:p-8 shadow-neo relative overflow-hidden">
                        <div className="absolute top-0 right-0 bg-neo-accent px-2 border-l-3 border-b-3 border-black font-bold text-xs">ACTIVE PROTOCOLS</div>
                        <h2 className="text-xl font-black uppercase mb-6 flex items-center gap-2">
                            <Zap className="w-6 h-6 text-neo-primary" /> Today's Objectives
                        </h2>

                        {tasks.length === 0 ? (
                            <div className="text-center py-8 border-2 border-dashed border-gray-300">
                                <p className="font-bold text-gray-400">NO TASKS ASSIGNED</p>
                                <p className="text-xs text-gray-400 mt-1">Did you forget to plan yesterday?</p>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                <AnimatePresence>
                                    {tasks.map((task) => (
                                        <motion.div
                                            key={task.id}
                                            layout
                                            initial={{ opacity: 0, y: 10 }}
                                            animate={{ opacity: 1, y: 0 }}
                                            exit={{ opacity: 0, scale: 0.9 }}
                                            className={`flex items-center gap-4 p-4 border-2 border-black transition-all ${task.is_completed
                                                ? 'bg-gray-100 opacity-50'
                                                : 'bg-white shadow-sm hover:shadow-md hover:-translate-y-1'
                                                }`}
                                        >
                                            <button
                                                onClick={() => toggleTask(task.id, !task.is_completed)}
                                                className={`w-8 h-8 border-2 border-black flex items-center justify-center transition-colors ${task.is_completed ? 'bg-neo-primary' : 'bg-white hover:bg-gray-100'
                                                    }`}
                                            >
                                                {task.is_completed && <Check className="w-5 h-5 text-white" />}
                                            </button>
                                            <span className={`flex-1 font-bold text-lg ${task.is_completed ? 'line-through text-gray-500' : ''}`}>
                                                {task.content}
                                            </span>
                                            {task.is_optional && (
                                                <span className="text-xs font-bold bg-yellow-200 px-2 py-1 border border-black">BONUS</span>
                                            )}
                                        </motion.div>
                                    ))}
                                </AnimatePresence>
                            </div>
                        )}
                    </section>
                )}

                {/* Planning Button (Hide if Last Day or Pending) */}
                {!isLastDay && !isPending && (
                    <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={() => navigate('/plan')}
                        className="w-full btn-neo bg-neo-secondary text-black py-6 text-2xl font-black uppercase tracking-widest shadow-neo hover:translate-x-1 hover:translate-y-1 hover:shadow-none flex items-center justify-center gap-3"
                    >
                        <Plus className="w-8 h-8" />
                        Plan Tomorrow
                    </motion.button>
                )}

                {isLastDay && (
                    <div className="w-full bg-red-100 border-3 border-black p-4 text-center font-bold text-red-600 shadow-neo">
                        ⚠️ FINAL DAY - NO PLANNING REQUIRED
                    </div>
                )}

                {/* Break Day Button (Adventure only, hide during PRE_ADVENTURE) */}
                {isAdventureMode && adventure && !isPreBattle && adventure.break_days_used < 2 && (
                    <motion.button
                        whileHover={{ scale: 1.02 }}
                        whileTap={{ scale: 0.98 }}
                        onClick={handleScheduleBreak}
                        className="w-full max-w-3xl btn-neo bg-yellow-300 text-black py-4 text-lg font-black uppercase tracking-wide flex items-center justify-center gap-2"
                    >
                        <Coffee className="w-5 h-5" />
                        Schedule Break ({2 - adventure.break_days_used} remaining)
                    </motion.button>
                )}
            </div>

            {/* Danger Zone: Surrender/Retreat */}
            {!isPending && (
                <div className="w-full max-w-3xl mt-8 mb-12 flex justify-center">
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={isAdventureMode ? handleRetreat : handleForfeit}
                        className="flex items-center gap-2 px-6 py-3 bg-red-500 text-white font-bold border-3 border-black shadow-neo hover:bg-red-600 transition-colors"
                        title={isAdventureMode ? "Retreat from Adventure" : "Surrender Battle"}
                    >
                        <Flag className="w-5 h-5 fill-white" />
                        {isAdventureMode ? 'RETREAT' : 'SURRENDER'}
                    </motion.button>
                </div>
            )}
        </main >
    );
}
