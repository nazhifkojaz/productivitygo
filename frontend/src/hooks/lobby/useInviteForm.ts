/**
 * Custom hook for battle invite form state and logic.
 *
 * REFACTOR-005: Phase 5 - Item 6.2
 */

import { useState, useMemo, useCallback } from 'react';
import { toast } from 'sonner';
import { useChallengeMutations } from '../useChallengeMutations';

export interface InviteFormState {
    searchEmail: string;
    setSearchEmail: (email: string) => void;
    startDate: string | null;
    setStartDate: (date: string | null) => void;
    duration: number;
    setDuration: (duration: number) => void;
    dateOptions: Date[];
    handleInvite: () => Promise<void>;
    isSending: boolean;
    isValid: boolean;
}

export function useInviteForm(): InviteFormState {
    const { sendChallengeByEmailMutation, isSending } = useChallengeMutations();

    const [searchEmail, setSearchEmail] = useState('');
    const [startDate, setStartDate] = useState<string | null>(null);
    const [duration, setDuration] = useState(5);

    // Date Options (Next 7 days)
    const dateOptions = useMemo(() => Array.from({ length: 7 }, (_, i) => {
        const d = new Date();
        d.setDate(d.getDate() + i + 1);
        return d;
    }), []);

    const handleInvite = useCallback(async () => {
        if (!startDate) {
            toast.error("Please select a start date first!");
            return;
        }
        if (!searchEmail) {
            toast.error("Please enter an email address!");
            return;
        }

        await sendChallengeByEmailMutation.mutateAsync({
            emailOrUsername: searchEmail,
            startDate: startDate,
            duration: duration
        });

        setSearchEmail('');
    }, [startDate, searchEmail, duration, sendChallengeByEmailMutation]);

    const isValid = searchEmail.length > 0 && startDate !== null;

    return {
        searchEmail,
        setSearchEmail,
        startDate,
        setStartDate,
        duration,
        setDuration,
        dateOptions,
        handleInvite,
        isSending,
        isValid
    };
}
