import React from 'react';

interface RankBadgeProps {
    rank: string;
    level?: number;
    size?: 'small' | 'medium' | 'large';
    showLabel?: boolean;
}

const RankBadge: React.FC<RankBadgeProps> = ({ rank, level, size = 'medium', showLabel = true }) => {
    const sizeClasses = {
        small: 'px-2 py-1 text-xs',
        medium: 'px-3 py-1.5 text-sm',
        large: 'px-4 py-2 text-base'
    };

    const rankColors = {
        'Novice': 'bg-gradient-to-r from-gray-400 to-gray-500 text-white',
        'Challenger': 'bg-gradient-to-r from-amber-600 to-amber-700 text-white',
        'Fighter': 'bg-gradient-to-r from-gray-300 to-gray-400 text-gray-800',
        'Warrior': 'bg-gradient-to-r from-yellow-400 to-yellow-500 text-gray-900',
        'Champion': 'bg-gradient-to-r from-slate-300 to-slate-400 text-gray-900',
        'Legend': 'bg-gradient-to-r from-cyan-400 to-cyan-500 text-gray-900',
        'Mythic': 'bg-gradient-to-r from-purple-500 to-pink-500 text-white animate-pulse'
    };

    const rankIcons = {
        'Novice': '🌱',
        'Challenger': '⚔️',
        'Fighter': '🗡️',
        'Warrior': '🛡️',
        'Champion': '👑',
        'Legend': '💎',
        'Mythic': '✨'
    };

    return (
        <div
            className={`
                inline-flex items-center justify-center gap-1.5 rounded-full font-semibold
                ${sizeClasses[size]}
                ${rankColors[rank as keyof typeof rankColors] || rankColors['Novice']}
                shadow-lg cursor-help transition-transform hover:scale-105
            `}
            title={rank} // Native tooltip
        >
            {level !== undefined && <span>Level {level}</span>}
            <span>{rankIcons[rank as keyof typeof rankIcons] || '🌱'}</span>
            {showLabel && <span>{rank}</span>}
        </div>
    );
};

export default RankBadge;
