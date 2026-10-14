import { test, expect } from "@playwright/test";

test("compiled React uses authenticated FastAPI, publishes data and prevents excess jobs", async ({
  page,
  request,
}) => {
  let posts = 0;
  page.on("request", (request) => {
    if (request.method() === "POST" && request.url().endsWith("/api/analyses"))
      posts++;
  });
  await page.goto("/");
  await page.getByLabel("Qual ação vamos analisar?").fill("PETR4");
  await page.getByRole("button", { name: "Analisar ação" }).click();
  await expect(page.getByText("32,51", { exact: false }).first()).toBeVisible();
  await expect(
    page.getByText("Interpretação do teste integrado."),
  ).not.toBeVisible();
  const extra = await request.post("/api/analyses", {
    data: { ticker: "PETR4" },
  });
  expect(extra.status()).toBe(429);
  await expect(page.getByText("Interpretação do teste integrado.")).toBeVisible(
    { timeout: 10000 },
  );
  expect(posts).toBe(1);
});

test("provider exception retains financial data without exposing internal details", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByLabel("Qual ação vamos analisar?").fill("VALE3");
  await page.getByRole("button", { name: "Analisar ação" }).click();
  await expect(
    page.getByText("Interpretação indisponível", { exact: true }),
  ).toBeVisible({ timeout: 10000 });
  await expect(page.getByText("32,51", { exact: false }).first()).toBeVisible();
  await expect(page.locator("body")).not.toContainText(
    "private-provider-error",
  );
});

test("server deadline reaches the browser and retains published data", async ({
  page,
}) => {
  await page.goto("/");
  await page.getByLabel("Qual ação vamos analisar?").fill("ITUB4");
  await page.getByRole("button", { name: "Analisar ação" }).click();
  await expect(
    page.getByText("A análise excedeu o tempo limite.", { exact: false }),
  ).toBeVisible({ timeout: 12000 });
  await expect(page.getByText("32,51", { exact: false }).first()).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Analisar ação" }),
  ).toBeEnabled();
});
