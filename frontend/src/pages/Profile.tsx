import { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { motion, AnimatePresence } from 'framer-motion';
import { Edit2, X, Save, LogOut, User, ArrowLeft, Key, Shield } from 'lucide-react';
import { supabase } from '../lib/supabase';
import { toast } from 'sonner';

const EMOJI_OPTIONS = [
    '😀', '😃', '😄', '😎', '🤓', '🥳', '🤩', '😊', '🤗', '🤔',
    '🐶', '🐱', '🐼', '🐯', '🦁', '🐸', '🦊', '🦉', '🐔', '🐵',
    '🎮', '🎯', '🎲', '⚡', '🔥', '💎', '🏆', '🌟', '⭐', '👾'
];

export default function Profile() {
    const { user, session, signOut } = useAuth();
    const navigate = useNavigate();
    const [isEditing, setIsEditing] = useState(false);
    const [username, setUsername] = useState('');
    const [loading, setLoading] = useState(false);
    const [showEmojiPicker, setShowEmojiPicker] = useState(false);
    const [selectedEmoji, setSelectedEmoji] = useState('😀');
    const [profileData, setProfileData] = useState<any>(null);

    // Password Change State
    const [isChangingPassword, setIsChangingPassword] = useState(false);
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');

    useEffect(() => {
        if (session?.access_token) {
            loadProfile();
        }
    }, [session]);

    const loadProfile = async () => {
        if (!session?.access_token) return;
        try {
            const response = await axios.get('/api/users/profile', {
                headers: { Authorization: `Bearer ${session.access_token}` }
            });
            setProfileData(response.data);
            setUsername(response.data.username || '');
            setSelectedEmoji(response.data.avatar_emoji || '😀');
        } catch (error) {
            console.error("Failed to load profile", error);
        }
    };

    const handleSaveProfile = async () => {
        if (!session?.access_token) return;
        setLoading(true);
        try {
            await axios.put('/api/users/profile',
                { username, avatar_emoji: selectedEmoji },
                { headers: { Authorization: `Bearer ${session.access_token}` } }
            );
            setIsEditing(false);
            loadProfile();
            toast.success("Profile updated successfully!");
        } catch (error) {
            console.error("Failed to update profile", error);
            toast.error("Failed to update profile");
        } finally {
            setLoading(false);
        }
    };

    const handleSelectEmoji = async (emoji: string) => {
        setSelectedEmoji(emoji);
        setShowEmojiPicker(false);

        // Save immediately
        if (!session?.access_token) return;
        try {
            await axios.put('/api/users/profile',
                { avatar_emoji: emoji },
                { headers: { Authorization: `Bearer ${session.access_token}` } }
            );
            toast.success("Avatar updated!");
            loadProfile();
        } catch (error) {
            console.error("Failed to update avatar", error);
            toast.error("Failed to update avatar");
        }
    };

    const handleChangePassword = async () => {
        if (newPassword !== confirmPassword) {
            toast.error("Passwords do not match!");
            return;
        }
        setLoading(true);
        try {
            const { error } = await supabase.auth.updateUser({ password: newPassword });
            if (error) {
                throw error;
            }
            toast.success("Password updated successfully!");
            setIsChangingPassword(false);
            setNewPassword('');
            setConfirmPassword('');
        } catch (error: any) {
            console.error("Failed to update password", error);
            toast.error(error.message);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="min-h-screen bg-neo-bg p-4 md:p-8 pb-24 flex flex-col items-center">

            {/* Header */}
            <header className="w-full max-w-3xl flex items-stretch gap-4 mb-8">
                <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => navigate('/dashboard')}
                    className="flex btn-neo px-4 md:px-6 bg-white items-center justify-center"
                >
                    <ArrowLeft className="w-6 h-6 md:w-8 md:h-8" />
                </motion.button>
                <div className="bg-neo-white border-3 border-black p-4 shadow-neo-sm flex-1 text-center md:text-left relative overflow-hidden flex flex-col justify-center">
                    <div className="absolute top-0 right-0 bg-neo-accent px-2 border-l-3 border-b-3 border-black font-bold text-xs">PLAYER CARD</div>
                    <h1 className="text-2xl font-black italic uppercase">My <span className="text-neo-primary">Profile</span></h1>
                </div>
            </header>

            <div className="w-full max-w-3xl space-y-8">

                {/* Main Profile Card */}
                <div className="bg-neo-white border-3 border-black p-6 md:p-8 shadow-neo relative">
                    <button
                        onClick={() => setIsEditing(true)}
                        className="absolute top-4 right-4 p-2 hover:bg-gray-100 border-2 border-transparent hover:border-black transition-all rounded-sm"
                    >
                        <Edit2 className="w-5 h-5" />
                    </button>

                    <div className="flex flex-col md:flex-row items-center gap-8">
                        <div
                            className="w-32 h-32 bg-neo-accent border-3 border-black rounded-full flex items-center justify-center shadow-neo-sm flex-shrink-0 cursor-pointer hover:scale-105 transition-transform"
                            onClick={() => setShowEmojiPicker(true)}
                            title="Click to change avatar"
                        >
                            <span className="text-6xl">{selectedEmoji}</span>
                        </div>

                        <div className="text-center md:text-left flex-1">
                            <h2 className="text-3xl font-black uppercase mb-1">{profileData?.username || 'Challenger'}</h2>
                            <p className="text-gray-500 font-bold mb-4">{user?.email}</p>

                            <div className="flex gap-2 justify-center md:justify-start">
                                <span className="bg-neo-primary text-white px-3 py-1 border-2 border-black font-bold text-sm shadow-sm">
                                    LEVEL 1
                                </span>
                                <span className="bg-neo-dark text-white px-3 py-1 border-2 border-black font-bold text-sm shadow-sm">
                                    CHALLENGER
                                </span>
                            </div>
                        </div>
                    </div>

                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mt-8">
                        <div className="bg-gray-50 border-3 border-black p-4 text-center hover:bg-white transition-colors">
                            <div className="text-3xl font-black">{profileData?.stats?.battle_wins || 0}</div>
                            <div className="text-xs font-bold uppercase text-gray-500">Battle Wins</div>
                        </div>
                        <div className="bg-gray-50 border-3 border-black p-4 text-center hover:bg-white transition-colors">
                            <div className="text-3xl font-black">{profileData?.stats?.total_xp || 0}</div>
                            <div className="text-xs font-bold uppercase text-gray-500">Total XP</div>
                        </div>
                        <div className="bg-gray-50 border-3 border-black p-4 text-center hover:bg-white transition-colors">
                            <div className="text-3xl font-black">{profileData?.stats?.battle_fought || 0}</div>
                            <div className="text-xs font-bold uppercase text-gray-500">Battle Fought</div>
                        </div>
                        <div className="bg-gray-50 border-3 border-black p-4 text-center hover:bg-white transition-colors">
                            <div className="text-3xl font-black">{profileData?.stats?.win_rate || '0%'}</div>
                            <div className="text-xs font-bold uppercase text-gray-500">Win Rate</div>
                        </div>
                        <div className="bg-gray-50 border-3 border-black p-4 text-center hover:bg-white transition-colors md:col-span-2">
                            <div className="text-3xl font-black">{profileData?.stats?.tasks_completed || 0}</div>
                            <div className="text-xs font-bold uppercase text-gray-500">Tasks Completed</div>
                        </div>
                    </div>
                </div>

                {/* Settings Section */}
                <div className="bg-neo-secondary border-3 border-black p-6 md:p-8 shadow-neo">
                    <h3 className="text-xl font-black uppercase mb-6 flex items-center gap-2">
                        <Shield className="w-6 h-6" /> Account Security
                    </h3>

                    <div className="space-y-4">
                        {!isChangingPassword ? (
                            <button
                                onClick={() => setIsChangingPassword(true)}
                                className="w-full bg-white border-3 border-black p-4 font-bold uppercase hover:bg-gray-50 flex items-center justify-between group"
                            >
                                <span className="flex items-center gap-2"><Key className="w-5 h-5" /> Change Password</span>
                                <span className="text-neo-primary group-hover:translate-x-1 transition-transform">→</span>
                            </button>
                        ) : (
                            <motion.div
                                initial={{ opacity: 0, height: 0 }}
                                animate={{ opacity: 1, height: 'auto' }}
                                className="bg-white border-3 border-black p-6"
                            >
                                <div className="space-y-4">
                                    <input
                                        type="password"
                                        placeholder="New Password"
                                        value={newPassword}
                                        onChange={(e) => setNewPassword(e.target.value)}
                                        className="w-full input-neo"
                                    />
                                    <input
                                        type="password"
                                        placeholder="Confirm Password"
                                        value={confirmPassword}
                                        onChange={(e) => setConfirmPassword(e.target.value)}
                                        className="w-full input-neo"
                                    />
                                    <div className="flex gap-2">
                                        <button
                                            onClick={handleChangePassword}
                                            disabled={loading}
                                            className="flex-1 btn-neo bg-neo-primary text-white py-2 font-bold uppercase"
                                        >
                                            {loading ? 'Updating...' : 'Update Password'}
                                        </button>
                                        <button
                                            onClick={() => setIsChangingPassword(false)}
                                            className="px-4 btn-neo bg-gray-200 hover:bg-gray-300 font-bold uppercase"
                                        >
                                            Cancel
                                        </button>
                                    </div>
                                </div>
                            </motion.div>
                        )}

                        <button
                            onClick={() => signOut()}
                            className="w-full bg-red-400 border-3 border-black p-4 font-bold uppercase hover:bg-red-500 flex items-center justify-center gap-2 shadow-sm hover:shadow-none hover:translate-y-0.5 transition-all"
                        >
                            <LogOut className="w-5 h-5" /> Sign Out
                        </button>
                    </div>
                </div>

            </div>

            {/* Edit Profile Modal */}
            <AnimatePresence>
                {isEditing && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
                    >
                        <motion.div
                            initial={{ scale: 0.9, y: 20 }}
                            animate={{ scale: 1, y: 0 }}
                            exit={{ scale: 0.9, y: 20 }}
                            className="bg-neo-white border-3 border-black p-6 shadow-neo w-full max-w-md relative"
                        >
                            <button
                                onClick={() => setIsEditing(false)}
                                className="absolute top-2 right-2 p-1 hover:bg-gray-100"
                            >
                                <X className="w-6 h-6" />
                            </button>

                            <h2 className="text-xl font-black uppercase mb-6">Edit Identity</h2>

                            <div className="space-y-4">
                                <div>
                                    <label className="block font-bold text-sm mb-1">Username</label>
                                    <input
                                        type="text"
                                        value={username}
                                        onChange={(e) => setUsername(e.target.value)}
                                        className="w-full input-neo"
                                        placeholder="Enter username"
                                    />
                                </div>

                                <button
                                    onClick={handleSaveProfile}
                                    disabled={loading}
                                    className="w-full btn-neo bg-neo-primary text-white py-3 font-bold uppercase flex items-center justify-center gap-2"
                                >
                                    {loading ? 'Saving...' : <><Save className="w-5 h-5" /> Save Changes</>}
                                </button>
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>

            {/* Emoji Picker Modal */}
            <AnimatePresence>
                {showEmojiPicker && (
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50"
                        onClick={() => setShowEmojiPicker(false)}
                    >
                        <motion.div
                            initial={{ scale: 0.9 }}
                            animate={{ scale: 1 }}
                            exit={{ scale: 0.9 }}
                            className="bg-neo-white border-4 border-black shadow-neo max-w-md w-full p-6"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <div className="flex justify-between items-center mb-4">
                                <h2 className="text-xl font-black uppercase">Choose Your Avatar</h2>
                                <button
                                    onClick={() => setShowEmojiPicker(false)}
                                    className="p-2 hover:bg-gray-100 border-2 border-black"
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>

                            <div className="grid grid-cols-5 gap-3">
                                {EMOJI_OPTIONS.map((emoji) => (
                                    <button
                                        key={emoji}
                                        onClick={() => handleSelectEmoji(emoji)}
                                        className={`text-4xl p-3 border-3 border-black hover:bg-neo-accent transition-all active:scale-95 ${selectedEmoji === emoji ? 'bg-neo-primary' : 'bg-white'
                                            }`}
                                    >
                                        {emoji}
                                    </button>
                                ))}
                            </div>
                        </motion.div>
                    </motion.div>
                )}
            </AnimatePresence>
        </div>
    );
}
