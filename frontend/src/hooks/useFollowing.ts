import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';

export function useFollowing() {
    const { session } = useAuth();

    return useQuery({
        queryKey: ['social', 'following'],
        queryFn: async () => {
            const { data } = await axios.get('/api/social/following', {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
            return data;
        },
        enabled: !!session?.access_token,
    });
}
