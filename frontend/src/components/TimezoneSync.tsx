import { useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import axios from 'axios';
import { toast } from 'sonner';
import { useProfile } from '../hooks/useProfile';
import { useQueryClient } from '@tanstack/react-query';

export default function TimezoneSync() {
    const { session } = useAuth();
    const { data: profile } = useProfile();
    const queryClient = useQueryClient();

    useEffect(() => {
        const syncTimezone = async () => {
            if (!session?.access_token || !profile) return;

            const currentProfileTimezone = profile.timezone || 'UTC';
            const browserTimezone = Intl.DateTimeFormat().resolvedOptions().timeZone;

            // 2. Only auto-update if profile is UTC (default) and browser is NOT UTC
            // This ensures we catch new users (signup) but don't overwrite manual settings
            if (currentProfileTimezone === 'UTC' && browserTimezone !== 'UTC') {
                console.log(`Auto-syncing timezone from ${currentProfileTimezone} to ${browserTimezone}`);

                try {
                    await axios.put('/api/users/profile',
                        { timezone: browserTimezone },
                        { headers: { Authorization: `Bearer ${session.access_token}` } }
                    );

                    // Invalidate profile query to refetch updated data
                    queryClient.invalidateQueries({ queryKey: ['profile'] });

                    toast.success(`Timezone set to ${browserTimezone}`);
                } catch (error) {
                    console.error("Failed to sync timezone", error);
                }
            }
        };

        syncTimezone();
    }, [session, profile, queryClient]);

    return null; // Render nothing
}
