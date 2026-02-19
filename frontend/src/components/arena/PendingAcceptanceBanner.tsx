/**
 * PendingAcceptanceBanner Component
 *
 * Displays the rematch invite banner with accept button.
 * Shows different messaging for creator vs recipient.
 *
 * REFACTOR-005: Phase 5 - Week 3 - Arena.tsx Refactoring
 */

import { Shield } from 'lucide-react';

export interface PendingAcceptanceBannerProps {
    isCreator: boolean;
    onAcceptInvite: () => void;
}

export default function PendingAcceptanceBanner({
    isCreator,
    onAcceptInvite,
}: PendingAcceptanceBannerProps) {
    return (
        <div className="max-w-4xl mx-auto mb-6">
            <div className="bg-[#2A9D8F] border-4 border-black shadow-[6px_6px_0_0_#000] p-8 text-center">
                <h2 className="text-2xl font-black uppercase mb-2 flex items-center justify-center gap-2 text-white">
                    <Shield className="w-8 h-8" /> Rematch Invite
                </h2>
                {isCreator ? (
                    <p className="font-bold text-white">
                        Waiting for your rival to accept the challenge.
                    </p>
                ) : (
                    <div className="flex flex-col items-center gap-4">
                        <p className="font-bold text-white">
                            You have been challenged to a rematch!
                        </p>
                        <button
                            onClick={onAcceptInvite}
                            className="bg-white border-3 border-black px-6 py-3 font-black uppercase shadow-[4px_4px_0_0_#000] hover:translate-x-[2px] hover:translate-y-[2px] hover:shadow-[2px_2px_0_0_#000] transition-all"
                        >
                            Accept Challenge
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
}
