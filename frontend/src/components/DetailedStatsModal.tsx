import NeoModal from './NeoModal';
import { X, TrendingUp, Swords, Skull, Zap, Target, Trophy, Calendar, Activity, Star } from 'lucide-react';
import type { ProfileStats } from '../types/profile';
import { formatNumber, formatTierEmoji } from '../lib/formatters';

interface DetailedStatsModalProps {
    isOpen: boolean;
    stats: ProfileStats | null | undefined;
    createdAt?: string;
    onClose: () => void;
}

/**
 * Helper to calculate days active from created_at timestamp
 */
function calculateDaysActive(createdAt?: string): number {
    if (!createdAt) return 0;
    const created = new Date(createdAt);
    const now = new Date();
    const diffTime = Math.abs(now.getTime() - created.getTime());
    return Math.ceil(diffTime / (1000 * 60 * 60 * 24));
}

/**
 * Inner stat card component for the modal
 */
function StatCard({
    icon: Icon,
    label,
    value,
    color,
    bgColor
}: {
    icon: React.ComponentType<{ className?: string }>;
    label: string;
    value: string | number;
    color: string;
    bgColor: string;
}) {
    return (
        <div className={`flex items-center gap-3 p-3 ${bgColor} border-2 border-black rounded-lg`}>
            <div className={`p-2 ${color} border-2 border-black shadow-[2px_2px_0_0_#000]`}>
                <Icon className="w-4 h-4 text-white" />
            </div>
            <div className="flex-1">
                <div className="text-[10px] font-black uppercase text-gray-600">{label}</div>
                <div className="text-lg font-black">{value}</div>
            </div>
        </div>
    );
}

/**
 * DetailedStatsModal - Comprehensive stats breakdown
 *
 * Shows 3 sections: PvP, Adventure, General statistics
 * Supports frontend-calculated metrics (Days Active, Avg XP/Day)
 */
