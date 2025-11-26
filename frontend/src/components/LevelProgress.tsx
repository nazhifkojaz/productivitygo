import React from 'react';
import { TrendingUp } from 'lucide-react';

interface LevelProgressProps {
    currentLevel: number;
    nextLevel: number;
    xpProgress: number;
    xpNeeded: number;
    progressPercentage: number;
}

const LevelProgress: React.FC<LevelProgressProps> = ({
    currentLevel,
    nextLevel,
    xpProgress,
    xpNeeded,
    progressPercentage
}) => {
    return (
        <div className="space-y-2">
            {/* Header */}
            <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-purple-500" />
                    <span className="font-semibold">Level {currentLevel}</span>
                </div>
                <span className="text-gray-500">
                    {xpProgress.toLocaleString()} / {xpNeeded.toLocaleString()} XP
                </span>
            </div>

            {/* Progress Bar */}
            <div className="relative h-3 bg-gray-200 dark:bg-gray-700 rounded-full overflow-hidden">
                <div
                    className="absolute top-0 left-0 h-full bg-gradient-to-r from-purple-500 to-pink-500 rounded-full transition-all duration-500 ease-out"
                    style={{ width: `${Math.min(progressPercentage, 100)}%` }}
                />
                {/* Shine effect */}
                <div
                    className="absolute top-0 left-0 h-full w-full bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer"
                    style={{
                        animation: 'shimmer 2s infinite',
                        backgroundSize: '200% 100%'
                    }}
                />
            </div>

            {/* Next Level Indicator */}
            <div className="text-xs text-gray-500 text-right">
                Next: Level {nextLevel}
            </div>

            <style>{`
                @keyframes shimmer {
                    0% { background-position: -200% 0; }
                    100% { background-position: 200% 0; }
                }
            `}</style>
        </div>
    );
};

export default LevelProgress;
