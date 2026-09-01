/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL for backend API calls. Empty means same-origin relative paths. */
  readonly VITE_API_BASE_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
