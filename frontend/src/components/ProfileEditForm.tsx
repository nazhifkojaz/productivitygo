import { motion, AnimatePresence } from 'framer-motion';
import { X, Save } from 'lucide-react';

interface ProfileEditFormProps {
    isOpen: boolean;
    initialUsername: string;
    loading: boolean;
    onSave: (username: string) => Promise<void>;
    onClose: () => void;
}

export default function ProfileEditForm({
    isOpen,
    initialUsername,
    loading,
    onSave,
    onClose,
}: ProfileEditFormProps) {
    const handleSave = async () => {
        await onSave(initialUsername);
    };

    const handleBackdropClick = (e: React.MouseEvent) => {
        if (e.target === e.currentTarget) {
            onClose();
        }
    };

    return (
        <AnimatePresence>
            {isOpen && (
                <motion.div
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
                    onClick={handleBackdropClick}
                >
                    <motion.div
                        initial={{ scale: 0.9, y: 20 }}
                        animate={{ scale: 1, y: 0 }}
                        exit={{ scale: 0.9, y: 20 }}
                        className="bg-white border-4 border-black shadow-[6px_6px_0_0_#000] p-6 w-full max-w-md relative"
                        onClick={(e: { stopPropagation: () => void }) => e.stopPropagation()}
                    >
                        <button
                            onClick={onClose}
                            className="absolute top-2 right-2 p-1 hover:bg-gray-100"
                            aria-label="Close"
                        >
                            <X className="w-6 h-6" />
                        </button>

                        <h2 className="text-xl font-black uppercase mb-6">Edit Identity</h2>

                        <div className="space-y-4">
                            <div>
                                <label htmlFor="username-input" className="block font-black text-sm mb-1">
                                    [ USERNAME ]
                                </label>
                                <input
                                    id="username-input"
                                    type="text"
                                    value={initialUsername}
                                    onChange={() => {
                                        // Note: Parent controls state, this just notifies on save
                                        // For live updates, parent should pass setUsername too
                                    }}
                                    className="w-full border-3 border-black p-3 font-black focus:outline-none focus:ring-2 focus:ring-[#2A9D8F] bg-white shadow-[2px_2px_0_0_#000]"
                                    placeholder="Enter username"
                                    disabled={loading}
                                />
                            </div>

                            <button
                                onClick={handleSave}
                                disabled={loading}
                                className="w-full bg-[#2A9D8F] text-white border-3 border-black py-3 font-black uppercase shadow-[4px_4px_0_0_#000] flex items-center justify-center gap-2 disabled:opacity-50 transition-all active:translate-y-1 active:shadow-none"
                            >
                                {loading ? 'Saving...' : <><Save className="w-5 h-5" /> Save Changes</>}
                            </button>
                        </div>
                    </motion.div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
