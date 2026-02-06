import { useState } from 'react';
import { motion } from 'framer-motion';
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
        } catch (error) {
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
        <div className="bg-neo-secondary border-3 border-black p-6 md:p-8 shadow-neo">
            <h3 className="text-xl font-black uppercase mb-6 flex items-center gap-2">
                <Shield className="w-6 h-6" /> Account Security
            </h3>

            <div className="space-y-4">
                {!isChangingPassword ? (
                    <button
                        onClick={() => setIsChangingPassword(true)}
                        className="w-full bg-white border-3 border-black p-4 font-bold uppercase hover:bg-gray-50 flex items-center justify-between group"
                        disabled={!onChangePassword}
                    >
                        <span className="flex items-center gap-2"><Key className="w-5 h-5" /> Change Password</span>
                        <span className="text-neo-primary group-hover:translate-x-1 transition-transform">→</span>
                    </button>
                ) : (
                    <motion.div
                        initial={{ opacity: 0, height: 0 }}
                        animate={{ opacity: 1, height: 'auto' }}
                        exit={{ opacity: 0, height: 0 }}
                        className="bg-white border-3 border-black p-6"
                    >
                        <div className="space-y-4">
                            <input
                                type="password"
                                placeholder="New Password"
                                value={newPassword}
                                onChange={(e) => setNewPassword(e.target.value)}
                                className="w-full input-neo"
                                disabled={loading}
                            />
                            <input
                                type="password"
                                placeholder="Confirm Password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                className="w-full input-neo"
                                disabled={loading}
                            />
                            <div className="flex gap-2">
                                <button
                                    onClick={handlePasswordChange}
                                    disabled={loading || !newPassword || !confirmPassword}
                                    className="flex-1 btn-neo bg-neo-primary text-white py-2 font-bold uppercase disabled:opacity-50"
                                >
                                    {loading ? 'Updating...' : 'Update Password'}
                                </button>
                                <button
                                    onClick={handleCancelPasswordChange}
                                    disabled={loading}
                                    className="px-4 btn-neo bg-gray-200 hover:bg-gray-300 font-bold uppercase"
                                >
                                    Cancel
                                </button>
                            </div>
                        </div>
                    </motion.div>
                )}

                {/* Timezone Sync */}
                <div className="bg-white border-3 border-black p-4">
                    <div className="flex items-center justify-between mb-2">
                        <div className="flex items-center gap-2">
                            <span className="font-bold">🌍 Timezone</span>
                            <span className="text-gray-600">{currentTimezone || 'UTC'}</span>
                        </div>
                        <button
                            onClick={handleTimezoneSync}
                            disabled={loading}
                            className="btn-neo bg-neo-accent px-4 py-2 font-bold text-sm uppercase hover:bg-yellow-400 transition-colors disabled:opacity-50"
                        >
                            Sync to Device
                        </button>
                    </div>
                    <p className="text-xs text-gray-500 font-bold">
                        Automatically detected: {detectedTimezone}
                    </p>
                </div>

                <button
                    onClick={onSignOut}
                    className="w-full bg-red-400 border-3 border-black p-4 font-bold uppercase hover:bg-red-500 flex items-center justify-center gap-2 shadow-sm hover:shadow-none hover:translate-y-0.5 transition-all"
                >
                    <LogOut className="w-5 h-5" /> Sign Out
                </button>
            </div>
        </div>
    );
}
