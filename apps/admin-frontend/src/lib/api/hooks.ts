import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import type { UseQueryOptions, UseMutationOptions } from '@tanstack/react-query';
import { apiClient } from './client';
import type { ApiError } from './client';
import type { ApiResponse, QueryParams } from './types';

type QueryKey = readonly unknown[];

interface UseApiQueryOptions<TData> extends Omit<UseQueryOptions<TData, ApiError, TData, QueryKey>, 'queryKey' | 'queryFn'> {
  endpoint: string;
  queryKey: QueryKey;
  params?: QueryParams;
  enabled?: boolean;
}

interface UseApiMutationOptions<TData, TVariables> extends Omit<UseMutationOptions<TData, ApiError, TVariables>, 'mutationFn'> {
  endpoint: string;
  method?: 'POST' | 'PUT' | 'PATCH' | 'DELETE';
  invalidateQueries?: QueryKey[];
}

/**
 * Hook para realizar queries GET con React Query
 * @param options - Opciones de configuración del query
 * @returns Resultado del query con data, isLoading, error, etc.
 */
export function useApiQuery<TData = unknown>(options: UseApiQueryOptions<TData>) {
  const { endpoint, queryKey, params, enabled = true, ...queryOptions } = options;

  return useQuery<TData, ApiError>({
    queryKey: [...queryKey, params],
    queryFn: async (): Promise<TData> => {
      const response = await apiClient.getInstance().get<ApiResponse<TData>>(endpoint, { params });
      return response.data.data || (response.data as unknown as TData);
    },
    enabled,
    ...queryOptions,
  });
}

/**
 * Hook para realizar mutaciones (POST, PUT, PATCH, DELETE) con React Query
 * @param options - Opciones de configuración de la mutación
 * @returns Función de mutación y estado (mutate, mutateAsync, isLoading, error, etc.)
 */
export function useApiMutation<TData = unknown, TVariables = unknown>(
  options: UseApiMutationOptions<TData, TVariables>
) {
  const { endpoint, method = 'POST', invalidateQueries = [], ...mutationOptions } = options;
  const queryClient = useQueryClient();

  return useMutation<TData, ApiError, TVariables>({
    mutationFn: async (variables: TVariables): Promise<TData> => {
      const response = await apiClient.getInstance().request<ApiResponse<TData>>({
        url: endpoint,
        method,
        data: variables,
      });
      return response.data.data || (response.data as unknown as TData);
    },
    onSuccess: () => {
      invalidateQueries.forEach((queryKey) => {
        queryClient.invalidateQueries({ queryKey });
      });
    },
    ...mutationOptions,
  });
}

/**
 * Hook para invalidar queries manualmente
 * @returns Función para invalidar queries
 */
export function useInvalidateQueries() {
  const queryClient = useQueryClient();

  return (queryKey: QueryKey): void => {
    queryClient.invalidateQueries({ queryKey });
  };
}

/**
 * Hook para obtener el estado de autenticación basado en la API key
 * @returns Estado de autenticación y funciones para gestionar la API key
 */
export function useAuth() {
  const apiKey = localStorage.getItem('api_key');

  const setApiKey = (key: string): void => {
    apiClient.setApiKey(key);
  };

  const clearApiKey = (): void => {
    apiClient.clearApiKey();
  };

  return {
    isAuthenticated: Boolean(apiKey),
    apiKey: apiKey || null,
    setApiKey,
    clearApiKey,
  };
}

