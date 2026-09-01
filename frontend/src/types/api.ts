// Shared types describing the contract with the backend ask endpoint.
// The live request/response shapes mirror the existing FastAPI POST /ask:
//   request:  { "question": string }   (backend also accepts string[])
//   response: { "answer": string }     (a Markdown string)
// These types are used by the API skeletons and the UI state today; the live
// call is wired in Phase 4C via the future authenticated /api/ask proxy.

export interface AskRequest {
  question: string;
}

export interface AskResponse {
  answer: string;
}

export type AskStatus = 'idle' | 'loading' | 'success' | 'error';

export type AskErrorKind =
  | 'network'
  | 'unauthorised'
  | 'rate_limited'
  | 'server'
  | 'empty'
  | 'unknown';

export interface AskError {
  kind: AskErrorKind;
  message: string;
}

/** A single question/answer exchange rendered in the workspace. */
export interface ConversationEntry {
  id: string;
  question: string;
  answer: string | null;
  pending: boolean;
  error: AskError | null;
}
