const { defineConfig, devices } = require("@playwright/test");
const external = !!process.env.E2E_BASE_URL;

module.exports = defineConfig({
  testDir: "./e2e",
  workers: 1,
  timeout: 120000,
  expect: {
    timeout: 15000,
  },
  use: {
    baseURL: process.env.E2E_BASE_URL || "http://127.0.0.1:4175",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
    launchOptions: process.env.E2E_PROXY ? { proxy: { server: process.env.E2E_PROXY } } : {},
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
  webServer: external ? undefined : [
    { command: "node scripts/test-server.cjs backend", url: "http://127.0.0.1:8005/health", timeout: 60000, reuseExistingServer: false },
    { command: "node scripts/test-server.cjs frontend", url: "http://127.0.0.1:4175", timeout: 30000, reuseExistingServer: false }
  ],
});
