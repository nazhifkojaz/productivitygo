/**
 * AdventureStation component.
 *
 * Button to start a new adventure.
 *
 * REFACTOR-005: Phase 5 - Item 6.2
 */

import { Compass } from 'lucide-react';

interface AdventureStationProps {
    onStartAdventure: () => void;
}

export function AdventureStation({ onStartAdventure }: AdventureStationProps) {
    return (
        <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000]">
            <div className="bg-[#9D4EDD] text-white p-4 border-b-4 border-black">
                <h2 className="text-xl font-black uppercase flex items-center gap-2">
                    <Compass className="w-6 h-6" /> Adventure Station
                </h2>
                <p className="text-sm font-mono opacity-80">[ SOLO PVE COMBAT ]</p>
            </div>

            <div className="p-6">
                <p className="font-bold text-gray-600 mb-4 font-mono text-sm">
                    &gt; Battle AI monsters solo. Complete tasks to deal damage!
                </p>

                <button
                    onClick={onStartAdventure}
                    className="w-full bg-[#9D4EDD] border-3 border-black p-4 font-black uppercase text-white shadow-[4px_4px_0_0_#000] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0_0_#000] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none transition-all flex items-center justify-center gap-2"
                >
                    <Compass className="w-5 h-5" /> START ADVENTURE
                </button>
            </div>
        </div>
    );
}
