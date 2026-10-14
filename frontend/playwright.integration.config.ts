import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./integration",
  workers: 1,
  timeout: 25000,
  use: {
    ...devices["Desktop Chrome"],
    baseURL: "http://127.0.0.1:8012",
    httpCredentials: {
      username: "integration",
      password: "integration-test-only",
    },
    trace: "retain-on-failure",
  },
  webServer: {
    command: "node integration/start-server.mjs",
    url: "http://127.0.0.1:8012/healthz",
    reuseExistingServer: false,
  },
});
