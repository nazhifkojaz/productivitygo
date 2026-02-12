import { useState, useEffect } from 'react';
import { ArrowLeft, Lock, Star, Save, Clock, Info, X } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import type { TaskCreate, TaskCategory } from '../types';
import { useProfile } from '../hooks/useProfile';
import { useTaskQuota } from '../hooks/useTaskQuota';
import { useTaskDraft } from '../hooks/useTaskDraft';
import { useTaskMutations } from '../hooks/useTaskMutations';
import { TASK_CATEGORIES } from '../types/task';

interface TaskInput {
    content: string;
    category: TaskCategory;
}

export default function PlanTasks() {
    const navigate = useNavigate();
    const { data: profile } = useProfile();
    const [mandatoryTasks, setMandatoryTasks] = useState<TaskInput[]>([]);
    const [optionalTasks, setOptionalTasks] = useState<TaskInput[]>([
        { content: '', category: 'errand' },
        { content: '', category: 'errand' }
    ]);
    const [timeLeft, setTimeLeft] = useState<string>("");
    const [initializedQuota, setInitializedQuota] = useState<number | null>(null);
    const [showCategoryInfo, setShowCategoryInfo] = useState(false);

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
            // No draft tasks, initialize with empty objects
            const mandatoryFill = new Array(quota).fill(null).map(() => ({ content: '', category: 'errand' as TaskCategory }));
            setMandatoryTasks(mandatoryFill);
            setOptionalTasks([
                { content: '', category: 'errand' },
                { content: '', category: 'errand' }
            ]);
            setInitializedQuota(quota);
            return;
        }

        // Initialize Mandatory tasks from draft
        const existingMandatory = draftTasks.filter((t: TaskCreate) => !t.is_optional);
        const mandatoryFill = new Array(quota).fill(null).map(() => ({ content: '', category: 'errand' as TaskCategory }));
        existingMandatory.forEach((t: TaskCreate, i: number) => {
            if (i < quota) {
                mandatoryFill[i] = {
                    content: t.content,
                    category: t.category || 'errand'
                };
            }
        });
        setMandatoryTasks(mandatoryFill);

        // Initialize Optional tasks from draft
        const existingOptional = draftTasks.filter((t: TaskCreate) => t.is_optional);
        const optionalFill = [
            { content: '', category: 'errand' as TaskCategory },
            { content: '', category: 'errand' as TaskCategory }
        ];
        existingOptional.forEach((t: TaskCreate, i: number) => {
            if (i < 2) {
                optionalFill[i] = {
                    content: t.content,
                    category: t.category || 'errand'
                };
            }
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

            setTimeLeft(`${hours.toString().padStart(2, '0')}:${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`);
        }, 1000);

        return () => clearInterval(timer);
    }, [userTimezone]);

    const updateMandatoryTask = (index: number, field: 'content' | 'category', value: string) => {
        const newTasks = [...mandatoryTasks];
        if (field === 'category') {
            newTasks[index] = { ...newTasks[index], category: value as TaskCategory };
        } else {
            newTasks[index] = { ...newTasks[index], content: value };
        }
        setMandatoryTasks(newTasks);
    };

    const updateOptionalTask = (index: number, field: 'content' | 'category', value: string) => {
        const newTasks = [...optionalTasks];
        if (field === 'category') {
            newTasks[index] = { ...newTasks[index], category: value as TaskCategory };
        } else {
            newTasks[index] = { ...newTasks[index], content: value };
        }
        setOptionalTasks(newTasks);
    };

    // Calculate filled mandatory task count
    const filledMandatoryCount = mandatoryTasks.filter(t => t.content.trim().length > 0).length;
    const isMandatoryComplete = filledMandatoryCount === quota;

    // Relaxed validation: Allow saving if at least one task (mandatory or optional) is filled
    const isValid = mandatoryTasks.some(t => t.content.trim().length > 0) || optionalTasks.some(t => t.content.trim().length > 0);

    const handleSave = async () => {
        if (!isValid) return;

        // Filter out empty mandatory tasks before submitting
        const tasksToSubmit: TaskCreate[] = [
            ...mandatoryTasks.filter(t => t.content.trim().length > 0).map(t => ({
                content: t.content,
                category: t.category,
                is_optional: false,
            })),
            ...optionalTasks.filter(t => t.content.trim()).map(t => ({
                content: t.content,
                category: t.category,
                is_optional: true,
            }))
        ];

        await saveDraftMutation.mutateAsync(tasksToSubmit);
    };

    if (loading) return <div className="min-h-screen bg-[#E8E4D9] neo-grid-bg flex items-center justify-center font-black">LOADING PLAN...</div>;

    return (
        <div className="min-h-screen bg-[#E8E4D9] neo-grid-bg p-4 md:p-8">
            {/* Header */}
            <div className="max-w-3xl mx-auto mb-6">
                <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000] p-4 flex items-center gap-4">
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => navigate('/arena')}
                        className="p-3 bg-black text-white border-3 border-black shadow-[3px_3px_0_0_#000] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0_0_#000] transition-all"
                    >
                        <ArrowLeft className="w-6 h-6" />
                    </motion.button>

                    <div className="flex-1 flex items-center gap-3">
                        <button
                            onClick={() => setShowCategoryInfo(true)}
                            className="p-2 bg-gray-100 border-2 border-black hover:bg-gray-200 transition-colors"
                            title="View Category Info"
                        >
                            <Info className="w-4 h-4" />
                        </button>
                        <div>
                            <h1 className="text-2xl font-black uppercase">Plan Tomorrow</h1>
                            <p className="text-xs font-mono text-gray-500">// DEFINE YOUR OBJECTIVES</p>
                        </div>
                    </div>

                    <div className="text-right">
                        <div className="text-xs font-black uppercase font-mono text-gray-500">LOCKS IN</div>
                        <div className="font-mono font-black text-lg">{timeLeft}</div>
                    </div>
                </div>
            </div>

            <div className="max-w-3xl mx-auto space-y-6">
                {/* Mandatory Tasks */}
                <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000]">
                    <div className="bg-black text-white p-4 border-b-4 border-black flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Lock className="w-5 h-5" />
                            <span className="text-sm font-black uppercase">Core Objectives</span>
                        </div>
                        <div className="flex items-center gap-2">
                            <span className="text-xs font-mono">{filledMandatoryCount}/{quota} FILLED</span>
                            <span className="bg-[#F4A261] px-2 py-0.5 text-xs font-black border-2 border-white">+10 XP</span>
                        </div>
                    </div>

                    <div className="p-6 space-y-3">
                        {mandatoryTasks.map((task, index) => (
                            <div key={index} className="flex items-center gap-3">
                                <span className="text-2xl font-black text-gray-400 w-8 text-center flex-shrink-0">0{index + 1}</span>
                                <select
                                    value={task.category}
                                    onChange={(e) => updateMandatoryTask(index, 'category', e.target.value)}
                                    className="flex-shrink-0 w-36 border-3 border-black p-2 font-bold text-sm focus:outline-none focus:shadow-[3px_3px_0_0_#E63946] transition-all bg-white"
                                >
                                    {TASK_CATEGORIES.map(cat => (
                                        <option key={cat.key} value={cat.key}>
                                            {cat.emoji} {cat.label}
                                        </option>
                                    ))}
                                </select>
                                <div className="flex-1 relative">
                                    <input
                                        type="text"
                                        value={task.content}
                                        onChange={(e) => updateMandatoryTask(index, 'content', e.target.value)}
                                        className="w-full border-3 border-black p-3 font-bold focus:outline-none focus:shadow-[4px_4px_0_0_#E63946] transition-all"
                                        placeholder="Enter critical task..."
                                        autoFocus={index === 0}
                                    />
                                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-mono font-bold text-[#F4A261]">+10 XP</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Optional Tasks */}
                <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000]">
                    <div className="bg-[#9D4EDD] text-white p-4 border-b-4 border-black flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <Star className="w-5 h-5" />
                            <span className="text-sm font-black uppercase">Bonus Objectives</span>
                        </div>
                        <span className="bg-white px-2 py-0.5 text-xs font-black border-2 border-white text-[#9D4EDD]">+5 XP</span>
                    </div>

                    {!isMandatoryComplete && (
                        <div className="bg-[#F4A261] border-3 border-black p-3 text-center">
                            <p className="font-bold text-sm">
                                ⚠️ Fill all {quota} required tasks to unlock bonus objectives ({filledMandatoryCount}/{quota} filled)
                            </p>
                        </div>
                    )}

                    <div className={`p-6 space-y-3 ${!isMandatoryComplete ? 'opacity-50 pointer-events-none' : ''}`}>
                        {optionalTasks.map((task, index) => (
                            <div key={index} className="flex items-center gap-3">
                                <span className="text-2xl font-black text-gray-400 w-8 text-center flex-shrink-0">+</span>
                                <select
                                    value={task.category}
                                    onChange={(e) => updateOptionalTask(index, 'category', e.target.value)}
                                    className="flex-shrink-0 w-36 border-3 border-black p-2 font-bold text-sm focus:outline-none focus:shadow-[3px_3px_0_0_#9D4EDD] transition-all bg-white"
                                    disabled={!isMandatoryComplete}
                                >
                                    {TASK_CATEGORIES.map(cat => (
                                        <option key={cat.key} value={cat.key}>
                                            {cat.emoji} {cat.label}
                                        </option>
                                    ))}
                                </select>
                                <div className="flex-1 relative">
                                    <input
                                        type="text"
                                        value={task.content}
                                        onChange={(e) => updateOptionalTask(index, 'content', e.target.value)}
                                        className="w-full border-3 border-black p-3 font-bold focus:outline-none focus:shadow-[4px_4px_0_0_#9D4EDD] transition-all bg-white"
                                        placeholder="Enter bonus task..."
                                        disabled={!isMandatoryComplete}
                                    />
                                    <span className="absolute right-3 top-1/2 -translate-y-1/2 text-xs font-mono font-bold text-[#9D4EDD]">+5 XP</span>
                                </div>
                            </div>
                        ))}
                    </div>
                </div>

                {/* Progress Card */}
                <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000] p-4">
                    <div className="flex items-center justify-center gap-4">
                        <div className="text-center">
                            <div className="text-xs font-mono font-bold text-gray-500">PROGRESS</div>
                            <div className="text-2xl font-black">{filledMandatoryCount}/{quota} CORE</div>
                        </div>
                        <div className="flex-1 h-4 bg-gray-200 border-2 border-black">
                            <div
                                className="h-full bg-[#2A9D8F] transition-all"
                                style={{ width: `${(filledMandatoryCount / quota) * 100}%` }}
                            />
                        </div>
                    </div>
                </div>

                {/* Save Button */}
                <motion.button
                    whileHover={{ scale: 1.01 }}
                    whileTap={{ scale: 0.99 }}
                    onClick={handleSave}
                    disabled={!isValid || isSaving}
                    className={`w-full border-3 border-black p-4 font-black uppercase text-white shadow-[4px_4px_0_0_#000] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0_0_#000] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none transition-all flex items-center justify-center gap-2 text-lg ${
                        !isValid || isSaving ? 'bg-gray-300 cursor-not-allowed' : 'bg-[#E63946]'
                    }`}
                >
                    {isSaving ? (
                        <>
                            <Clock className="w-5 h-5 animate-spin" />
                            SAVING...
                        </>
                    ) : (
                        <>
                            <Save className="w-5 h-5" />
                            [ SAVE PLAN ]
                        </>
                    )}
                </motion.button>

                {/* Footer */}
                <div className="text-center">
                    <p className="text-xs font-mono font-bold text-gray-500">
                        [ PLAN AUTO-LOCKS AT MIDNIGHT ]
                    </p>
                </div>
            </div>

            {/* Category Info Modal */}
            {showCategoryInfo && (
                <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50" onClick={() => setShowCategoryInfo(false)}>
                    <div
                        className="bg-white border-4 border-black shadow-[8px_8px_0_0_#000] w-full max-w-lg max-h-[80vh] overflow-y-auto"
                        onClick={(e) => e.stopPropagation()}
                    >
                        {/* Modal Header */}
                        <div className="bg-black text-white p-4 border-b-4 border-black flex items-center justify-between">
                            <h2 className="text-lg font-black uppercase">Task Categories</h2>
                            <button
                                onClick={() => setShowCategoryInfo(false)}
                                className="p-1 hover:bg-gray-800 transition-colors"
                            >
                                <X className="w-5 h-5" />
                            </button>
                        </div>

                        {/* Categories List */}
                        <div className="p-6 space-y-4">
                            {TASK_CATEGORIES.map((cat) => (
                                <div
                                    key={cat.key}
                                    className="flex items-start gap-4 p-4 border-2 border-black bg-gray-50"
                                >
                                    <span className="text-3xl">{cat.emoji}</span>
                                    <div className="flex-1">
                                        <div className="flex items-center gap-2 mb-1">
                                            <h3 className="font-black uppercase">{cat.label}</h3>
                                            <span className="px-2 py-0.5 text-xs font-bold border border-black bg-white">
                                                {cat.element}
                                            </span>
                                        </div>
                                        <p className="text-sm text-gray-600">{cat.description}</p>
                                    </div>
                                </div>
                            ))}

                            {/* Footer Info */}
                            <div className="mt-6 p-4 bg-[#2A9D8F] border-2 border-black text-white text-center">
                                <p className="font-bold text-sm">
                                    Different elements are more or less effective against different monster types.
                                </p>
                                <p className="text-xs mt-1">
                                    Discover weaknesses through combat!
                                </p>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
