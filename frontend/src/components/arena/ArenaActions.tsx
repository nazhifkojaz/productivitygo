/**
 * ArenaActions Component
 *
 * Contains the action buttons for planning tomorrow, scheduling breaks,
 * and surrendering/retreating from battle/adventure.
 *
 * REFACTOR-005: Phase 5 - Week 3 - Arena.tsx Refactoring
 */

import { motion } from 'framer-motion';
import { Plus, Coffee, Flag } from 'lucide-react';
import type { ArenaMode, Adventure } from '../../types/arena';

export interface ArenaActionsProps {
    mode: ArenaMode;
    isLastDay: boolean;
    isPending: boolean;
    adventure?: Adventure | null;
    onPlanTomorrow: () => void;
    onScheduleBreak: () => void;
    onForfeitOrRetreat: () => void;
}

export default function ArenaActions({
    mode,
    isLastDay,
    isPending,
    adventure,
    onPlanTomorrow,
    onScheduleBreak,
    onForfeitOrRetreat,
}: ArenaActionsProps) {
    const isAdventure = mode === 'adventure';
    const canScheduleBreak =
        isAdventure && adventure && adventure.break_days_used < 2;

    return (
        <>
            {/* Planning Button */}
            {!isLastDay && !isPending && (
                <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={onPlanTomorrow}
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
            {canScheduleBreak && (
                <motion.button
                    whileHover={{ scale: 1.02 }}
                    whileTap={{ scale: 0.98 }}
                    onClick={onScheduleBreak}
                    className="w-full bg-yellow-300 border-3 border-black p-4 text-lg font-black uppercase shadow-[4px_4px_0_0_#000] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0_0_#000] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none transition-all flex items-center justify-center gap-2"
                >
                    <Coffee className="w-5 h-5" />
                    Schedule Break ({2 - (adventure?.break_days_used || 0)} remaining)
                </motion.button>
            )}

            {/* Forfeit/Retreat Button */}
            {!isPending && (
                <button
                    onClick={onForfeitOrRetreat}
                    className="w-full bg-[#E63946] border-3 border-black p-4 font-bold uppercase text-white shadow-[4px_4px_0_0_#000] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0_0_#000] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none transition-all flex items-center justify-center gap-2"
                >
                    <Flag className="w-5 h-5" />{' '}
                    {isAdventure ? 'RETREAT' : 'SURRENDER BATTLE'}
                </button>
            )}
        </>
    );
}
