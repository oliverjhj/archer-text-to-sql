// API client foundation for the Archer frontend.
//
// No secrets belong in frontend code. The browser authenticates with the
// archer_session session cookie and nothing else; the backend proxy injects the
// webhook secret server-side. WEBHOOK_SECRET must never appear here, in a
// VITE_* variable, or in any bundled asset.

import type { AskErrorKind } from '../types/api';

/** Base URL for API calls. Empty string means same-origin relative paths. */
export const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? '').replace(
  /\/$/,
  '',
);

/** Resolve a path against the configured base URL. */
export function apiUrl(path: string): string {
  const normalisedPath = path.startsWith('/') ? path : `/${path}`;
  return `${API_BASE_URL}${normalisedPath}`;
}

/**
 * A failed API call, classified so callers can react to the kind of failure
 * rather than parse a message string.
 */
export class ApiError extends Error {
  readonly kind: AskErrorKind;
  readonly status: number | null;

  constructor(kind: AskErrorKind, message: string, status: number | null = null) {
    super(message);
    this.name = 'ApiError';
    this.kind = kind;
    this.status = status;
  }
}

function classify(status: number): { kind: AskErrorKind; message: string } {
  if (status === 401 || status === 403) {
    return {
      kind: 'unauthorised',
      message: 'Your session has expired. Sign in again to continue.',
    };
  }
  if (status === 429) {
    return {
      kind: 'rate_limited',
      message: 'Too many questions in a short period. Wait a moment and try again.',
    };
  }
  if (status >= 500) {
    return {
      kind: 'server',
      message: 'The server could not complete that request. Try again shortly.',
    };
  }
  return {
    kind: 'unknown',
    message: `The request failed (status ${status}).`,
  };
}

export interface JsonRequestOptions {
  signal?: AbortSignal;
}

/**
 * POST a JSON body and parse a JSON response.
 *
 * `credentials: 'include'` sends the same-origin archer_session cookie, which is
 * what authenticates /api/ask.
 *
 * `redirect: 'manual'` is a safety net rather than the main path. The backend
 * answers an unauthenticated /api/ request with a JSON 401, but page routes
 * still redirect to /login, so following a redirect here could hand back an
 * HTML login page with a 200 status. Treating a redirect as a session failure
 * removes that possibility entirely.
 */
export async function postJson<TResponse>(
  path: string,
  body: unknown,
  options: JsonRequestOptions = {},
): Promise<TResponse> {
  let response: Response;

  try {
    response = await fetch(apiUrl(path), {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      credentials: 'include',
      redirect: 'manual',
      signal: options.signal,
    });
  } catch (cause) {
    if (cause instanceof DOMException && cause.name === 'AbortError') {
      throw cause;
    }
    throw new ApiError('network', 'Could not reach the server. Check your connection.');
  }

  if (response.type === 'opaqueredirect') {
    throw new ApiError(
      'unauthorised',
      'Your session has expired. Sign in again to continue.',
      null,
    );
  }

  if (!response.ok) {
    const { kind, message } = classify(response.status);
    throw new ApiError(kind, message, response.status);
  }

  try {
    return (await response.json()) as TResponse;
  } catch {
    throw new ApiError('server', 'The server returned a response that could not be read.');
  }
}
