import { useState, useCallback } from 'react';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import { supabase } from '../lib/supabase';
import { toast } from 'sonner';
import type { ProfileData } from '../types';

interface UseProfileFormReturn {
    // Data
    profile: ProfileData | null;
    isLoading: boolean;
    error: Error | null;

    // Edit state (local UI state not managed by React Query)
    isEditing: boolean;
    username: string;
    selectedEmoji: string;
    showEmojiPicker: boolean;

    // Setters
    setIsEditing: (value: boolean) => void;
    setUsername: (value: string) => void;
    setShowEmojiPicker: (value: boolean) => void;

    // Mutations
    updateProfile: () => Promise<void>;
    updateAvatar: (emoji: string) => Promise<void>;
    updateTimezone: (timezone: string) => Promise<void>;
    updatePassword: (password: string) => Promise<void>;

    // Refetch
    refetch: () => void;
}

export function useProfileForm(): UseProfileFormReturn {
    const { session } = useAuth();
    const queryClient = useQueryClient();

    // Local UI state (not managed by React Query)
    const [isEditing, setIsEditing] = useState(false);
    const [username, setUsername] = useState('');
    const [selectedEmoji, setSelectedEmoji] = useState('😀');
    const [showEmojiPicker, setShowEmojiPicker] = useState(false);

    // Fetch profile data
    const {
        data: profile,
        isLoading,
        error,
        refetch,
    } = useQuery({
        queryKey: ['profile'],
        queryFn: async (): Promise<ProfileData> => {
            const { data } = await axios.get('/api/users/profile', {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
            // Sync local state with fetched data
            setUsername(data.username || '');
            setSelectedEmoji(data.avatar_emoji || '😀');
            return data;
        },
        enabled: !!session?.access_token,
    });

    // Update profile mutation (username + avatar_emoji)
    const updateProfileMutation = useMutation({
        mutationFn: async (data: { username?: string; avatar_emoji?: string }) => {
            return axios.put('/api/users/profile', data, {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
        },
        onSuccess: () => {
            // Invalidate profile query to refetch updated data
            queryClient.invalidateQueries({ queryKey: ['profile'] });
            setIsEditing(false);
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
            setShowEmojiPicker(false);
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

    // Update password mutation (uses Supabase directly)
    const updatePasswordMutation = useMutation({
        mutationFn: async (password: string) => {
            const { error } = await supabase.auth.updateUser({ password });
            if (error) throw error;
        },
        onSuccess: () => {
            toast.success('Password updated successfully!');
        },
        onError: (error: any) => {
            toast.error(error.message);
            throw error;
        },
    });

    // Wrapped mutation functions
    const updateProfile = useCallback(async () => {
        await updateProfileMutation.mutateAsync({
            username,
            avatar_emoji: selectedEmoji,
        });
    }, [username, selectedEmoji, updateProfileMutation]);

    const updateAvatar = useCallback(async (emoji: string) => {
        setSelectedEmoji(emoji);
        await updateAvatarMutation.mutateAsync(emoji);
    }, [updateAvatarMutation]);

    const updateTimezone = useCallback(async (timezone: string) => {
        await updateTimezoneMutation.mutateAsync(timezone);
    }, [updateTimezoneMutation]);

    const updatePassword = useCallback(async (password: string) => {
        await updatePasswordMutation.mutateAsync(password);
    }, [updatePasswordMutation]);

    return {
        profile: profile || null,
        isLoading,
        error,
        isEditing,
        username,
        selectedEmoji,
        showEmojiPicker,
        setIsEditing,
        setUsername,
        setShowEmojiPicker,
        updateProfile,
        updateAvatar,
        updateTimezone,
        updatePassword,
        refetch: () => refetch(),
    };
}
