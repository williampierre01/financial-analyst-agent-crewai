import { test as base, expect } from "@playwright/test";

// Existing analysis tests start with an authenticated API response, not a
// production auth bypass. Login-specific tests use Playwright directly.
export const test = base.extend({
  page: async ({ page }, use) => {
    await page.route("**/api/auth/me", (route) =>
      route.fulfill({ json: { uid: "alice", role: "user" } }),
    );
    await use(page);
  },
});
export { expect };
