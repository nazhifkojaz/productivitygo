import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';

export function useUserSearch(query: string) {
    const { session } = useAuth();

    return useQuery({
        queryKey: ['social', 'search', query],
        queryFn: async () => {
            const { data } = await axios.get(`/api/social/search?q=${query}`, {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
            return data;
        },
        enabled: !!session?.access_token && query.length > 0,
        staleTime: 2 * 60 * 1000, // 2 minutes - search results can go stale faster
    });
}
