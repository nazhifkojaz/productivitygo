import { useAuth } from '../context/AuthContext';
import { useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Edit2, ArrowLeft, ChevronLeft, ChevronRight } from 'lucide-react';
import RankBadge from '../components/RankBadge';
import ProfileStats from '../components/ProfileStats';
import ProfileEditForm from '../components/ProfileEditForm';
import SecuritySettings from '../components/SecuritySettings';
import { useProfileForm } from '../hooks/useProfileForm';
import type { MatchHistory } from '../types/profile';
import { useState } from 'react';

const EMOJI_OPTIONS = [
    '😀', '😃', '😄', '😎', '🤓', '🥳', '🤩', '😊', '🤗', '🤔',
    '🐶', '🐱', '🐼', '🐯', '🦁', '🐸', '🦊', '🦉', '🐔', '🐵',
    '🎮', '🎯', '🎲', '⚡', '🔥', '💎', '🏆', '🌟', '⭐', '👾'
];

const ITEMS_PER_PAGE = 10;

export default function Profile() {
    const { user, signOut } = useAuth();
    const navigate = useNavigate();
    const [historyPage, setHistoryPage] = useState(1);

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

    // Pagination logic
    const totalPages = profile?.match_history ? Math.ceil(profile.match_history.length / ITEMS_PER_PAGE) : 1;
    const startIndex = (historyPage - 1) * ITEMS_PER_PAGE;
    const endIndex = startIndex + ITEMS_PER_PAGE;
    const currentHistory = profile?.match_history?.slice(startIndex, endIndex) || [];

    const handlePrevPage = () => {
        if (historyPage > 1) setHistoryPage(historyPage - 1);
    };

    const handleNextPage = () => {
        if (historyPage < totalPages) setHistoryPage(historyPage + 1);
    };

    return (
        <div className="min-h-screen bg-[#E8E4D9] p-4 md:p-8 pb-24 flex flex-col items-center">

            {/* Header */}
            <header className="w-full max-w-3xl flex items-stretch gap-4 mb-8">
                <motion.button
                    whileHover={{ scale: 1.05 }}
                    whileTap={{ scale: 0.95 }}
                    onClick={() => navigate('/lobby')}
                    className="flex btn-neo px-4 md:px-6 bg-white items-center justify-center"
                >
                    <ArrowLeft className="w-6 h-6 md:w-8 md:h-8" />
                </motion.button>
                <div className="bg-white border-3 border-black shadow-[4px_4px_0_0_#000] p-4 flex-1 text-center md:text-left relative overflow-hidden flex flex-col justify-center">
                    <div className="absolute top-0 right-0 bg-[#F4A261] px-2 border-l-3 border-b-3 border-black font-bold text-xs text-white">[ PLAYER CARD ]</div>
                    <h1 className="text-2xl font-black italic uppercase">My <span className="text-[#2A9D8F]">Profile</span></h1>
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
                    <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000] p-6 md:p-8 relative">
                        <button
                            onClick={() => setIsEditing(true)}
                            className="absolute top-4 right-4 p-2 bg-[#F4A261] border-2 border-black shadow-[2px_2px_0_0_#000] hover:translate-y-0.5 hover:shadow-[1px_1px_0_0_#000] transition-all"
                        >
                            <Edit2 className="w-5 h-5 text-white" />
                        </button>

                        <div className="flex flex-col md:flex-row items-center gap-8 mb-8">
                            <div
                                className="w-32 h-32 bg-[#F4A261] border-4 border-black flex items-center justify-center shadow-[4px_4px_0_0_#000] flex-shrink-0 cursor-pointer hover:scale-105 transition-transform"
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
                                    <span className="bg-[#2A9D8F] text-white px-3 py-1 border-2 border-black font-bold text-sm shadow-[2px_2px_0_0_#000]">
                                        [ LEVEL {profile.level} ]
                                    </span>
                                    <span className="bg-[#457B9D] text-white px-3 py-1 border-2 border-black font-bold text-sm shadow-[2px_2px_0_0_#000]">
                                        [ {profile.rank?.toUpperCase() || 'CHALLENGER'} ]
                                    </span>
                                    {profile.stats?.current_streak !== undefined && profile.stats.current_streak > 0 && (
                                        <span className="bg-[#E63946] text-white px-3 py-1 border-2 border-black font-bold text-sm shadow-[2px_2px_0_0_#000]">
                                            [ 🔥 {profile.stats.current_streak} ]
                                        </span>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Stats Section - with border separator */}
                        <div className="border-t-3 border-black pt-8">
                            <ProfileStats stats={profile.stats} />
                        </div>
                    </div>

                    {/* Match History Section - now before Settings */}
                    {profile.match_history && profile.match_history.length > 0 && (
                        <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000] p-6">
                            <div className="bg-black text-white px-4 py-2 -mx-6 -mt-6 mb-6 font-black uppercase text-sm border-b-4 border-black flex items-center justify-between">
                                <span>// Recent Battles //</span>
                                <span className="text-xs font-normal opacity-80">
                                    Page {historyPage} of {totalPages}
                                </span>
                            </div>
                            <div className="space-y-3">
                                {currentHistory.map((match: MatchHistory) => (
                                    <div key={match.id} className="bg-[#E8E4D9] border-3 border-black p-4 flex justify-between items-center shadow-[3px_3px_0_0_#000]">
                                        <div className="flex items-center gap-3">
                                            <span className="text-2xl">{match.emoji || '⚔️'}</span>
                                            <div>
                                                <div className="font-black text-lg uppercase">
                                                    {match.type === 'adventure' ? 'VS ' : ''}{match.rival}
                                                </div>
                                                <div className="text-xs text-gray-600 font-bold">
                                                    {new Date(match.date).toLocaleDateString()} • {match.duration} DAYS
                                                    {match.xp_earned !== undefined && ` • +${match.xp_earned} XP`}
                                                </div>
                                            </div>
                                        </div>
                                        <div className={`font-black text-xl px-4 py-1 border-2 border-black shadow-[2px_2px_0_0_#000] ${
                                            match.result === 'WIN' ? 'bg-[#2A9D8F] text-white' :
                                            match.result === 'LOSS' ? 'bg-[#E63946] text-white' :
                                            match.result === 'ESCAPED' ? 'bg-[#F4A261] text-white' :
                                            match.result === 'COMPLETED' ? 'bg-[#457B9D] text-white' :
                                            'bg-gray-300'
                                        }`}>
                                            {match.result}
                                        </div>
                                    </div>
                                ))}
                            </div>

                            {/* Pagination */}
                            {totalPages > 1 && (
                                <div className="flex items-center justify-center gap-4 mt-6 pt-4 border-t-3 border-black">
                                    <button
                                        onClick={handlePrevPage}
                                        disabled={historyPage === 1}
                                        className={`px-4 py-2 border-3 border-black font-black flex items-center gap-2 shadow-[2px_2px_0_0_#000] active:translate-y-0.5 active:shadow-none transition-all ${
                                            historyPage === 1
                                                ? 'bg-gray-300 cursor-not-allowed'
                                                : 'bg-white hover:bg-gray-100'
                                        }`}
                                    >
                                        <ChevronLeft className="w-4 h-4" /> PREV
                                    </button>
                                    <span className="font-black text-sm">
                                        {historyPage} / {totalPages}
                                    </span>
                                    <button
                                        onClick={handleNextPage}
                                        disabled={historyPage === totalPages}
                                        className={`px-4 py-2 border-3 border-black font-black flex items-center gap-2 shadow-[2px_2px_0_0_#000] active:translate-y-0.5 active:shadow-none transition-all ${
                                            historyPage === totalPages
                                                ? 'bg-gray-300 cursor-not-allowed'
                                                : 'bg-white hover:bg-gray-100'
                                        }`}
                                    >
                                        NEXT <ChevronRight className="w-4 h-4" />
                                    </button>
                                </div>
                            )}
                        </div>
                    )}

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
                            className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000] max-w-md w-full p-6"
                            onClick={(e) => e.stopPropagation()}
                        >
                            <div className="flex justify-between items-center mb-4">
                                <h2 className="text-xl font-black uppercase">Choose Your Avatar</h2>
                                <button
                                    onClick={() => setShowEmojiPicker(false)}
                                    className="p-2 hover:bg-gray-100 border-2 border-black shadow-[2px_2px_0_0_#000]"
                                >
                                    ←
                                </button>
                            </div>

                            <div className="grid grid-cols-6 gap-2">
                                {EMOJI_OPTIONS.map((emoji) => (
                                    <button
                                        key={emoji}
                                        onClick={() => updateAvatar(emoji)}
                                        className={`text-4xl p-2 border-2 border-black hover:bg-[#F4A261] transition-all active:translate-y-0.5 ${selectedEmoji === emoji ? 'bg-[#2A9D8F]' : 'bg-white'
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
