import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';

export function useCurrentBattle() {
    const { session } = useAuth();

    return useQuery({
        queryKey: ['battle', 'current'],
        queryFn: async () => {
            const { data } = await axios.get('/api/battles/current', {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
            return data;
        },
        enabled: !!session?.access_token,
        retry: false, // Don't retry on 404 (no active battle)
        throwOnError: false, // Don't throw on error, just return error state
    });
}
