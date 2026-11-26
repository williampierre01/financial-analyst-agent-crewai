import { test, expect } from "./authFixture";
import fixture from "./fixture.json" with { type: "json" };

test("reported operating income shows source and keeps unapproved periods unavailable", async ({
  page,
}, info) => {
  const periods = fixture.data.statements.income_statement;
  const reference = {
    value: 26113000000,
    source_field: "annualTotalOperatingIncomeAsReported",
    document_url:
      "https://www.sec.gov/Archives/edgar/data/1119639/000129281426002168/pbrform20f_2025.htm",
    document_location: "F-4",
    evidence_digest: "a".repeat(64),
    reviewed_at: "2026-11-26T22:41:09+00:00",
    scope: "Revisão documental com alcance limitado; não constitui auditoria.",
  };
  const data = {
    ...fixture.data,
    schema_version: "3.1",
    statements: {
      ...fixture.data.statements,
      income_statement: [
        {
          ...periods[0],
          currency: "USD",
          values: {
            ...periods[0].values,
            operating_income: null,
            reported_operating_income: 26113000000,
          },
          reported_operating_income_reference: reference,
        },
        {
          ...periods[0],
          period_end: "2024-12-31",
          currency: "USD",
          values: {
            ...periods[0].values,
            operating_income: null,
            reported_operating_income: null,
          },
          reported_operating_income_reference: null,
        },
      ],
    },
  };
  await page.route("**/api/analyses**", (route) =>
    route.fulfill({
      status: route.request().method() === "POST" ? 202 : 200,
      json: { ...fixture, data },
    }),
  );
  await page.goto("/");
  await page.getByLabel("Qual ação vamos analisar?").fill("PETR4");
  await page.getByRole("button", { name: "Analisar ação" }).click();
  const row = page
    .getByRole("row")
    .filter({ hasText: "Resultado operacional reportado" });
  await expect(row).toContainText("USD 26.113,00 mi");
  await expect(row).toContainText("Não disponível");
  await expect(
    row.getByRole("link", { name: "Fonte oficial · F-4" }),
  ).toHaveAttribute("href", reference.document_url);
  await expect(row).toContainText(reference.scope);
  await row.screenshot({
    path: info.outputPath("reported-operating-income.png"),
  });
});
