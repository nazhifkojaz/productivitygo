import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import { motion } from 'framer-motion';
import { User, Sword, Mail, Check, X, Search, Loader } from 'lucide-react';

export default function UserDashboard() {
    const { user, session } = useAuth();
    const navigate = useNavigate();
    const [profile, setProfile] = useState<any>(null);

    const [invites, setInvites] = useState<any[]>([]);
    const [searchEmail, setSearchEmail] = useState('');
    const [startDate, setStartDate] = useState('');
    const [duration, setDuration] = useState(5);
    const [loading, setLoading] = useState(false);
    const [inviteStatus, setInviteStatus] = useState<string | null>(null);

    useEffect(() => {
        if (session) {
            loadInvites();
            loadProfile();
        }
    }, [session]);

    const loadProfile = async () => {
        if (!session?.access_token) return;
        try {
            const response = await axios.get('/api/users/profile', {
                headers: { Authorization: `Bearer ${session.access_token}` }
            });
            setProfile(response.data);
        } catch (error) {
            console.error("Failed to load profile", error);
        }
    };

    const loadInvites = async () => {
        if (!session?.access_token) return;
        try {
            const response = await axios.get('/api/battles/invites', {
                headers: { Authorization: `Bearer ${session.access_token}` }
            });
            setInvites(response.data);
        } catch (error) {
            console.error("Failed to load invites", error);
        }
    };

    const handleInvite = async () => {
        if (!searchEmail || !startDate || !session?.access_token) return;
        setLoading(true);
        setInviteStatus(null);
        try {
            await axios.post('/api/battles/invite',
                {
                    rival_email: searchEmail,
                    start_date: startDate,
                    duration: duration
                },
                { headers: { Authorization: `Bearer ${session.access_token}` } }
            );
            setInviteStatus('Invite sent successfully!');
            setSearchEmail('');
            setStartDate('');
            setDuration(5);
        } catch (error: any) {
            const detail = error.response?.data?.detail;
            if (typeof detail === 'string') {
                setInviteStatus(detail);
            } else if (Array.isArray(detail)) {
                setInviteStatus(detail.map((e: any) => e.msg).join(', '));
            } else {
                setInviteStatus('Failed to send invite');
            }
        } finally {
            setLoading(false);
        }
    };

    const handleAccept = async (battleId: string) => {
        if (!session?.access_token) return;
        try {
            await axios.post(`/api/battles/${battleId}/accept`, {}, {
                headers: { Authorization: `Bearer ${session.access_token}` }
            });
            window.location.reload();
        } catch (error) {
            console.error("Failed to accept", error);
            alert("Failed to accept invite");
        }
    };

    const handleReject = async (battleId: string) => {
        if (!session?.access_token) return;
        try {
            await axios.post(`/api/battles/${battleId}/reject`, {}, {
                headers: { Authorization: `Bearer ${session.access_token}` }
            });
            loadInvites();
        } catch (error) {
            console.error("Failed to reject", error);
        }
    };

    return (
        <div className="min-h-screen bg-neo-bg p-4 md:p-8 flex flex-col items-center">
            {/* Header */}
            <header className="w-full max-w-4xl mb-12 flex items-center justify-between bg-neo-white border-3 border-black p-4 shadow-neo">
                <div className="flex items-center gap-3">
                    <h1 className="text-2xl font-black italic uppercase">Productivity<span className="text-neo-primary">GO</span></h1>
                </div>
                <button onClick={() => navigate('/login')} className="text-xs font-bold hover:underline text-gray-500">
                    SIGN OUT
                </button>
            </header>

            <div className="w-full max-w-4xl grid grid-cols-1 md:grid-cols-2 gap-8">

                {/* Left Column: User Stats */}
                <div className="space-y-8">
                    <div className="bg-neo-white border-3 border-black p-8 shadow-neo relative">
                        <div className="absolute top-4 right-4">
                            <button onClick={() => navigate('/profile')} className="text-xs font-bold underline hover:text-neo-primary">Edit Profile</button>
                        </div>
                        <div className="flex flex-col items-center">
                            <div className="w-32 h-32 bg-neo-accent border-3 border-black rounded-full flex items-center justify-center mb-6 shadow-neo-sm">
                                <User className="w-16 h-16" />
                            </div>
                            <h2 className="text-3xl font-black uppercase mb-2">{profile?.username || user?.email?.split('@')[0]}</h2>
                            <p className="text-gray-500 font-bold mb-6">Level {profile?.level || 1} Challenger</p>

                            <div className="grid grid-cols-2 gap-4 w-full">
                                <div className="text-center bg-gray-50 border-2 border-black p-2">
                                    <div className="font-black text-xl">{profile?.stats?.battle_wins || 0}</div>
                                    <div className="text-[10px] font-bold uppercase">Battle Wins</div>
                                </div>
                                <div className="text-center bg-gray-50 border-2 border-black p-2">
                                    <div className="font-black text-xl">{profile?.stats?.total_xp || 0}</div>
                                    <div className="text-[10px] font-bold uppercase">Total XP</div>
                                </div>
                                <div className="text-center bg-gray-50 border-2 border-black p-2">
                                    <div className="font-black text-xl">{profile?.stats?.rounds_won || 0}</div>
                                    <div className="text-[10px] font-bold uppercase">Rounds Won</div>
                                </div>
                                <div className="text-center bg-gray-50 border-2 border-black p-2">
                                    <div className="font-black text-xl">{profile?.stats?.tasks_completed || 0}</div>
                                    <div className="text-[10px] font-bold uppercase">Tasks Done</div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Right Column: Battle Management */}
                <div className="space-y-8">

                    {/* Send Invite */}
                    <div className="bg-neo-secondary border-3 border-black p-8 shadow-neo">
                        <h3 className="text-xl font-black uppercase mb-4 flex items-center gap-2">
                            <Sword className="w-6 h-6" /> Challenge a Rival
                        </h3>
                        <p className="text-sm font-bold mb-4">Enter your rival's email to send a battle request.</p>

                        <div className="space-y-4 mb-4">
                            {/* Email Input */}
                            <div className="relative">
                                <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
                                <input
                                    type="email"
                                    value={searchEmail}
                                    onChange={(e) => setSearchEmail(e.target.value)}
                                    className="w-full input-neo pl-10"
                                    placeholder="rival@example.com"
                                />
                            </div>

                            {/* Battle Settings */}
                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-xs font-bold uppercase mb-1 block">Start Date</label>
                                    <select
                                        value={startDate}
                                        onChange={(e) => setStartDate(e.target.value)}
                                        className="w-full input-neo"
                                    >
                                        <option value="" disabled>Select Date</option>
                                        {Array.from({ length: 7 }).map((_, i) => {
                                            const d = new Date();
                                            d.setDate(d.getDate() + i + 1); // Start from tomorrow
                                            // Use local YYYY-MM-DD format to avoid UTC shifts
                                            const year = d.getFullYear();
                                            const month = String(d.getMonth() + 1).padStart(2, '0');
                                            const day = String(d.getDate()).padStart(2, '0');
                                            const dateStr = `${year}-${month}-${day}`;

                                            const displayStr = d.toLocaleDateString('en-US', { weekday: 'short', month: 'short', day: 'numeric' });
                                            return (
                                                <option key={dateStr} value={dateStr}>
                                                    {displayStr}
                                                </option>
                                            );
                                        })}
                                    </select>
                                </div>
                                <div>
                                    <label className="text-xs font-bold uppercase mb-1 block">Duration</label>
                                    <select
                                        value={duration}
                                        onChange={(e) => setDuration(parseInt(e.target.value))}
                                        className="w-full input-neo"
                                    >
                                        <option value={3}>3 Days</option>
                                        <option value={4}>4 Days</option>
                                        <option value={5}>5 Days</option>
                                    </select>
                                </div>
                            </div>

                            <button
                                onClick={handleInvite}
                                disabled={loading || !searchEmail || !startDate}
                                className="w-full btn-neo bg-neo-primary text-white p-3 disabled:opacity-50 flex items-center justify-center gap-2"
                            >
                                {loading ? <Loader className="w-6 h-6 animate-spin" /> : <><Sword className="w-6 h-6" /> SEND CHALLENGE</>}
                            </button>
                        </div>
                        {
                            inviteStatus && (
                                <p className={`text-xs font-bold ${inviteStatus.includes('success') ? 'text-green-600' : 'text-red-600'}`}>
                                    {inviteStatus}
                                </p>
                            )
                        }
                    </div>

                    {/* Pending Invites */}
                    <div className="bg-white border-3 border-black p-8 shadow-neo min-h-[200px]">
                        <h3 className="text-xl font-black uppercase mb-4 flex items-center gap-2">
                            <Mail className="w-6 h-6" /> Pending Invites
                        </h3>

                        {invites.length === 0 ? (
                            <div className="text-center py-8 text-gray-400 font-bold italic">
                                No pending invites...
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {invites.map((invite) => (
                                    <motion.div
                                        key={invite.id}
                                        initial={{ opacity: 0, y: 10 }}
                                        animate={{ opacity: 1, y: 0 }}
                                        className="bg-gray-50 border-2 border-black p-4 flex items-center justify-between"
                                    >
                                        <div>
                                            <p className="font-black uppercase text-sm">{invite.user1?.username || 'Unknown Rival'}</p>
                                            <p className="text-xs font-bold text-gray-500 mb-1">Challenged you!</p>
                                            <div className="text-xs bg-gray-200 p-1 rounded inline-block">
                                                <span className="font-bold">Start:</span> {new Date(invite.start_date).toLocaleDateString()} <br />
                                                <span className="font-bold">Duration:</span> {invite.duration || 5} Days
                                            </div>
                                        </div>
                                        <div className="flex gap-2">
                                            <button
                                                onClick={() => handleAccept(invite.id)}
                                                className="btn-neo bg-green-400 p-2 hover:bg-green-500"
                                            >
                                                <Check className="w-4 h-4" />
                                            </button>
                                            <button
                                                onClick={() => handleReject(invite.id)}
                                                className="btn-neo bg-red-400 p-2 hover:bg-red-500"
                                            >
                                                <X className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </motion.div>
                                ))}
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}
