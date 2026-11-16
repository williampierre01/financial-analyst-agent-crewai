import AxeBuilder from "@axe-core/playwright";
import type { Page } from "@playwright/test";
import { test, expect } from "./authFixture";
import fixture from "./fixture.json" with { type: "json" };
import type { Analysis, Snapshot } from "../src/services/api";

const complete = () =>
  structuredClone(fixture) as Omit<Analysis, "data" | "interpretation"> & {
    data: Snapshot;
    interpretation: string;
  };

test("provider definitions remain explicit without changing supplied amounts", async ({
  page,
}) => {
  await mock(page);
  await page.goto("/");
  await search(page);
  await expect(
    page.getByRole("row", { name: /Lucro líquido informado pelo provedor/ }),
  ).toContainText("acionistas");
  await expect(
    page.getByRole("row", { name: /Fluxo de caixa livre do provedor/ }),
  ).toContainText("Fórmula não conciliada");
  await expect(
    page.getByText("Lucro líquido anual do provedor", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText("Fluxo de caixa livre anual do provedor", { exact: true }),
  ).toBeVisible();
});
async function mock(page: Page, result = complete()) {
  let posts = 0;
  await page.route("**/api/analyses**", async (route) => {
    if (route.request().method() === "POST") posts++;
    await route.fulfill({
      json:
        route.request().method() === "POST"
          ? { ...result, status: "running", data: null, interpretation: null }
          : result,
      status: route.request().method() === "POST" ? 202 : 200,
    });
  });
  return () => posts;
}
async function search(page: Page) {
  await page.getByLabel("Qual ação vamos analisar?").fill("petr4");
  await page.getByRole("button", { name: "Analisar ação" }).click();
}

test("initial state is honest, responsive and validates before requesting", async ({
  page,
}, info) => {
  const posts = await mock(page);
  await page.goto("/");
  await expect(page.getByText("Seu ponto de partida")).toBeVisible();
  await page.getByRole("button", { name: "Analisar ação" }).click();
  await expect(page.getByRole("alert")).toContainText(
    "Informe um código da B3",
  );
  await page.getByLabel("Qual ação vamos analisar?").fill("AAPL");
  await page.getByLabel("Qual ação vamos analisar?").press("Enter");
  await expect(page.getByRole("alert")).toBeVisible();
  expect(posts()).toBe(0);
  await page.getByRole("button", { name: "VALE3", exact: true }).click();
  await expect(page.getByLabel("Qual ação vamos analisar?")).toHaveValue(
    "VALE3",
  );
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: info.outputPath("initial.png"),
    fullPage: true,
  });
});

test("data arrives before interpretation and polling never repeats POST", async ({
  page,
}, info) => {
  let ready = false,
    posts = 0;
  await page.route("**/api/analyses**", async (route) => {
    const result = complete();
    if (route.request().method() === "POST") {
      posts++;
      expect(route.request().postDataJSON()).toEqual({ ticker: "PETR4" });
      await route.fulfill({
        status: 202,
        json: {
          ...result,
          status: "running",
          data: null,
          interpretation: null,
        },
      });
    } else {
      await route.fulfill({
        json: ready
          ? result
          : {
              ...result,
              status: "running",
              stage: "quant",
              interpretation_status: "running",
              interpretation: null,
            },
      });
    }
  });
  await page.goto("/");
  await search(page);
  await expect(page.getByRole("heading", { name: /PETR4/ })).toBeVisible();
  await expect(page.getByText("R$ 32,51", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Analisando…" }),
  ).toBeDisabled();
  await expect(
    page.getByRole("heading", { name: "Preparando uma leitura dos dados" }),
  ).toBeVisible();
  ready = true;
  await expect(
    page.getByRole("heading", { name: "Leitura dos resultados" }),
  ).toBeVisible();
  expect(posts).toBe(1);
  await expect(
    page.getByRole("button", { name: "Analisar ação" }),
  ).toBeEnabled();
  await expect(page.locator("thead").first()).toContainText("31/12/2025");
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: info.outputPath("completed.png"),
    fullPage: true,
  });
});

