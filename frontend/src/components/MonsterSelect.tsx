import { motion } from 'framer-motion';
import { RefreshCw, Loader } from 'lucide-react';
import type { Monster } from '../hooks/useMonsters';
import { getMonsterTypeMeta } from '../types/monster';

interface MonsterSelectProps {
    monsters: Monster[];
    refreshesRemaining: number;
    onSelect: (monsterId: string) => void;
    onRefresh: () => void;
    isLoading?: boolean;
    isRefreshing?: boolean;
}

/**
 * Tier-specific styling
 */
const TIER_STYLES: Record<string, { bg: string; border: string; badge: string }> = {
    easy: {
        bg: 'bg-green-100',
        border: 'border-green-500',
        badge: 'bg-green-500',
    },
    medium: {
        bg: 'bg-yellow-100',
        border: 'border-yellow-500',
        badge: 'bg-yellow-500',
    },
    hard: {
        bg: 'bg-orange-100',
        border: 'border-orange-500',
        badge: 'bg-orange-500',
    },
    expert: {
        bg: 'bg-red-100',
        border: 'border-red-500',
        badge: 'bg-red-500',
    },
    boss: {
        bg: 'bg-purple-100',
        border: 'border-purple-500',
        badge: 'bg-purple-500',
    },
};

/**
 * Monster selection grid for starting an adventure.
 *
 * Features:
 * - 2x2 grid of monster cards
 * - Refresh button (max 3 times)
 * - Tier-colored cards
 * - Click to select
 *
 * Usage:
 * ```tsx
 * <MonsterSelect
 *   monsters={pool.monsters}
 *   refreshesRemaining={pool.refreshes_remaining}
 *   onSelect={handleStartAdventure}
 *   onRefresh={handleRefresh}
 *   isLoading={startMutation.isPending}
 *   isRefreshing={refreshMutation.isPending}
 * />
 * ```
 */
export default function MonsterSelect({
    monsters,
    refreshesRemaining,
    onSelect,
    onRefresh,
    isLoading = false,
    isRefreshing = false,
}: MonsterSelectProps) {
    return (
        <div>
            {/* Header with Refresh Button */}
            <div className="flex justify-between items-center mb-4">
                <h3 className="font-black uppercase text-sm text-gray-600">
                    Choose Your Challenge
                </h3>
                <button
                    onClick={onRefresh}
                    disabled={refreshesRemaining <= 0 || isRefreshing}
                    className={`flex items-center gap-1 px-3 py-1 border-2 border-black font-bold text-sm transition-colors
                        ${refreshesRemaining > 0
                            ? 'bg-white hover:bg-gray-100'
                            : 'bg-gray-200 cursor-not-allowed opacity-50'
                        }`}
                    title={refreshesRemaining > 0 ? 'Get new monsters' : 'No refreshes left'}
                >
                    {isRefreshing ? (
                        <Loader className="w-4 h-4 animate-spin" />
                    ) : (
                        <RefreshCw className="w-4 h-4" />
                    )}
                    Refresh ({refreshesRemaining})
                </button>
            </div>

            {/* Monster Grid (2x2) */}
            <div className="grid grid-cols-2 gap-4">
                {monsters.map((monster) => {
                    const style = TIER_STYLES[monster.tier] || TIER_STYLES.easy;

                    return (
                        <motion.button
                            key={monster.id}
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={() => onSelect(monster.id)}
                            disabled={isLoading}
                            className={`p-4 border-3 border-black shadow-neo text-left relative
                                ${style.bg} ${style.border}
                                hover:translate-x-1 hover:translate-y-1 hover:shadow-none
                                disabled:opacity-50 disabled:cursor-not-allowed
                                transition-all duration-150`}
                        >
                            {/* Tier Badge */}
                            <span className={`absolute top-2 right-2 px-2 py-0.5 text-white text-[10px] font-bold uppercase ${style.badge}`}>
                                {monster.tier}
                            </span>

                            {/* Monster Info */}
                            <div className="flex items-center gap-3 mb-2">
                                <span className="text-3xl">{monster.emoji}</span>
                                <div className="min-w-0">
                                    <h4 className="font-black text-sm leading-tight truncate">
                                        {monster.name}
                                    </h4>
                                    <div className="flex items-center gap-2">
                                        {monster.monster_type && (
                                            <span className="text-xs font-bold text-gray-700">
                                                {getMonsterTypeMeta(monster.monster_type).emoji} {getMonsterTypeMeta(monster.monster_type).label}
                                            </span>
                                        )}
                                        <span className="text-xs font-bold text-gray-600">
                                            HP: {monster.base_hp}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* Description */}
                            <p className="text-xs text-gray-600 italic line-clamp-2">
                                "{monster.description}"
                            </p>
                        </motion.button>
                    );
                })}
            </div>

            {/* Loading Overlay */}
            {isLoading && (
                <div className="text-center py-4 font-bold text-gray-500">
                    <Loader className="w-6 h-6 animate-spin mx-auto mb-2" />
                    Starting adventure...
                </div>
            )}
        </div>
    );
}
