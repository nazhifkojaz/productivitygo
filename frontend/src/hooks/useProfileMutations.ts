import { useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { toast } from 'sonner';

/**
 * Profile mutations for updating user profile data.
 * Separated from data fetching to follow single responsibility principle.
 */
export function useProfileMutations() {
    const { session } = useAuth();
    const queryClient = useQueryClient();

    // Update profile (username + avatar_emoji)
    const updateProfileMutation = useMutation({
        mutationFn: async (data: { username?: string; avatar_emoji?: string }) => {
            return axios.put('/api/users/profile', data, {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['profile'] });
            toast.success('Profile updated successfully!');
        },
        onError: () => {
            toast.error('Failed to update profile');
        },
    });

    // Update avatar only (immediate save)
    const updateAvatarMutation = useMutation({
        mutationFn: async (emoji: string) => {
            return axios.put('/api/users/profile', { avatar_emoji: emoji }, {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['profile'] });
            toast.success('Avatar updated!');
        },
        onError: () => {
            toast.error('Failed to update avatar');
        },
    });

    // Update timezone mutation
    const updateTimezoneMutation = useMutation({
        mutationFn: async (timezone: string) => {
            return axios.put('/api/users/profile', { timezone }, {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
        },
        onSuccess: (_, timezone) => {
            queryClient.invalidateQueries({ queryKey: ['profile'] });
            toast.success(`Timezone updated to ${timezone}`);
        },
        onError: () => {
            toast.error('Failed to update timezone');
        },
    });

    return {
        updateProfileMutation,
        updateAvatarMutation,
        updateTimezoneMutation,
    };
}
