import { useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import confetti from 'canvas-confetti';
import { Calendar, Home, RefreshCw } from 'lucide-react';
import { toast } from 'sonner';
import { motion } from 'framer-motion';
import RankBadge from '../components/RankBadge';
import { useBattleDetails } from '../hooks/useBattleDetails';
import { usePendingRematch } from '../hooks/usePendingRematch';
import { useQueryClient } from '@tanstack/react-query';

export default function BattleResult() {
    const { battleId } = useParams();
    const { session, user } = useAuth();
    const navigate = useNavigate();
    const { data: battle, isLoading: loading } = useBattleDetails(battleId);
    const { data: pendingRematch } = usePendingRematch(battleId);

    // Trigger confetti on win
    useEffect(() => {
        if (battle && battle.winner_id === user?.id) {
            confetti({
                particleCount: 150,
                spread: 70,
                origin: { y: 0.6 },
                colors: ['#FFD700', '#FFA500', '#FF4500']
            });
        }
    }, [battle, user]);



    const queryClient = useQueryClient();

    const handleEndCampaign = async () => {
        if (!confirm("End this campaign and return to lobby?")) return;
        try {
            await axios.post(`/api/battles/${battleId}/leave`, {}, {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
            // Invalidate cache to ensure Dashboard refetches
            await queryClient.invalidateQueries({ queryKey: ['currentBattle'] });
            navigate('/lobby');
        } catch (error) {
            console.error('Failed to leave battle:', error);
            navigate('/lobby'); // Navigate anyway
        }
    };

    const handleRematch = async () => {
        try {
            await axios.post(`/api/invites/${battleId}/rematch`, {}, {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
            // Reload to show pending rematch UI
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
            // Also leave the battle to clear current_battle
            await axios.post(`/api/battles/${battleId}/leave`, {}, {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
            navigate('/lobby');
        } catch (error) {
            toast.error("Failed to decline rematch.");
        }
    };

    if (loading) return <div className="min-h-screen bg-neo-bg flex items-center justify-center font-black">CALCULATING RESULTS...</div>;
    if (!battle) return <div className="min-h-screen bg-neo-bg flex items-center justify-center font-black">RESULT NOT FOUND</div>;

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
        <div className="min-h-screen bg-neo-bg p-4 md:p-8 flex flex-col items-center">

            {/* Header / Winner Announcement */}
            <motion.div
                initial={{ scale: 0.8, opacity: 0 }}
                animate={{ scale: 1, opacity: 1 }}
                className="text-center mb-8 mt-8"
            >
                <div className="inline-block bg-neo-white border-4 border-black p-6 shadow-neo mb-4 rotate-1">
                    <h1 className="text-4xl md:text-6xl font-black uppercase italic">
                        {isWinner ? "VICTORY!" : isDraw ? "DRAW!" : "DEFEAT"}
                    </h1>
                </div>
                <p className="text-xl font-bold text-gray-600">
                    {isWinner ? "You crushed it!" : isDraw ? "Evenly matched!" : `Better luck next time against ${rivalName}.`}
                </p>
            </motion.div>

            {/* Scoreboard */}
            <div className="w-full max-w-4xl grid grid-cols-1 md:grid-cols-2 gap-8 mb-12">
                {/* My Score */}
                <div className={`bg-neo-white border-3 border-black p-6 shadow-neo flex flex-col items-center ${isWinner ? 'bg-yellow-100' : ''}`}>
                    <h2 className="text-2xl font-black mb-2">YOU</h2>
                    <div className="text-6xl font-black text-neo-primary mb-2">{myScore} XP</div>
                    {(isUser1 ? user1.rank : user2.rank) && (
                        <RankBadge
                            rank={isUser1 ? user1.rank : user2.rank}
                            level={isUser1 ? user1.level : user2.level}
                            size="small"
                            showLabel={false}
                        />
                    )}
                </div>

                {/* Rival Score */}
                <div className="bg-neo-secondary border-3 border-black p-6 shadow-neo flex flex-col items-center opacity-90">
                    <h2 className="text-2xl font-black mb-2">{rivalName.toUpperCase()}</h2>
                    <div className="text-6xl font-black text-gray-700 mb-2">{rivalScore} XP</div>
                    {(isUser1 ? user2.rank : user1.rank) && (
                        <RankBadge
                            rank={isUser1 ? user2.rank : user1.rank}
                            level={isUser1 ? user2.level : user1.level}
                            size="small"
                            showLabel={false}
                        />
                    )}
                </div>
            </div>

            {/* Daily Breakdown */}
            <div className="w-full max-w-4xl bg-white border-3 border-black p-6 shadow-neo mb-12">
                <h3 className="text-2xl font-black uppercase mb-6 flex items-center gap-2 border-b-3 border-black pb-2">
                    <Calendar className="w-6 h-6" /> Battle Log
                </h3>

                <div className="overflow-x-auto">
                    <table className="w-full text-left border-collapse">
                        <thead>
                            <tr className="border-b-2 border-black">
                                <th className="p-3 font-black uppercase">Date</th>
                                <th className="p-3 font-black uppercase">You (XP)</th>
                                <th className="p-3 font-black uppercase">{rivalName} (XP)</th>
                                <th className="p-3 font-black uppercase text-center">Winner</th>
                            </tr>
                        </thead>
                        <tbody>
                            {battle.daily_breakdown?.map((day: any, i: number) => {
                                const myDayXp = isUser1 ? day.user1_xp : day.user2_xp;
                                const rivalDayXp = isUser1 ? day.user2_xp : day.user1_xp;

                                return (
                                    <tr key={i} className="border-b border-gray-200 hover:bg-gray-50 font-bold">
                                        <td className="p-3">{day.date}</td>
                                        <td className="p-3 text-neo-primary">{myDayXp}</td>
                                        <td className="p-3 text-gray-600">{rivalDayXp}</td>
                                        <td className="p-3 text-center">
                                            {day.winner_id === user?.id ? (
                                                <span className="bg-yellow-300 text-black px-2 py-1 text-xs border border-black shadow-sm">WIN</span>
                                            ) : day.winner_id ? (
                                                <span className="bg-gray-200 text-gray-500 px-2 py-1 text-xs">LOSS</span>
                                            ) : (
                                                <span className="bg-white text-black px-2 py-1 text-xs border border-black">DRAW</span>
                                            )}
                                        </td>
                                    </tr>
                                );
                            })}
                        </tbody>
                    </table>
                </div>
            </div>

            {/* Actions */}
            <div className="w-full max-w-2xl mb-12">
                {pendingRematch?.exists ? (
                    // Rematch request exists
                    pendingRematch.is_requester ? (
                        // User sent rematch request -> Waiting for rival
                        <div className="bg-blue-100 border-3 border-black p-6 text-center shadow-neo">
                            <h3 className="text-xl font-black uppercase mb-2">⏳ Waiting for Rival</h3>
                            <p className="font-bold mb-4">Your rival is reviewing the rematch request...</p>
                            <div className="flex flex-col md:flex-row gap-4">
                                <button
                                    onClick={() => handleDeclineRematch()}
                                    className="flex-1 btn-neo bg-white text-black py-4 text-xl font-black uppercase flex items-center justify-center gap-2 hover:bg-gray-100"
                                >
                                    <Home className="w-6 h-6" /> Cancel & Return to Lobby
                                </button>
                            </div>
                        </div>
                    ) : (
                        // User received rematch request -> Accept or Decline
                        <div className="bg-green-100 border-3 border-black p-6 text-center shadow-neo">
                            <h3 className="text-xl font-black uppercase mb-2">🔥 Rematch Request!</h3>
                            <p className="font-bold mb-4">Your rival wants a rematch! What's your call?</p>
                            <div className="flex flex-col md:flex-row gap-4">
                                <button
                                    onClick={handleAcceptRematch}
                                    className="flex-1 btn-neo bg-neo-primary text-white py-4 text-xl font-black uppercase flex items-center justify-center gap-2 hover:bg-blue-600"
                                >
                                    <RefreshCw className="w-6 h-6" /> Accept Rematch
                                </button>
                                <button
                                    onClick={handleDeclineRematch}
                                    className="flex-1 btn-neo bg-red-500 text-white py-4 text-xl font-black uppercase flex items-center justify-center gap-2 hover:bg-red-600"
                                >
                                    <Home className="w-6 h-6" /> Decline & End Campaign
                                </button>
                            </div>
                        </div>
                    )
                ) : (
                    // No rematch request -> Show original buttons
                    <div className="flex flex-col md:flex-row gap-4">
                        <button
                            onClick={handleEndCampaign}
                            className="flex-1 btn-neo bg-white text-black py-4 text-xl font-black uppercase flex items-center justify-center gap-2 hover:bg-gray-100"
                        >
                            <Home className="w-6 h-6" /> End Campaign
                        </button>

                        <button
                            onClick={handleRematch}
                            className="flex-1 btn-neo bg-neo-primary text-white py-4 text-xl font-black uppercase flex items-center justify-center gap-2 hover:bg-blue-600"
                        >
                            <RefreshCw className="w-6 h-6" /> Continue Battle
                        </button>
                    </div>
                )}
            </div>

        </div>
    );
}
