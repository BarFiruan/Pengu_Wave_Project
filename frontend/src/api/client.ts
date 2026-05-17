/**
 * Thin fetch wrapper that always sends cookies (`credentials: "include"`)
 * and throws a typed ApiError on non-2xx responses.
 *
 * We send cookies (not a Bearer token in Authorization) because the session
 * sid lives in an httpOnly cookie set by the backend.
 */

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:3001";

/** Thrown by apiFetch when the server returns an error status. */
export class ApiError extends Error {
  status: number;

  constructor(status: number, message: string) {
    super(message);
    this.status = status;
    this.name = "ApiError";
  }
}

/**
 * JSON API helper. Cookies carry the session; no localStorage token.
 */
export async function apiFetch<T>(
  path: string,
  options: RequestInit = {},
): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    ...options,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
      ...(options.headers ?? {}),
    },
  });

  const data = await response.json().catch(() => ({}));

  if (!response.ok) {
    const message =
      typeof data === "object" && data && "error" in data
        ? String((data as { error: string }).error)
        : response.statusText;
    throw new ApiError(response.status, message);
  }

  return data as T;
}
