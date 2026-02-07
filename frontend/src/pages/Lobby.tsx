import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Swords, Trophy, Star, Target, Mail, Loader, Users, User, Compass } from 'lucide-react';
import { toast } from 'sonner';
import TabButton from '../components/TabButton';
import UserCard from '../components/UserCard';
import MonsterSelect from '../components/MonsterSelect';
import StatCard from '../components/StatCard';
import { useProfile } from '../hooks/useProfile';
import { useBattleInvites } from '../hooks/useBattleInvites';
import { useFollowing } from '../hooks/useFollowing';
import { useFollowers } from '../hooks/useFollowers';
import { useUserSearch } from '../hooks/useUserSearch';
import { useSocialMutations } from '../hooks/useSocialMutations';
import { useBattleMutations } from '../hooks/useBattleMutations';
import { useChallengeMutations } from '../hooks/useChallengeMutations';
import { useMonsters } from '../hooks/useMonsters';
import { useAdventureMutations } from '../hooks/useAdventureMutations';

export default function Lobby() {
    const navigate = useNavigate();

    // React Query hooks
    const { data: profile } = useProfile();
    const { data: invites = [] } = useBattleInvites();
    const { data: following = [] } = useFollowing();
    const { data: followers = [] } = useFollowers();
    const { followMutation, unfollowMutation } = useSocialMutations();
    const { acceptInviteMutation, rejectInviteMutation } = useBattleMutations();
    const { sendChallengeByEmailMutation, isSending: isInviteSending } = useChallengeMutations();

    // Adventure hooks
    const [showMonsterSelect, setShowMonsterSelect] = useState(false);
    const { data: monsterPool } = useMonsters();
    const { startAdventureMutation, refreshMonstersMutation } = useAdventureMutations();
    const { refetch: refetchProfile } = useProfile();

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

        await sendChallengeByEmailMutation.mutateAsync({
            emailOrUsername: searchEmail,
            startDate: startDate,
            duration: duration
        });

        setSearchEmail('');
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

    const handleStartAdventure = async (monsterId: string) => {
        try {
            await startAdventureMutation.mutateAsync(monsterId);
            toast.success("Adventure started! Good luck!");
            setShowMonsterSelect(false);
            await refetchProfile();
            navigate('/arena');
        } catch (error: any) {
            console.error("Failed to start adventure", error);
            toast.error(error.response?.data?.detail || "Failed to start adventure");
        }
    };

    const handleRefreshMonsters = async () => {
        try {
            await refreshMonstersMutation.mutateAsync();
        } catch (error: any) {
            console.error("Failed to refresh monsters", error);
            toast.error(error.response?.data?.detail || "No refreshes remaining");
        }
    };

    // Date Options (Next 7 days)
    const dateOptions = Array.from({ length: 7 }, (_, i) => {
        const d = new Date();
        d.setDate(d.getDate() + i + 1);
        return d;
    });

    return (
        <div className="min-h-screen bg-[#E8E4D9] neo-grid-bg p-4 md:p-8">
            {/* Header */}
            <div className="max-w-6xl mx-auto mb-8">
                <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000] p-6 flex items-center justify-between">
                    <div className="flex items-center gap-4">
                        <div className="w-16 h-16 bg-[#F4A261] border-3 border-black flex items-center justify-center">
                            <span className="text-3xl">{profile?.avatar_emoji || '😀'}</span>
                        </div>
                        <div>
                            <h1 className="text-3xl font-black uppercase">{profile?.username || 'User'}</h1>
                            <div className="flex items-center gap-2 mt-1">
                                <span className="bg-[#F4A261] border-2 border-black px-2 py-0.5 text-xs font-black">
                                    LEVEL {profile?.level || 1}
                                </span>
                                {profile?.rank && (
                                    <span className="bg-[#E63946] border-2 border-black px-2 py-0.5 text-xs font-black text-white">
                                        {profile.rank.toUpperCase()}
                                    </span>
                                )}
                                <span className="text-xs font-mono font-bold text-gray-500">
                                    STREAK: {profile?.stats?.current_streak || 0}🔥
                                </span>
                            </div>
                        </div>
                    </div>

                    <div className="flex gap-2">
                        <button
                            onClick={() => navigate('/profile')}
                            className="p-3 bg-white border-3 border-black shadow-[3px_3px_0_0_#000] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0_0_#000] transition-all"
                        >
                            <User className="w-5 h-5" />
                        </button>
                    </div>
                </div>
            </div>

            <div className="max-w-6xl mx-auto grid md:grid-cols-12 gap-6">
                {/* Left Column - Stats */}
                <div className="md:col-span-4 space-y-6">
                    {/* Stats Card */}
                    <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000]">
                        <div className="bg-black text-white p-3 border-b-4 border-black">
                            <h3 className="text-sm font-black uppercase font-mono">// STATISTICS</h3>
                        </div>
                        <div className="p-4 grid grid-cols-2 gap-3">
                            <StatCard label="WINS" value={profile?.stats?.battle_wins || 0} icon={<Trophy className="w-4 h-4" />} color="bg-[#2A9D8F]" />
                            <StatCard label="BATTLES" value={profile?.stats?.battle_fought || 0} icon={<Swords className="w-4 h-4" />} color="bg-[#457B9D]" />
                            <StatCard label="TASKS" value={profile?.stats?.tasks_completed || 0} icon={<Target className="w-4 h-4" />} color="bg-[#F4A261]" />
                            <StatCard label="XP" value={profile?.stats?.total_xp || 0} icon={<Star className="w-4 h-4" />} color="bg-[#9D4EDD]" />
                        </div>
                    </div>

                    {/* Match History - placeholder for now, will be populated when API returns match history */}
                    <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000]">
                        <div className="bg-black text-white p-3 border-b-4 border-black">
                            <h3 className="text-sm font-black uppercase font-mono">// RECENT BATTLES</h3>
                        </div>
                        <div className="p-4 text-center text-gray-400 font-bold text-sm">
                            No recent battles
                        </div>
                    </div>

                    {/* Pending Invites */}
                    {invites.length > 0 && (
                        <div className="bg-[#F4A261] border-4 border-black shadow-[6px_6px_0_0_#000] p-6">
                            <h3 className="text-xl font-black uppercase mb-4 flex items-center gap-2">
                                <Mail className="w-5 h-5" /> PENDING INVITES
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
                                                className="flex-1 bg-[#2A9D8F] border-2 border-black font-bold py-1 text-white hover:bg-[#238B80]"
                                            >
                                                ACCEPT
                                            </button>
                                            <button
                                                onClick={() => handleReject(invite.id)}
                                                className="flex-1 bg-[#E63946] border-2 border-black font-bold py-1 text-white hover:bg-[#c42d37]"
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

                {/* Right Column - Battle Station & Social Hub */}
                <div className="md:col-span-8 space-y-6">
                    {/* Battle Station */}
                    <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000]">
                        <div className="bg-[#E63946] text-white p-4 border-b-4 border-black">
                            <h2 className="text-xl font-black uppercase flex items-center gap-2">
                                <Swords className="w-6 h-6" /> Battle Station
                            </h2>
                            <p className="text-sm font-mono opacity-80">[ INITIATE PVP COMBAT ]</p>
                        </div>

                        <div className="p-6 grid md:grid-cols-2 gap-6">
                            {/* Settings */}
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-xs font-black uppercase font-mono mb-2">
                                        [ START DATE ]
                                    </label>
                                    <select
                                        className="w-full border-3 border-black p-3 font-bold bg-white focus:outline-none focus:shadow-[4px_4px_0_0_#E63946]"
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
                                    <label className="block text-xs font-black uppercase font-mono mb-2">
                                        [ DURATION ]
                                    </label>
                                    <div className="flex gap-2">
                                        {[3, 4, 5].map(d => (
                                            <button
                                                key={d}
                                                onClick={() => setDuration(d)}
                                                className={`flex-1 border-3 border-black p-3 font-black transition-all ${
                                                    duration === d
                                                        ? 'bg-[#E63946] text-white shadow-[3px_3px_0_0_#000]'
                                                        : 'bg-white hover:bg-gray-100'
                                                }`}
                                            >
                                                {d}D
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            </div>

                            {/* Challenge Form */}
                            <div className="space-y-4">
                                <div>
                                    <label className="block text-xs font-black uppercase font-mono mb-2">
                                        [ CHALLENGE EMAIL ]
                                    </label>
                                    <div className="relative">
                                        <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                                        <input
                                            type="email"
                                            placeholder="rival@productivity.go"
                                            className="w-full border-3 border-black p-3 pl-10 font-bold focus:outline-none focus:shadow-[4px_4px_0_0_#E63946]"
                                            value={searchEmail}
                                            onChange={(e) => setSearchEmail(e.target.value)}
                                        />
                                    </div>
                                </div>

                                <button
                                    onClick={handleInvite}
                                    disabled={isInviteSending || !searchEmail || !startDate}
                                    className={`w-full border-3 border-black p-4 font-black uppercase text-white shadow-[4px_4px_0_0_#000] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0_0_#000] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none transition-all flex items-center justify-center gap-2 ${
                                        isInviteSending || !searchEmail || !startDate
                                            ? 'bg-gray-300 cursor-not-allowed'
                                            : 'bg-[#E63946]'
                                    }`}
                                >
                                    {isInviteSending ? <Loader className="w-4 h-4 animate-spin" /> : <Swords className="w-5 h-5" />}
                                    {isInviteSending ? 'SENDING...' : 'SEND CHALLENGE'}
                                </button>
                            </div>
                        </div>
                    </div>

                    {/* Adventure Station */}
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
                                onClick={() => setShowMonsterSelect(true)}
                                className="w-full bg-[#9D4EDD] border-3 border-black p-4 font-black uppercase text-white shadow-[4px_4px_0_0_#000] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0_0_#000] active:translate-x-[4px] active:translate-y-[4px] active:shadow-none transition-all flex items-center justify-center gap-2"
                            >
                                <Compass className="w-5 h-5" /> START ADVENTURE
                            </button>
                        </div>
                    </div>

                    {/* Social Hub */}
                    <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000]">
                        <div className="bg-black text-white p-4 border-b-4 border-black flex items-center justify-between">
                            <h2 className="text-xl font-black uppercase flex items-center gap-2">
                                <Users className="w-6 h-6" /> Social Hub
                            </h2>
                            <div className="flex gap-1">
                                <TabButton active={activeTab === 'following'} onClick={() => setActiveTab('following')}>FOLLOWING</TabButton>
                                <TabButton active={activeTab === 'followers'} onClick={() => setActiveTab('followers')}>FOLLOWERS</TabButton>
                                <TabButton active={activeTab === 'search'} onClick={() => setActiveTab('search')}>SEARCH</TabButton>
                            </div>
                        </div>

                        <div className="p-4">
                            {activeTab === 'following' && (
                                <div className="space-y-2">
                                    {following.length > 0 ? (
                                        following.map((f: any) => (
                                            <UserCard
                                                key={f.id}
                                                user={f}
                                                onViewProfile={() => navigate(`/user/${f.username}`)}
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
                                <div className="space-y-2">
                                    {followers.length > 0 ? (
                                        followers.map((f: any) => {
                                            const isFollowingBack = following.some((followed: any) => followed.id === f.id);
                                            return (
                                                <UserCard
                                                    key={f.id}
                                                    user={f}
                                                    onViewProfile={() => navigate(`/user/${f.username}`)}
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
                                <div className="space-y-4">
                                    <div className="relative">
                                        <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
                                        <input
                                            type="text"
                                            value={searchQuery}
                                            onChange={(e) => handleSearch(e.target.value)}
                                            placeholder="Search warriors..."
                                            className="w-full border-3 border-black p-3 pl-10 font-bold focus:outline-none focus:shadow-[4px_4px_0_0_#9D4EDD]"
                                        />
                                    </div>
                                    <div className="space-y-2 max-h-64 overflow-y-auto">
                                        {searchResults.map((u: any) => {
                                            const isFollowingUser = following.some((f: any) => f.id === u.id);
                                            return (
                                                <UserCard
                                                    key={u.id}
                                                    user={u}
                                                    onViewProfile={() => navigate(`/user/${u.username}`)}
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

            {/* Monster Select Modal */}
            {showMonsterSelect && monsterPool && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000] max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                        <div className="bg-[#9D4EDD] p-4 border-b-4 border-black flex justify-between items-center">
                            <h2 className="text-xl font-black uppercase text-white">Choose Your Monster</h2>
                            <button
                                onClick={() => setShowMonsterSelect(false)}
                                className="w-8 h-8 bg-white border-2 border-black font-black hover:bg-gray-100"
                            >
                                ✕
                            </button>
                        </div>

                        <div className="p-6">
                            <div className="flex justify-between items-center mb-4">
                                <div className="text-sm font-bold text-gray-500">
                                    Rating: {monsterPool.current_rating} |
                                    Unlocked: {monsterPool.unlocked_tiers.join(', ')}
                                </div>
                            </div>

                            <MonsterSelect
                                monsters={monsterPool.monsters}
                                refreshesRemaining={monsterPool.refreshes_remaining}
                                onSelect={handleStartAdventure}
                                onRefresh={handleRefreshMonsters}
                                isLoading={startAdventureMutation.isPending}
                                isRefreshing={refreshMonstersMutation.isPending}
                            />
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}
