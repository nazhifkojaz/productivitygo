import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { motion, AnimatePresence } from 'framer-motion';
import { toast } from 'sonner';
import {
    Trophy, Flame, Shield, Zap, Check, Plus,
    Clock, User, Lock, Upload, AlertTriangle, Flag
} from 'lucide-react';
import RivalRadar from '../components/RivalRadar';

interface Task {
    id: string;
    content: string;
    is_completed: boolean;
    is_optional: boolean;
    assigned_score: number;
}

export default function Dashboard() {
    const { session, user } = useAuth();
    const navigate = useNavigate();
    const [battle, setBattle] = useState<any>(null);
    const [tasks, setTasks] = useState<Task[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        if (session?.access_token) {
            fetchDashboardData();
        }
    }, [session]);

    const fetchDashboardData = async () => {
        try {
            // 1. Get Current Battle
            const battleRes = await axios.get('/api/battles/current', {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
            const battleData = battleRes.data;
            setBattle(battleData);

            // 2. Get Today's Tasks (Only if IN_BATTLE or LAST_BATTLE_DAY)
            if (battleData.app_state === 'IN_BATTLE' || battleData.app_state === 'LAST_BATTLE_DAY') {
                const tasksRes = await axios.get('/api/tasks/today', {
                    headers: { Authorization: `Bearer ${session?.access_token}` }
                });
                setTasks(tasksRes.data);
            } else {
                setTasks([]);
            }

        } catch (error: any) {
            console.error("Failed to load dashboard", error);
            if (error.response?.status === 404) {
                // No active battle -> Show lobby/idle state
                setBattle(null);
                setTasks([]);
            }
        } finally {
            setLoading(false);
        }
    };

    const toggleTask = async (taskId: string, isCompleted: boolean) => {
        // Optimistic Update
        setTasks(prev => prev.map(t => t.id === taskId ? { ...t, is_completed: isCompleted } : t));

        try {
            if (isCompleted) {
                await axios.post(`/api/tasks/${taskId}/complete`, {}, {
                    headers: { Authorization: `Bearer ${session?.access_token}` }
                });
            } else {
                // Undo completion (if supported API-wise, currently only complete endpoint exists)
                // Assuming we can't undo for now or need undo endpoint.
                // For MVP, let's assume complete is one-way or add undo endpoint later.
                // Reverting optimistic update if not supported
                toast.error("Undoing tasks is not yet supported by the protocol.");
                setTasks(prev => prev.map(t => t.id === taskId ? { ...t, is_completed: !isCompleted } : t));
            }
        } catch (error) {
            console.error("Failed to update task", error);
            // Revert
            setTasks(prev => prev.map(t => t.id === taskId ? { ...t, is_completed: !isCompleted } : t));
        }
    };

    if (loading) return <div className="min-h-screen bg-neo-bg flex items-center justify-center font-black">INITIALIZING BATTLEFIELD...</div>;

    const appState = battle?.app_state || 'IN_BATTLE';
    const isPreBattle = appState === 'PRE_BATTLE';
    const isLastDay = appState === 'LAST_BATTLE_DAY';
    const isPending = appState === 'PENDING_ACCEPTANCE';
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

    return (
        <div className="min-h-screen bg-neo-bg p-4 md:p-8 pb-48 flex flex-col items-center">
            {/* Desktop Sidebar (Hidden on Mobile) */}
            <div className="hidden md:flex flex-col fixed left-0 top-0 bottom-0 w-64 bg-neo-white border-r-3 border-black p-6 z-40">
                <div className="flex items-center gap-3 font-black italic uppercase text-xl tracking-tighter mb-10">
                    <img src="/logo.svg" alt="Logo" className="w-10 h-10" />
                    <span>Productivity<span className="text-neo-primary">GO</span></span>
                </div>
            </div>
            {/* Header */}
            <header className="w-full max-w-3xl flex justify-between items-center mb-8">
                <div className="bg-neo-white border-3 border-black p-4 shadow-neo-sm">
                    <h1 className="text-2xl font-black italic uppercase">Battle <span className="text-neo-primary">Dashboard</span></h1>
                    <div className="text-xs font-bold text-gray-500">
                        {isPreBattle ? 'PREPARING FOR BATTLE' : isPending ? 'AWAITING RIVAL' : `ROUND ${battle?.rounds_played || 1} / 5`}
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
                        <AlertTriangle className="w-8 h-8" /> Battle Pending
                    </h2>
                    <p className="font-bold">The battle begins tomorrow! Prepare your protocols.</p>
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
                {/* Rival Radar */}
                <RivalRadar battle={battle} />

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
            </div>

            {/* Danger Zone: Surrender */}
            {!isPending && (
                <div className="w-full max-w-3xl mt-8 mb-12 flex justify-center">
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={handleForfeit}
                        className="flex items-center gap-2 px-6 py-3 bg-red-500 text-white font-bold border-3 border-black shadow-neo hover:bg-red-600 transition-colors"
                        title="Surrender Battle"
                    >
                        <Flag className="w-5 h-5 fill-white" />
                        SURRENDER
                    </motion.button>
                </div>
            )}
        </main>
    );
}
