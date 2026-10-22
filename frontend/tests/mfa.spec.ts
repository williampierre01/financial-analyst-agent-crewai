import { test, expect, type Page } from "@playwright/test";

// Firebase SDK double only in Playwright routing; no real account or secret.
async function enrollment(page: Page, failure: string) {
  await page.route("**/api/auth/me", (route) =>
    route.fulfill({ status: 401, json: {} }),
  );
  await page.route("**/api/auth/config", (route) =>
    route.fulfill({
      json: {
        apiKey: "test-only",
        authDomain: "test.invalid",
        projectId: "test-only",
      },
    }),
  );
  await page.route("**/api/auth/session", (route) =>
    route.fulfill({ status: 403, json: { detail: { code: "mfa_required" } } }),
  );
  await page.route(
    /\/node_modules\/\.vite\/deps\/firebase_auth\.js(?:\?.*)?$/,
    (route) =>
      route.fulfill({
        contentType: "application/javascript",
        body: `
      let attempts = 0;
      const auth = {};
      const user = { emailVerified: true, getIdToken: async () => 'test-token' };
      export const inMemoryPersistence = {};
      export const browserPopupRedirectResolver = {};
      export const initializeAuth = () => auth;
      export const signOut = async () => {};
      export const signInWithEmailAndPassword = async () => ({user});
      export const signInWithPopup = async () => ({user});
      export class GoogleAuthProvider { setCustomParameters() {} }
      export const sendPasswordResetEmail = async () => {};
      export const sendEmailVerification = async () => {};
      export const getMultiFactorResolver = () => ({});
      export const multiFactor = () => ({enrolledFactors: [], getSession: async () => ({}),
        enroll: async () => { if (attempts++ === 0) throw {code: ${JSON.stringify(failure)}, message: 'PRIVATE-MUST-NOT-APPEAR'}; }
      });
      export const TotpMultiFactorGenerator = {
        FACTOR_ID: 'totp',
        generateSecret: async () => ({secretKey: 'TEST-ONLY-NOT-A-REAL-SECRET'}),
        assertionForEnrollment: () => ({}), assertionForSignIn: () => ({})
      };
    `,
      }),
  );
  await page.goto("/");
  await page.getByLabel("E-mail", { exact: true }).fill("test@example.invalid");
  await page.getByLabel("Senha", { exact: true }).fill("test-only-password");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByText("TEST-ONLY-NOT-A-REAL-SECRET")).toBeVisible();
  await page.getByLabel("Código do autenticador").fill("000000");
  await page.getByRole("button", { name: "Confirmar autenticador" }).click();
}

test("invalid TOTP preserves enrollment for retry and then requires fresh login", async ({
  page,
}) => {
  await enrollment(page, "auth/invalid-verification-code");
  await expect(page.getByRole("status")).toContainText(
    "código do autenticador não foi aceito",
  );
  await expect(page.getByText("TEST-ONLY-NOT-A-REAL-SECRET")).toBeVisible();
  await expect(page.getByLabel("Código do autenticador")).toHaveValue("");
  await expect(page.getByLabel("Senha", { exact: true })).not.toBeVisible();
  await expect(page.getByLabel("Qual ação vamos analisar?")).not.toBeVisible();
  await page.getByLabel("Código do autenticador").fill("123456");
  await page.getByRole("button", { name: "Confirmar autenticador" }).click();
  await expect(page.getByRole("status")).toContainText(
    "Autenticador cadastrado",
  );
  await expect(page.getByLabel("Senha", { exact: true })).toBeVisible();
  await expect(page.getByText("TEST-ONLY-NOT-A-REAL-SECRET")).not.toBeVisible();
});

for (const failure of [
  "auth/session-expired",
  "auth/operation-not-allowed",
  "auth/unknown",
]) {
  test(`non-retryable MFA failure clears temporary enrollment: ${failure}`, async ({
    page,
  }) => {
    await enrollment(page, failure);
    await expect(page.getByLabel("Senha", { exact: true })).toBeVisible();
    await expect(
      page.getByText("TEST-ONLY-NOT-A-REAL-SECRET"),
    ).not.toBeVisible();
    await expect(page.getByRole("status")).not.toContainText(
      "Confira os dados",
    );
    await expect(page.getByRole("status")).not.toContainText(
      "PRIVATE-MUST-NOT-APPEAR",
    );
    await expect(
      page.getByLabel("Qual ação vamos analisar?"),
    ).not.toBeVisible();
  });
}
