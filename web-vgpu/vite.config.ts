import { defineConfig } from "vite";
import { wgslVitePlugin } from "vgpu/client";

export default defineConfig({
  plugins: [wgslVitePlugin({ minify: true })],
  server: {
    port: 4173,
    strictPort: true,
  },
});
