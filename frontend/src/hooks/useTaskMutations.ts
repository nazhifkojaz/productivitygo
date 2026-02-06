import { useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import type { TaskCreate } from '../types';
import { toast } from 'sonner';

/**
 * Task mutations for completing tasks and saving draft tasks.
 * Provides optimistic updates and automatic cache invalidation.
 */
export function useTaskMutations() {
    const { session } = useAuth();
    const queryClient = useQueryClient();

    const completeTaskMutation = useMutation({
        mutationFn: async (taskId: string) => {
            await axios.post(`/api/tasks/${taskId}/complete`, {}, {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
        },
        onSuccess: () => {
            // Invalidate today's tasks to reflect the completion
            queryClient.invalidateQueries({ queryKey: ['tasks', 'today'] });
        },
        onError: (error) => {
            console.error('Failed to complete task:', error);
            toast.error('Failed to complete task');
        },
    });

    const saveDraftMutation = useMutation({
        mutationFn: async (tasks: TaskCreate[]) => {
            await axios.post('/api/tasks/draft', tasks, {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
        },
        onSuccess: () => {
            // Invalidate draft query to get the latest data
            queryClient.invalidateQueries({ queryKey: ['tasks', 'draft'] });
            toast.success('Plan saved successfully! You can edit this until midnight.');
        },
        onError: (error) => {
            console.error('Failed to save tasks:', error);
            toast.error('Failed to save plan.');
        },
    });

    return {
        completeTaskMutation,
        saveDraftMutation,
        isCompleting: completeTaskMutation.isPending,
        isSaving: saveDraftMutation.isPending,
    };
}
