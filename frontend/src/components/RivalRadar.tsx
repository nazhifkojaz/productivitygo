interface RivalInfo {
    avatar_emoji?: string;
    username?: string;
    level?: number;
    rank?: string;
    tasks_completed?: number;
    tasks_total?: number;
}

interface RivalRadarProps {
    battle: { rival?: RivalInfo };
}

/**
 * RivalRadar component for Design 1
 * Displays rival information with inline card pattern
 */
export default function RivalRadar({ battle }: RivalRadarProps) {
    const rival = battle?.rival;

    const tasksCompleted = rival?.tasks_completed || 0;
    const tasksTotal = rival?.tasks_total || 0;
    const progressPercent = tasksTotal > 0 ? (tasksCompleted / tasksTotal) * 100 : 0;

    return (
        <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000] p-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
                <div className="w-14 h-14 bg-[#F4A261] border-3 border-black flex items-center justify-center">
                    <span className="text-3xl">{rival?.avatar_emoji || '😈'}</span>
                </div>
                <div>
                    <div className="font-black text-lg">VS {rival?.username || 'Rival'}</div>
                    <div className="text-xs font-mono text-gray-500">
                        LVL {rival?.level || 1} · {(rival?.rank || 'BRONZE').toUpperCase()}
                    </div>
                </div>
            </div>
            <div className="text-right">
                <div className="text-xs font-mono text-gray-500">RIVAL PROGRESS</div>
                <div className="w-32 h-4 bg-gray-200 border-2 border-black mt-1">
                    <div
                        className="h-full bg-[#E63946] transition-all duration-500"
                        style={{ width: `${progressPercent}%` }}
                    />
                </div>
                <div className="text-xs font-mono text-gray-500 mt-1">
                    {tasksCompleted}/{tasksTotal} TASKS
                </div>
            </div>
        </div>
    );
}
