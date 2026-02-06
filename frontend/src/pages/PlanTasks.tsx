import { useState, useEffect } from 'react';
import { ArrowLeft, Lock, Star, Save, Clock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import type { TaskCreate } from '../types';
import { motion, AnimatePresence } from 'framer-motion';
import { useProfile } from '../hooks/useProfile';
import { useTaskQuota } from '../hooks/useTaskQuota';
import { useTaskDraft } from '../hooks/useTaskDraft';
import { useTaskMutations } from '../hooks/useTaskMutations';

export default function PlanTasks() {
    const navigate = useNavigate();
    const { data: profile } = useProfile();
    const [mandatoryTasks, setMandatoryTasks] = useState<string[]>([]);
    const [optionalTasks, setOptionalTasks] = useState<string[]>(['', '']);
    const [timeLeft, setTimeLeft] = useState<string>("");
    const [initializedQuota, setInitializedQuota] = useState<number | null>(null);

    const userTimezone = profile?.timezone || 'UTC';

    // Use React Query hooks for data fetching
    const { data: quota = 3, isLoading: quotaLoading } = useTaskQuota();
    const { data: draftTasks = [], isLoading: draftLoading } = useTaskDraft();
    const { saveDraftMutation, isSaving } = useTaskMutations();

    const loading = quotaLoading || draftLoading;

    // Populate form from draft tasks when data changes
    useEffect(() => {
        // Skip if already initialized for this quota value to prevent infinite loop
        if (initializedQuota === quota) return;

        if (draftTasks.length === 0) {
            // No draft tasks, initialize with empty strings
            const mandatoryFill = new Array(quota).fill('');
            setMandatoryTasks(mandatoryFill);
            setOptionalTasks(['', '']);
            setInitializedQuota(quota);
            return;
        }

        // Initialize Mandatory tasks from draft
        const existingMandatory = draftTasks.filter((t: TaskCreate) => !t.is_optional).map((t: TaskCreate) => t.content);
        const mandatoryFill = new Array(quota).fill('');
        existingMandatory.forEach((content: string, i: number) => {
            if (i < quota) mandatoryFill[i] = content;
        });
        setMandatoryTasks(mandatoryFill);

        // Initialize Optional tasks from draft
        const existingOptional = draftTasks.filter((t: TaskCreate) => t.is_optional).map((t: TaskCreate) => t.content);
        const optionalFill = new Array(2).fill('');
        existingOptional.forEach((content: string, i: number) => {
            if (i < 2) optionalFill[i] = content;
        });
        setOptionalTasks(optionalFill);
        setInitializedQuota(quota);
    }, [draftTasks, quota, initializedQuota]);

    // Countdown Timer - separate effect to use userTimezone
    useEffect(() => {
        const timer = setInterval(() => {
            // Calculate midnight in user's timezone
            const now = new Date();

            // Get current time in user's timezone
            const userNowStr = now.toLocaleString('en-US', { timeZone: userTimezone });
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

            setTimeLeft(`${hours}h ${minutes}m ${seconds}s`);
        }, 1000);

        return () => clearInterval(timer);
    }, [userTimezone]);

    const updateMandatoryTask = (index: number, value: string) => {
        const newTasks = [...mandatoryTasks];
        newTasks[index] = value;
        setMandatoryTasks(newTasks);
    };

    const updateOptionalTask = (index: number, value: string) => {
        const newTasks = [...optionalTasks];
        newTasks[index] = value;
        setOptionalTasks(newTasks);
    };

    // Calculate filled mandatory task count
    const filledMandatoryCount = mandatoryTasks.filter(t => t.trim().length > 0).length;
    const isMandatoryComplete = filledMandatoryCount === quota;

    // Relaxed validation: Allow saving if at least one task (mandatory or optional) is filled
    const isValid = mandatoryTasks.some(t => t.trim().length > 0) || optionalTasks.some(t => t.trim().length > 0);

    const handleSave = async () => {
        if (!isValid) return;

        // Filter out empty mandatory tasks before submitting
        // Empty optional tasks are already filtered
        const tasksToSubmit: TaskCreate[] = [
            ...mandatoryTasks.filter(t => t.trim().length > 0).map(content => ({ content, is_optional: false, assigned_score: 10 })),
            ...optionalTasks.filter(t => t.trim()).map(content => ({ content, is_optional: true, assigned_score: 5 }))
        ];

        await saveDraftMutation.mutateAsync(tasksToSubmit);
    };

    if (loading) return <div className="min-h-screen bg-neo-bg flex items-center justify-center font-black">LOADING PLAN...</div>;

    return (
        <div className="min-h-screen bg-neo-bg p-4 md:p-8 pb-24 flex flex-col items-center">
            {/* Header */}
            <header className="w-full max-w-3xl flex items-stretch gap-4 mb-8">
                <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => navigate('/arena')}
                    className="flex btn-neo px-4 md:px-6 bg-white items-center justify-center"
                >
                    <ArrowLeft className="w-6 h-6 md:w-8 md:h-8" />
                </motion.button>
                <div className="bg-neo-white border-3 border-black p-4 shadow-neo-sm flex-1 text-center md:text-left relative overflow-hidden flex flex-col justify-center">
                    <div className="absolute top-0 right-0 bg-neo-accent px-2 border-l-3 border-b-3 border-black font-bold text-xs flex items-center gap-1">
                        <Clock className="w-3 h-3" /> {timeLeft}
                    </div>
                    <h1 className="text-2xl font-black italic uppercase">Plan <span className="text-neo-primary">Tomorrow</span></h1>
                </div>
            </header>

            <div className="w-full max-w-3xl space-y-8">

                {/* Mandatory Tasks */}
                <section className="bg-neo-white border-3 border-black p-6 md:p-8 shadow-neo relative">
                    <div className="flex justify-between items-center mb-6 border-b-3 border-black pb-4">
                        <h2 className="text-xl font-black uppercase flex items-center gap-2">
                            <Lock className="w-6 h-6" /> Core Objectives
                        </h2>
                        <span className="text-xs font-bold bg-neo-accent px-2 py-1 border-2 border-black shadow-sm">REQUIRED ({quota})</span>
                    </div>

                    <div className="space-y-4">
                        <AnimatePresence>
                            {mandatoryTasks.map((task, index) => (
                                <motion.div
                                    key={index}
                                    initial={{ opacity: 0, x: -20 }}
                                    animate={{ opacity: 1, x: 0 }}
                                    className="flex gap-3 items-center"
                                >
                                    <span className="font-black text-2xl w-8 text-gray-300 select-none">0{index + 1}</span>
                                    <input
                                        type="text"
                                        value={task}
                                        onChange={(e) => updateMandatoryTask(index, e.target.value)}
                                        className="flex-1 input-neo text-lg font-bold"
                                        placeholder="Enter critical task..."
                                        autoFocus={index === 0}
                                    />
                                </motion.div>
                            ))}
                        </AnimatePresence>
                    </div>
                    <p className="mt-4 text-xs font-bold text-gray-500 text-center">
                        * Up to {quota} mandatory tasks available. Fill at least one to save.
                    </p>
                </section>

                {/* Optional Tasks */}
                <section className="bg-neo-secondary border-3 border-black p-6 md:p-8 shadow-neo">
                    <div className="flex justify-between items-center mb-6 border-b-3 border-black pb-4">
                        <h2 className="text-xl font-black uppercase flex items-center gap-2">
                            <Star className="w-6 h-6" /> Bonus Objectives
                        </h2>
                        <span className="text-xs font-bold bg-white px-2 py-1 border-2 border-black shadow-sm">OPTIONAL (MAX 2)</span>
                    </div>

                    {!isMandatoryComplete && (
                        <div className="bg-yellow-100 border-2 border-yellow-400 p-4 mb-4 text-center">
                            <p className="font-bold text-sm text-yellow-800">
                                ⚠️ Fill all {quota} required tasks to unlock bonus objectives ({filledMandatoryCount}/{quota} filled)
                            </p>
                        </div>
                    )}

                    <div className={`space-y-4 ${!isMandatoryComplete ? 'opacity-50 pointer-events-none' : ''}`}>
                        {optionalTasks.map((task, index) => (
                            <div key={index} className="flex gap-3 items-center">
                                <span className="font-black text-2xl w-8 text-gray-500 select-none">+</span>
                                <input
                                    type="text"
                                    value={task}
                                    onChange={(e) => updateOptionalTask(index, e.target.value)}
                                    className="flex-1 input-neo bg-white/90 text-lg font-bold"
                                    placeholder="Enter bonus task..."
                                    disabled={!isMandatoryComplete}
                                />
                            </div>
                        ))}
                    </div>
                </section>

                {/* Save Button */}
                <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={handleSave}
                    disabled={!isValid || isSaving}
                    className="w-full btn-neo bg-neo-primary text-white py-5 text-2xl font-black uppercase tracking-widest shadow-neo hover:translate-x-1 hover:translate-y-1 hover:shadow-none disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
                >
                    <Save className="w-6 h-6" />
                    {isSaving ? 'Saving...' : 'Save Plan'}
                </motion.button>

                <p className="text-center text-xs font-bold text-gray-400">
                    Plan auto-locks at midnight.
                </p>

            </div>
        </div>
    );
}
