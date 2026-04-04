import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import path from "path";

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@rid/shared": path.resolve(__dirname, "../../packages/shared/src")
    }
  },
  build: {
    outDir: "dist",
    rollupOptions: {
      output: {
        // Stable filenames so Django {% static %} references don't change
        entryFileNames: "assets/index.js",
        chunkFileNames: "assets/[name].js",
        assetFileNames: "assets/[name].[ext]"
      }
    }
  },
  server: {
    port: 5173,
    proxy: {
      // Proxy API calls to Django/Uvicorn during local dev
      "/api": "http://localhost:8000",
      "/accounts": "http://localhost:8000"
    }
  }
});