test("partial and missing values retain zero and negative numbers with honest scaling", async ({
  page,
}) => {
  const result = complete();
  result.data.status = "partial";
  result.data.warnings = ["Moeda de um demonstrativo não confirmada."];
  const period = result.data.statements.income_statement[0];
  period.values.revenue = 0;
  period.values.net_income = -1000000;
  period.values.diluted_eps = 1.52;
  result.interpretation_status = "failed";
  result.interpretation = "";
  result.errors = [
    {
      code: "interpretation_failed",
      message: "A interpretação está indisponível.",
    },
  ];
  await mock(page, result);
  await page.goto("/");
  await search(page);
  await expect(page.getByText("Dados parciais", { exact: true })).toBeVisible();
  await expect(page.getByText(result.data.warnings[0])).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Interpretação indisponível" }),
  ).toBeVisible();
  const table = page.getByRole("table").first();
  await expect(table.getByRole("row", { name: /^Receita/ })).toContainText(
    "R$ 0,00 mi",
  );
  await expect(
    table.getByRole("row", { name: /^Lucro líquido/ }),
  ).toContainText("R$ -1,00 mi");
  await expect(
    table.getByRole("row", { name: /^Lucro diluído/ }),
  ).toContainText("R$ 1,52");
  await expect(
    table.getByRole("row", { name: /^Resultado operacional/ }),
  ).toContainText("Não disponível");
  await page.getByLabel("Escala dos valores").selectOption("full");
  await expect(
    table.getByRole("row", { name: /^Lucro líquido/ }),
  ).toContainText("R$ -1.000.000,00");
});

