import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';

export function useFollowers() {
    const { session } = useAuth();

    return useQuery({
        queryKey: ['social', 'followers'],
        queryFn: async () => {
            const { data } = await axios.get('/api/social/followers', {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
            return data;
        },
        enabled: !!session?.access_token,
    });
}
