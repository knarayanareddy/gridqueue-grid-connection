import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// GitHub Pages serves the project site under /<repo>/. Only the static Pages build (`--mode pages`, see .env.pages)
// uses that base; dev, `vite preview` and the API-backed build keep "/" so the /v1 proxy and the dev preview work.
export const PAGES_BASE = "/gridqueue-grid-connection/";

// The browser only ever calls relative /v1/... URLs; Vite proxies them to the FastAPI backend
// (`make api`, port 8000). host 0.0.0.0 + allowedHosts so the dev server works behind a preview proxy.
export default defineConfig(({ mode }) => ({
  base: mode === "pages" ? PAGES_BASE : "/",
  plugins: [react()],
  server: {
    host: "0.0.0.0",
    port: 5173,
    allowedHosts: true,
    proxy: {
      "/v1": { target: "http://127.0.0.1:8000", changeOrigin: true },
      "/health": { target: "http://127.0.0.1:8000", changeOrigin: true },
    },
  },
  preview: { host: "0.0.0.0", port: 4173, allowedHosts: true },
}));
