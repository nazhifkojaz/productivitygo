/**
 * PreBattleCountdown Component
 *
 * Displays the countdown banner before a battle or adventure starts.
 * Shows the time remaining until the game begins.
 *
 * REFACTOR-005: Phase 5 - Week 3 - Arena.tsx Refactoring
 */

import { AlertTriangle } from 'lucide-react';
import type { ArenaMode } from '../../types/arena';

export interface PreBattleCountdownProps {
    mode: ArenaMode;
    timeUntilBattle: string;
}

export default function PreBattleCountdown({
    mode,
    timeUntilBattle,
}: PreBattleCountdownProps) {
    const isAdventure = mode === 'adventure';

    return (
        <div className="max-w-4xl mx-auto mb-6">
            <div className="bg-[#F4A261] border-4 border-black shadow-[6px_6px_0_0_#000] p-8 text-center">
                <h2 className="text-2xl font-black uppercase mb-2 flex items-center justify-center gap-2">
                    <AlertTriangle className="w-8 h-8" />
                    {isAdventure ? 'Adventure Pending' : 'Battle Pending'}
                </h2>
                <p className="font-bold mb-1">
                    {isAdventure ? 'The hunt begins in' : 'The battle begins in'}
                </p>
                <div className="text-3xl font-black mb-2">
                    {timeUntilBattle || 'Loading...'}
                </div>
                <p className="font-bold text-sm">
                    {isAdventure ? 'Plan your first day of tasks.' : 'Prepare your protocols.'}
                </p>
            </div>
        </div>
    );
}
