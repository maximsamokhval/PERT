const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export class ApiError extends Error {
  readonly code: string;
  readonly detail: string;
  readonly status: number;

  constructor(code: string, message: string, detail: string, status: number) {
    super(message);
    this.name = "ApiError";
    this.code = code;
    this.detail = detail;
    this.status = status;
  }
}

interface ApiErrorResponse {
  code: string;
  message: string;
  detail: string;
  request_id: string;
}

export interface ApiFetchOptions {
  method?: string;
  body?: unknown;
  token?: string;
}

export async function apiFetch<T>(
  path: string,
  options: ApiFetchOptions = {}
): Promise<T> {
  const { method = "GET", body, token } = options;

  const headers: Record<string, string> = {
    "Content-Type": "application/json",
  };

  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const init: RequestInit = {
    method,
    headers,
  };

  if (body !== undefined) {
    init.body = JSON.stringify(body);
  }

  const response = await fetch(`${API_BASE_URL}${path}`, init);

  if (!response.ok) {
    let errorData: ApiErrorResponse;

    try {
      errorData = (await response.json()) as ApiErrorResponse;
    } catch {
      throw new ApiError(
        "UNKNOWN_ERROR",
        `HTTP error ${response.status}`,
        `Request to ${path} failed with status ${response.status}`,
        response.status
      );
    }

    throw new ApiError(
      errorData.code ?? "UNKNOWN_ERROR",
      errorData.message ?? "An error occurred",
      errorData.detail ?? "",
      response.status
    );
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json() as Promise<T>;
}
