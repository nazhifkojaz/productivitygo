import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Calendar, Home, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import { motion } from 'framer-motion';
import { useBattleDetails } from '../hooks/useBattleDetails';
import { usePendingRematch } from '../hooks/usePendingRematch';
import { useQueryClient } from '@tanstack/react-query';

export default function BattleResult() {
    const { battleId } = useParams();
    const { session, user } = useAuth();
    const navigate = useNavigate();
    const { data: battle, isLoading: loading } = useBattleDetails(battleId);
    const { data: pendingRematch } = usePendingRematch(battleId);

    const queryClient = useQueryClient();

    const handleEndCampaign = async () => {
        if (!confirm("End this campaign and return to lobby?")) return;
        try {
            await axios.post(`/api/battles/${battleId}/leave`, {}, {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
            await queryClient.invalidateQueries({ queryKey: ['currentBattle'] });
            navigate('/lobby');
        } catch (error) {
            console.error('Failed to leave battle:', error);
            navigate('/lobby');
        }
    };

    const handleRematch = async () => {
        try {
            await axios.post(`/api/invites/${battleId}/rematch`, {}, {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
            window.location.reload();
        } catch (error: any) {
            console.error('Failed to start rematch:', error);
            toast.error("Failed to start rematch");
        }
    };

    const handleAcceptRematch = async () => {
        if (!pendingRematch?.battle_id) {
            console.error("No pending rematch battle_id:", pendingRematch);
            toast.error("No pending rematch found");
            return;
        }

        try {
            await axios.post(`/api/invites/${pendingRematch.battle_id}/accept`, {}, {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
            toast.success("Rematch accepted! Good luck!");
            navigate('/lobby');
        } catch (error: any) {
            console.error('Failed to accept rematch:', error);
            toast.error(`Failed to accept rematch: ${error.response?.data?.detail || error.message}`);
        }
    };

    const handleDeclineRematch = async () => {
        if (!pendingRematch?.battle_id) return;
        if (!confirm("Decline rematch? This will end the campaign.")) return;
        try {
            await axios.post(`/api/invites/${pendingRematch.battle_id}/decline`, {}, {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
            await axios.post(`/api/battles/${battleId}/leave`, {}, {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
            navigate('/lobby');
        } catch (error) {
            toast.error("Failed to decline rematch.");
        }
    };

    if (loading) return <div className="min-h-screen bg-[#E8E4D9] neo-grid-bg flex items-center justify-center font-black">CALCULATING RESULTS...</div>;
    if (!battle) return <div className="min-h-screen bg-[#E8E4D9] neo-grid-bg flex items-center justify-center font-black">RESULT NOT FOUND</div>;

    const isWinner = battle.winner_id === user?.id;
    const isDraw = !battle.winner_id;
    const user1 = battle.user1;
    const user2 = battle.user2;
    const scores = battle.scores || { user1_xp: 0, user2_xp: 0 };

    // Determine current user's role (user1 or user2) to display correctly
    const isUser1 = user?.id === battle.user1_id;
    const myScore = isUser1 ? scores.user1_xp : scores.user2_xp;
    const rivalScore = isUser1 ? scores.user2_xp : scores.user1_xp;
    const rivalName = isUser1 ? user2.username : user1.username;

    return (
        <div className="min-h-screen bg-[#E8E4D9] neo-grid-bg p-4 md:p-8 flex flex-col items-center">
            {/* Victory Banner */}
            <motion.div
                initial={{ scale: 0.8, opacity: 0, rotate: -5 }}
                animate={{ scale: 1, opacity: 1, rotate: 0 }}
                className="w-full max-w-2xl mb-8 mt-8"
            >
                <div className={`border-5 border-black p-8 text-center shadow-[8px_8px_0_0_#000] ${isWinner ? 'bg-[#F4A261]' : isDraw ? 'bg-gray-300' : 'bg-gray-400'}`}>
                    <motion.div
                        initial={{ y: -20 }}
                        animate={{ y: [0, -10, 0] }}
                        transition={{ repeat: Infinity, duration: 2, repeatDelay: 1 }}
                        className="text-6xl mb-4"
                    >
                        {isWinner ? '🏆' : isDraw ? '🤝' : '💔'}
                    </motion.div>
                    <h1 className="text-5xl md:text-7xl font-black uppercase italic">
                        {isWinner ? 'VICTORY!' : isDraw ? 'DRAW!' : 'DEFEAT'}
                    </h1>
                    <p className="text-xl font-bold mt-4">
                        {isWinner ? 'You dominated the arena!' : isDraw ? 'Evenly matched!' : `Better luck next time against ${rivalName}`}
                    </p>
                </div>
            </motion.div>

            {/* Final Scoreboard */}
            <div className="w-full max-w-3xl mb-8">
                <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000]">
                    <div className="bg-black text-white p-4 border-b-4 border-black text-center">
                        <h2 className="text-xl font-black uppercase font-mono">// FINAL SCORE //</h2>
                    </div>
                    <div className="grid grid-cols-2">
                        {/* My Score */}
                        <div className={`p-6 text-center border-r-4 border-black ${isWinner ? 'bg-[#2A9D8F] text-white' : ''}`}>
                            <div className="text-sm font-black uppercase font-mono mb-2">YOU</div>
                            <div className="text-6xl font-black">{myScore}</div>
                            <div className="text-sm font-bold mt-2">TOTAL XP</div>
                        </div>

                        {/* Rival Score */}
                        <div className={`p-6 text-center ${!isWinner && !isDraw && myScore !== rivalScore ? 'bg-[#E63946] text-white' : ''}`}>
                            <div className="text-sm font-black uppercase font-mono mb-2">{rivalName.toUpperCase()}</div>
                            <div className="text-6xl font-black">{rivalScore}</div>
                            <div className="text-sm font-bold mt-2">TOTAL XP</div>
                        </div>
                    </div>
                </div>
            </div>

            {/* Battle Log */}
            <div className="w-full max-w-3xl mb-8">
                <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000]">
                    <div className="bg-black text-white p-4 border-b-4 border-black">
                        <h2 className="text-xl font-black uppercase flex items-center gap-2">
                            <Calendar className="w-6 h-6" /> Battle Log
                        </h2>
                    </div>

                    <div className="overflow-x-auto">
                        <table className="w-full text-left">
                            <thead>
                                <tr className="border-b-4 border-black">
                                    <th className="p-4 font-black uppercase text-sm">DATE</th>
                                    <th className="p-4 font-black uppercase text-sm">YOU</th>
                                    <th className="p-4 font-black uppercase text-sm">{rivalName.toUpperCase()}</th>
                                    <th className="p-4 font-black uppercase text-sm text-center">WINNER</th>
                                </tr>
                            </thead>
                            <tbody>
                                {battle.daily_breakdown?.map((day: any, i: number) => {
                                    const myDayXp = isUser1 ? day.user1_xp : day.user2_xp;
                                    const rivalDayXp = isUser1 ? day.user2_xp : day.user1_xp;

                                    return (
                                        <tr key={i} className="border-b-2 border-black">
                                            <td className="p-4 font-bold">{day.date}</td>
                                            <td className={`p-4 font-black ${myDayXp > rivalDayXp ? 'text-[#2A9D8F]' : ''}`}>{myDayXp}</td>
                                            <td className={`p-4 font-black ${rivalDayXp > myDayXp ? 'text-[#E63946]' : ''}`}>{rivalDayXp}</td>
                                            <td className="p-4 text-center">
                                                {day.winner_id === user?.id ? (
                                                    <span className="bg-[#2A9D8F] text-white px-3 py-1 text-xs font-black border-2 border-black">WIN</span>
                                                ) : day.winner_id ? (
                                                    <span className="bg-[#E63946] text-white px-3 py-1 text-xs font-black border-2 border-black">LOSS</span>
                                                ) : (
                                                    <span className="bg-gray-300 text-black px-3 py-1 text-xs font-black border-2 border-black">DRAW</span>
                                                )}
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            {/* XP Earned */}
            <div className="w-full max-w-3xl mb-8">
                <div className="bg-[#F4A261] border-4 border-black shadow-[6px_6px_0_0_#000] p-6 flex items-center justify-between">
                    <div>
                        <div className="text-sm font-black uppercase font-mono">XP EARNED</div>
                        <div className="text-4xl font-black">+{myScore}</div>
                    </div>
                    <div className="text-right">
                        <div className="text-sm font-black uppercase font-mono">NEW LEVEL</div>
                        <div className="text-2xl font-black">{(isUser1 ? user1.level : user2.level) + 1} ↗</div>
                    </div>
                </div>
            </div>

            {/* Actions */}
            <div className="w-full max-w-3xl flex flex-col md:flex-row gap-4 mb-12">
                {pendingRematch?.exists ? (
                    pendingRematch.is_requester ? (
                        <div className="w-full bg-blue-100 border-4 border-black p-6 text-center shadow-[4px_4px_0_0_#000]">
                            <h3 className="text-xl font-black uppercase mb-2">⏳ Waiting for Rival</h3>
                            <p className="font-bold mb-4">Your rival is reviewing the rematch request...</p>
                            <button
                                onClick={handleDeclineRematch}
                                className="w-full bg-white border-3 border-black p-4 text-xl font-black uppercase shadow-[4px_4px_0_0_#000] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0_0_#000] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none transition-all flex items-center justify-center gap-2"
                            >
                                <Home className="w-6 h-6" /> Cancel & Return to Lobby
                            </button>
                        </div>
                    ) : (
                        <div className="w-full bg-[#2A9D8F] border-4 border-black p-6 text-center shadow-[4px_4px_0_0_#000]">
                            <h3 className="text-xl font-black uppercase mb-2 text-white">🔥 Rematch Request!</h3>
                            <p className="font-bold mb-4 text-white">Your rival wants a rematch! What's your call?</p>
                            <div className="flex flex-col md:flex-row gap-4">
                                <button
                                    onClick={handleAcceptRematch}
                                    className="flex-1 bg-white border-3 border-black p-4 text-xl font-black uppercase shadow-[4px_4px_0_0_#000] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0_0_#000] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none transition-all flex items-center justify-center gap-2"
                                >
                                    <RefreshCw className="w-6 h-6" /> Accept Rematch
                                </button>
                                <button
                                    onClick={handleDeclineRematch}
                                    className="flex-1 bg-[#E63946] border-3 border-black p-4 text-xl font-black uppercase text-white shadow-[4px_4px_0_0_#000] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0_0_#000] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none transition-all flex items-center justify-center gap-2"
                                >
                                    <Home className="w-6 h-6" /> Decline & End Campaign
                                </button>
                            </div>
                        </div>
                    )
                ) : (
                    <>
                        <motion.button
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={handleEndCampaign}
                            className="flex-1 bg-white border-4 border-black p-6 text-xl font-black uppercase shadow-[4px_4px_0_0_#000] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0_0_#000] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none transition-all flex items-center justify-center gap-2"
                        >
                            <Home className="w-6 h-6" /> Return to Lobby
                        </motion.button>

                        <motion.button
                            whileHover={{ scale: 1.02 }}
                            whileTap={{ scale: 0.98 }}
                            onClick={handleRematch}
                            className="flex-1 bg-[#E63946] border-4 border-black p-6 text-xl font-black uppercase text-white shadow-[4px_4px_0_0_#000] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0_0_#000] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none transition-all flex items-center justify-center gap-2"
                        >
                            <RefreshCw className="w-6 h-6" /> Rematch
                        </motion.button>
                    </>
                )}
            </div>
        </div>
    );
}
