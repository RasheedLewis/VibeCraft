import { useQuery } from '@tanstack/react-query'

interface FeatureFlags {
  sections: boolean
}

export const useFeatureFlags = () => {
  return useQuery<FeatureFlags>({
    queryKey: ['featureFlags'],
    queryFn: async () => {
      const response = await fetch('/api/v1/config/features')
      if (!response.ok) {
        throw new Error('Failed to fetch feature flags')
      }
      return response.json()
    },
    staleTime: 5 * 60 * 1000, // Cache for 5 minutes
    retry: 1,
  })
}
