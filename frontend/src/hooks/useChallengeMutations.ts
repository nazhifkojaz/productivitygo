import { useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';

/**
 * Parameters for sending a challenge to a known user (by ID)
 */
export interface SendChallengeParams {
    rivalId: string;
    startDate: string;  // Format: YYYY-MM-DD
    duration: number;   // 3, 5, or 7 days
}

/**
 * Parameters for sending a challenge by searching for user first (by email or username)
 */
export interface SendChallengeByEmailParams {
    emailOrUsername: string;
    startDate: string;
    duration: number;
}

/**
 * Challenge/Invite mutations for sending battle invites.
 * Supports both sending to a known user ID and searching by email/username first.
 */
export function useChallengeMutations() {
    const { session } = useAuth();
    const queryClient = useQueryClient();

    // Send challenge to a known user (by ID)
    const sendChallengeMutation = useMutation({
        mutationFn: async ({ rivalId, startDate, duration }: SendChallengeParams) => {
            const { data } = await axios.post('/api/invites/send', {
                rival_id: rivalId,
                start_date: startDate,
                duration: duration
            }, {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
            return data;
        },
        onSuccess: () => {
            // Invalidate invites list so it refreshes
            queryClient.invalidateQueries({ queryKey: ['battles', 'invites'] });
            toast.success(`Challenge sent successfully!`);
        },
        onError: (error: any) => {
            console.error('Failed to send challenge:', error);
            const errorDetail = error.response?.data?.detail;
            if (typeof errorDetail === 'string') {
                toast.error(errorDetail);
            } else if (Array.isArray(errorDetail)) {
                // Pydantic validation errors
                const messages = errorDetail.map((e: any) => `• ${e.msg}`).join('\n');
                toast.error(`Validation errors:\n${messages}`);
            } else {
                toast.error('Failed to send challenge. Please try again.');
            }
        },
    });

    // Send challenge by email/username (searches first, then sends)
    const sendChallengeByEmailMutation = useMutation({
        mutationFn: async ({ emailOrUsername, startDate, duration }: SendChallengeByEmailParams) => {
            // Step 1: Search for user by email or username
            const searchResponse = await axios.get(`/api/social/search?q=${encodeURIComponent(emailOrUsername)}`, {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });

            // Try to find exact match by email or username
            const rivalUser = searchResponse.data.find((u: any) =>
                u.email?.toLowerCase() === emailOrUsername.toLowerCase() ||
                u.username?.toLowerCase() === emailOrUsername.toLowerCase()
            );

            if (!rivalUser) {
                throw new Error(`User "${emailOrUsername}" not found in the system.`);
            }

            // Step 2: Send invite using rival_id
            const { data } = await axios.post('/api/invites/send', {
                rival_id: rivalUser.id,
                start_date: startDate,
                duration: duration
            }, {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });

            return { ...data, rivalUsername: rivalUser.username };
        },
        onSuccess: (data) => {
            // Invalidate invites list so it refreshes
            queryClient.invalidateQueries({ queryKey: ['battles', 'invites'] });
            toast.success(`Invite sent to ${data.rivalUsername}!`);
        },
        onError: (error: any) => {
            console.error('Failed to send challenge:', error);
            const errorMessage = error.message || error.response?.data?.detail;
            toast.error(errorMessage || 'Failed to send invite');
        },
    });

    return {
        sendChallengeMutation,
        sendChallengeByEmailMutation,
        isSending: sendChallengeMutation.isPending || sendChallengeByEmailMutation.isPending,
    };
}
