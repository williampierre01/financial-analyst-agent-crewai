import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Browser requests stay on the same origin; no permissive CORS is needed.
const proxy = {
  "/api": {
    target: process.env.API_TARGET ?? "http://127.0.0.1:8000",
    changeOrigin: true,
    rewrite: (path: string) => path.replace(/^\/api/, ""),
  },
};
export default defineConfig({
  plugins: [react()],
  server: { port: 5173, strictPort: true, proxy },
  preview: { port: 4173, strictPort: true, proxy },
});
