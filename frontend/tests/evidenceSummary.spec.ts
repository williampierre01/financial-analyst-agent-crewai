import AxeBuilder from "@axe-core/playwright";
import { test, expect } from "./authFixture";
import fixture from "./fixture.json" with { type: "json" };
import metrics from "./metrics.fixture.json" with { type: "json" };
import { missingReportSections } from "../src/services/reportMarkdown";

test("structure check ignores code and preserves missing sections", () => {
  expect(
    missingReportSections(
      "### Leitura dos resultados\nTexto\n```text\n### Notícias e fontes\n```\n### Limitações da análise",
    ),
  ).toEqual(["Notícias e fontes"]);
  expect(
    missingReportSections(
      "### Leitura dos resultados\n### Notícias e fontes\n### Limitações da análise",
    ),
  ).toEqual([]);
});

test("calculated highlights and evidence survive interpretation failure", async ({
  page,
}, info) => {
  await page.route("**/api/analyses**", (route) =>
    route.fulfill({
      status: route.request().method() === "POST" ? 202 : 200,
      json: {
        ...fixture,
        metrics,
        interpretation: null,
        interpretation_status: "failed",
      },
    }),
  );
  await page.goto("/");
  await page.getByLabel("Qual ação vamos analisar?").fill("PETR4");
  await page.getByRole("button", { name: "Analisar ação" }).click();
  const panel = page.locator(".evidence-panel");
  await expect(
    panel.getByRole("heading", { name: "Destaques dos indicadores" }),
  ).toBeVisible();
  await expect(panel.locator(".evidence-highlights article")).toHaveCount(2);
  await expect(
    page.getByRole("heading", { name: "Interpretação indisponível" }),
  ).toBeVisible();
  await panel.locator("summary").click();
  await expect(
    panel.getByText("Fórmula:", { exact: false }).first(),
  ).toBeVisible();
  await expect(
    panel.getByText("Fonte: Yahoo Finance", { exact: false }).first(),
  ).toBeVisible();
  expect(
    (await new AxeBuilder({ page }).include(".evidence-panel").analyze())
      .violations,
  ).toEqual([]);
  await panel.screenshot({ path: info.outputPath("evidence-summary.png") });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBeTruthy();
});

test("missing operands show reasons without synthetic highlights", async ({
  page,
}) => {
  const unavailable = metrics.map((m) => ({
    ...m,
    status: "unavailable",
    value: null,
    inputs: [null],
    reason: "Faltam valores necessários para este cálculo.",
  }));
  await page.route("**/api/analyses**", (route) =>
    route.fulfill({
      status: route.request().method() === "POST" ? 202 : 200,
      json: {
        ...fixture,
        metrics: unavailable,
        interpretation: "### Leitura dos resultados\nTexto preservado.",
      },
    }),
  );
  await page.goto("/");
  await page.getByLabel("Qual ação vamos analisar?").fill("PETR4");
  await page.getByRole("button", { name: "Analisar ação" }).click();
  await expect(
    page.getByText(
      "Sem indicadores calculados para o exercício mais recente. Consulte os motivos abaixo.",
    ),
  ).toBeVisible();
  await page.locator(".evidence-panel summary").click();
  await expect(
    page.getByText("Valor necessário ausente na base.").first(),
  ).toBeVisible();
  await expect(
    page.getByText("Relatório com estrutura incompleta.", { exact: false }),
  ).toBeVisible();
});
