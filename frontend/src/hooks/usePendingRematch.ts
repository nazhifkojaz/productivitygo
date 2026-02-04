import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';

export function usePendingRematch(battleId: string | undefined) {
    const { session } = useAuth();

    return useQuery({
        queryKey: ['battles', battleId, 'pendingRematch'],
        queryFn: async () => {
            const { data } = await axios.get(`/api/invites/${battleId}/pending-rematch`, {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
            return data;
        },
        enabled: !!battleId && !!session?.access_token,
    });
}
