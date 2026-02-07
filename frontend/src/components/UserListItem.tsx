import React, { useState } from 'react';
import RankBadge from './RankBadge';
import type { SocialUser } from '../types/profile';

interface UserListItemProps {
    user: SocialUser;
    onProfile: () => void;
    isFollowing: boolean;
    onFollowToggle: () => Promise<void>;
}

export default function UserListItem({ user, onProfile, isFollowing, onFollowToggle }: UserListItemProps) {
    const [loading, setLoading] = useState(false);

    const handleFollowClick = async (e: React.MouseEvent) => {
        e.stopPropagation();
        setLoading(true);
        await onFollowToggle();
        setLoading(false);
    };

    return (
        <div className="bg-white border-3 border-black p-4 flex items-center justify-between shadow-[3px_3px_0_0_#000] hover:translate-y-0.5 hover:shadow-[2px_2px_0_0_#000] transition-all">
            <div className="flex items-center gap-4 cursor-pointer" onClick={onProfile}>
                <div className="w-12 h-12 bg-[#F4A261] border-3 border-black flex items-center justify-center shadow-[2px_2px_0_0_#000]">
                    <span className="text-2xl">{user.avatar_emoji || '😀'}</span>
                </div>
                <div>
                    <div className="font-black text-lg hover:underline uppercase">{user.username}</div>
                    {user.rank && <RankBadge rank={user.rank} level={user.level} size="small" showLabel={false} />}
                </div>
            </div>
            <button
                onClick={handleFollowClick}
                disabled={loading}
                className={`border-3 border-black px-4 py-2 font-black text-sm transition-all shadow-[2px_2px_0_0_#000] active:translate-y-0.5 active:shadow-none ${loading ? 'bg-gray-300 cursor-wait' :
                    isFollowing ? 'bg-gray-300 hover:bg-gray-400' : 'bg-[#2A9D8F] text-white hover:bg-[#21867a]'
                    }`}
            >
                {loading ? '...' : isFollowing ? 'UNFOLLOW' : 'FOLLOW'}
            </button>
        </div>
    );
}
