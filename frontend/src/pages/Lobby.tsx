import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { toast } from 'sonner';
import MonsterSelect from '../components/MonsterSelect';
import ActiveSessionBanner from '../components/ActiveSessionBanner';
import NeoModal from '../components/NeoModal';
import { useProfile } from '../hooks/useProfile';
import { useBattleInvites } from '../hooks/useBattleInvites';
import { useFollowing } from '../hooks/useFollowing';
import { useFollowers } from '../hooks/useFollowers';
import { useSocialMutations } from '../hooks/useSocialMutations';
import { useBattleMutations } from '../hooks/useBattleMutations';
import { useMonsters } from '../hooks/useMonsters';
import { useAdventureMutations } from '../hooks/useAdventureMutations';
import { useUserSearch } from '../hooks/useUserSearch';
import { useActiveSession } from '../hooks/lobby/useActiveSession';
import { useInviteForm } from '../hooks/lobby/useInviteForm';
import { LobbyHeader } from '../components/lobby/LobbyHeader';
import { LobbyStatsPanel } from '../components/lobby/LobbyStatsPanel';
import { BattleStation } from '../components/lobby/BattleStation';
import { AdventureStation } from '../components/lobby/AdventureStation';
import { SocialHub } from '../components/lobby/SocialHub';
import type { SocialTab } from '../types/lobby';

/**
 * Lobby page - Main dashboard for the app.
 *
 * Displays user profile, stats, battle station, adventure station,
 * and social hub for following/following users.
 *
 * REFACTOR-005: Phase 5 - Item 6.2
 * - Extracted components for better maintainability
 * - Extracted hooks for session detection and form state
 * - Reduced from 567 lines to ~150 lines
 */
export default function Lobby() {
    const navigate = useNavigate();

    // React Query hooks
    const { data: profile } = useProfile();
    const { data: invites = [] } = useBattleInvites();
    const { data: following = [] } = useFollowing();
    const { data: followers = [] } = useFollowers();
    const { followMutation, unfollowMutation } = useSocialMutations();
    const { acceptInviteMutation, rejectInviteMutation } = useBattleMutations();

    // Adventure hooks
    const [showMonsterSelect, setShowMonsterSelect] = useState(false);
    const { data: monsterPool } = useMonsters();
    const { startAdventureMutation, refreshMonstersMutation } = useAdventureMutations();
    const { refetch: refetchProfile } = useProfile();

    // Active session detection
    const { showBanner, bannerProps } = useActiveSession(profile);

    // Invite form hook
    const inviteForm = useInviteForm();

    // Social state
    const [activeTab, setActiveTab] = useState<SocialTab['following']>('following');
    const [searchQuery, setSearchQuery] = useState('');

    // Debounced search for SocialHub
    const [debouncedQuery, setDebouncedQuery] = useState('');
    useEffect(() => {
        const timer = setTimeout(() => setDebouncedQuery(searchQuery), 300);
        return () => clearTimeout(timer);
    }, [searchQuery]);

    const { data: searchResults = [] } = useUserSearch(debouncedQuery);

    // Event handlers
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

    return (
        <div className="min-h-screen bg-[#E8E4D9] neo-grid-bg p-4 md:p-8">
            {/* Header */}
            <LobbyHeader profile={profile} />

            {/* Active Session Banner */}
            {showBanner && bannerProps && (
                <div className="max-w-6xl mx-auto mb-8">
                    <ActiveSessionBanner
                        {...bannerProps}
                        onGoToArena={() => navigate('/arena')}
                    />
                </div>
            )}

            <div className="max-w-6xl mx-auto grid md:grid-cols-12 gap-6">
                {/* Left Column - Stats */}
                <LobbyStatsPanel
                    profile={profile}
                    invites={invites}
                    onAcceptInvite={handleAccept}
                    onRejectInvite={handleReject}
                />

                {/* Right Column - Battle Station & Social Hub */}
                <div className="md:col-span-8 space-y-6">
                    {!showBanner && (
                        <>
                            <BattleStation {...inviteForm} />
                            <AdventureStation
                                onStartAdventure={() => setShowMonsterSelect(true)}
                            />
                        </>
                    )}

                    <SocialHub
                        activeTab={activeTab}
                        onTabChange={setActiveTab}
                        searchQuery={searchQuery}
                        onSearchChange={setSearchQuery}
                        following={following}
                        followers={followers}
                        searchResults={searchResults}
                        onFollowToggle={handleFollowToggle}
                        onViewProfile={(username) => navigate(`/user/${username}`)}
                    />
                </div>
            </div>

            {/* Monster Select Modal */}
            <NeoModal
                isOpen={showMonsterSelect && !!monsterPool}
                onClose={() => setShowMonsterSelect(false)}
                maxWidth="max-w-2xl"
                maxHeight="max-h-[90vh]"
                showCloseButton={false}
            >
                <div className="bg-[#9D4EDD] p-4 -mx-6 -mt-6 border-b-4 border-black flex justify-between items-center">
                    <h2 className="text-xl font-black uppercase text-white">Choose Your Monster</h2>
                    <button
                        onClick={() => setShowMonsterSelect(false)}
                        className="w-8 h-8 bg-white border-2 border-black font-black hover:bg-gray-100"
                    >
                        ✕
                    </button>
                </div>

                <div className="p-6">
                    {monsterPool && (
                        <>
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
                        </>
                    )}
                </div>
            </NeoModal>
        </div>
    );
}
