import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Search, Swords, Shield, Trophy, Star, Target, Mail, Loader, Users, User } from 'lucide-react';
import { toast } from 'sonner';
import RankBadge from '../components/RankBadge';
import StatBox from '../components/StatBox';
import TabButton from '../components/TabButton';
import UserListItem from '../components/UserListItem';
import { useProfile } from '../hooks/useProfile';
import { useBattleInvites } from '../hooks/useBattleInvites';
import { useFollowing } from '../hooks/useFollowing';
import { useFollowers } from '../hooks/useFollowers';
import { useUserSearch } from '../hooks/useUserSearch';
import { useSocialMutations } from '../hooks/useSocialMutations';
import { useBattleMutations } from '../hooks/useBattleMutations';

export default function UserDashboard() {
    const { session } = useAuth();
    const navigate = useNavigate();

    // React Query hooks - replaces all manual data fetching
    const { data: profile } = useProfile();
    const { data: invites = [] } = useBattleInvites();
    const { data: following = [] } = useFollowing();
    const { data: followers = [] } = useFollowers();
    const { followMutation, unfollowMutation } = useSocialMutations();
    const { acceptInviteMutation, rejectInviteMutation } = useBattleMutations();

    // Social State
    const [searchQuery, setSearchQuery] = useState('');
    const [activeTab, setActiveTab] = useState<'following' | 'followers' | 'search'>('following');

    // Debounce search query
    const [debouncedQuery, setDebouncedQuery] = useState('');
    useEffect(() => {
        const timer = setTimeout(() => setDebouncedQuery(searchQuery), 300);
        return () => clearTimeout(timer);
    }, [searchQuery]);

    const { data: searchResults = [] } = useUserSearch(debouncedQuery);

    // Invite State
    const [searchEmail, setSearchEmail] = useState('');
    const [startDate, setStartDate] = useState<string | null>(null);
    const [duration, setDuration] = useState(5);
    const [loading, setLoading] = useState(false);
    const [inviteStatus, setInviteStatus] = useState<string | null>(null);

    const handleFollowToggle = async (userId: string, isCurrentlyFollowing: boolean) => {
        try {
            if (isCurrentlyFollowing) {
                await unfollowMutation.mutateAsync(userId);
            } else {
                await followMutation.mutateAsync(userId);
            }
        } catch (error) {
            console.error("Follow toggle failed", error);
            toast.error("Failed to update follow status");
        }
    };

    const handleSearch = (query: string) => {
        setSearchQuery(query);
    };

    const handleInvite = async () => {
        if (!startDate) {
            toast.error("Please select a start date first!");
            return;
        }
        if (!searchEmail) {
            toast.error("Please enter an email address!");
            return;
        }

        setLoading(true);
        try {
            // Step 1: Look up user by email/username to get their ID
            const searchResponse = await axios.get(`/api/social/search?q=${searchEmail}`, {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });

            // Try to find exact match by email or username
            let rivalUser = searchResponse.data.find((u: any) =>
                u.email?.toLowerCase() === searchEmail.toLowerCase() ||
                u.username?.toLowerCase() === searchEmail.toLowerCase()
            );

            if (!rivalUser) {
                toast.error(`User "${searchEmail}" not found in the system.`);
                setLoading(false);
                return;
            }

            // Step 2: Send invite using rival_id
            await axios.post('/api/battles/invite', {
                rival_id: rivalUser.id,
                start_date: startDate,
                duration: duration
            }, {
                headers: { Authorization: `Bearer ${session?.access_token} ` }
            });

            toast.success(`Invite sent to ${rivalUser.username}!`);
            setInviteStatus(`Invite sent to ${rivalUser.username}!`);
            setSearchEmail('');
            // Invites will auto-refresh via React Query
        } catch (error: any) {
            console.error('Failed to send invite:', error);
            const errorDetail = error.response?.data?.detail;
            toast.error(errorDetail || 'Failed to send invite');
        } finally {
            setLoading(false);
        }
    };

    const handleAccept = async (battleId: string) => {
        try {
            await acceptInviteMutation.mutateAsync(battleId);
            toast.success("Battle accepted! Good luck!");
            window.location.reload();
        } catch (error) {
            console.error("Failed to accept", error);
            toast.error("Failed to accept invite");
        }
    };

    const handleReject = async (battleId: string) => {
        try {
            await rejectInviteMutation.mutateAsync(battleId);
        } catch (error) {
            console.error("Failed to reject", error);
        }
    };

    // Date Options (Next 7 days)
    const dateOptions = Array.from({ length: 7 }, (_, i) => {
        const d = new Date();
        d.setDate(d.getDate() + i + 1);
        return d;
    });

    return (
        <div className="min-h-screen bg-neo-bg text-black font-sans p-4 md:p-8 pb-24">
            {/* Header */}
            <header className="w-full max-w-6xl mx-auto flex justify-between items-center mb-8">
                <div className="bg-neo-white border-3 border-black p-4 shadow-neo-sm">
                    <h1 className="text-2xl font-black italic uppercase">Lobby <span className="text-neo-primary">Station</span></h1>
                    <div className="text-xs font-bold text-gray-500">
                        FIND A RIVAL. START A WAR.
                    </div>
                </div>
                <div className="flex gap-2">
                    <motion.button
                        whileHover={{ scale: 1.05 }}
                        whileTap={{ scale: 0.95 }}
                        onClick={() => navigate('/profile')}
                        className="w-12 h-12 bg-white border-3 border-black shadow-neo flex items-center justify-center"
                    >
                        <User className="w-6 h-6" />
                    </motion.button>
                </div>
            </header>

            <div className="max-w-6xl mx-auto grid grid-cols-1 md:grid-cols-12 gap-8">

                {/* LEFT COLUMN: Stats & Profile */}
                <div className="md:col-span-4 space-y-8">
                    <div className="bg-neo-white border-4 border-black shadow-neo p-6">
                        <div
                            className="flex items-center gap-4 mb-6 cursor-pointer hover:bg-gray-50 -m-2 p-2 rounded transition-colors"
                            onClick={() => navigate('/profile')}
                            title="View my profile"
                        >
                            <div className="w-16 h-16 bg-neo-accent border-3 border-black rounded-full flex items-center justify-center">
                                <span className="text-3xl">{profile?.avatar_emoji || '😀'}</span>
                            </div>
                            <div>
                                <h2 className="text-2xl font-black uppercase hover:underline">{profile?.username || 'User'}</h2>
                                {profile?.rank && <RankBadge rank={profile.rank} level={profile.level} size="small" showLabel={false} />}
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-4">
                            <StatBox label="Wins" value={profile?.stats?.battle_wins} icon={<Trophy className="w-4 h-4" />} />
                            <StatBox label="Battles" value={profile?.stats?.battle_fought} icon={<Shield className="w-4 h-4" />} />
                            <StatBox label="XP" value={profile?.stats?.total_xp} icon={<Star className="w-4 h-4" />} />
                            <StatBox label="Tasks" value={profile?.stats?.tasks_completed} icon={<Target className="w-4 h-4" />} />
                        </div>
                    </div>

                    {/* Pending Invites */}
                    {invites.length > 0 && (
                        <div className="bg-yellow-300 border-4 border-black shadow-neo p-6">
                            <h3 className="text-xl font-black uppercase mb-4 flex items-center gap-2">
                                <Mail className="w-5 h-5" /> Pending Invites
                            </h3>
                            <div className="space-y-3">
                                {invites.map((invite: any) => (
                                    <div key={invite.id} className="bg-white border-3 border-black p-3">
                                        <div className="font-bold mb-1">VS {invite.user1?.username || 'Unknown'}</div>
                                        <div className="text-xs font-bold text-gray-500 mb-2">
                                            {invite.duration} Days • Starts {new Date(invite.start_date).toLocaleDateString()}
                                        </div>
                                        <div className="flex gap-2">
                                            <button
                                                onClick={() => handleAccept(invite.id)}
                                                className="flex-1 bg-neo-primary border-2 border-black font-bold py-1 hover:bg-green-400"
                                            >
                                                ACCEPT
                                            </button>
                                            <button
                                                onClick={() => handleReject(invite.id)}
                                                className="flex-1 bg-red-400 border-2 border-black font-bold py-1 hover:bg-red-500"
                                            >
                                                DECLINE
                                            </button>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>

                {/* RIGHT COLUMN: Battle Station & Social Hub */}
                <div className="md:col-span-8 space-y-8">

                    {/* BATTLE STATION (Challenge) */}
                    <div className="bg-neo-white border-4 border-black shadow-neo p-6">
                        <div className="bg-neo-accent border-3 border-black p-4 mb-6 -mt-10 mx-auto w-max shadow-neo-sm transform -rotate-1">
                            <h2 className="text-xl font-black uppercase flex items-center gap-2">
                                <Swords className="w-6 h-6" /> Battle Station
                            </h2>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                            {/* Settings */}
                            <div className="bg-gray-100 border-3 border-black p-4">
                                <h4 className="font-black uppercase mb-3 text-xs text-gray-500 flex items-center gap-1">
                                    <Target className="w-3 h-3" /> Mission Parameters
                                </h4>
                                <div className="space-y-4">
                                    <div>
                                        <label className="block text-[10px] font-bold mb-1 uppercase text-gray-400">Start Date</label>
                                        <select
                                            className="w-full border-2 border-black p-2 font-bold bg-white text-sm focus:outline-none focus:ring-2 focus:ring-neo-primary"
                                            value={startDate || ''}
                                            onChange={(e) => setStartDate(e.target.value)}
                                        >
                                            <option value="">Select Date</option>
                                            {dateOptions.map(date => (
                                                <option key={date.toISOString()} value={date.toISOString().split('T')[0]}>
                                                    {date.toLocaleDateString(undefined, { weekday: 'short', month: 'short', day: 'numeric' })}
                                                </option>
                                            ))}
                                        </select>
                                    </div>
                                    <div>
                                        <label className="block text-[10px] font-bold mb-1 uppercase text-gray-400">Duration</label>
                                        <div className="flex gap-1">
                                            {[3, 4, 5].map(d => (
                                                <button
                                                    key={d}
                                                    onClick={() => setDuration(d)}
                                                    className={`flex-1 border-2 border-black font-black py-1 text-sm ${duration === d ? 'bg-neo-primary' : 'bg-white hover:bg-gray-200'
                                                        }`}
                                                >
                                                    {d}D
                                                </button>
                                            ))}
                                        </div>
                                    </div>
                                </div>
                            </div>

                            {/* Invite Form */}
                            <div className="flex flex-col justify-between">
                                <div>
                                    <h4 className="font-black uppercase mb-3 text-xs text-gray-500 flex items-center gap-1">
                                        <Mail className="w-3 h-3" /> Direct Challenge
                                    </h4>
                                    <div className="relative mb-2">
                                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                                        <input
                                            type="email"
                                            placeholder="rival@example.com"
                                            className="w-full border-3 border-black p-2 pl-9 font-bold text-sm focus:outline-none focus:ring-2 focus:ring-neo-primary"
                                            value={searchEmail}
                                            onChange={(e) => setSearchEmail(e.target.value)}
                                        />
                                    </div>
                                </div>

                                <button
                                    onClick={handleInvite}
                                    disabled={loading || !searchEmail || !startDate}
                                    className={`w-full py-3 font-black border-3 border-black shadow-neo-sm transition-all active:translate-y-1 active:shadow-none flex items-center justify-center gap-2 ${loading || !searchEmail || !startDate ? 'bg-gray-300 cursor-not-allowed' : 'bg-neo-primary hover:bg-green-400'
                                        }`}
                                >
                                    {loading ? <Loader className="w-4 h-4 animate-spin" /> : "SEND INVITE"}
                                </button>
                                {inviteStatus && <p className="mt-2 text-xs font-bold text-center text-green-600">{inviteStatus}</p>}
                            </div>
                        </div>
                    </div>

                    {/* SOCIAL HUB */}
                    <div className="bg-neo-white border-4 border-black shadow-neo min-h-[400px] flex flex-col">
                        <div className="bg-black text-white p-4">
                            <h2 className="text-xl font-black uppercase flex items-center gap-2 mb-3 md:mb-0">
                                <Users className="w-5 h-5" /> Social Hub
                            </h2>
                            <div className="flex gap-2 text-xs md:text-sm flex-wrap">
                                <TabButton active={activeTab === 'following'} onClick={() => setActiveTab('following')}>Following</TabButton>
                                <TabButton active={activeTab === 'followers'} onClick={() => setActiveTab('followers')}>Followers</TabButton>
                                <TabButton active={activeTab === 'search'} onClick={() => setActiveTab('search')}>Find Users</TabButton>
                            </div>
                        </div>

                        <div className="p-6 flex-1">
                            {activeTab === 'following' && (
                                <div className="space-y-3">
                                    {following.length > 0 ? (
                                        following.map((f: any) => (
                                            <UserListItem
                                                key={f.id}
                                                user={f}
                                                onProfile={() => navigate(`/user/${f.username}`)}
                                                isFollowing={true}
                                                onFollowToggle={() => handleFollowToggle(f.id, true)}
                                            />
                                        ))
                                    ) : (
                                        <div className="text-center py-12 text-gray-400 font-bold italic border-2 border-dashed border-gray-300">
                                            You are not following anyone yet.
                                        </div>
                                    )}
                                </div>
                            )}

                            {activeTab === 'followers' && (
                                <div className="space-y-3">
                                    {followers.length > 0 ? (
                                        followers.map((f: any) => {
                                            const isFollowingBack = following.some((followed: any) => followed.id === f.id);
                                            return (
                                                <UserListItem
                                                    key={f.id}
                                                    user={f}
                                                    onProfile={() => navigate(`/user/${f.username}`)}
                                                    isFollowing={isFollowingBack}
                                                    onFollowToggle={() => handleFollowToggle(f.id, isFollowingBack)}
                                                />
                                            );
                                        })
                                    ) : (
                                        <div className="text-center py-12 text-gray-400 font-bold italic border-2 border-dashed border-gray-300">
                                            No followers yet.
                                        </div>
                                    )}
                                </div>
                            )}

                            {activeTab === 'search' && (
                                <div>
                                    <div className="relative mb-6">
                                        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
                                        <input
                                            type="text"
                                            placeholder="Search users by username..."
                                            className="w-full border-3 border-black p-3 pl-12 font-bold text-lg focus:outline-none focus:ring-4 focus:ring-neo-primary/50"
                                            value={searchQuery}
                                            onChange={(e) => handleSearch(e.target.value)}
                                        />
                                    </div>
                                    <div className="space-y-3">
                                        {searchResults.map((u: any) => {
                                            const isFollowingUser = following.some((f: any) => f.id === u.id);
                                            return (
                                                <UserListItem
                                                    key={u.id}
                                                    user={u}
                                                    onProfile={() => navigate(`/user/${u.username}`)}
                                                    isFollowing={isFollowingUser}
                                                    onFollowToggle={() => handleFollowToggle(u.id, isFollowingUser)}
                                                />
                                            );
                                        })}
                                        {searchQuery.length > 1 && searchResults.length === 0 && (
                                            <div className="text-center py-8 text-gray-400 font-bold">
                                                No users found.
                                            </div>
                                        )}
                                    </div>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}
