import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import confetti from 'canvas-confetti';
import { Home, Trophy, Skull, Flag, Zap, Calendar, Heart } from 'lucide-react';
import { motion } from 'framer-motion';
import { useAdventureDetails } from '../hooks/useAdventureDetails';

export default function AdventureResult() {
    const { adventureId } = useParams();
    const navigate = useNavigate();
    const { data: adventure, isLoading } = useAdventureDetails(adventureId);

    // Trigger confetti on victory
    useEffect(() => {
        if (adventure && adventure.status === 'completed') {
            confetti({
                particleCount: 150,
                spread: 70,
                origin: { y: 0.6 },
                colors: ['#A855F7', '#EC4899', '#8B5CF6'] // Purple/pink theme
            });
        }
    }, [adventure]);

    if (isLoading) {
        return (
            <div className="min-h-screen bg-neo-bg flex items-center justify-center font-black">
                CALCULATING RESULTS...
            </div>
        );
    }

    if (!adventure) {
        return (
            <div className="min-h-screen bg-neo-bg flex items-center justify-center font-black">
                ADVENTURE NOT FOUND
            </div>
        );
    }

    const isVictory = adventure.status === 'completed';

    const outcomeConfig = {
        completed: {
            title: 'VICTORY!',
            subtitle: `You defeated ${adventure.monster?.name || 'the monster'}!`,
            bgColor: 'bg-purple-400',
            icon: <Trophy className="w-12 h-12" />,
        },
        escaped: {
            title: 'ESCAPED!',
            subtitle: `${adventure.monster?.name || 'The monster'} got away...`,
            bgColor: 'bg-gray-400',
            icon: <Skull className="w-12 h-12" />,
        },
        abandoned: {
            title: 'RETREATED',
            subtitle: 'You lived to fight another day.',
            bgColor: 'bg-yellow-400',
            icon: <Flag className="w-12 h-12" />,
        },
    };

    const outcome = outcomeConfig[adventure.status as keyof typeof outcomeConfig] || outcomeConfig.escaped;

    // Calculate HP bar percentage
    const hpPercent = Math.max(0, (adventure.monster_current_hp / adventure.monster_max_hp) * 100);

    return (
        <div className="min-h-screen bg-neo-bg p-4 md:p-8 flex flex-col items-center">
            {/* Header / Outcome Announcement */}
            <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="text-center mb-8 mt-8"
            >
                <div className={`inline-block ${outcome.bgColor} border-4 border-black p-6 shadow-neo mb-4 rotate-1`}>
                    <div className="flex items-center justify-center gap-4">
                        {outcome.icon}
                        <h1 className="text-4xl md:text-6xl font-black uppercase italic">
                            {outcome.title}
                        </h1>
                    </div>
                </div>
                <p className="text-xl font-bold text-gray-600">{outcome.subtitle}</p>
            </motion.div>

            {/* Monster Card */}
            <div className="w-full max-w-md bg-neo-white border-4 border-black p-6 shadow-neo mb-8">
                <div className="text-center mb-4">
                    <span className="text-6xl">{adventure.monster?.emoji || '👹'}</span>
                    <h2 className="text-2xl font-black mt-2">{adventure.monster?.name || 'Unknown Monster'}</h2>
                    <span className={`inline-block px-2 py-1 text-xs font-bold border-2 border-black mt-2 ${
                        adventure.monster?.tier === 'boss' ? 'bg-red-400' :
                        adventure.monster?.tier === 'expert' ? 'bg-purple-400' :
                        adventure.monster?.tier === 'hard' ? 'bg-orange-400' :
                        adventure.monster?.tier === 'medium' ? 'bg-yellow-400' :
                        'bg-green-400'
                    }`}>
                        {adventure.monster?.tier?.toUpperCase() || 'EASY'}
                    </span>
                </div>

                {/* HP Bar */}
                <div className="mb-4">
                    <div className="flex justify-between text-sm font-bold mb-1">
                        <span className="flex items-center gap-1">
                            <Heart className="w-4 h-4 text-red-500" /> HP
                        </span>
                        <span>{adventure.monster_current_hp} / {adventure.monster_max_hp}</span>
                    </div>
                    <div className="w-full h-4 bg-gray-200 border-2 border-black">
                        <div
                            className={`h-full transition-all ${isVictory ? 'bg-gray-400' : 'bg-red-500'}`}
                            style={{ width: `${hpPercent}%` }}
                        />
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-2 gap-4">
                    <div className="bg-gray-100 border-2 border-black p-3 text-center">
                        <Zap className="w-5 h-5 mx-auto mb-1 text-neo-primary" />
                        <div className="text-2xl font-black">{adventure.total_damage_dealt}</div>
                        <div className="text-xs font-bold text-gray-500">TOTAL DAMAGE</div>
                    </div>
                    <div className="bg-gray-100 border-2 border-black p-3 text-center">
                        <Calendar className="w-5 h-5 mx-auto mb-1 text-blue-500" />
                        <div className="text-2xl font-black">{adventure.current_round}</div>
                        <div className="text-xs font-bold text-gray-500">DAYS SURVIVED</div>
                    </div>
                </div>
            </div>

            {/* XP Earned */}
            <div className="w-full max-w-md bg-yellow-300 border-4 border-black p-6 shadow-neo mb-8 text-center">
                <h3 className="text-xl font-black uppercase mb-2">XP EARNED</h3>
                <div className="text-5xl font-black text-neo-primary">
                    +{adventure.xp_earned} XP
                </div>
                {!isVictory && (
                    <p className="text-sm font-bold text-gray-600 mt-2">
                        (50% penalty applied)
                    </p>
                )}
            </div>

            {/* Daily Breakdown */}
            {adventure.daily_breakdown && adventure.daily_breakdown.length > 0 && (
                <div className="w-full max-w-md bg-white border-3 border-black p-6 shadow-neo mb-8">
                    <h3 className="text-xl font-black uppercase mb-4 flex items-center gap-2 border-b-3 border-black pb-2">
                        <Calendar className="w-5 h-5" /> Adventure Log
                    </h3>

                    <div className="space-y-2">
                        {adventure.daily_breakdown.map((day: any, i: number) => (
                            <div
                                key={i}
                                className="flex justify-between items-center p-2 border-2 border-black bg-gray-50"
                            >
                                <span className="font-bold">Day {i + 1}</span>
                                <span className="font-black text-neo-primary">
                                    {day.damage_dealt} DMG
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            {/* Return Button */}
            <motion.button
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
                onClick={() => navigate('/lobby')}
                className="btn-neo bg-neo-primary text-white py-4 px-8 text-xl font-black uppercase flex items-center gap-2"
            >
                <Home className="w-6 h-6" /> Return to Lobby
            </motion.button>
        </div>
    );
}
