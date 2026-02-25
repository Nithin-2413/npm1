import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => ({
  server: {
    host: "0.0.0.0",
    port: 3000,
    hmr: {
      overlay: false,
    },
    allowedHosts: [
      "localhost",
      "9750af0c-7d6a-4e8d-bcd5-e8391389a9da.preview.emergentagent.com",
      "9750af0c-7d6a-4e8d-bcd5-e8391389a9da.cluster-0.preview.emergentcf.cloud",
      ".preview.emergentagent.com",
      ".emergentcf.cloud",
    ],
  },
  plugins: [react(), mode === "development" && componentTagger()].filter(Boolean),
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
}));
