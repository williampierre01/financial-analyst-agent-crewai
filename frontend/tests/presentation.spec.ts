import { test, expect } from "@playwright/test";
import { reportMarkdown } from "../src/services/reportMarkdown";
import { money } from "../src/services/format";
import fixture from "./fixture.json" with { type: "json" };

test("known report titles are repaired without changing numbers, links or code", () => {
  const values = "R$ -1.500,00 mi; R$ 12,34 por ação; USD 10,00; 0; 15%; 2,3x";
  const source =
    "```markdown\n**###Leitura dos resultados**\n" +
    values +
    "\n\\#\\#\\# Notícias e fontes\n[fonte](https://example.com/#origem)\n### Limitações da análise\n```";
  const result = reportMarkdown(source);
  expect(result).toContain("### Leitura dos resultados\n");
  expect(result).toContain("\n### Notícias e fontes\n");
  expect(result).toContain(values);
  expect(result).toContain("[fonte](https://example.com/#origem)");
  const code = "```text\n###Leitura dos resultados\n```";
  expect(reportMarkdown(code)).toBe(code);
  expect(reportMarkdown("    ###Leitura dos resultados")).toBe(
    "    ###Leitura dos resultados",
  );
  expect(reportMarkdown("Citação literal: ### Leitura dos resultados")).toBe(
    "Citação literal: ### Leitura dos resultados",
  );
  expect(reportMarkdown(result)).toBe(result.trim());
});

test("currency formatting preserves per-share, small, negative and missing values", () => {
  expect(money(1500000000, "BRL", true)).toBe("R$ 1.500,00 mi");
  expect(money(-1500000000, "BRL", true)).toBe("R$ -1.500,00 mi");
  expect(money(12.34, "BRL", false)).toBe("R$ 12,34");
  expect(money(1200000, "BRL", false)).toBe("R$ 1.200.000,00");
  expect(money(12.34, "BRL", true)).toBe("R$ 12,34");
  expect(money(0, "BRL", false)).toBe("R$ 0,00");
  expect(money(null, "BRL", true)).toBe("Não disponível");
  expect(money(12.34, "USD")).toBe("USD 12,34");
  expect(money(12.34, null)).toBe("Moeda não informada 12,34");
});

test("progress reflects received data and malformed report headings render as headings", async ({
  page,
}, info) => {
  let stage = 0;
  await page.route("**/api/analyses**", async (route) => {
    await route.fulfill({
      status: route.request().method() === "POST" ? 202 : 200,
      json: {
        ...fixture,
        status: stage < 2 ? "running" : "completed",
        stage: stage === 0 ? "gathering" : stage === 1 ? "quant" : "done",
        data: stage === 0 ? null : fixture.data,
        interpretation_status: stage < 2 ? "running" : "completed",
        interpretation:
          stage < 2
            ? null
            : "```markdown\n**###Leitura dos resultados**\nReceita: R$ 1.500,00 mi. Lucro diluído por ação: R$ 12,34 por ação.\n\\#\\#\\# Notícias e fontes\nSem notícias nesta simulação.\n### Limitações da análise\nDados fictícios.\n```",
      },
    });
  });
  await page.goto("/");
  await page.getByLabel("Qual ação vamos analisar?").fill("PETR4");
  await page.getByRole("button", { name: "Analisar ação" }).click();
  await expect(
    page.getByText("Os dados aparecerão assim que estiverem disponíveis."),
  ).toBeVisible();
  stage = 1;
  await expect(
    page.getByText(
      "Dados disponíveis abaixo. A interpretação está em andamento.",
    ),
  ).toBeVisible();
  await expect(
    page.getByText("Os dados aparecerão assim que estiverem disponíveis."),
  ).toHaveCount(0);
  stage = 2;
  await expect(
    page.getByRole("heading", { name: "Leitura dos resultados", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Notícias e fontes", exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Limitações da análise", exact: true }),
  ).toBeVisible();
  await expect(page.locator(".markdown")).not.toContainText("###");
  await expect(page.locator(".markdown")).toContainText("R$ 12,34 por ação");
  await expect(
    page.getByRole("region", { name: "Andamento da análise" }),
  ).toHaveCount(0);
  await page
    .locator(".interpretation-panel")
    .screenshot({ path: info.outputPath("presentation.png") });
});
