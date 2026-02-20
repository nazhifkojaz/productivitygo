/**
 * BattleScoreboard Component
 *
 * Displays the PVP score comparison between the user and their rival.
 * Shows leading status with color-coded backgrounds.
 *
 * REFACTOR-005: Phase 5 - Week 3 - Arena.tsx Refactoring
 */

import type { ArenaScores, BattleData } from '../../types/arena';

export interface BattleScoreboardProps {
    scores: ArenaScores;
    battle: BattleData;
}

export default function BattleScoreboard({ scores, battle }: BattleScoreboardProps) {
    const { myScore, rivalScore, isLeading } = scores;
    const rivalName = battle?.rival?.username?.toUpperCase() || 'RIVAL';

    return (
        <div className="grid grid-cols-2 gap-4">
            {/* User's Score */}
            <div
                className={`border-4 border-black p-6 text-center ${
                    isLeading ? 'bg-[#2A9D8F] text-white' : 'bg-white'
                }`}
            >
                <div className="text-xs font-black uppercase font-mono mb-2">
                    YOUR SCORE
                </div>
                <div className="text-5xl font-black">{myScore}</div>
                <div className="text-sm font-bold mt-2">XP EARNED</div>
                {isLeading && (
                    <div className="mt-2 inline-block bg-white text-black px-3 py-1 text-xs font-black border-2 border-black">
                        LEADING
                    </div>
                )}
            </div>

            {/* Rival's Score */}
            <div
                className={`border-4 border-black p-6 text-center ${
                    !isLeading && rivalScore > 0 ? 'bg-[#E63946] text-white' : 'bg-white'
                }`}
            >
                <div className="text-xs font-black uppercase font-mono mb-2">
                    {rivalName}
                </div>
                <div className="text-5xl font-black">{rivalScore}</div>
                <div className="text-sm font-bold mt-2">XP EARNED</div>
                {!isLeading && rivalScore > myScore && (
                    <div className="mt-2 inline-block bg-white text-black px-3 py-1 text-xs font-black border-2 border-black">
                        LEADING
                    </div>
                )}
            </div>
        </div>
    );
}
