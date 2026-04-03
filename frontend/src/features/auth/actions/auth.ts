"use server";

import { cookies } from "next/headers";
import { apiFetch, ApiError } from "@/lib/api";
import type { components } from "@/types/api";

type UserData = components["schemas"]["UserRead"];

type AuthTokenResponse = components["schemas"]["TokenResponse"];

const ACCESS_TOKEN_COOKIE = "access_token";
const REFRESH_TOKEN_COOKIE = "refresh_token";
const ACCESS_TOKEN_MAX_AGE = 14 * 60; // 14 minutes (slightly less than 15 min server TTL)
const REFRESH_TOKEN_MAX_AGE = 30 * 24 * 60 * 60; // 30 days

const IS_PRODUCTION = process.env.NODE_ENV === "production";

const COOKIE_BASE_OPTIONS = {
  httpOnly: true,
  secure: IS_PRODUCTION,
  sameSite: "lax" as const,
  path: "/",
};

async function setAuthCookies(tokens: AuthTokenResponse): Promise<void> {
  const cookieStore = await cookies();

  cookieStore.set(ACCESS_TOKEN_COOKIE, tokens.access_token, {
    ...COOKIE_BASE_OPTIONS,
    maxAge: ACCESS_TOKEN_MAX_AGE,
  });

  cookieStore.set(REFRESH_TOKEN_COOKIE, tokens.refresh_token, {
    ...COOKIE_BASE_OPTIONS,
    maxAge: REFRESH_TOKEN_MAX_AGE,
  });
}

async function clearAuthCookies(): Promise<void> {
  const cookieStore = await cookies();
  cookieStore.delete(ACCESS_TOKEN_COOKIE);
  cookieStore.delete(REFRESH_TOKEN_COOKIE);
}

export async function loginAction(
  email: string,
  password: string
): Promise<{ success: boolean; error?: string }> {
  try {
    const tokens = await apiFetch<AuthTokenResponse>("/api/auth/login", {
      method: "POST",
      body: { email, password },
    });

    await setAuthCookies(tokens);
    return { success: true };
  } catch (err) {
    if (err instanceof ApiError) {
      return { success: false, error: err.message };
    }
    return { success: false, error: "An unexpected error occurred" };
  }
}

export async function registerAction(
  email: string,
  display_name: string,
  password: string
): Promise<{ success: boolean; error?: string }> {
  try {
    const tokens = await apiFetch<AuthTokenResponse>("/api/auth/register", {
      method: "POST",
      body: { email, display_name, password },
    });

    await setAuthCookies(tokens);
    return { success: true };
  } catch (err) {
    if (err instanceof ApiError) {
      return { success: false, error: err.message };
    }
    return { success: false, error: "An unexpected error occurred" };
  }
}

export async function logoutAction(): Promise<void> {
  await clearAuthCookies();
}

export async function getCurrentUserAction(): Promise<UserData | null> {
  try {
    const cookieStore = await cookies();
    const accessToken = cookieStore.get(ACCESS_TOKEN_COOKIE)?.value;

    if (!accessToken) {
      return null;
    }

    const user = await apiFetch<UserData>("/api/auth/me", {
      token: accessToken,
    });

    return user;
  } catch (err) {
    if (err instanceof ApiError && err.status === 401) {
      // Attempt token refresh
      try {
        const cookieStore = await cookies();
        const refreshToken = cookieStore.get(REFRESH_TOKEN_COOKIE)?.value;

        if (!refreshToken) {
          await clearAuthCookies();
          return null;
        }

        const tokens = await apiFetch<AuthTokenResponse>("/api/auth/refresh", {
          method: "POST",
          body: { refresh_token: refreshToken },
        });

        await setAuthCookies(tokens);

        const user = await apiFetch<UserData>("/api/auth/me", {
          token: tokens.access_token,
        });

        return user;
      } catch {
        await clearAuthCookies();
        return null;
      }
    }
    return null;
  }
}
