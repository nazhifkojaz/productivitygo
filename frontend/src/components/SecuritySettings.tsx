import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { LogOut, Key, Shield } from 'lucide-react';

interface SecuritySettingsProps {
    currentTimezone: string | undefined;
    detectedTimezone: string;
    onTimezoneSync: (timezone: string) => Promise<void>;
    onSignOut: () => void;
    onChangePassword?: (newPassword: string) => Promise<void>;
}

export default function SecuritySettings({
    currentTimezone,
    detectedTimezone,
    onTimezoneSync,
    onSignOut,
    onChangePassword,
}: SecuritySettingsProps) {
    const [isChangingPassword, setIsChangingPassword] = useState(false);
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [loading, setLoading] = useState(false);

    const handlePasswordChange = async () => {
        if (!onChangePassword) {
            setIsChangingPassword(false);
            setNewPassword('');
            setConfirmPassword('');
            return;
        }

        if (newPassword !== confirmPassword) {
            // Parent should handle validation error via toast
            return;
        }

        setLoading(true);
        try {
            await onChangePassword(newPassword);
            setIsChangingPassword(false);
            setNewPassword('');
            setConfirmPassword('');
        } catch {
            // Parent handles error via toast
        } finally {
            setLoading(false);
        }
    };

    const handleCancelPasswordChange = () => {
        setIsChangingPassword(false);
        setNewPassword('');
        setConfirmPassword('');
    };

    const handleTimezoneSync = async () => {
        setLoading(true);
        try {
            await onTimezoneSync(detectedTimezone);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000] p-6 md:p-8">
            {/* Black Header Bar */}
            <div className="bg-black text-white px-4 py-2 -mx-6 -mt-6 mb-6 font-black uppercase text-sm border-b-4 border-black">
                // Account Security //
            </div>

            <h3 className="text-xl font-black uppercase mb-6 flex items-center gap-2">
                <Shield className="w-6 h-6" /> Settings
            </h3>

            <div className="space-y-4">
                <AnimatePresence>
                    {isChangingPassword ? (
                        <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            className="bg-[#E8E4D9] border-3 border-black p-6"
                        >
                            <div className="space-y-4">
                                <div>
                                    <label className="block font-black text-sm mb-1">[ NEW PASSWORD ]</label>
                                    <input
                                        type="password"
                                        placeholder="Enter new password"
                                        value={newPassword}
                                        onChange={(e) => setNewPassword(e.target.value)}
                                        className="w-full border-3 border-black p-3 font-black focus:outline-none focus:ring-2 focus:ring-[#2A9D8F] bg-white shadow-[2px_2px_0_0_#000]"
                                        disabled={loading}
                                    />
                                </div>
                                <div>
                                    <label className="block font-black text-sm mb-1">[ CONFIRM PASSWORD ]</label>
                                    <input
                                        type="password"
                                        placeholder="Confirm new password"
                                        value={confirmPassword}
                                        onChange={(e) => setConfirmPassword(e.target.value)}
                                        className="w-full border-3 border-black p-3 font-black focus:outline-none focus:ring-2 focus:ring-[#2A9D8F] bg-white shadow-[2px_2px_0_0_#000]"
                                        disabled={loading}
                                    />
                                </div>
                                <div className="flex gap-2">
                                    <button
                                        onClick={handlePasswordChange}
                                        disabled={loading || !newPassword || !confirmPassword}
                                        className="flex-1 bg-[#2A9D8F] text-white border-3 border-black py-2 font-black uppercase disabled:opacity-50 shadow-[3px_3px_0_0_#000] active:translate-y-1 active:shadow-none transition-all"
                                    >
                                        {loading ? 'Updating...' : 'Update'}
                                    </button>
                                    <button
                                        onClick={handleCancelPasswordChange}
                                        disabled={loading}
                                        className="px-4 bg-gray-300 hover:bg-gray-400 border-3 border-black font-black uppercase shadow-[2px_2px_0_0_#000] active:translate-y-0.5 active:shadow-none transition-all"
                                    >
                                        Cancel
                                    </button>
                                </div>
                            </div>
                        </motion.div>
                    ) : (
                        <button
                            onClick={() => setIsChangingPassword(true)}
                            className="w-full bg-white border-3 border-black p-4 font-black uppercase hover:bg-[#E8E4D9] flex items-center justify-between group shadow-[3px_3px_0_0_#000] active:translate-y-1 active:shadow-none transition-all"
                            disabled={!onChangePassword}
                        >
                            <span className="flex items-center gap-2"><Key className="w-5 h-5" /> Change Password</span>
                            <span className="text-[#2A9D8F] group-hover:translate-x-1 transition-transform">→</span>
                        </button>
                    )}
                </AnimatePresence>

                {/* Timezone Sync */}
                <div className="bg-[#E8E4D9] border-3 border-black p-4 shadow-[3px_3px_0_0_#000]">
                    <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                            <span className="font-black">🌍</span>
                            <span className="font-black uppercase text-sm">[ Timezone ]</span>
                            <span className="text-gray-600 font-bold">{currentTimezone || 'UTC'}</span>
                        </div>
                        <button
                            onClick={handleTimezoneSync}
                            disabled={loading}
                            className="bg-[#F4A261] text-white border-3 border-black px-4 py-2 font-black text-sm uppercase shadow-[3px_3px_0_0_#000] active:translate-y-1 active:shadow-none transition-all disabled:opacity-50"
                        >
                            Sync
                        </button>
                    </div>
                    <p className="text-xs text-gray-600 font-bold">
                        Detected: {detectedTimezone}
                    </p>
                </div>

                <button
                    onClick={onSignOut}
                    className="w-full bg-[#E63946] text-white border-3 border-black p-4 font-black uppercase hover:bg-[#d32f2f] flex items-center justify-center gap-2 shadow-[4px_4px_0_0_#000] active:translate-y-1 active:shadow-none transition-all"
                >
                    <LogOut className="w-5 h-5" /> Sign Out
                </button>
            </div>
        </div>
    );
}
