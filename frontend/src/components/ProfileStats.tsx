import { Trophy, Star, Target, Swords, Skull, Zap } from 'lucide-react';
import { formatNumber } from '../lib/formatters';

interface ProfileStatsProps {
    stats?: {
        battle_wins?: number;
        total_xp?: number;
        battle_fought?: number;
        tasks_completed?: number;
        current_streak?: number;

        // Adventure stats (Feature 3)
        monster_rating?: number;
        monster_defeats?: number;
        monster_escapes?: number;
        adventure_count?: number;
        highest_tier_reached?: string;
        total_damage_dealt?: number;
        adventure_completion_rate?: string;
        avg_damage_per_adventure?: number;
    } | null;
    className?: string;
}

/**
 * ProfileStats component - Feature 3 Design
 *
 * Displays 6 stat cards: 3 PvP highlights + 3 adventure highlights
 * Grid: 2 columns mobile, 3 columns desktop
 */
export default function ProfileStats({ stats, className = '' }: ProfileStatsProps) {
    return (
        <div className={`grid grid-cols-2 md:grid-cols-3 gap-4 ${className}`}>
            {/* PvP: Wins */}
            <div
                className="bg-[#2A9D8F] border-3 border-black shadow-[4px_4px_0_0_#000] p-4 text-center"
                aria-label={`PvP Battle Wins: ${stats?.battle_wins ?? 0}`}
            >
                <Trophy className="w-5 h-5 mx-auto mb-2 text-white" aria-hidden="true" />
                <div className="text-2xl font-black text-white">{stats?.battle_wins ?? 0}</div>
                <div className="text-[10px] font-black uppercase text-white">
                    <span className="sr-only">PvP Battle </span>WINS
                </div>
            </div>

            {/* Adventure: Monster Rating */}
            <div
                className="bg-[#9D4EDD] border-3 border-black shadow-[4px_4px_0_0_#000] p-4 text-center"
                aria-label={`Monster Rating: ${stats?.monster_rating ?? 0}`}
            >
                <Star className="w-5 h-5 mx-auto mb-2 text-white" aria-hidden="true" />
                <div className="text-2xl font-black text-white">{stats?.monster_rating ?? 0}</div>
                <div className="text-[10px] font-black uppercase text-white">RATING</div>
            </div>

            {/* Total XP */}
            <div
                className="bg-[#F4A261] border-3 border-black shadow-[4px_4px_0_0_#000] p-4 text-center"
                aria-label={`Total XP: ${stats?.total_xp ?? 0}`}
            >
                <Zap className="w-5 h-5 mx-auto mb-2 text-white" aria-hidden="true" />
                <div className="text-2xl font-black text-white">{stats?.total_xp ?? 0}</div>
                <div className="text-[10px] font-black uppercase text-white">TOTAL XP</div>
            </div>

            {/* Adventure: Monsters Defeated */}
            <div
                className="bg-[#457B9D] border-3 border-black shadow-[4px_4px_0_0_#000] p-4 text-center"
                aria-label={`Monsters Slain: ${stats?.monster_defeats ?? 0}`}
            >
                <Skull className="w-5 h-5 mx-auto mb-2 text-white" aria-hidden="true" />
                <div className="text-2xl font-black text-white">{stats?.monster_defeats ?? 0}</div>
                <div className="text-[10px] font-black uppercase text-white">SLAIN</div>
            </div>

            {/* Tasks Completed */}
            <div
                className="bg-[#F4A261] border-3 border-black shadow-[4px_4px_0_0_#000] p-4 text-center"
                aria-label={`Tasks Completed: ${stats?.tasks_completed ?? 0}`}
            >
                <Target className="w-5 h-5 mx-auto mb-2 text-white" aria-hidden="true" />
                <div className="text-2xl font-black text-white">{stats?.tasks_completed ?? 0}</div>
                <div className="text-[10px] font-black uppercase text-white">TASKS</div>
            </div>

            {/* Adventure: Total Damage (abbreviated) */}
            <div
                className="bg-[#E63946] border-3 border-black shadow-[4px_4px_0_0_#000] p-4 text-center"
                aria-label={`Total Damage: ${formatNumber(stats?.total_damage_dealt ?? 0)}`}
            >
                <Swords className="w-5 h-5 mx-auto mb-2 text-white" aria-hidden="true" />
                <div className="text-2xl font-black text-white">
                    {formatNumber(stats?.total_damage_dealt)}
                </div>
                <div className="text-[10px] font-black uppercase text-white">DAMAGE</div>
            </div>
        </div>
    );
}
