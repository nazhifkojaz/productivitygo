import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';

export function useBattleInvites() {
    const { session } = useAuth();

    return useQuery({
        queryKey: ['battles', 'invites'],
        queryFn: async () => {
            const { data } = await axios.get('/api/battles/invites', {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
            return data;
        },
        enabled: !!session?.access_token,
    });
}
