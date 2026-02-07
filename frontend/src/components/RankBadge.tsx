import React from 'react';

interface RankBadgeProps {
    rank: string;
    level?: number;
    size?: 'small' | 'medium' | 'large';
    showLabel?: boolean;
}

/**
 * RankBadge component - Design 1 colors
 *
 * Uses Design 1 palette (neobrutalist colors) instead of gradients
 * Maintains 7 rank tiers with icons
 */
const RankBadge: React.FC<RankBadgeProps> = ({ rank, level, size = 'medium', showLabel = true }) => {
    const sizeClasses = {
        small: 'px-2 py-1 text-xs',
        medium: 'px-3 py-1.5 text-sm',
        large: 'px-4 py-2 text-base'
    };

    // Design 1 rank colors (solid, no gradient)
    const rankColors: Record<string, { bg: string; text: string }> = {
        'Novice': { bg: 'bg-gray-300', text: 'text-black' },
        'Challenger': { bg: 'bg-[#F4A261]', text: 'text-white' },     // orange/yellow
        'Fighter': { bg: 'bg-[#F4A261]', text: 'text-white' },       // orange/yellow
        'Warrior': { bg: 'bg-[#457B9D]', text: 'text-white' },        // blue
        'Champion': { bg: 'bg-[#2A9D8F]', text: 'text-white' },      // teal/green
        'Legend': { bg: 'bg-[#9D4EDD]', text: 'text-white' },        // purple
        'Mythic': { bg: 'bg-[#E63946]', text: 'text-white' },       // red
    };

    const rankIcons: Record<string, string> = {
        'Novice': '🌱',
        'Challenger': '⚔️',
        'Fighter': '🗡️',
        'Warrior': '🛡️',
        'Champion': '👑',
        'Legend': '💎',
        'Mythic': '✨'
    };

    const colors = rankColors[rank] || rankColors['Novice'];

    return (
        <span
            className={`
                inline-flex items-center justify-center gap-1.5 font-semibold
                ${sizeClasses[size]}
                ${colors.bg} ${colors.text}
                border-2 border-black
                shadow-[3px_3px_0_0_#000]
                cursor-help
            `}
            title={rank}
        >
            {level !== undefined && <span>LVL {level}</span>}
            <span>{rankIcons[rank] || '🌱'}</span>
            {showLabel && <span>{rank.toUpperCase()}</span>}
        </span>
    );
};

export default RankBadge;
