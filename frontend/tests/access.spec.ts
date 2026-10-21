import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import fixture from "./fixture.json" with { type: "json" };

test("anonymous visitors see accessible login and no analysis requests", async ({
  page,
}) => {
  let analyses = 0;
  await page.route("**/api/auth/me", (route) =>
    route.fulfill({
      status: 401,
      json: { detail: { code: "unauthenticated" } },
    }),
  );
  page.on("request", (request) => {
    if (request.url().includes("/api/analyses")) analyses++;
  });
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Entre para acessar suas análises" }),
  ).toBeVisible();
  await expect(page.getByLabel("E-mail", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Entrar com Google" }),
  ).toBeVisible();
  await expect(page.getByLabel("Senha", { exact: true })).toHaveAttribute(
    "type",
    "password",
  );
  expect(analyses).toBe(0);
  const result = await new AxeBuilder({ page })
    .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
    .analyze();
  expect(result.violations).toEqual([]);
});

test("Google configuration failure keeps private content inaccessible", async ({
  page,
}) => {
  let sessions = 0;
  let configurations = 0;
  await page.route("**/api/auth/me", (route) =>
    route.fulfill({
      status: 401,
      json: { detail: { code: "unauthenticated" } },
    }),
  );
  await page.route("**/api/auth/config", (route) => {
    configurations++;
    return route.fulfill({ status: 503, json: {} });
  });
  await page.route("**/api/auth/session", (route) => {
    sessions++;
    return route.fulfill({ status: 403, json: {} });
  });
  await page.goto("/");
  await page.getByRole("button", { name: "Entrar com Google" }).click();
  await expect(
    page.getByText(
      "O serviço de acesso está temporariamente indisponível. Tente novamente mais tarde ou contate o administrador.",
    ),
  ).toBeVisible();
  await expect(page.getByLabel("Qual ação vamos analisar?")).not.toBeVisible();
  expect(sessions).toBe(0);
  await page.getByRole("button", { name: "Entrar com Google" }).click();
  await expect(
    page.getByRole("button", { name: "Entrar com Google" }),
  ).toBeEnabled();
  expect(configurations).toBe(2);
  expect(sessions).toBe(0);
});

test("email login shows service incident without blaming credentials", async ({
  page,
}) => {
  const incident = "a".repeat(32);
  await page.route("**/api/auth/me", (route) =>
    route.fulfill({ status: 401, json: {} }),
  );
  await page.route("**/api/auth/config", (route) =>
    route.fulfill({
      status: 503,
      json: { detail: { code: "auth_unavailable", incident } },
    }),
  );
  await page.goto("/");
  await page.getByLabel("E-mail", { exact: true }).fill("test@example.invalid");
  await page.getByLabel("Senha", { exact: true }).fill("test-only-password");
  await page.getByRole("button", { name: "Entrar", exact: true }).click();
  await expect(page.getByRole("status")).toContainText(
    "serviço de acesso está temporariamente indisponível",
  );
  await expect(page.getByRole("status")).toContainText(incident);
  await expect(page.getByRole("status")).not.toContainText("Confira os dados");
  await expect(page.getByLabel("Senha", { exact: true })).toHaveValue("");
  await expect(page.getByLabel("Qual ação vamos analisar?")).not.toBeVisible();
});

test("logout clears private state even when server is unavailable and offers retry", async ({
  page,
}) => {
  await page.route("**/api/auth/me", (route) =>
    route.fulfill({ json: { uid: "alice", role: "user" } }),
  );
  await page.route("**/api/auth/logout", (route) =>
    route.fulfill({ status: 503, json: {} }),
  );
  await page.route("**/api/analyses**", (route) =>
    route.fulfill({ json: fixture }),
  );
  await page.addInitScript(
    (id) => sessionStorage.setItem("analista.active-analysis.alice", id),
    fixture.id,
  );
  await page.goto("/");
  await page.getByRole("button", { name: "Sair da conta" }).click();
  await expect(
    page.getByRole("button", { name: "Concluir saída" }),
  ).toBeVisible();
  await expect(page.getByLabel("Qual ação vamos analisar?")).not.toBeVisible();
  expect(
    await page.evaluate(() =>
      Object.keys(sessionStorage).filter((key) =>
        key.startsWith("analista.active-analysis"),
      ),
    ),
  ).toEqual([]);
  await page.route("**/api/auth/logout", (route) =>
    route.fulfill({ status: 204 }),
  );
  await page.getByRole("button", { name: "Concluir saída" }).click();
  await expect(page.getByLabel("Senha", { exact: true })).toBeVisible();
});

test("expired API session returns to login without private results", async ({
  page,
}) => {
  await page.route("**/api/auth/me", (route) =>
    route.fulfill({ json: { uid: "bob", role: "user" } }),
  );
  await page.route("**/api/analyses**", (route) =>
    route.fulfill({ status: 401, json: {} }),
  );
  await page.goto("/");
  await page.getByLabel("Qual ação vamos analisar?").fill("PETR4");
  await page.getByRole("button", { name: "Analisar ação" }).click();
  await expect(
    page.getByText("Sua sessão terminou. Entre novamente."),
  ).toBeVisible();
  await expect(page.getByLabel("Senha", { exact: true })).toBeVisible();
});

test("a different account does not restore the previous account analysis", async ({
  page,
}) => {
  let reads = 0;
  await page.route("**/api/auth/me", (route) =>
    route.fulfill({ json: { uid: "bob", role: "user" } }),
  );
  await page.route("**/api/analyses**", (route) => {
    reads++;
    return route.fulfill({ json: fixture });
  });
  await page.addInitScript(
    (id) => sessionStorage.setItem("analista.active-analysis.alice", id),
    fixture.id,
  );
  await page.goto("/");
  await expect(page.getByLabel("Qual ação vamos analisar?")).toBeVisible();
  expect(reads).toBe(0);
});
