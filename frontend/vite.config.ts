import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The browser only ever calls relative /v1/... URLs; Vite proxies them to the FastAPI backend
// (`make api`, port 8000). host 0.0.0.0 + allowedHosts so the dev server works behind a preview proxy.
export default defineConfig({
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
});