test("unavailable data displays no invented quote or interpretation", async ({
  page,
}) => {
  const result = complete();
  const unavailable = {
    ...result,
    interpretation: null,
    interpretation_status: "skipped",
    data: {
      ...result.data,
      status: "unavailable",
      quote: null,
      provider_used: null,
      statements: { income_statement: [], balance_sheet: [], cash_flow: [] },
    },
  };
  await page.route("**/api/analyses**", (route) =>
    route.fulfill({ json: unavailable }),
  );
  await page.goto("/");
  await search(page);
  await expect(
    page.getByText("Dados indisponíveis", { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole("heading", { name: "Sem base para interpretar" }),
  ).toBeVisible();
  await expect(page.getByText("Não disponível", { exact: true })).toBeVisible();
});

test("capacity errors are readable and do not automatically create jobs", async ({
  page,
}) => {
  let requests = 0;
  await page.route("**/api/analyses", (route) => {
    requests++;
    return route.fulfill({ status: 429, json: { detail: "capacity" } });
  });
  await page.goto("/");
  await search(page);
  await expect(page.getByRole("alert")).toContainText("limite de análises");
  expect(requests).toBe(1);
  await expect(
    page.getByRole("button", { name: "Analisar ação" }),
  ).toBeEnabled();
});

test("expiration preserves last data and allows a new search", async ({
  page,
}) => {
  let reads = 0;
  await page.route("**/api/analyses**", (route) => {
    if (route.request().method() === "POST")
      return route.fulfill({
        status: 202,
        json: { ...complete(), status: "running", data: null },
      });
    reads++;
    return route.fulfill(
      reads === 1
        ? { json: { ...complete(), status: "running", interpretation: null } }
        : { status: 404, json: { detail: "expired" } },
    );
  });
  await page.goto("/");
  await search(page);
  await expect(page.getByText("R$ 32,51", { exact: true })).toBeVisible();
  await expect(page.getByRole("alert")).toContainText("expirou");
  await expect(page.getByText("R$ 32,51", { exact: true })).toBeVisible();
  await expect(
    page.getByRole("button", { name: "Analisar ação" }),
  ).toBeEnabled();
});

test("network failure keeps data and resumes only with GET", async ({
  page,
}) => {
  let reads = 0,
    posts = 0,
    resumed = false;
  await page.route("**/api/analyses**", (route) => {
    if (route.request().method() === "POST") {
      posts++;
      return route.fulfill({
        status: 202,
        json: { ...complete(), status: "running", data: null },
      });
    }
    reads++;
    if (reads > 1 && !resumed) return route.abort("failed");
    return route.fulfill({
      json: { ...complete(), status: resumed ? "completed" : "running" },
    });
  });
  await page.goto("/");
  await search(page);
  await expect(
    page.getByRole("button", { name: "Retomar acompanhamento" }),
  ).toBeVisible({ timeout: 15000 });
  await expect(page.getByText("R$ 32,51", { exact: true })).toBeVisible();
  resumed = true;
  await page.getByRole("button", { name: "Retomar acompanhamento" }).click();
  await expect(
    page.getByRole("button", { name: "Analisar ação" }),
  ).toBeEnabled();
  expect(posts).toBe(1);
});

test("reload resumes a known job without POST and markdown is not executable", async ({
  page,
}) => {
  let posts = 0;
  const result = complete();
  result.interpretation =
    '<img src=x onerror="window.injected=1">\n\n[Link inseguro](javascript:alert(1))\n\n### Texto seguro';
  await page.route("**/api/analyses**", (route) => {
    if (route.request().method() === "POST") posts++;
    return route.fulfill({ json: result });
  });
  await page.addInitScript(
    (id) => sessionStorage.setItem("analista.active-analysis.alice", id),
    result.id,
  );
  await page.goto("/");
  await expect(
    page.getByRole("heading", { name: "Texto seguro" }),
  ).toBeVisible();
  expect(posts).toBe(0);
  expect(await page.locator(".markdown img").count()).toBe(0);
  expect(
    (await page.locator(".markdown a").first().getAttribute("href")) ?? "",
  ).not.toContain("javascript:");
});

test("key pages have no automated WCAG AA violations", async ({ page }) => {
  await mock(page);
  await page.goto("/");
  const check = async () => {
    const results = await new AxeBuilder({ page })
      .withTags(["wcag2a", "wcag2aa", "wcag21aa"])
      .analyze();
    expect(
      results.violations.map((v) => ({
        id: v.id,
        nodes: v.nodes.map((n) => ({
          target: n.target,
          summary: n.failureSummary,
        })),
      })),
    ).toEqual([]);
  };
  await check();
  await search(page);
  await expect(
    page.getByRole("heading", { name: "Leitura dos resultados" }),
  ).toBeVisible();
  await check();
});

test("long reports keep page contained and tables independently scrollable", async ({
  page,
}, info) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  const result = complete();
  const longWord = "Documento".repeat(50);
  const url = `https://example.com/${"fonte".repeat(65)}`;
  const headers = Array.from({ length: 12 }, (_, i) => `Exercício ${2025 - i}`);
  result.interpretation = [
    "## Relatório extenso",
    `Texto longo ${longWord}`,
    `[${url}](${url})`,
    `| Indicador | ${headers.join(" | ")} |`,
    `| --- | ${headers.map(() => "---").join(" | ")} |`,
    `| Receita | ${headers.map(() => "R$ 123.456.789.012,34").join(" | ")} |`,
    "",
    "Parágrafo após a tabela permanece legível sem rolagem lateral.",
    "```text\n" + longWord + "\n```",
    `> ${longWord}`,
    `- ${longWord}`,
  ]
    .join("\n\n")
    .replace(/\|\n\n\|/g, "|\n|");
  result.data.warnings = [longWord];
  for (const periods of Object.values(result.data.statements)) {
    const period = periods[0];
    periods.splice(
      0,
      periods.length,
      ...headers.map((_, index) => ({
        ...structuredClone(period),
        period_end: `${2025 - index}-12-31`,
      })),
    );
  }
  await mock(page, result);
  await page.goto("/");
  await search(page);
  await expect(
    page.getByRole("heading", { name: "Relatório extenso" }),
  ).toBeVisible();
  for (const width of [320, 390, 700, 768, 1150, 1280, 1440, 1920]) {
    await page.setViewportSize({ width, height: 1000 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
      `page at ${width}`,
    ).toBe(true);
    const financial = await page.locator(".financial-panel").boundingBox();
    const interpretation = await page
      .locator(".interpretation-panel")
      .boundingBox();
    expect(interpretation!.y).toBeGreaterThanOrEqual(
      financial!.y + financial!.height,
    );
    expect(interpretation!.width).toBeCloseTo(financial!.width, 0);
    expect(
      await page
        .locator(".markdown")
        .evaluate((el) => el.scrollWidth <= el.clientWidth),
    ).toBe(true);
    for (const region of await page.locator(".table-scroll").all()) {
      const overflows = await region.evaluate(
        (el) => el.scrollWidth > el.clientWidth,
      );
      if (width <= 390) expect(overflows).toBe(true);
      await region.focus();
      await expect(region).toBeFocused();
      if (overflows) {
        await region.evaluate((el) => {
          el.scrollLeft = 0;
        });
        await region.press("ArrowRight");
        await expect
          .poll(() => region.evaluate((el) => el.scrollLeft))
          .toBeGreaterThan(0);
      }
      await region.evaluate((el) => {
        el.scrollLeft = el.scrollWidth;
      });
      if (overflows)
        expect(await region.evaluate((el) => el.scrollLeft > 0)).toBe(true);
      await expect
        .poll(() =>
          region.evaluate((el) => {
            // Measure together after scrolling; keyboard scrolling can still be settling.
            el.scrollLeft = el.scrollWidth;
            const lastCell = el.querySelector("tr:last-child td:last-child")!;
            return (
              lastCell.getBoundingClientRect().right -
              el.getBoundingClientRect().right
            );
          }),
        )
        .toBeLessThanOrEqual(1);
    }
    await page.getByLabel("Escala dos valores").selectOption("full");
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    if (width === 390 || width === 1440) {
      await page
        .locator(".interpretation-panel")
        .screenshot({ path: info.outputPath(`report-${width}.png`) });
    }
  }
});
