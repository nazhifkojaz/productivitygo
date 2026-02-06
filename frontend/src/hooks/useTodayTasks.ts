import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';
import type { Task } from '../types';

interface UseTodayTasksOptions {
    enabled?: boolean;
}

/**
 * Fetch today's tasks for the active battle or adventure.
 * Uses React Query for caching and automatic refetching.
 *
 * @param options - Query options like enabled flag
 * @returns Query result with tasks data
 */
export function useTodayTasks(options?: UseTodayTasksOptions) {
    const { session } = useAuth();

    return useQuery({
        queryKey: ['tasks', 'today'],
        queryFn: async (): Promise<Task[]> => {
            const { data } = await axios.get('/api/tasks/today', {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
            return data;
        },
        enabled: !!session?.access_token && (options?.enabled !== false),
        staleTime: 1000 * 60 * 5, // 5 minutes - tasks don't change that often
        retry: 2,
    });
}
