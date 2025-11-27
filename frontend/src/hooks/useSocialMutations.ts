import { useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';

export function useSocialMutations() {
    const { session } = useAuth();
    const queryClient = useQueryClient();

    const followMutation = useMutation({
        mutationFn: async (userId: string) => {
            return axios.post(`/api/social/follow/${userId}`, {}, {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
        },
        onSuccess: () => {
            // Invalidate following list and any public profiles
            queryClient.invalidateQueries({ queryKey: ['social', 'following'] });
            queryClient.invalidateQueries({ queryKey: ['publicProfile'] });
        },
    });

    const unfollowMutation = useMutation({
        mutationFn: async (userId: string) => {
            return axios.delete(`/api/social/unfollow/${userId}`, {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
        },
        onSuccess: () => {
            // Invalidate following list and any public profiles
            queryClient.invalidateQueries({ queryKey: ['social', 'following'] });
            queryClient.invalidateQueries({ queryKey: ['publicProfile'] });
        },
    });

    return { followMutation, unfollowMutation };
}
