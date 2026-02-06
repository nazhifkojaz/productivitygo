interface ProfileStatsProps {
    stats?: {
        battle_wins?: number;
        total_xp?: number;
        battle_fought?: number;
        win_rate?: string;
        tasks_completed?: number;
    } | null;
    className?: string;
}

export default function ProfileStats({ stats, className = '' }: ProfileStatsProps) {
    return (
        <div className={`grid grid-cols-2 md:grid-cols-3 gap-4 mt-8 ${className}`}>
            <div className="bg-gray-50 border-3 border-black p-4 text-center hover:bg-white transition-colors">
                <div className="text-3xl font-black">{stats?.battle_wins || 0}</div>
                <div className="text-xs font-bold uppercase text-gray-500">Battle Wins</div>
            </div>
            <div className="bg-gray-50 border-3 border-black p-4 text-center hover:bg-white transition-colors">
                <div className="text-3xl font-black">{stats?.total_xp || 0}</div>
                <div className="text-xs font-bold uppercase text-gray-500">Total XP</div>
            </div>
            <div className="bg-gray-50 border-3 border-black p-4 text-center hover:bg-white transition-colors">
                <div className="text-3xl font-black">{stats?.battle_fought || 0}</div>
                <div className="text-xs font-bold uppercase text-gray-500">Battle Fought</div>
            </div>
            <div className="bg-gray-50 border-3 border-black p-4 text-center hover:bg-white transition-colors">
                <div className="text-3xl font-black">{stats?.win_rate || '0%'}</div>
                <div className="text-xs font-bold uppercase text-gray-500">Win Rate</div>
            </div>
            <div className="bg-gray-50 border-3 border-black p-4 text-center hover:bg-white transition-colors md:col-span-2">
                <div className="text-3xl font-black">{stats?.tasks_completed || 0}</div>
                <div className="text-xs font-bold uppercase text-gray-500">Tasks Completed</div>
            </div>
        </div>
    );
}
