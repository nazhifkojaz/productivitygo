import { useState, useEffect } from 'react';
import { useProfile } from './useProfile';
import { useProfileMutations } from './useProfileMutations';
import type { ProfileData } from '../types';

interface UseProfileFormReturn {
    // Data (from useProfile)
    profile: ProfileData | null;
    isLoading: boolean;
    error: unknown;

    // Form state (local only)
    username: string;
    selectedEmoji: string;
    isEditing: boolean;
    showEmojiPicker: boolean;

    // Setters
    setUsername: (value: string) => void;
    setSelectedEmoji: (value: string) => void;
    setIsEditing: (value: boolean) => void;
    setShowEmojiPicker: (value: boolean) => void;

    // Mutations (from useProfileMutations)
    updateProfile: () => Promise<void>;
    updateAvatar: (emoji: string) => Promise<void>;
    updateTimezone: (timezone: string) => Promise<void>;
    updatePassword: (password: string) => Promise<void>;

    // Refetch
    refetch: () => void;
}

/**
 * Profile form hook that combines data fetching, mutations, and UI state.
 * Refactored to use useProfile for data fetching and useProfileMutations for mutations.
 * This hook now only manages UI state (editing mode, emoji picker, form values).
 */
export function useProfileForm(): UseProfileFormReturn {
    // Use existing hooks for data fetching and mutations
    const { data: profile, isLoading, error, refetch } = useProfile();
    const {
        updateProfileMutation,
        updateAvatarMutation,
        updateTimezoneMutation,
        updatePasswordMutation,
    } = useProfileMutations();

    // Local UI state
    const [isEditing, setIsEditing] = useState(false);
    const [showEmojiPicker, setShowEmojiPicker] = useState(false);

    // Form state - sync with profile data when it changes
    const [username, setUsername] = useState('');
    const [selectedEmoji, setSelectedEmoji] = useState('😀');

    // Sync form state when profile data changes
    useEffect(() => {
        if (profile) {
            setUsername(profile.username || '');
            setSelectedEmoji(profile.avatar_emoji || '😀');
        }
    }, [profile]);

    // Wrapped mutation functions with UI state management
    const updateProfile = async () => {
        await updateProfileMutation.mutateAsync({
            username,
            avatar_emoji: selectedEmoji,
        });
        setIsEditing(false);
    };

    const updateAvatar = async (emoji: string) => {
        setSelectedEmoji(emoji);
        await updateAvatarMutation.mutateAsync(emoji);
        setShowEmojiPicker(false);
    };

    const updateTimezone = async (timezone: string) => {
        await updateTimezoneMutation.mutateAsync(timezone);
    };

    const updatePassword = async (password: string) => {
        await updatePasswordMutation.mutateAsync(password);
    };

    return {
        profile: profile || null,
        isLoading,
        error,
        username,
        selectedEmoji,
        isEditing,
        showEmojiPicker,
        setUsername,
        setSelectedEmoji,
        setIsEditing,
        setShowEmojiPicker,
        updateProfile,
        updateAvatar,
        updateTimezone,
        updatePassword,
        refetch: () => refetch(),
    };
}
