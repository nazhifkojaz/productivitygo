import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 5 * 60 * 1000, // 5 minutes - data is fresh for this long
            gcTime: 10 * 60 * 1000,   // 10 minutes - cached data garbage collection time
            retry: 1,                  // Only retry failed requests once
            refetchOnWindowFocus: false, // Don't refetch when window regains focus
        },
    },
});
