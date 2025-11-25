import { Shield } from 'lucide-react';

interface RivalRadarProps {
    battle: any;
}

export default function RivalRadar({ battle }: RivalRadarProps) {
    const stats = battle?.rival?.stats;

    return (
        <aside className="w-full bg-neo-dark text-neo-white border-3 border-black p-6 shadow-neo relative">
            <div className="absolute top-0 right-0 bg-neo-accent text-black px-3 py-1 font-bold border-l-3 border-b-3 border-black text-sm">
                RIVAL DETECTED
            </div>
            <h2 className="text-xl font-black uppercase mb-4 flex items-center gap-2 text-neo-white">
                <Shield className="w-5 h-5" /> Rival Radar
            </h2>

            {/* Panel 1: Rival Stats */}
            <div className="bg-gray-800 border-3 border-white p-4 mb-6">
                <div className="flex items-center gap-4 mb-4 border-b-2 border-gray-600 pb-4">
                    <div className="w-12 h-12 bg-gray-600 rounded-full border-2 border-white flex items-center justify-center">
                        <span className="text-xl">😈</span>
                    </div>
                    <div>
                        <h3 className="text-lg font-bold text-white leading-none">{battle?.rival?.username || 'Rival'}</h3>
                        <p className="text-neo-secondary font-bold text-xs">Level {battle?.rival?.level || '?'}</p>
                    </div>
                </div>

                <div className="grid grid-cols-3 gap-2 text-center">
                    <div className="bg-gray-700 p-2 rounded border border-gray-600">
                        <div className="text-lg font-black text-white">{stats?.battle_wins || 0}</div>
                        <div className="text-[10px] font-bold uppercase text-gray-400">Wins</div>
                    </div>
                    <div className="bg-gray-700 p-2 rounded border border-gray-600">
                        <div className="text-lg font-black text-white">{stats?.battle_fought || 0}</div>
                        <div className="text-[10px] font-bold uppercase text-gray-400">Battles</div>
                    </div>
                    <div className="bg-gray-700 p-2 rounded border border-gray-600">
                        <div className="text-lg font-black text-white">{stats?.total_xp || 0}</div>
                        <div className="text-[10px] font-bold uppercase text-gray-400">XP</div>
                    </div>
                </div>
            </div>

            {/* Panel 2: Battle Progress */}
            <div className="space-y-4">
                <div className="flex justify-between items-center text-xs font-bold uppercase">
                    <span>Daily Progress</span>
                    <span>{battle?.rival?.tasks_completed || 0}/{battle?.rival?.tasks_total || 0} Tasks</span>
                </div>
                <div className="w-full h-4 bg-gray-700 border-3 border-white relative">
                    <div
                        className="h-full bg-neo-primary transition-all duration-500"
                        style={{ width: `${battle?.rival?.tasks_total ? (battle.rival.tasks_completed / battle.rival.tasks_total) * 100 : 0}%` }}
                    ></div>
                </div>

                <div className="mt-4 p-3 bg-gray-800 border-2 border-dashed border-gray-500 flex items-center gap-3">
                    <div className="w-2 h-2 bg-green-500 rounded-full animate-pulse"></div>
                    <p className="text-gray-300 font-bold text-xs">
                        {battle?.rival?.tasks_completed > 0
                            ? `Rival finished ${battle.rival.tasks_completed} task(s) today!`
                            : "Rival hasn't started yet..."}
                    </p>
                </div>
            </div>
        </aside>
    );
}
