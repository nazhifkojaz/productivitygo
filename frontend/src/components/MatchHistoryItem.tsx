import type { MatchHistory } from '../types/profile';

const RESULT_COLORS: Record<string, string> = {
    WIN: 'bg-[#2A9D8F] text-white',
    LOSS: 'bg-[#E63946] text-white',
    ESCAPED: 'bg-[#F4A261] text-white',
    COMPLETED: 'bg-[#457B9D] text-white',
    DRAW: 'bg-gray-400 text-white',
} as const;

interface MatchHistoryItemProps {
    match: MatchHistory;
    compact?: boolean;
    showDuration?: boolean;
    showXP?: boolean;
}

export default function MatchHistoryItem({
    match,
    compact = false,
    showDuration = true,
    showXP = true,
}: MatchHistoryItemProps) {
    const resultColor = RESULT_COLORS[match.result] || 'bg-gray-300';

    const formatDate = (dateStr: string): string => {
        if (!dateStr) return 'Unknown date';
        const date = new Date(dateStr);
        if (isNaN(date.getTime())) return 'Unknown date';
        return date.toLocaleDateString();
    };

    return (
        <article
            className={`bg-[#E8E4D9] border-3 border-black flex justify-between items-center ${
                compact ? 'p-3 shadow-[2px_2px_0_0_#000]' : 'p-4 shadow-[3px_3px_0_0_#000]'
            }`}
        >
            <div className={`flex items-center ${compact ? 'gap-2' : 'gap-3'}`}>
                <span className={compact ? 'text-xl' : 'text-2xl'} aria-hidden="true">
                    {match.emoji || '⚔️'}
                </span>
                <div>
                    <div className={`font-black uppercase ${compact ? 'text-sm' : 'text-lg'}`}>
                        {match.type === 'adventure' ? 'VS ' : ''}
                        {match.rival}
                    </div>
                    <div className="text-xs text-gray-600 font-bold">
                        <time dateTime={match.date}>{formatDate(match.date)}</time>
                        {showDuration && match.duration !== undefined && (
                            <span> • {match.duration} DAYS</span>
                        )}
                        {showXP && match.xp_earned !== undefined && (
                            <span> • +{match.xp_earned} XP</span>
                        )}
                    </div>
                </div>
            </div>
            <div
                className={`font-black border-2 border-black shadow-[2px_2px_0_0_#000] ${
                    resultColor
                } ${compact ? 'text-sm px-3' : 'text-xl px-4'} py-1`}
                aria-label={`Result: ${match.result}`}
            >
                {match.result}
            </div>
        </article>
    );
}
