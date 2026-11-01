import { tanstackStart } from "@tanstack/react-start/plugin/vite";
import viteReact from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Static-only build: SPA mode prerenders one shell, the browser loads data at runtime.
// `base: "./"` keeps every asset URL relative so the same build works under any
// GitHub Pages project subpath or as a downloaded artifact folder.
export default defineConfig({
  base: "./",
  plugins: [
    tanstackStart({
      spa: { enabled: true, prerender: { outputPath: "/index.html", crawlLinks: false } },
    }),
    viteReact(),
  ],
});
