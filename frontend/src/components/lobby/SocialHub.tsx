import { Users, Search } from 'lucide-react';
import TabButton from '../TabButton';
import UserCard from '../UserCard';
import type { SocialUser } from '../../types/profile';
import type { SocialTab } from '../../types/lobby';

interface SocialHubProps {
    activeTab: SocialTab['following'];
    onTabChange: (tab: SocialTab['following']) => void;
    searchQuery: string;
    onSearchChange: (query: string) => void;
    following: SocialUser[];
    followers: SocialUser[];
    searchResults: SocialUser[];
    onFollowToggle: (userId: string, isCurrentlyFollowing: boolean) => Promise<void>;
    onViewProfile: (username: string) => void;
}

export function SocialHub({
    activeTab,
    onTabChange,
    searchQuery,
    onSearchChange,
    following,
    followers,
    searchResults,
    onFollowToggle,
    onViewProfile
}: SocialHubProps) {

    return (
        <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000]">
            <div className="bg-black text-white p-4 border-b-4 border-black flex items-center justify-between">
                <h2 className="text-xl font-black uppercase flex items-center gap-2">
                    <Users className="w-6 h-6" /> Social Hub
                </h2>
                <div className="flex gap-1">
                    <TabButton active={activeTab === 'following'} onClick={() => onTabChange('following')}>FOLLOWING</TabButton>
                    <TabButton active={activeTab === 'followers'} onClick={() => onTabChange('followers')}>FOLLOWERS</TabButton>
                    <TabButton active={activeTab === 'search'} onClick={() => onTabChange('search')}>SEARCH</TabButton>
                </div>
            </div>

            <div className="p-4">
                {activeTab === 'following' && (
                    <div className="space-y-2">
                        {following.length > 0 ? (
                            following.map((f: SocialUser, i: number) => (
                                <UserCard
                                    key={f.id || `following-${i}`}
                                    user={f}
                                    onViewProfile={() => onViewProfile(f.username)}
                                    isFollowing={true}
                                    onFollowToggle={() => onFollowToggle(f.id, true)}
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
                            followers.map((f: SocialUser, i: number) => {
                                const isFollowingBack = following.some((followed: SocialUser) => followed.id === f.id);
                                return (
                                    <UserCard
                                        key={f.id || `follower-${i}`}
                                        user={f}
                                        onViewProfile={() => onViewProfile(f.username)}
                                        isFollowing={isFollowingBack}
                                        onFollowToggle={() => onFollowToggle(f.id, isFollowingBack)}
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
                                onChange={(e) => onSearchChange(e.target.value)}
                                placeholder="Search warriors..."
                                className="w-full border-3 border-black p-3 pl-10 font-bold focus:outline-none focus:shadow-[4px_4px_0_0_#9D4EDD]"
                            />
                        </div>
                        <div className="space-y-2 max-h-64 overflow-y-auto">
                            {searchResults.map((u: SocialUser, i: number) => {
                                const isFollowingUser = following.some((f: SocialUser) => f.id === u.id);
                                return (
                                    <UserCard
                                        key={u.id || `search-${i}`}
                                        user={u}
                                        onViewProfile={() => onViewProfile(u.username)}
                                        isFollowing={isFollowingUser}
                                        onFollowToggle={() => onFollowToggle(u.id, isFollowingUser)}
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
    );
}
