import { useState } from 'react';
import { LogOut, Shield } from 'lucide-react';

interface SecuritySettingsProps {
    currentTimezone: string | undefined;
    detectedTimezone: string;
    onTimezoneSync: (timezone: string) => Promise<void>;
    onSignOut: () => void;
}

export default function SecuritySettings({
    currentTimezone,
    detectedTimezone,
    onTimezoneSync,
    onSignOut,
}: SecuritySettingsProps) {
    const [loading, setLoading] = useState(false);

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
