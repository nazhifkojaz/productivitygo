import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';

interface TaskQuotaResponse {
    quota: number;
}

/**
 * Fetch the current task quota (number of mandatory tasks).
 * The quota determines how many mandatory tasks users must plan.
 *
 * @returns Query result with quota number (default 3 on error)
 */
export function useTaskQuota() {
    const { session } = useAuth();

    return useQuery({
        queryKey: ['tasks', 'quota'],
        queryFn: async (): Promise<number> => {
            const { data } = await axios.get<TaskQuotaResponse>('/api/tasks/quota', {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
            return data.quota;
        },
        enabled: !!session?.access_token,
        staleTime: 1000 * 60 * 60, // 1 hour - quota doesn't change often
        retry: 3,
        retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    });
}
