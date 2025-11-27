import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { useAuth } from '../context/AuthContext';

export function useBattleDetails(battleId: string | undefined) {
    const { session } = useAuth();

    return useQuery({
        queryKey: ['battles', battleId],
        queryFn: async () => {
            const { data } = await axios.get(`/api/battles/${battleId}`, {
                headers: { Authorization: `Bearer ${session?.access_token}` }
            });
            return data;
        },
        enabled: !!battleId && !!session?.access_token,
    });
}
