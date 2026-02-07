import { Skull, Clock, Zap, Coffee } from 'lucide-react';
import type { Adventure } from '../hooks/useCurrentAdventure';

interface MonsterCardProps {
    adventure: Adventure;
}

/**
 * Displays the monster during an active adventure.
 *
 * Shows:
 * - Monster emoji, name, tier
 * - HP bar (current/max)
 * - Total damage dealt
 * - Days remaining (from backend computed field)
 * - Breaks remaining
 * - On-break status banner
 *
 * Usage:
 * ```tsx
 * <MonsterCard adventure={currentAdventure} />
 * ```
 */
export default function MonsterCard({ adventure }: MonsterCardProps) {
    // Calculate HP percentage for bar
    const hpPercent = (adventure.monster_current_hp / adventure.monster_max_hp) * 100;

    // Use backend-computed days_remaining, fallback to calculated from deadline
    const daysRemaining = adventure.days_remaining ?? 0;

    // Calculate breaks remaining
    const breaksRemaining = adventure.max_break_days - adventure.break_days_used;

    // Tier-specific colors for Design 1 palette
    const tierConfig: Record<string, { color: string; bgClass: string }> = {
        easy: { color: '#2A9D8F', bgClass: 'bg-[#2A9D8F]' },
        medium: { color: '#F4A261', bgClass: 'bg-[#F4A261]' },
        hard: { color: '#E63946', bgClass: 'bg-[#E63946]' },
        expert: { color: '#9D4EDD', bgClass: 'bg-[#9D4EDD]' },
        boss: { color: '#000000', bgClass: 'bg-black' },
    };

    const tier = adventure.monster?.tier || 'easy';
    const tierInfo = tierConfig[tier] || tierConfig.easy;

    return (
        <aside className="w-full bg-white text-black border-4 border-black shadow-[6px_6px_0_0_#000] p-6 relative">
            {/* Black header bar */}
            <div className="bg-black text-white p-4 border-b-4 border-black -mx-6 -mt-6 mb-6 text-center">
                <h2 className="text-xl font-black uppercase">// MONSTER //</h2>
            </div>

            {/* On Break Banner */}
            {adventure.is_on_break && (
                <div className="bg-blue-500 text-white p-3 mb-6 text-center font-bold border-3 border-black flex items-center justify-center gap-2">
                    <Coffee className="w-5 h-5" />
                    REST DAY - Adventure paused
                </div>
            )}

            {/* Monster Info */}
            <div className="flex flex-col items-center mb-6">
                <div className="w-20 h-20 bg-gray-50 border-3 border-black flex items-center justify-center text-5xl mb-4">
                    {adventure.monster?.emoji || '👹'}
                </div>
                <h3 className="text-2xl font-black uppercase text-center">
                    {adventure.monster?.name || 'Unknown Monster'}
                </h3>
                <span
                    className={`inline-block mt-2 px-4 py-2 text-sm font-black border-3 border-black text-white ${tierInfo.bgClass}`}
                >
                    {tier.toUpperCase()} TIER
                </span>
            </div>

            {/* HP Bar - Design 1 style with border-3 and larger height */}
            <div className="mb-6">
                <div className="flex justify-between text-xs font-bold mb-2">
                    <span className="flex items-center gap-1 font-mono">
                        <Skull className="w-4 h-4" /> MONSTER HP
                    </span>
                    <span className="font-mono">{adventure.monster_current_hp}/{adventure.monster_max_hp}</span>
                </div>
                <div className="w-full h-6 bg-gray-200 border-3 border-black relative overflow-hidden">
                    <div
                        className="h-full bg-gradient-to-r from-red-600 to-red-400 transition-all duration-500"
                        style={{ width: `${hpPercent}%` }}
                    />
                    {/* HP segments for visual effect */}
                    <div className="absolute inset-0 flex">
                        {[...Array(10)].map((_, i) => (
                            <div
                                key={i}
                                className="flex-1 border-r border-gray-400 last:border-r-0"
                            />
                        ))}
                    </div>
                </div>
            </div>

            {/* Stats Grid - Design 1 style with border-r-4 dividers */}
            <div className="grid grid-cols-3 gap-0 border-3 border-black bg-gray-50">
                <div className="p-4 text-center border-r-4 border-black">
                    <Zap className="w-5 h-5 mx-auto mb-2 text-[#E63946]" />
                    <div className="text-2xl font-black">{adventure.total_damage_dealt}</div>
                    <div className="text-[10px] font-black uppercase font-mono text-gray-500">DAMAGE</div>
                </div>
                <div className="p-4 text-center border-r-4 border-black">
                    <Clock className="w-5 h-5 mx-auto mb-2 text-[#F4A261]" />
                    <div className="text-2xl font-black">{daysRemaining}d</div>
                    <div className="text-[10px] font-black uppercase font-mono text-gray-500">REMAINING</div>
                </div>
                <div className="p-4 text-center">
                    <Coffee className="w-5 h-5 mx-auto mb-2 text-[#457B9D]" />
                    <div className="text-2xl font-black">{breaksRemaining}</div>
                    <div className="text-[10px] font-black uppercase font-mono text-gray-500">BREAKS</div>
                </div>
            </div>

            {/* Monster Description - Design 1 style */}
            <div className="mt-6 p-4 bg-gray-100 border-3 border-black border-dashed">
                <p className="text-gray-700 text-sm font-mono italic text-center">
                    "{adventure.monster?.description || 'A mysterious creature...'}"
                </p>
            </div>
        </aside>
    );
}
