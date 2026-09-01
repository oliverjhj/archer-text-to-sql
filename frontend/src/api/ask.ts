import { postJson } from './client';
import type { AskRequest, AskResponse } from '../types/api';

// Endpoint for the future authenticated proxy added in Phase 4C.
// The proxy validates the archer_session session cookie and injects the x-api-key
// header server-side before forwarding to the existing POST /ask. This keeps
// the backend secret out of the browser entirely.
export const ASK_ENDPOINT = '/api/ask';

/**
 * Send a question to the backend and return the answer.
 *
 * Phase 4B skeleton: defined and typed but intentionally not called anywhere
 * yet. The UI runs on mock state until Phase 4C wires this in.
 */
export async function ask(
  request: AskRequest,
  options: { signal?: AbortSignal } = {},
): Promise<AskResponse> {
  return postJson<AskResponse>(ASK_ENDPOINT, request, options);
}
