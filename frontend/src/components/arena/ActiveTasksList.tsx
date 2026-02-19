/**
 * ActiveTasksList Component
 *
 * Displays the list of active tasks for the current day.
 * Shows task completion status with animations and point values.
 *
 * REFACTOR-005: Phase 5 - Week 3 - Arena.tsx Refactoring
 */

import { motion, AnimatePresence } from 'framer-motion';
import { Zap, Check } from 'lucide-react';
import type { Task } from '../../types/task';
import { getTaskCategoryMeta } from '../../types/task';

export interface ActiveTasksListProps {
    tasks: Task[];
    onToggleTask: (taskId: string, complete: boolean) => void;
}

export default function ActiveTasksList({ tasks, onToggleTask }: ActiveTasksListProps) {
    const completedCount = tasks.filter((t) => t.is_completed).length;

    return (
        <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000]">
            <div className="bg-black text-white p-4 border-b-4 border-black flex items-center justify-between">
                <h2 className="text-xl font-black uppercase flex items-center gap-2">
                    <Zap className="w-6 h-6" /> Active Protocols
                </h2>
                <span className="font-mono text-sm">
                    {completedCount}/{tasks.length} COMPLETE
                </span>
            </div>

            <div className="p-4 space-y-3">
                {tasks.length === 0 ? (
                    <div className="text-center py-8 border-2 border-dashed border-gray-300">
                        <p className="font-bold text-gray-400">NO TASKS ASSIGNED</p>
                        <p className="text-xs text-gray-400 mt-1">
                            Did you forget to plan yesterday?
                        </p>
                    </div>
                ) : (
                    <AnimatePresence>
                        {tasks.map((task, index) => (
                            <motion.div
                                key={task.id || `task-${index}`}
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
                                onClick={() => onToggleTask(task.id, !task.is_completed)}
                            >
                                <span className="font-mono text-xl font-black text-gray-400 w-6">
                                    0{index + 1}
                                </span>

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

                                <span
                                    className={`flex-1 font-bold ${
                                        task.is_completed ? 'line-through text-gray-500' : ''
                                    }`}
                                >
                                    {task.content}
                                </span>

                                <span
                                    className={`px-2 py-1 text-xs font-black border-2 border-black ${
                                        task.is_optional
                                            ? 'bg-[#F4A261]'
                                            : 'bg-[#E63946] text-white'
                                    }`}
                                >
                                    {task.is_optional ? '+5 BONUS' : '+10'}
                                </span>
                            </motion.div>
                        ))}
                    </AnimatePresence>
                )}
            </div>
        </div>
    );
}
