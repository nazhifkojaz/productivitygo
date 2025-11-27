import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';

export function useProfile() {
    const { session } = useAuth();

    return useQuery({
        queryKey: ['profile'],
        queryFn: async () => {
            const { data } = await axios.get('/api/users/profile', {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
            return data;
        },
        enabled: !!session?.access_token,
    });
}
