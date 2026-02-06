import { useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';

export function useBattleMutations() {
    const { session } = useAuth();
    const queryClient = useQueryClient();

    const acceptInviteMutation = useMutation({
        mutationFn: async (battleId: string) => {
            return axios.post(`/api/invites/${battleId}/accept`, {}, {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
        },
        onSuccess: () => {
            // Accepting an invite affects: invites list, current battle, and profile
            queryClient.invalidateQueries({ queryKey: ['battles', 'invites'] });
            queryClient.invalidateQueries({ queryKey: ['battles', 'current'] });
            queryClient.invalidateQueries({ queryKey: ['profile'] });
        },
    });

    const rejectInviteMutation = useMutation({
        mutationFn: async (battleId: string) => {
            return axios.post(`/api/invites/${battleId}/reject`, {}, {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
        },
        onSuccess: () => {
            // Rejecting only affects the invites list
            queryClient.invalidateQueries({ queryKey: ['battles', 'invites'] });
        },
    });

    return { acceptInviteMutation, rejectInviteMutation };
}
