import { Trophy, Swords, Target, Star, Mail } from 'lucide-react';
import StatCard from '../StatCard';
import MatchHistoryItem from '../MatchHistoryItem';
import type { LobbyProfileData } from '../../types/lobby';

interface BattleInviteData {
    id: string;
    user1?: {
        username?: string;
    };
    duration: number;
    start_date: string;
}

interface LobbyStatsPanelProps {
    profile: LobbyProfileData | null;
    invites: BattleInviteData[];
    onAcceptInvite: (battleId: string) => void;
    onRejectInvite: (battleId: string) => void;
}

export function LobbyStatsPanel({
    profile,
    invites,
    onAcceptInvite,
    onRejectInvite
}: LobbyStatsPanelProps) {
    if (!profile) {
        return (
            <div className="md:col-span-4 space-y-6">
                <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000] p-6">
                    <div className="animate-pulse">Loading stats...</div>
                </div>
            </div>
        );
    }

    return (
        <div className="md:col-span-4 space-y-6">
            <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000]">
                <div className="bg-black text-white p-3 border-b-4 border-black">
                    <h3 className="text-sm font-black uppercase font-mono">// STATISTICS</h3>
                </div>
                <div className="p-4 grid grid-cols-2 gap-3">
                    <StatCard
                        label="WINS"
                        value={profile.stats?.battle_wins || 0}
                        icon={<Trophy className="w-4 h-4" />}
                        color="bg-[#2A9D8F]"
                    />
                    <StatCard
                        label="BATTLES"
                        value={profile.stats?.battle_fought || 0}
                        icon={<Swords className="w-4 h-4" />}
                        color="bg-[#457B9D]"
                    />
                    <StatCard
                        label="TASKS"
                        value={profile.stats?.tasks_completed || 0}
                        icon={<Target className="w-4 h-4" />}
                        color="bg-[#F4A261]"
                    />
                    <StatCard
                        label="XP"
                        value={profile.stats?.total_xp || 0}
                        icon={<Star className="w-4 h-4" />}
                        color="bg-[#9D4EDD]"
                    />
                </div>
            </div>

            <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000]">
                <div className="bg-black text-white p-3 border-b-4 border-black">
                    <h3 className="text-sm font-black uppercase font-mono">// RECENT BATTLES</h3>
                </div>
                <div className="p-4">
                    {profile.match_history && profile.match_history.length > 0 ? (
                        <div className="space-y-2">
                            {profile.match_history.slice(0, 5).map((match, i) => (
                                <MatchHistoryItem
                                    key={match.id || `lobby-${i}`}
                                    match={match}
                                    compact
                                    showDuration={false}
                                />
                            ))}
                        </div>
                    ) : (
                        <div className="text-center text-gray-400 font-bold text-sm py-4">
                            No recent battles
                        </div>
                    )}
                </div>
            </div>

            {invites.length > 0 && (
                <div className="bg-[#F4A261] border-4 border-black shadow-[6px_6px_0_0_#000] p-6">
                    <h3 className="text-xl font-black uppercase mb-4 flex items-center gap-2">
                        <Mail className="w-5 h-5" /> PENDING INVITES
                    </h3>
                    <div className="space-y-3">
                        {invites.map((invite: BattleInviteData, i: number) => (
                            <div key={invite.id || `invite-${i}`} className="bg-white border-3 border-black p-3">
                                <div className="font-bold mb-1">VS {invite.user1?.username || 'Unknown'}</div>
                                <div className="text-xs font-bold text-gray-500 mb-2">
                                    {invite.duration} Days • Starts {new Date(invite.start_date).toLocaleDateString()}
                                </div>
                                <div className="flex gap-2">
                                    <button
                                        onClick={() => onAcceptInvite(invite.id)}
                                        className="flex-1 bg-[#2A9D8F] border-2 border-black font-bold py-1 text-white hover:bg-[#238B80]"
                                    >
                                        ACCEPT
                                    </button>
                                    <button
                                        onClick={() => onRejectInvite(invite.id)}
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
    );
}
