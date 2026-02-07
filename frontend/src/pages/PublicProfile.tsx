import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { Swords, ArrowLeft, Trophy, Shield, Target, Star, X, Loader, Calendar } from 'lucide-react';
import { toast } from 'sonner';
import RankBadge from '../components/RankBadge';
import { usePublicProfile } from '../hooks/usePublicProfile';
import { useSocialMutations } from '../hooks/useSocialMutations';
import { useChallengeMutations } from '../hooks/useChallengeMutations';

export default function PublicProfile() {
    const { userId } = useParams();
    const { user } = useAuth();
    const navigate = useNavigate();
    const { data: profile, isLoading: loading } = usePublicProfile(userId);
    const { followMutation, unfollowMutation } = useSocialMutations();
    const { sendChallengeMutation, isSending: isInviteSending } = useChallengeMutations();

    // Challenge Modal State
    const [showChallengeModal, setShowChallengeModal] = useState(false);
    const [startDate, setStartDate] = useState<string | null>(null);
    const [duration, setDuration] = useState(5);

    const handleFollowToggle = async () => {
        if (!profile) return;
        try {
            if (profile.is_following) {
                await unfollowMutation.mutateAsync(profile.id);
            } else {
                await followMutation.mutateAsync(profile.id);
            }
            toast.success(profile.is_following ? "Unfollowed!" : "Followed!");
        } catch (error) {
            console.error('Failed to update follow status', error);
            toast.error("Failed to update follow status");
        }
    };

    const handleSendChallenge = async () => {
        if (!startDate || !profile) {
            toast.error("Please select a start date!");
            return;
        }

        await sendChallengeMutation.mutateAsync({
            rivalId: profile.id,
            startDate: startDate,
            duration: duration
        });

        setShowChallengeModal(false);
        setStartDate(null);
    };

    // Date Options (Next 7 days)
    const dateOptions = Array.from({ length: 7 }, (_, i) => {
        const d = new Date();
        d.setDate(d.getDate() + i + 1);
        return d;
    });

    if (loading) return <div className="min-h-screen bg-[#E8E4D9] flex items-center justify-center font-black">LOADING PROFILE...</div>;

    if (!profile) return <div className="min-h-screen bg-[#E8E4D9] flex items-center justify-center font-black">USER NOT FOUND</div>;

    return (
        <div className="min-h-screen bg-[#E8E4D9] text-black font-sans p-4 md:p-8 pb-24">
            <div className="max-w-4xl mx-auto">
                {/* Header - Matching Profile.tsx style */}
                <header className="flex gap-4 mb-8 w-full">
                    <button
                        onClick={() => navigate(-1)}
                        className="flex btn-neo px-4 md:px-6 bg-white items-center justify-center"
                    >
                        <ArrowLeft className="w-6 h-6 md:w-8 md:h-8" />
                    </button>
                    <div className="bg-white border-3 border-black shadow-[4px_4px_0_0_#000] p-4 flex-1 text-center md:text-left relative overflow-hidden flex flex-col justify-center">
                        <div className="absolute top-0 right-0 bg-[#F4A261] px-2 border-l-3 border-b-3 border-black font-bold text-xs text-white">[ INTEL DOSSIER ]</div>
                        <h1 className="text-2xl font-black italic uppercase">Player <span className="text-[#2A9D8F]">Profile</span></h1>
                    </div>
                </header>

                {/* Profile Card */}
                <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000] p-6 mb-8 relative overflow-hidden">
                    <div className="absolute top-0 right-0 bg-[#2A9D8F] px-4 py-1 font-black border-l-4 border-b-4 border-black text-white">
                        LEVEL {profile.level}
                    </div>

                    <div className="flex flex-col md:flex-row items-center gap-6">
                        <div className="w-24 h-24 bg-[#F4A261] border-4 border-black flex items-center justify-center shadow-[4px_4px_0_0_#000]">
                            <span className="text-5xl">{profile.avatar_emoji || '😀'}</span>
                        </div>

                        <div className="text-center md:text-left flex-1">
                            <div className="flex items-center justify-center md:justify-start gap-3 mb-2">
                                <h2 className="text-3xl font-black uppercase">{profile.username}</h2>
                                {profile.rank && <RankBadge rank={profile.rank} level={profile.level} size="medium" showLabel={false} />}
                            </div>
                            <div className="flex flex-wrap gap-3 justify-center md:justify-start">
                                {user?.id !== profile.id && (
                                    <>
                                        <button
                                            onClick={handleFollowToggle}
                                            className={`px-6 py-2 font-bold border-3 border-black shadow-[3px_3px_0_0_#000] transition-all active:translate-y-1 active:shadow-none ${profile.is_following ? 'bg-gray-300' : 'bg-[#F4A261] text-white'
                                                }`}
                                        >
                                            {profile.is_following ? 'UNFOLLOW' : 'FOLLOW'}
                                        </button>
                                        <button
                                            onClick={() => setShowChallengeModal(true)}
                                            className="px-6 py-2 font-bold bg-[#2A9D8F] text-white border-3 border-black shadow-[3px_3px_0_0_#000] transition-all active:translate-y-1 active:shadow-none flex items-center gap-2"
                                        >
                                            <Swords className="w-4 h-4" /> CHALLENGE
                                        </button>
                                    </>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Stats Grid - Design 1 colored cards */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                    <div className="bg-[#F4A261] border-3 border-black shadow-[4px_4px_0_0_#000] p-4 text-center">
                        <Trophy className="w-5 h-5 mx-auto mb-2 text-white" />
                        <div className="text-2xl font-black text-white">{profile.stats.battle_wins}</div>
                        <div className="text-[10px] font-black uppercase text-white">WINS</div>
                    </div>
                    <div className="bg-[#457B9D] border-3 border-black shadow-[4px_4px_0_0_#000] p-4 text-center">
                        <Shield className="w-5 h-5 mx-auto mb-2 text-white" />
                        <div className="text-2xl font-black text-white">{profile.stats.battle_fought}</div>
                        <div className="text-[10px] font-black uppercase text-white">BATTLES</div>
                    </div>
                    <div className="bg-[#2A9D8F] border-3 border-black shadow-[4px_4px_0_0_#000] p-4 text-center">
                        <Target className="w-5 h-5 mx-auto mb-2 text-white" />
                        <div className="text-2xl font-black text-white">{profile.stats.tasks_completed}</div>
                        <div className="text-[10px] font-black uppercase text-white">TASKS</div>
                    </div>
                    <div className="bg-[#9D4EDD] border-3 border-black shadow-[4px_4px_0_0_#000] p-4 text-center">
                        <Star className="w-5 h-5 mx-auto mb-2 text-white" />
                        <div className="text-2xl font-black text-white">{profile.stats.total_xp}</div>
                        <div className="text-[10px] font-black uppercase text-white">TOTAL XP</div>
                    </div>
                </div>

                {/* Match History */}
                <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000] p-6">
                    <div className="bg-black text-white px-4 py-2 -mx-6 -mt-6 mb-6 font-black uppercase text-sm border-b-4 border-black">
                        // Recent Battles //
                    </div>
                    <div className="space-y-3">
                        {profile.match_history.length > 0 ? (
                            profile.match_history.map((match: { id: string; rival: string; date: string; duration: number; result: string }) => (
                                <div key={match.id} className="bg-[#E8E4D9] border-3 border-black p-4 flex justify-between items-center shadow-[3px_3px_0_0_#000]">
                                    <div>
                                        <div className="font-black text-lg uppercase">VS {match.rival}</div>
                                        <div className="text-xs text-gray-600 font-bold">{new Date(match.date).toLocaleDateString()} • {match.duration} DAYS</div>
                                    </div>
                                    <div className={`font-black text-xl px-4 py-1 border-2 border-black shadow-[2px_2px_0_0_#000] ${match.result === 'WIN' ? 'bg-[#2A9D8F] text-white' :
                                        match.result === 'LOSS' ? 'bg-[#E63946] text-white' : 'bg-gray-300'
                                        }`}>
                                        {match.result}
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="text-center py-8 text-gray-500 font-black italic border-3 border-dashed border-gray-400 bg-[#E8E4D9]">
                                NO BATTLE HISTORY RECORDED
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* Challenge Modal */}
            {showChallengeModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000] max-w-md w-full p-6 relative">
                        <button
                            onClick={() => setShowChallengeModal(false)}
                            className="absolute top-4 right-4 p-2 hover:bg-gray-200 border-2 border-black"
                        >
                            <X className="w-5 h-5" />
                        </button>

                        <h2 className="text-2xl font-black uppercase mb-8 flex items-center gap-2">
                            <Swords className="w-6 h-6" /> Challenge {profile.username}
                        </h2>

                        <div className="space-y-6">
                            {/* Opponent Info */}
                            <div className="bg-[#E8E4D9] border-3 border-black p-4 shadow-[3px_3px_0_0_#000]">
                                <div className="text-xs font-black text-gray-600 uppercase mb-1">[ OPPONENT ]</div>
                                <div className="font-black text-lg">{profile.username}</div>
                                <div className="text-sm text-gray-600">{profile.email}</div>
                            </div>

                            {/* Start Date */}
                            <div>
                                <label className="block text-xs font-black mb-2 uppercase text-gray-600 flex items-center gap-1">
                                    <Calendar className="w-3 h-3" /> [ BATTLE START DATE ]
                                </label>
                                <select
                                    className="w-full border-3 border-black p-3 font-black focus:outline-none focus:ring-2 focus:ring-[#2A9D8F] bg-white shadow-[2px_2px_0_0_#000]"
                                    value={startDate || ''}
                                    onChange={(e) => setStartDate(e.target.value)}
                                >
                                    <option value="">SELECT DATE</option>
                                    {dateOptions.map(date => (
                                        <option key={date.toISOString()} value={date.toISOString().split('T')[0]}>
                                            {date.toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' })}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            {/* Duration */}
                            <div>
                                <label className="block text-xs font-black mb-2 uppercase text-gray-600">[ BATTLE DURATION ]</label>
                                <div className="flex gap-2">
                                    {[3, 4, 5].map(d => (
                                        <button
                                            key={d}
                                            onClick={() => setDuration(d)}
                                            className={`flex-1 py-3 border-3 border-black font-black text-lg transition-colors shadow-[2px_2px_0_0_#000] ${duration === d ? 'bg-[#2A9D8F] text-white' : 'bg-white hover:bg-gray-200'
                                                }`}
                                        >
                                            {d} DAYS
                                        </button>
                                    ))}
                                </div>
                            </div>

                            {/* Send Button */}
                            <button
                                onClick={handleSendChallenge}
                                disabled={isInviteSending || !startDate}
                                className={`w-full py-4 font-black text-lg border-3 border-black shadow-[4px_4px_0_0_#000] transition-all active:translate-y-1 active:shadow-none flex items-center justify-center gap-2 mt-4 ${isInviteSending || !startDate ? 'bg-gray-300 cursor-not-allowed' : 'bg-[#2A9D8F] text-white hover:bg-[#21867a]'
                                    }`}
                            >
                                {isInviteSending ? <Loader className="w-5 h-5 animate-spin" /> : <Swords className="w-5 h-5" />}
                                {isInviteSending ? 'SENDING...' : 'SEND CHALLENGE'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
