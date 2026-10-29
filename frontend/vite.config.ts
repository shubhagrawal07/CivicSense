/// <reference types="vitest/config" />
import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".");
  const apiUrl = env.VITE_API_BASE_URL ?? "http://localhost:8000/api";
  const backend = apiUrl.replace(/\/api\/?$/, "");

  return {
    plugins: [react()],
    server: {
      proxy: { "/uploads": backend },
    },
    test: {
      environment: "jsdom",
      globals: true,
      setupFiles: ["./src/setupTests.ts"],
    },
  };
});
