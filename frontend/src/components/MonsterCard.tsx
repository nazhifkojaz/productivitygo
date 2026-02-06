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

    // Tier-specific colors
    const tierColors: Record<string, string> = {
        easy: 'text-green-400',
        medium: 'text-yellow-400',
        hard: 'text-orange-400',
        expert: 'text-red-400',
        boss: 'text-purple-400',
    };

    // HP bar color based on remaining HP
    const getHpBarColor = () => {
        if (hpPercent > 60) return 'from-red-600 to-red-400';
        if (hpPercent > 30) return 'from-orange-600 to-orange-400';
        return 'from-yellow-600 to-yellow-400';
    };

    return (
        <aside className="w-full bg-neo-dark text-neo-white border-3 border-black p-6 shadow-neo relative">
            {/* Corner badge */}
            <div className="absolute top-0 right-0 bg-red-500 text-white px-3 py-1 font-bold border-l-3 border-b-3 border-black text-sm">
                MONSTER HUNT
            </div>

            {/* On Break Banner */}
            {adventure.is_on_break && (
                <div className="bg-blue-500 text-white p-2 mb-4 text-center font-bold border-2 border-white flex items-center justify-center gap-2">
                    <Coffee className="w-4 h-4" />
                    REST DAY - Adventure paused
                </div>
            )}

            {/* Monster Info */}
            <div className="flex items-center gap-4 mb-6">
                <div className="w-16 h-16 bg-gray-800 rounded-full border-3 border-white flex items-center justify-center text-4xl">
                    {adventure.monster?.emoji || '👹'}
                </div>
                <div>
                    <h3 className="text-xl font-black">
                        {adventure.monster?.name || 'Unknown Monster'}
                    </h3>
                    <span className={`text-xs font-bold uppercase ${tierColors[adventure.monster?.tier || 'easy']}`}>
                        {adventure.monster?.tier || 'easy'} tier
                    </span>
                </div>
            </div>

            {/* HP Bar */}
            <div className="mb-6">
                <div className="flex justify-between text-xs font-bold mb-1">
                    <span className="flex items-center gap-1">
                        <Skull className="w-3 h-3" /> Monster HP
                    </span>
                    <span>{adventure.monster_current_hp}/{adventure.monster_max_hp}</span>
                </div>
                <div className="w-full h-6 bg-gray-700 border-3 border-white relative overflow-hidden">
                    <div
                        className={`h-full bg-gradient-to-r ${getHpBarColor()} transition-all duration-500`}
                        style={{ width: `${hpPercent}%` }}
                    />
                    {/* HP segments for visual effect */}
                    <div className="absolute inset-0 flex">
                        {[...Array(10)].map((_, i) => (
                            <div
                                key={i}
                                className="flex-1 border-r border-gray-600 last:border-r-0"
                            />
                        ))}
                    </div>
                </div>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-3 gap-3">
                <div className="bg-gray-800 p-3 border-2 border-gray-600 text-center">
                    <Zap className="w-4 h-4 mx-auto text-neo-primary mb-1" />
                    <div className="text-lg font-black">{adventure.total_damage_dealt}</div>
                    <div className="text-[10px] font-bold uppercase text-gray-400">Damage</div>
                </div>
                <div className="bg-gray-800 p-3 border-2 border-gray-600 text-center">
                    <Clock className="w-4 h-4 mx-auto text-yellow-400 mb-1" />
                    <div className="text-lg font-black">{daysRemaining}d</div>
                    <div className="text-[10px] font-bold uppercase text-gray-400">Left</div>
                </div>
                <div className="bg-gray-800 p-3 border-2 border-gray-600 text-center">
                    <Coffee className="w-4 h-4 mx-auto text-blue-400 mb-1" />
                    <div className="text-lg font-black">{breaksRemaining}</div>
                    <div className="text-[10px] font-bold uppercase text-gray-400">Breaks</div>
                </div>
            </div>

            {/* Monster Description */}
            <div className="mt-4 p-3 bg-gray-800 border-2 border-dashed border-gray-500">
                <p className="text-gray-300 text-sm italic">
                    "{adventure.monster?.description || 'A mysterious creature...'}"
                </p>
            </div>
        </aside>
    );
}
