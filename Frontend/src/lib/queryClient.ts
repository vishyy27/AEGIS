import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 5000,
      gcTime: 10 * 60 * 1000,
      refetchOnWindowFocus: true,
      retry: 2,
    },
  },
});