export default function DetailedStatsModal({ isOpen, stats, createdAt, onClose }: DetailedStatsModalProps) {
    if (!stats) return null;

    // Derived calculations
    const daysActive = calculateDaysActive(createdAt);
    const avgXpPerDay = daysActive > 0 ? Math.round((stats.total_xp || 0) / daysActive) : 0;
    const gamesPlayed = (stats.battle_fought || 0) + (stats.adventure_count || 0);
    const battleLosses = (stats.battle_fought || 0) - (stats.battle_wins || 0);
    const avgXpPerBattle = (stats.battle_fought || 0) > 0
        ? Math.round((stats.total_xp || 0) / (stats.battle_fought || 1))
        : 0;

    return (
        <NeoModal
            isOpen={isOpen}
            onClose={onClose}
            maxWidth="max-w-2xl"
            maxHeight="max-h-[90vh]"
            padding="p-0"
            showCloseButton={false}
            titleId="stats-modal-title"
            className="flex flex-col"
        >
            {/* Sticky Header */}
            <div className="sticky top-0 bg-black text-white px-6 py-4 border-b-4 border-black z-10 flex items-center justify-between">
                <h2 id="stats-modal-title" className="text-xl font-black uppercase flex items-center gap-2">
                    <TrendingUp className="w-6 h-6" aria-hidden="true" /> Detailed Statistics
                </h2>
                <button
                    onClick={onClose}
                    className="p-2 hover:bg-gray-800 border-2 border-white transition-colors"
                    aria-label="Close modal"
                >
                    <X className="w-5 h-5" />
                </button>
            </div>

            {/* Scrollable Content */}
            <div className="flex-1 overflow-y-auto p-6 space-y-8">
                {/* PvP Statistics */}
                <section aria-labelledby="pvp-stats-heading">
                    <h3 id="pvp-stats-heading" className="text-sm font-black uppercase text-gray-500 mb-4 flex items-center gap-2">
                        <Swords className="w-4 h-4" aria-hidden="true" /> PvP Statistics
                    </h3>
                    <div className="grid grid-cols-2 gap-3">
                        <StatCard
                            icon={Trophy}
                            label="Win Rate"
                            value={stats.win_rate || '0%'}
                            color="bg-[#2A9D8F]"
                            bgColor="bg-[#E8E4D9]"
                        />
                        <StatCard
                            icon={Activity}
                            label="PvP Record (W-L)"
                            value={`${stats.battle_wins ?? 0}-${battleLosses}`}
                            color="bg-[#457B9D]"
                            bgColor="bg-[#E8E4D9]"
                        />
                        <StatCard
                            icon={Target}
                            label="Total Battles"
                            value={stats.battle_fought ?? 0}
                            color="bg-[#F4A261]"
                            bgColor="bg-[#E8E4D9]"
                        />
                        <StatCard
                            icon={Zap}
                            label="Avg XP/Battle"
                            value={avgXpPerBattle}
                            color="bg-[#9D4EDD]"
                            bgColor="bg-[#E8E4D9]"
                        />
                    </div>
                </section>

                {/* Adventure Statistics */}
                <section aria-labelledby="adventure-stats-heading">
                    <h3 id="adventure-stats-heading" className="text-sm font-black uppercase text-gray-500 mb-4 flex items-center gap-2">
                        <Skull className="w-4 h-4" aria-hidden="true" /> Adventure Statistics
                    </h3>
                    <div className="grid grid-cols-2 gap-3">
                        <StatCard
                            icon={Star}
                            label="Monster Rating"
                            value={stats.monster_rating ?? 0}
                            color="bg-[#9D4EDD]"
                            bgColor="bg-[#E8E4D9]"
                        />
                        <StatCard
                            icon={Target}
                            label="Completion Rate"
                            value={stats.adventure_completion_rate || '0%'}
                            color="bg-[#2A9D8F]"
                            bgColor="bg-[#E8E4D9]"
                        />
                        <StatCard
                            icon={Skull}
                            label="Monsters Defeated"
                            value={stats.monster_defeats ?? 0}
                            color="bg-[#E63946]"
                            bgColor="bg-[#E8E4D9]"
                        />
                        <StatCard
                            icon={Activity}
                            label="Escaped"
                            value={stats.monster_escapes ?? 0}
                            color="bg-[#F4A261]"
                            bgColor="bg-[#E8E4D9]"
                        />
                        <StatCard
                            icon={Trophy}
                            label="Highest Tier"
                            value={`${formatTierEmoji(stats.highest_tier_reached)} ${(stats.highest_tier_reached || 'easy').toUpperCase()}`}
                            color="bg-[#457B9D]"
                            bgColor="bg-[#E8E4D9]"
                        />
                        <StatCard
                            icon={Zap}
                            label="Total Damage"
                            value={formatNumber(stats.total_damage_dealt)}
                            color="bg-[#E63946]"
                            bgColor="bg-[#E8E4D9]"
                        />
                        <StatCard
                            icon={Swords}
                            label="Avg Damage/Adventure"
                            value={stats.avg_damage_per_adventure ?? 0}
                            color="bg-[#F4A261]"
                            bgColor="bg-[#E8E4D9]"
                        />
                        <StatCard
                            icon={Target}
                            label="Total Adventures"
                            value={stats.adventure_count ?? 0}
                            color="bg-[#9D4EDD]"
                            bgColor="bg-[#E8E4D9]"
                        />
                    </div>
                </section>

                {/* General Statistics */}
                <section aria-labelledby="general-stats-heading">
                    <h3 id="general-stats-heading" className="text-sm font-black uppercase text-gray-500 mb-4 flex items-center gap-2">
                        <Zap className="w-4 h-4" aria-hidden="true" /> General Statistics
                    </h3>
                    <div className="grid grid-cols-2 gap-3">
                        <StatCard
                            icon={Zap}
                            label="Total XP"
                            value={stats.total_xp ?? 0}
                            color="bg-[#F4A261]"
                            bgColor="bg-[#E8E4D9]"
                        />
                        <StatCard
                            icon={Trophy}
                            label="Level"
                            value={Math.floor((stats.total_xp ?? 0) / 500) + 1}
                            color="bg-[#2A9D8F]"
                            bgColor="bg-[#E8E4D9]"
                        />
                        <StatCard
                            icon={Target}
                            label="Tasks Completed"
                            value={stats.tasks_completed ?? 0}
                            color="bg-[#457B9D]"
                            bgColor="bg-[#E8E4D9]"
                        />
                        <StatCard
                            icon={Calendar}
                            label="Days Active"
                            value={daysActive}
                            color="bg-[#9D4EDD]"
                            bgColor="bg-[#E8E4D9]"
                        />
                        <StatCard
                            icon={TrendingUp}
                            label="Avg XP/Day"
                            value={avgXpPerDay}
                            color="bg-[#2A9D8F]"
                            bgColor="bg-[#E8E4D9]"
                        />
                        <StatCard
                            icon={Activity}
                            label="Games Played"
                            value={gamesPlayed}
                            color="bg-[#F4A261]"
                            bgColor="bg-[#E8E4D9]"
                        />
                    </div>
                </section>
            </div>

            {/* Footer */}
            <div className="border-t-3 border-black p-4 bg-[#E8E4D9]">
                <button
                    onClick={onClose}
                    className="w-full py-3 bg-white border-3 border-black font-black uppercase shadow-[4px_4px_0_0_#000] hover:translate-y-0.5 hover:shadow-[2px_2px_0_0_#000] transition-all active:translate-y-1 active:shadow-none"
                >
                    Close
                </button>
            </div>
        </NeoModal>
    );
}
