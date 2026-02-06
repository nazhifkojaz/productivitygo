import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import type { TaskCreate } from '../types';

/**
 * Fetch the current draft tasks for planning.
 * Draft tasks are the tasks the user has planned for tomorrow.
 *
 * @returns Query result with draft tasks array
 */
export function useTaskDraft() {
    const { session } = useAuth();

    return useQuery({
        queryKey: ['tasks', 'draft'],
        queryFn: async (): Promise<TaskCreate[]> => {
            const { data } = await axios.get('/api/tasks/draft', {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
            return data;
        },
        enabled: !!session?.access_token,
        staleTime: 0, // Always fresh - user may be editing
        retry: 2,
    });
}
