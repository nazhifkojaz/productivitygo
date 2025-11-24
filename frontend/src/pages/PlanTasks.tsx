import React, { useState, useEffect } from 'react';
import { ArrowLeft, Lock, Star, Save, Clock } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { TasksService, type TaskCreate } from '../api';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';

export default function PlanTasks() {
    const navigate = useNavigate();
    const { session } = useAuth();
    const [mandatoryTasks, setMandatoryTasks] = useState<string[]>([]);
    const [optionalTasks, setOptionalTasks] = useState<string[]>(['', '']);
    const [quota, setQuota] = useState<number>(0);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);
    const [timeLeft, setTimeLeft] = useState<string>("");

    useEffect(() => {
        if (session?.access_token) {
            loadData();
        }

        // Countdown Timer
        const timer = setInterval(() => {
            const now = new Date();
            const tomorrow = new Date(now);
            tomorrow.setDate(tomorrow.getDate() + 1);
            tomorrow.setHours(0, 0, 0, 0);

            const diff = tomorrow.getTime() - now.getTime();
            const hours = Math.floor(diff / (1000 * 60 * 60));
            const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((diff % (1000 * 60)) / 1000);

            setTimeLeft(`${hours}h ${minutes}m ${seconds}s`);
        }, 1000);

        return () => clearInterval(timer);
    }, [session]);

    const loadData = async () => {
        if (!session?.access_token) return;
        try {
            // 1. Get Quota
            const quotaRes = await axios.get('/api/tasks/quota', {
                headers: { Authorization: `Bearer ${session.access_token}` }
            });
            const q = quotaRes.data.quota;
            setQuota(q);

            // 2. Get Existing Draft
            const draftRes = await axios.get('/api/tasks/draft', {
                headers: { Authorization: `Bearer ${session.access_token}` }
            });

            const existingTasks = draftRes.data;

            // Initialize Mandatory
            const existingMandatory = existingTasks.filter((t: any) => !t.is_optional).map((t: any) => t.content);
            const mandatoryFill = new Array(q).fill('');
            existingMandatory.forEach((content: string, i: number) => {
                if (i < q) mandatoryFill[i] = content;
            });
            setMandatoryTasks(mandatoryFill);

            // Initialize Optional
            const existingOptional = existingTasks.filter((t: any) => t.is_optional).map((t: any) => t.content);
            const optionalFill = new Array(2).fill('');
            existingOptional.forEach((content: string, i: number) => {
                if (i < 2) optionalFill[i] = content;
            });
            setOptionalTasks(optionalFill);

        } catch (error) {
            console.error("Failed to load data", error);
            // Fallback if quota fails
            setQuota(3);
            setMandatoryTasks(['', '', '']);
        } finally {
            setLoading(false);
        }
    };

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

    const isValid = mandatoryTasks.every(t => t.trim().length > 0);

    const handleSave = async () => {
        if (!isValid) return;
        setSubmitting(true);

        try {
            const tasksToSubmit: TaskCreate[] = [
                ...mandatoryTasks.map(content => ({ content, is_optional: false })),
                ...optionalTasks.filter(t => t.trim()).map(content => ({ content, is_optional: true }))
            ];

            await axios.post('/api/tasks/draft', tasksToSubmit, {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
            alert("Plan saved successfully! You can edit this until midnight.");
        } catch (error) {
            console.error("Failed to save tasks", error);
            alert("Failed to save plan.");
        } finally {
            setSubmitting(false);
        }
    };

    if (loading) return <div className="min-h-screen bg-neo-bg flex items-center justify-center font-black">LOADING PLAN...</div>;

    return (
        <div className="min-h-screen bg-neo-bg p-4 md:p-8 pb-24 flex flex-col items-center">
            {/* Header */}
            <header className="w-full max-w-3xl flex items-stretch gap-4 mb-8">
                <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => navigate('/dashboard')}
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
                        * The system has assigned {quota} mandatory slots for tomorrow. All must be filled.
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

                    <div className="space-y-4">
                        {optionalTasks.map((task, index) => (
                            <div key={index} className="flex gap-3 items-center">
                                <span className="font-black text-2xl w-8 text-gray-500 select-none">+</span>
                                <input
                                    type="text"
                                    value={task}
                                    onChange={(e) => updateOptionalTask(index, e.target.value)}
                                    className="flex-1 input-neo bg-white/90 text-lg font-bold"
                                    placeholder="Enter bonus task..."
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
                    disabled={!isValid || submitting}
                    className="w-full btn-neo bg-neo-primary text-white py-5 text-2xl font-black uppercase tracking-widest shadow-neo hover:translate-x-1 hover:translate-y-1 hover:shadow-none disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center justify-center gap-2"
                >
                    <Save className="w-6 h-6" />
                    {submitting ? 'Saving...' : 'Save Plan'}
                </motion.button>

                <p className="text-center text-xs font-bold text-gray-400">
                    Plan auto-locks at midnight.
                </p>

            </div>
        </div>
    );
}
