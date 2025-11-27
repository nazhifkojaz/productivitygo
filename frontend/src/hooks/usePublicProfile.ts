import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';

export function usePublicProfile(userId: string | undefined) {
    const { session } = useAuth();

    return useQuery({
        queryKey: ['publicProfile', userId],
        queryFn: async () => {
            const { data } = await axios.get(`/api/users/${userId}/public_profile`, {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
            return data;
        },
        enabled: !!userId && !!session?.access_token,
    });
}
