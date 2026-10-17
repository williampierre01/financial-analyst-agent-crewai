import { test, expect } from "@playwright/test";
import { reportPresentation } from "../src/services/reportPresentation";
import fixture from "./fixture.json" with { type: "json" };

type MarkdownNode = Parameters<ReturnType<typeof reportPresentation>>[0];

test("news titles and quotations retain literal technical words", () => {
  const title = {
    type: "heading",
    depth: 4,
    children: [{ type: "text", value: "Company reported growth" }],
  };
  const quote = {
    type: "blockquote",
    children: [
      {
        type: "paragraph",
        children: [
          {
            type: "text",
            value: "reported; date_label; article_verified = false",
          },
        ],
      },
    ],
  };
  const root: MarkdownNode = {
    type: "root",
    children: [
      {
        type: "heading",
        depth: 3,
        children: [{ type: "text", value: "Notícias e fontes" }],
      },
      title,
      quote,
    ],
  };
  const original = JSON.stringify(root);
  reportPresentation()(root);
  expect(JSON.stringify(root)).toBe(original);
});

test("verification cells preserve links, code and formatting", () => {
  for (const value of ["false", "true"]) {
    const variants: MarkdownNode[] = [
      {
        type: "link",
        url: "https://example.com/evidence",
        children: [{ type: "text", value }],
      },
      { type: "strong", children: [{ type: "text", value }] },
      { type: "inlineCode", value },
    ];
    for (const content of variants) {
      const cell = (value: string): MarkdownNode => ({
        type: "tableCell",
        children: [{ type: "text", value }],
      });
      const original = JSON.stringify(content);
      const root: MarkdownNode = {
        type: "root",
        children: [
          {
            type: "heading",
            depth: 3,
            children: [{ type: "text", value: "Notícias e fontes" }],
          },
          {
            type: "table",
            children: [
              {
                type: "tableRow",
                children: [
                  cell("Título"),
                  cell("URL"),
                  cell("article_verified"),
                ],
              },
              {
                type: "tableRow",
                children: [
                  cell("Notícia"),
                  cell("https://example.com/news"),
                  { type: "tableCell", children: [content] },
                ],
              },
            ],
          },
        ],
      };
      reportPresentation()(root);
      const verification = root.children![1].children![0].children![1];
      expect(verification.children![0].value).toBe(
        "Verificação da publicação: ",
      );
      expect(JSON.stringify(verification.children![1])).toBe(original);
    }
  }
});

test("presentation leaves code, destinations, dates and financial text intact", () => {
  const root = {
    type: "root",
    children: [
      {
        type: "paragraph",
        children: [{ type: "text", value: "R$ 2.352,00 mi; reported" }],
      },
      {
        type: "heading",
        depth: 3,
        children: [{ type: "text", value: "Notícias e fontes" }],
      },
      { type: "code", value: "article_verified = false" },
      {
        type: "paragraph",
        children: [
          {
            type: "text",
            value:
              "article_verified = false; date_label: 16/10/2026 12:07; reported",
          },
          {
            type: "link",
            url: "https://example.com/date_label?q=reported",
            children: [{ type: "text", value: "Título reported" }],
          },
        ],
      },
    ],
  };
  reportPresentation()(root);
  expect(root.children[0].children![0].value).toBe("R$ 2.352,00 mi; reported");
  expect(root.children[2].value).toBe("article_verified = false");
  const body = root.children[3].children!;
  expect(body[0].value).toBe(
    "article_verified = false; date_label: 16/10/2026 12:07; reported",
  );
  expect(body[1]).toEqual({
    type: "link",
    url: "https://example.com/date_label?q=reported",
    children: [{ type: "text", value: "Título reported" }],
  });
});

