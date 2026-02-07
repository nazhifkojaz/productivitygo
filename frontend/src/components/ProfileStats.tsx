import { Trophy, Star, Target, Swords } from 'lucide-react';

interface ProfileStatsProps {
    stats?: {
        battle_wins?: number;
        total_xp?: number;
        battle_fought?: number;
        tasks_completed?: number;
        current_streak?: number;
    } | null;
    className?: string;
}

/**
 * ProfileStats component - Design 1
 *
 * Uses colored StatCard pattern instead of uniform gray cards
 * Displays key user statistics with icons
 */
export default function ProfileStats({ stats, className = '' }: ProfileStatsProps) {
    return (
        <div className={`grid grid-cols-2 md:grid-cols-4 gap-4 ${className}`}>
            <div className="bg-[#2A9D8F] border-3 border-black shadow-[4px_4px_0_0_#000] p-4 text-center">
                <Trophy className="w-5 h-5 mx-auto mb-2 text-white" />
                <div className="text-2xl font-black text-white">{stats?.battle_wins || 0}</div>
                <div className="text-[10px] font-black uppercase text-white">WINS</div>
            </div>
            <div className="bg-[#457B9D] border-3 border-black shadow-[4px_4px_0_0_#000] p-4 text-center">
                <Swords className="w-5 h-5 mx-auto mb-2 text-white" />
                <div className="text-2xl font-black text-white">{stats?.battle_fought || 0}</div>
                <div className="text-[10px] font-black uppercase text-white">BATTLES</div>
            </div>
            <div className="bg-[#F4A261] border-3 border-black shadow-[4px_4px_0_0_#000] p-4 text-center">
                <Target className="w-5 h-5 mx-auto mb-2 text-white" />
                <div className="text-2xl font-black text-white">{stats?.tasks_completed || 0}</div>
                <div className="text-[10px] font-black uppercase text-white">TASKS</div>
            </div>
            <div className="bg-[#9D4EDD] border-3 border-black shadow-[4px_4px_0_0_#000] p-4 text-center">
                <Star className="w-5 h-5 mx-auto mb-2 text-white" />
                <div className="text-2xl font-black text-white">{stats?.total_xp || 0}</div>
                <div className="text-[10px] font-black uppercase text-white">TOTAL XP</div>
            </div>
        </div>
    );
}
