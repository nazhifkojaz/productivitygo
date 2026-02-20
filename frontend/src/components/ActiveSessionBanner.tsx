import { motion } from 'framer-motion';
import { Swords, Compass } from 'lucide-react';

/**
 * Props for the ActiveSessionBanner component
 */
export interface ActiveSessionBannerProps {
    /** The type of active session */
    sessionType: 'battle' | 'adventure';
    /** Opponent's display name (rival username or monster name) */
    opponentName: string;
    /** Opponent's avatar emoji */
    opponentEmoji?: string;
    /** Current day of the battle/adventure */
    currentDay: number;
    /** Total days/duration of the battle/adventure */
    totalDays: number;
    /** Callback when user clicks "GO TO ARENA" button */
    onGoToArena: () => void;
}

/**
 * ActiveSessionBanner Component
 *
 * Displays a prominent banner when the user has an active battle or adventure.
 * Shows opponent info, day progress, and provides a "GO TO ARENA" button.
 *
 * Used in Lobby.tsx to replace Battle/Adventure Stations when a game is active.
 *
 * @example
 * ```tsx
 * <ActiveSessionBanner
 *     sessionType="battle"
 *     opponentName="Challenger123"
 *     opponentEmoji="?"
 *     currentDay={3}
 *     totalDays={5}
 *     onGoToArena={() => navigate('/arena')}
 * />
 * ```
 */
export default function ActiveSessionBanner({
    sessionType,
    opponentName,
    opponentEmoji,
    currentDay,
    totalDays,
    onGoToArena,
}: ActiveSessionBannerProps) {
    // Color scheme based on session type
    const isBattle = sessionType === 'battle';
    const bgColor = isBattle ? 'bg-[#E63946]' : 'bg-[#9D4EDD]';
    const Icon = isBattle ? Swords : Compass;
    const sessionLabel = isBattle ? 'BATTLE' : 'ADVENTURE';
    const opponentLabel = isBattle ? 'VS' : 'FIGHTING';

    return (
        <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3, ease: 'easeOut' }}
            className={`${bgColor} text-white border-4 border-black shadow-[6px_6px_0_0_#000] p-6 mb-8`}
        >
            <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                {/* Left: Opponent Info */}
                <div className="flex items-center gap-4">
                    {/* Icon */}
                    <div className="w-16 h-16 bg-white/20 border-3 border-white flex items-center justify-center flex-shrink-0">
                        {opponentEmoji ? (
                            <span className="text-3xl">{opponentEmoji}</span>
                        ) : (
                            <Icon className="w-8 h-8" strokeWidth={3} />
                        )}
                    </div>

                    {/* Session Info */}
                    <div>
                        <div className="flex items-center gap-2 mb-1">
                            <Icon className="w-4 h-4" strokeWidth={2.5} />
                            <span className="text-xs font-black tracking-wider opacity-90">
                                ACTIVE {sessionLabel}
                            </span>
                        </div>
                        <div className="text-xl md:text-2xl font-black">
                            {opponentLabel} {opponentName}
                        </div>
                        <div className="text-sm font-bold opacity-90 font-mono">
                            Day {currentDay} of {totalDays}
                        </div>
                    </div>
                </div>

                {/* Right: Action Button */}
                <motion.button
                    onClick={onGoToArena}
                    whileHover={{ x: 2, y: 2 }}
                    whileTap={{ x: 4, y: 4 }}
                    className="bg-white text-black border-3 border-black shadow-[4px_4px_0_0_#000]
                               px-6 py-4 font-black uppercase tracking-wider
                               hover:shadow-[2px_2px_0_0_#000]
                               active:shadow-[0px_0px_0_0_#000]
                               transition-all whitespace-nowrap"
                >
                    <span className="flex items-center gap-2">
                        Go To Arena
                        <svg
                            xmlns="http://www.w3.org/2000/svg"
                            width="20"
                            height="20"
                            viewBox="0 0 24 24"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="3"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        >
                            <path d="M5 12h14" />
                            <path d="m12 5 7 7-7 7" />
                        </svg>
                    </span>
                </motion.button>
            </div>
        </motion.div>
    );
}
