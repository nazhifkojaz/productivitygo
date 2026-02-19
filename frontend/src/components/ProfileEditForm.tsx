import { Save } from 'lucide-react';
import NeoModal from './NeoModal';

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

    return (
        <NeoModal
            isOpen={isOpen}
            onClose={onClose}
            maxWidth="max-w-md"
            title="Edit Identity"
        >
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
        </NeoModal>
    );
}
