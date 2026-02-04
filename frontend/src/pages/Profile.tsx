import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Edit2, ArrowLeft } from 'lucide-react';
import RankBadge from '../components/RankBadge';
import ProfileStats from '../components/ProfileStats';
import ProfileEditForm from '../components/ProfileEditForm';
import SecuritySettings from '../components/SecuritySettings';
import { useProfileForm } from '../hooks/useProfileForm';

const EMOJI_OPTIONS = [
    '😀', '😃', '😄', '😎', '🤓', '🥳', '🤩', '😊', '🤗', '🤔',
    '🐶', '🐱', '🐼', '🐯', '🦁', '🐸', '🦊', '🦉', '🐔', '🐵',
    '🎮', '🎯', '🎲', '⚡', '🔥', '💎', '🏆', '🌟', '⭐', '👾'
];

export default function Profile() {
    const { user, signOut } = useAuth();
    const navigate = useNavigate();

    // Use the custom hook for profile data and mutations
    const {
        profile,
        isLoading,
        isEditing,
        username,
        selectedEmoji,
        showEmojiPicker,
        setIsEditing,
        setShowEmojiPicker,
        updateProfile,
        updateAvatar,
        updateTimezone,
        updatePassword,
    } = useProfileForm();

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

            {/* Loading state */}
            {isLoading && (
                <div className="w-full max-w-3xl text-center py-8">
                    <p className="font-bold text-gray-500">Loading profile...</p>
                </div>
            )}

            {/* Profile content */}
            {!isLoading && profile && (
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
                                <div className="flex items-center justify-center md:justify-start gap-3 mb-1">
                                    <h2 className="text-3xl font-black uppercase">{profile.username || 'Challenger'}</h2>
                                    {profile.rank && <RankBadge rank={profile.rank} level={profile.level} size="medium" showLabel={false} />}
                                </div>
                                <p className="text-gray-500 font-bold mb-4">{user?.email}</p>

                                <div className="flex gap-2 justify-center md:justify-start">
                                    <span className="bg-neo-primary text-white px-3 py-1 border-2 border-black font-bold text-sm shadow-sm">
                                        LEVEL {profile.level}
                                    </span>
                                    <span className="bg-neo-dark text-white px-3 py-1 border-2 border-black font-bold text-sm shadow-sm">
                                        CHALLENGER
                                    </span>
                                </div>
                            </div>
                        </div>

                        <ProfileStats stats={profile.stats} />
                    </div>

                    {/* Settings Section */}
                    <SecuritySettings
                        currentTimezone={profile.timezone}
                        detectedTimezone={Intl.DateTimeFormat().resolvedOptions().timeZone}
                        onTimezoneSync={updateTimezone}
                        onSignOut={signOut}
                        onChangePassword={updatePassword}
                    />

                </div>
            )}

            {/* Edit Profile Modal */}
            <ProfileEditForm
                isOpen={isEditing}
                initialUsername={username}
                loading={false}
                onSave={async () => {
                    await updateProfile();
                }}
                onClose={() => setIsEditing(false)}
            />

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
                                    ←
                                </button>
                            </div>

                            <div className="grid grid-cols-5 gap-3">
                                {EMOJI_OPTIONS.map((emoji) => (
                                    <button
                                        key={emoji}
                                        onClick={() => updateAvatar(emoji)}
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
