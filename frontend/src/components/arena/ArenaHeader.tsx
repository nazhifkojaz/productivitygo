/**
 * ArenaHeader Component
 *
 * Displays the header section with title, game mode badge,
 * countdown to midnight, and navigation buttons.
 *
 * REFACTOR-005: Phase 5 - Week 3 - Arena.tsx Refactoring
 */

import { ArrowLeft, User } from 'lucide-react';
import type { ArenaMode, RoundInfo } from '../../types/arena';

export interface ArenaHeaderProps {
    mode: ArenaMode;
    roundInfo: RoundInfo | null;
    appState: string;
    timeLeft: string;
    onNavigateToLobby: () => void;
    onNavigateToProfile: () => void;
}

export default function ArenaHeader({
    mode,
    roundInfo,
    appState,
    timeLeft,
    onNavigateToLobby,
    onNavigateToProfile,
}: ArenaHeaderProps) {
    const getStatusBadge = () => {
        if (mode === 'adventure') {
            if (appState === 'PRE_ADVENTURE') return '[ PREPARING FOR ADVENTURE ]';
            return `[ DAY ${roundInfo?.currentDay || 1} OF ${roundInfo?.totalDays || 5} ]`;
        }
        // Battle mode
        if (appState === 'PRE_BATTLE') return '[ PREPARING FOR BATTLE ]';
        if (appState === 'PENDING_ACCEPTANCE') return '[ AWAITING RIVAL ]';
        return `[ ${roundInfo?.label || ''} ]`;
    };

    return (
        <div className="max-w-4xl mx-auto mb-6">
            <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000] p-4 flex items-center justify-between">
                <div>
                    <h1 className="text-2xl font-black uppercase">Battle Arena</h1>
                    <p className="text-xs font-mono text-gray-500">
                        {getStatusBadge()}
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <div className="text-right">
                        <div className="text-xs font-mono font-bold text-gray-500">TIME REMAINING</div>
                        <div className="font-mono font-black text-lg">{timeLeft}</div>
                    </div>
                    <button
                        onClick={onNavigateToLobby}
                        className="p-3 bg-white border-3 border-black shadow-[3px_3px_0_0_#000] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0_0_#000] transition-all"
                        title="Back to Lobby"
                    >
                        <ArrowLeft className="w-5 h-5" />
                    </button>
                    <button
                        onClick={onNavigateToProfile}
                        className="p-3 bg-white border-3 border-black shadow-[3px_3px_0_0_#000] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0_0_#000] transition-all"
                        title="Profile"
                    >
                        <User className="w-5 h-5" />
                    </button>
                </div>
            </div>
        </div>
    );
}
