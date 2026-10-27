/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** "true" only in the static GitHub Pages build (`--mode pages`, .env.pages). */
  readonly VITE_STATIC_DEMO?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
