import { existsSync } from "node:fs";
import { defineConfig } from "@playwright/test";

const systemChromium = ["/usr/bin/chromium", "/usr/bin/chromium-browser"].find((p) => existsSync(p));

export default defineConfig({
  testDir: "tests/e2e",
  use: {
    baseURL: "http://127.0.0.1:4319",
    launchOptions: systemChromium && !process.env.PLAYWRIGHT_BUNDLED ? { executablePath: systemChromium } : {},
  },
  projects: [
    { name: "desktop", use: { viewport: { width: 1440, height: 900 } } },
    { name: "mobile", use: { viewport: { width: 390, height: 844 } } },
  ],
  webServer: { command: "node tests/e2e/serve.mjs", url: "http://127.0.0.1:4319/hackathon/", reuseExistingServer: true },
});
