import { useNavigate } from 'react-router-dom';
import { User } from 'lucide-react';
import type { LobbyProfileData } from '../../types/lobby';

interface LobbyHeaderProps {
    profile: LobbyProfileData | null;
}

export function LobbyHeader({ profile }: LobbyHeaderProps) {
    const navigate = useNavigate();

    if (!profile) {
        return (
            <div className="max-w-6xl mx-auto mb-8">
                <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000] p-6">
                    <div className="animate-pulse">Loading profile...</div>
                </div>
            </div>
        );
    }

    return (
        <div className="max-w-6xl mx-auto mb-8">
            <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000] p-6 flex items-center justify-between">
                <div className="flex items-center gap-4">
                    <div className="w-16 h-16 bg-[#F4A261] border-3 border-black flex items-center justify-center">
                        <span className="text-3xl">{profile.avatar_emoji || '😀'}</span>
                    </div>
                    <div>
                        <h1 className="text-3xl font-black uppercase">{profile.username}</h1>
                        <div className="flex items-center gap-2 mt-1">
                            <span className="bg-[#F4A261] border-2 border-black px-2 py-0.5 text-xs font-black">
                                LEVEL {profile.level || 1}
                            </span>
                            {profile.rank && (
                                <span className="bg-[#E63946] border-2 border-black px-2 py-0.5 text-xs font-black text-white">
                                    {profile.rank.toUpperCase()}
                                </span>
                            )}
                            <span className="text-xs font-mono font-bold text-gray-500">
                                STREAK: {profile.stats?.current_streak || 0}🔥
                            </span>
                        </div>
                    </div>
                </div>

                <div className="flex gap-2">
                    <button
                        onClick={() => navigate('/profile')}
                        className="p-3 bg-white border-3 border-black shadow-[3px_3px_0_0_#000] hover:translate-x-[1px] hover:translate-y-[1px] hover:shadow-[2px_2px_0_0_#000] transition-all"
                        aria-label="View profile"
                    >
                        <User className="w-5 h-5" />
                    </button>
                </div>
            </div>
        </div>
    );
}
