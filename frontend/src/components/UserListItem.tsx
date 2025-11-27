import React, { useState } from 'react';
import RankBadge from './RankBadge';

interface UserListItemProps {
    user: any;
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
        <div className="bg-white border-3 border-black p-4 flex items-center justify-between shadow-sm hover:shadow-md transition-shadow">
            <div className="flex items-center gap-4 cursor-pointer" onClick={onProfile}>
                <div className="w-12 h-12 bg-neo-accent rounded-full border-2 border-black flex items-center justify-center">
                    <span className="text-2xl">{user.avatar_emoji || '😀'}</span>
                </div>
                <div>
                    <div className="font-black text-lg hover:underline">{user.username}</div>
                    {user.rank && <RankBadge rank={user.rank} level={user.level} size="small" showLabel={false} />}
                </div>
            </div>
            <button
                onClick={handleFollowClick}
                disabled={loading}
                className={`border-2 border-black px-4 py-2 font-bold text-sm transition-colors ${loading ? 'bg-gray-300 cursor-wait' :
                    isFollowing ? 'bg-red-400 hover:bg-red-500 text-white' : 'bg-neo-primary hover:bg-green-400'
                    }`}
            >
                {loading ? 'Loading...' : isFollowing ? 'UNFOLLOW' : 'FOLLOW'}
            </button>
        </div>
    );
}
