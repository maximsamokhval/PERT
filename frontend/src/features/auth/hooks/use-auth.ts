"use client";

import {
  useQuery,
  useMutation,
  useQueryClient,
  type UseQueryResult,
  type UseMutationResult,
} from "@tanstack/react-query";
import {
  loginAction,
  registerAction,
  logoutAction,
  getCurrentUserAction,
  type UserData,
} from "@/features/auth/actions/auth";

const CURRENT_USER_QUERY_KEY = ["currentUser"] as const;

export function useCurrentUser(): UseQueryResult<UserData | null> {
  return useQuery({
    queryKey: CURRENT_USER_QUERY_KEY,
    queryFn: () => getCurrentUserAction(),
    staleTime: 5 * 60 * 1000, // 5 minutes
    retry: false,
  });
}

interface LoginVariables {
  email: string;
  password: string;
}

export function useLogin(): UseMutationResult<
  { success: boolean; error?: string },
  Error,
  LoginVariables
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ email, password }: LoginVariables) =>
      loginAction(email, password),
    onSuccess: (result) => {
      if (result.success) {
        void queryClient.invalidateQueries({ queryKey: CURRENT_USER_QUERY_KEY });
      }
    },
  });
}

interface RegisterVariables {
  email: string;
  display_name: string;
  password: string;
}

export function useRegister(): UseMutationResult<
  { success: boolean; error?: string },
  Error,
  RegisterVariables
> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: ({ email, display_name, password }: RegisterVariables) =>
      registerAction(email, display_name, password),
    onSuccess: (result) => {
      if (result.success) {
        void queryClient.invalidateQueries({ queryKey: CURRENT_USER_QUERY_KEY });
      }
    },
  });
}

export function useLogout(): UseMutationResult<void, Error, void> {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => logoutAction(),
    onSuccess: () => {
      queryClient.setQueryData(CURRENT_USER_QUERY_KEY, null);
      void queryClient.removeQueries({ queryKey: CURRENT_USER_QUERY_KEY });
    },
  });
}
