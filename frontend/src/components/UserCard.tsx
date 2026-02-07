import { useState } from 'react';
import { motion } from 'framer-motion';

interface UserCardProps {
    user: any;
    onViewProfile: () => void;
    isFollowing?: boolean;
    onFollowToggle?: () => Promise<void>;
}

/**
 * UserCard component for Design 1
 * Used in Lobby Social Hub with square avatar and VIEW button
 * Optionally supports follow toggle functionality
 */
export default function UserCard({ user, onViewProfile, isFollowing, onFollowToggle }: UserCardProps) {
    const [loading, setLoading] = useState(false);
    const hasFollowAction = !!onFollowToggle;

    const handleFollowClick = async (e: React.MouseEvent) => {
        e.stopPropagation();
        if (!onFollowToggle) return;
        setLoading(true);
        try {
            await onFollowToggle();
        } finally {
            setLoading(false);
        }
    };

    return (
        <motion.div
            whileHover={{ x: 2 }}
            className="flex items-center justify-between p-3 border-2 border-black bg-gray-50 cursor-pointer hover:bg-white hover:shadow-[3px_3px_0_0_#000] transition-all"
            onClick={onViewProfile}
        >
            <div className="flex items-center gap-3">
                <div className="w-10 h-10 bg-[#F4A261] border-2 border-black flex items-center justify-center">
                    <span className="text-xl">{user.avatar_emoji || '😀'}</span>
                </div>
                <div>
                    <div className="font-black text-sm">{user.username}</div>
                    <div className="text-xs font-mono text-gray-500">
                        LVL {user.level || 1} · {(user.rank || 'BRONZE').toUpperCase()}
                    </div>
                </div>
            </div>
            {hasFollowAction ? (
                <button
                    onClick={handleFollowClick}
                    disabled={loading}
                    className={`px-3 py-1 text-xs font-black border-2 border-black transition-colors ${
                        loading
                            ? 'bg-gray-300 cursor-wait'
                            : isFollowing
                            ? 'bg-[#E63946] text-white hover:bg-[#c42d37]'
                            : 'bg-[#2A9D8F] text-white hover:bg-[#238B80]'
                    }`}
                >
                    {loading ? '...' : isFollowing ? 'UNFOLLOW' : 'FOLLOW'}
                </button>
            ) : (
                <button className="px-3 py-1 text-xs font-black border-2 border-black bg-[#2A9D8F] text-white hover:bg-[#238B80]">
                    VIEW
                </button>
            )}
        </motion.div>
    );
}
