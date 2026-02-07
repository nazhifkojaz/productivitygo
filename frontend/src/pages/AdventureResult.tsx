import { useParams, useNavigate } from 'react-router-dom';
import { Home, Zap, Calendar, Heart } from 'lucide-react';
import { motion } from 'framer-motion';
import { useAdventureDetails } from '../hooks/useAdventureDetails';

export default function AdventureResult() {
    const { adventureId } = useParams();
    const navigate = useNavigate();
    const { data: adventure, isLoading } = useAdventureDetails(adventureId);

    if (isLoading) {
        return (
            <div className="min-h-screen bg-[#E8E4D9] neo-grid-bg flex items-center justify-center font-black">
                CALCULATING RESULTS...
            </div>
        );
    }

    if (!adventure) {
        return (
            <div className="min-h-screen bg-[#E8E4D9] neo-grid-bg flex items-center justify-center font-black">
                ADVENTURE NOT FOUND
            </div>
        );
    }

    const isVictory = adventure.status === 'completed';

    const outcomeConfig = {
        completed: {
            title: 'VICTORY!',
            subtitle: `You defeated ${adventure.monster?.name || 'the monster'}!`,
            bgColor: 'bg-[#9D4EDD]',
            icon: '🐉',
        },
        escaped: {
            title: 'ESCAPED!',
            subtitle: `${adventure.monster?.name || 'The monster'} got away...`,
            bgColor: 'bg-gray-400',
            icon: '💨',
        },
        abandoned: {
            title: 'RETREATED',
            subtitle: 'You lived to fight another day.',
            bgColor: 'bg-gray-400',
            icon: '🏳',
        },
    };

    const outcome = outcomeConfig[adventure.status as keyof typeof outcomeConfig] || outcomeConfig.escaped;

    // Calculate HP bar percentage
    const hpPercent = Math.max(0, (adventure.monster_current_hp / adventure.monster_max_hp) * 100);

    // Tier colors
    const tierColors: Record<string, string> = {
        easy: 'bg-[#2A9D8F]',
        medium: 'bg-[#F4A261]',
        hard: 'bg-[#E63946]',
        expert: 'bg-[#9D4EDD]',
        boss: 'bg-black',
    };

    const tier = adventure.monster?.tier || 'easy';
    const tierBg = tierColors[tier] || tierColors.easy;

    return (
        <div className="min-h-screen bg-[#E8E4D9] neo-grid-bg p-4 md:p-8 flex flex-col items-center">
            {/* Victory/Defeat Banner */}
            <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="w-full max-w-2xl mb-8 mt-8"
            >
                <div className={`${outcome.bgColor} border-5 border-black p-8 text-center shadow-[8px_8px_0_0_#000]`}>
                    <div className="text-6xl mb-4">
                        {outcome.icon}
                    </div>
                    <h1 className="text-5xl md:text-7xl font-black uppercase italic text-white">
                        {outcome.title}
                    </h1>
                    <p className="text-xl font-bold mt-4 text-white">
                        {outcome.subtitle}
                    </p>
                </div>
            </motion.div>

            {/* Monster Card */}
            <div className="w-full max-w-md mb-8">
                <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000]">
                    <div className="bg-black text-white p-4 border-b-4 border-black text-center">
                        <h2 className="text-xl font-black uppercase">// MONSTER //</h2>
                    </div>

                    <div className="p-6 text-center">
                        <div className="text-7xl mb-4">{adventure.monster?.emoji || '👹'}</div>
                        <h3 className="text-2xl font-black uppercase">{adventure.monster?.name || 'Unknown'}</h3>

                        <span className={`inline-block px-4 py-2 text-sm font-black border-3 border-black mt-4 text-white ${tierBg}`}>
                            {tier.toUpperCase()}
                        </span>

                        {/* HP Bar */}
                        <div className="mt-6">
                            <div className="flex justify-between text-sm font-bold mb-2 font-mono">
                                <span className="flex items-center gap-2">
                                    <Heart className="w-5 h-5 text-[#E63946]" /> HP
                                </span>
                                <span>{adventure.monster_current_hp} / {adventure.monster_max_hp}</span>
                            </div>
                            <div className="w-full h-6 bg-gray-200 border-3 border-black">
                                <div
                                    className={`h-full transition-all ${isVictory ? 'bg-gray-400' : 'bg-[#E63946]'}`}
                                    style={{ width: `${hpPercent}%` }}
                                />
                            </div>
                        </div>
                    </div>

                    {/* Stats */}
                    <div className="grid grid-cols-2 border-t-4 border-black">
                        <div className="p-4 border-r-4 border-black text-center bg-gray-50">
                            <Zap className="w-6 h-6 mx-auto mb-2 text-[#E63946]" />
                            <div className="text-3xl font-black">{adventure.total_damage_dealt}</div>
                            <div className="text-xs font-black uppercase font-mono">Damage Dealt</div>
                        </div>
                        <div className="p-4 text-center bg-gray-50">
                            <Calendar className="w-6 h-6 mx-auto mb-2 text-[#457B9D]" />
                            <div className="text-3xl font-black">{adventure.current_round}</div>
                            <div className="text-xs font-black uppercase font-mono">Days Survived</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* XP Earned */}
            <div className="w-full max-w-md mb-8">
                <div className="bg-[#FFD700] border-4 border-black shadow-[6px_6px_0_0_#000] p-6 text-center">
                    <div className="text-sm font-black uppercase font-mono mb-2">XP EARNED</div>
                    <motion.div
                        initial={{ scale: 0 }}
                        animate={{ scale: 1 }}
                        transition={{ delay: 0.3, type: 'spring' }}
                        className="text-6xl font-black"
                    >
                        +{adventure.xp_earned}
                    </motion.div>
                    {!isVictory && (
                        <p className="text-sm font-bold mt-2">(50% penalty applied)</p>
                    )}
                </div>
            </div>

            {/* Daily Breakdown */}
            {adventure.daily_breakdown && adventure.daily_breakdown.length > 0 && (
                <div className="w-full max-w-md mb-8">
                    <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000]">
                        <div className="bg-black text-white p-4 border-b-4 border-black">
                            <h2 className="text-lg font-black uppercase flex items-center gap-2">
                                <Calendar className="w-5 h-5" /> Adventure Log
                            </h2>
                        </div>

                        <div className="p-4 space-y-2">
                            {adventure.daily_breakdown.map((day: any, i: number) => (
                                <div key={i} className="flex items-center justify-between p-3 border-3 border-black bg-gray-50">
                                    <span className="font-black">DAY {i + 1}</span>
                                    <span className="font-mono font-black text-[#E63946]">{day.damage_dealt} DMG</span>
                                    <span className="text-xs font-bold bg-[#2A9D8F] text-white px-2 py-1 border-2 border-black">
                                        {day.tasks_completed} TASKS
                                    </span>
                                </div>
                            ))}
                        </div>
                    </div>
                </div>
            )}

            {/* Return Button */}
            <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => navigate('/lobby')}
                className="bg-[#9D4EDD] border-4 border-black p-6 text-xl font-black uppercase text-white shadow-[6px_6px_0_0_#000] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[4px_4px_0_0_#000] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none transition-all flex items-center gap-3"
            >
                <Home className="w-6 h-6" /> Return to Lobby
            </motion.button>
        </div>
    );
}
