import { useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { Shield, Swords, ArrowLeft, Trophy, Star, Target, X, Loader, Calendar } from 'lucide-react';
import { toast } from 'sonner';
import RankBadge from '../components/RankBadge';
import { usePublicProfile } from '../hooks/usePublicProfile';
import { useSocialMutations } from '../hooks/useSocialMutations';

export default function PublicProfile() {
    const { userId } = useParams();
    const { session, user } = useAuth();
    const navigate = useNavigate();
    const { data: profile, isLoading: loading } = usePublicProfile(userId);
    const { followMutation, unfollowMutation } = useSocialMutations();

    // Challenge Modal State
    const [showChallengeModal, setShowChallengeModal] = useState(false);
    const [startDate, setStartDate] = useState<string | null>(null);
    const [duration, setDuration] = useState(5);
    const [sendingInvite, setSendingInvite] = useState(false);



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

        setSendingInvite(true);
        try {
            await axios.post('/api/invites/send', {
                rival_id: profile.id,
                start_date: startDate,
                duration: duration
            }, {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });

            setShowChallengeModal(false);
            setStartDate(null);
            toast.success(`Challenge sent to ${profile.username}!`);
        } catch (error: any) {
            console.error('Failed to send challenge:', error);
            console.error('Error response:', error.response?.data);

            // Show detailed error message
            const errorDetail = error.response?.data?.detail;
            if (typeof errorDetail === 'string') {
                toast.error(errorDetail);
            } else if (Array.isArray(errorDetail)) {
                // Pydantic validation errors
                const messages = errorDetail.map((e: any) => `• ${e.msg}`).join('\n');
                toast.error(`Validation errors:\n${messages}`);
            } else {
                toast.error('Failed to send challenge. Please try again.');
            }
        } finally {
            setSendingInvite(false);
        }
    };

    // Date Options (Next 7 days)
    const dateOptions = Array.from({ length: 7 }, (_, i) => {
        const d = new Date();
        d.setDate(d.getDate() + i + 1);
        return d;
    });

    if (loading) return <div className="min-h-screen bg-neo-bg flex items-center justify-center font-black">LOADING PROFILE...</div>;

    if (!profile) return <div className="min-h-screen bg-neo-bg flex items-center justify-center font-black">USER NOT FOUND</div>;

    return (
        <div className="min-h-screen bg-neo-bg text-black font-sans p-4 md:p-8 pb-24">
            <div className="max-w-4xl mx-auto">
                {/* Header - Matching Profile.tsx style */}
                <header className="flex gap-4 mb-8 w-full">
                    <button
                        onClick={() => navigate(-1)}
                        className="flex btn-neo px-4 md:px-6 bg-white items-center justify-center"
                    >
                        <ArrowLeft className="w-6 h-6 md:w-8 md:h-8" />
                    </button>
                    <div className="bg-neo-white border-3 border-black p-4 shadow-neo-sm flex-1 text-center md:text-left relative overflow-hidden flex flex-col justify-center">
                        <div className="absolute top-0 right-0 bg-neo-accent px-2 border-l-3 border-b-3 border-black font-bold text-xs">INTEL DOSSIER</div>
                        <h1 className="text-2xl font-black italic uppercase">Player <span className="text-neo-primary">Profile</span></h1>
                    </div>
                </header>

                {/* Profile Card */}
                <div className="bg-neo-white border-4 border-black shadow-neo p-6 mb-8 relative overflow-hidden">
                    <div className="absolute top-0 right-0 bg-neo-primary px-4 py-1 font-bold border-l-4 border-b-4 border-black">
                        LEVEL {profile.level}
                    </div>

                    <div className="flex flex-col md:flex-row items-center gap-6">
                        <div className="w-24 h-24 bg-neo-accent border-4 border-black rounded-full flex items-center justify-center">
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
                                            className={`px-6 py-2 font-bold border-3 border-black shadow-neo-sm transition-all active:translate-y-1 active:shadow-none ${profile.is_following ? 'bg-gray-300' : 'bg-neo-accent'
                                                }`}
                                        >
                                            {profile.is_following ? 'UNFOLLOW' : 'FOLLOW'}
                                        </button>
                                        <button
                                            onClick={() => setShowChallengeModal(true)}
                                            className="px-6 py-2 font-bold bg-neo-primary border-3 border-black shadow-neo-sm transition-all active:translate-y-1 active:shadow-none flex items-center gap-2"
                                        >
                                            <Swords className="w-4 h-4" /> CHALLENGE
                                        </button>
                                    </>
                                )}
                            </div>
                        </div>
                    </div>
                </div>

                {/* Stats Grid */}
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                    <StatCard icon={<Trophy className="w-6 h-6" />} label="Battle Wins" value={profile.stats.battle_wins} />
                    <StatCard icon={<Shield className="w-6 h-6" />} label="Battle Fought" value={profile.stats.battle_fought} />
                    <StatCard icon={<Target className="w-6 h-6" />} label="Tasks Done" value={profile.stats.tasks_completed} />
                    <StatCard icon={<Star className="w-6 h-6" />} label="Total XP" value={profile.stats.total_xp} />
                </div>

                {/* Match History */}
                <h3 className="text-xl font-black uppercase mb-4 flex items-center gap-2">
                    <Swords className="w-6 h-6" /> Recent Battles
                </h3>
                <div className="space-y-4">
                    {profile.match_history.length > 0 ? (
                        profile.match_history.map((match: any) => (
                            <div key={match.id} className="bg-white border-3 border-black p-4 flex justify-between items-center shadow-sm">
                                <div>
                                    <div className="font-bold text-lg">VS {match.rival}</div>
                                    <div className="text-xs text-gray-500 font-bold">{new Date(match.date).toLocaleDateString()} • {match.duration} Days</div>
                                </div>
                                <div className={`font-black text-xl px-3 py-1 border-2 border-black ${match.result === 'WIN' ? 'bg-neo-primary' :
                                    match.result === 'LOSS' ? 'bg-red-400' : 'bg-gray-300'
                                    }`}>
                                    {match.result}
                                </div>
                            </div>
                        ))
                    ) : (
                        <div className="text-center py-8 text-gray-500 font-bold italic border-3 border-dashed border-gray-300">
                            NO BATTLE HISTORY RECORDED
                        </div>
                    )}
                </div>
            </div>

            {/* Challenge Modal */}
            {showChallengeModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
                    <div className="bg-neo-white border-4 border-black shadow-neo max-w-md w-full p-6 relative">
                        <button
                            onClick={() => setShowChallengeModal(false)}
                            className="absolute top-4 right-4 p-2 hover:bg-gray-200 border-2 border-black"
                        >
                            <X className="w-5 h-5" />
                        </button>

                        <h2 className="text-2xl font-black uppercase mb-6 flex items-center gap-2">
                            <Swords className="w-6 h-6" /> Challenge {profile.username}
                        </h2>

                        <div className="space-y-4">
                            {/* Opponent Info */}
                            <div className="bg-gray-100 border-3 border-black p-4">
                                <div className="text-xs font-bold text-gray-500 uppercase mb-1">Opponent</div>
                                <div className="font-black text-lg">{profile.username}</div>
                                <div className="text-sm text-gray-600">{profile.email}</div>
                            </div>

                            {/* Start Date */}
                            <div>
                                <label className="block text-xs font-bold mb-2 uppercase text-gray-500 flex items-center gap-1">
                                    <Calendar className="w-3 h-3" /> Battle Start Date
                                </label>
                                <select
                                    className="w-full border-3 border-black p-3 font-bold focus:outline-none focus:ring-2 focus:ring-neo-primary"
                                    value={startDate || ''}
                                    onChange={(e) => setStartDate(e.target.value)}
                                >
                                    <option value="">Select Date</option>
                                    {dateOptions.map(date => (
                                        <option key={date.toISOString()} value={date.toISOString().split('T')[0]}>
                                            {date.toLocaleDateString(undefined, { weekday: 'long', month: 'short', day: 'numeric' })}
                                        </option>
                                    ))}
                                </select>
                            </div>

                            {/* Duration */}
                            <div>
                                <label className="block text-xs font-bold mb-2 uppercase text-gray-500">Battle Duration</label>
                                <div className="flex gap-2">
                                    {[3, 4, 5].map(d => (
                                        <button
                                            key={d}
                                            onClick={() => setDuration(d)}
                                            className={`flex-1 py-3 border-3 border-black font-black text-lg transition-colors ${duration === d ? 'bg-neo-primary' : 'bg-white hover:bg-gray-200'
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
                                disabled={sendingInvite || !startDate}
                                className={`w-full py-4 font-black text-lg border-3 border-black shadow-neo transition-all active:translate-y-1 active:shadow-none flex items-center justify-center gap-2 ${sendingInvite || !startDate ? 'bg-gray-300 cursor-not-allowed' : 'bg-neo-primary hover:bg-green-400'
                                    }`}
                            >
                                {sendingInvite ? <Loader className="w-5 h-5 animate-spin" /> : <Swords className="w-5 h-5" />}
                                {sendingInvite ? 'SENDING...' : 'SEND CHALLENGE'}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

function StatCard({ icon, label, value }: { icon: any, label: string, value: string | number }) {
    return (
        <div className="bg-white border-3 border-black p-4 text-center shadow-neo-sm">
            <div className="flex justify-center mb-2 text-black">{icon}</div>
            <div className="text-2xl font-black">{value}</div>
            <div className="text-xs font-bold uppercase text-gray-500">{label}</div>
        </div>
    );
}