test("news tables become readable lists while preserving source, date and links", async ({
  page,
}, info) => {
  const url = `https://example.com/${"noticia-extensa-".repeat(45)}?origem=busca`;
  const result = {
    ...fixture,
    interpretation: [
      "### Leitura dos resultados",
      "R$ 2.352,00 mi / R$ 33.509,00 mi × 100 = 7,02%.",
      "### Notícias e fontes",
      "| Título | URL | Fonte | date_label | article_verified | Observação |",
      "| --- | --- | --- | --- | --- | --- |",
      `| Vale conclui venda | [${url}](${url}) | Veículo de teste | 16/10/2026 12:07 (Brasília; data informada pela busca, não verificada) | false | Resumo parcial |`,
      "",
      "article_verified = false. Data: reported.",
      "",
      "[https://example.org/outra](https://example.org/outra)",
      "### Limitações da análise",
      "Comparabilidade não confirmada. Aviso final preservado.",
    ].join("\n"),
  };
  await page.route("**/api/analyses**", async (route) =>
    route.fulfill({
      status: route.request().method() === "POST" ? 202 : 200,
      json: result,
    }),
  );
  await page.goto("/");
  await page.getByLabel("Qual ação vamos analisar?").fill("VALE3");
  await page.getByRole("button", { name: "Analisar ação" }).click();
  const report = page.locator(".markdown");
  const title = report.getByRole("link", { name: /Vale conclui venda/ });
  await expect(title).toHaveAttribute("href", url);
  await expect(title).toHaveAttribute("target", "_blank");
  await expect(report.locator("table")).toHaveCount(0);
  await expect(report).toContainText("Veículo: Veículo de teste");
  await expect(report).toContainText("16/10/2026 12:07");
  await expect(report).toContainText("Resumo parcial");
  await expect(report).toContainText("Não verificada na publicação original.");
  await expect(report.locator("li")).not.toContainText("article_verified");
  await expect(report.locator("li")).not.toContainText("date_label");
  await expect(report).toContainText(
    "article_verified = false. Data: reported.",
  );
  await expect(report).toContainText("7,02%");
  await expect(report).toContainText("Aviso final preservado.");
  await expect(
    report.getByRole("link", { name: /Ler notícia em example.org/ }),
  ).toHaveAttribute("href", "https://example.org/outra");
  await title.focus();
  await expect(title).toBeFocused();
  for (const width of [320, 390, 768, 1440, 1920]) {
    await page.setViewportSize({ width, height: 1000 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    expect(
      await report.evaluate((el) => el.scrollWidth <= el.clientWidth),
    ).toBe(true);
    if (width === 390 || width === 1440) {
      await report.screenshot({ path: info.outputPath(`news-${width}.png`) });
    }
  }
});

test("unrecognized tables are not discarded", () => {
  const cell = (value: string) => ({
    type: "tableCell",
    children: [{ type: "text", value }],
  });
  const table = {
    type: "table",
    children: [
      { type: "tableRow", children: [cell("Indicador"), cell("2025")] },
      { type: "tableRow", children: [cell("Receita"), cell("R$ 1.234,00 mi")] },
    ],
  };
  const root = {
    type: "root",
    children: [
      {
        type: "heading",
        depth: 3,
        children: [{ type: "text", value: "Notícias e fontes" }],
      },
      table,
    ],
  };
  const original = JSON.stringify(table);
  reportPresentation()(root);
  expect(JSON.stringify(root.children[1])).toBe(original);
});

test("news tables preserve extra URL-cell text and unknown columns", () => {
  const cell = (value: string) => ({
    type: "tableCell",
    children: [{ type: "text", value }],
  });
  const root = {
    type: "root",
    children: [
      {
        type: "heading",
        depth: 3,
        children: [{ type: "text", value: "Notícias e fontes" }],
      },
      {
        type: "table",
        children: [
          {
            type: "tableRow",
            children: [cell("Título"), cell("URL"), cell("Detalhe")],
          },
          {
            type: "tableRow",
            children: [
              cell("Título preservado"),
              cell("https://example.com/ ressalva importante"),
              cell("2025; 12,34%"),
            ],
          },
        ],
      },
    ],
  };
  reportPresentation()(root);
  const rendered = JSON.stringify(root);
  expect(rendered).toContain("ressalva importante");
  expect(rendered).toContain("2025; 12,34%");
  expect(rendered).toContain("Título preservado");
  expect(rendered).not.toContain('"url":');
});
