/** Presentation-only Markdown transforms. Never rewrite numbers, dates or URLs. */
type Node = {
  type: string;
  value?: string;
  url?: string;
  children?: Node[];
  depth?: number;
  ordered?: boolean;
  spread?: boolean;
};

const text = (value: string): Node => ({ type: "text", value });
const paragraph = (children: Node[]): Node => ({ type: "paragraph", children });
const plain = (node: Node): string =>
  node.value ?? node.children?.map(plain).join("") ?? "";

const labels: Record<string, string> = {
  title: "Título",
  título: "Título",
  titulo: "Título",
  url: "Link",
  link: "Link",
  source: "Veículo",
  fonte: "Veículo",
  veículo: "Veículo",
  date_label: "Data informada pela busca",
  data: "Data informada pela busca",
  article_verified: "Verificação da publicação",
};

function httpUrl(value: string): boolean {
  if (!value || /\s/.test(value)) return false;
  try {
    const url = new URL(value);
    return (
      ["http:", "https:"].includes(url.protocol) &&
      !url.username &&
      !url.password
    );
  } catch {
    return false;
  }
}

function newsList(table: Node): Node {
  const rows = table.children ?? [];
  const headers =
    rows[0]?.children?.map((cell) => plain(cell).trim().toLowerCase()) ?? [];
  const titleIndex = headers.findIndex((name) =>
    ["title", "título", "titulo"].includes(name),
  );
  const urlIndex = headers.findIndex((name) => ["url", "link"].includes(name));
  // Unknown layouts stay intact rather than losing or mislabelling cells.
  if (
    titleIndex < 0 ||
    urlIndex < 0 ||
    rows.length < 2 ||
    rows.slice(1).some((row) => row.children?.length !== headers.length)
  )
    return table;
  return {
    type: "list",
    ordered: false,
    spread: true,
    children: rows.slice(1).map((row) => {
      const cells = row.children!;
      const urlCell = cells[urlIndex];
      const link =
        urlCell.children?.length === 1 && urlCell.children[0].type === "link"
          ? urlCell.children[0]
          : undefined;
      const url = link?.url ?? plain(urlCell).trim();
      const title = cells[titleIndex].children ?? [];
      // Link titles only when this cannot drop extra content or create nested links.
      const canLink =
        httpUrl(url) &&
        (link
          ? plain(link).trim() === url ||
            plain(link) === plain(cells[titleIndex])
          : urlCell.children?.every((n) => n.type === "text")) &&
        plain(cells[titleIndex]).trim().length > 0 &&
        title.every((n) => n.type === "text");
      const children = [
        paragraph(canLink ? [{ type: "link", url, children: title }] : title),
      ];
      cells.forEach((cell, index) => {
        if (index === titleIndex || (index === urlIndex && canLink)) return;
        let content = cell.children ?? [];
        if (
          headers[index] === "article_verified" &&
          content.length === 1 &&
          content[0].type === "text"
        ) {
          const value = plain(cell).trim().toLowerCase();
          if (value === "false")
            content = [text("Não verificada na publicação original.")];
          if (value === "true")
            content = [
              text(
                "Informada como verificada no relatório; não conferida por esta interface.",
              ),
            ];
        }
        children.push(
          paragraph([
            text(
              `${labels[headers[index]] ?? plain(rows[0].children![index])}: `,
            ),
            ...content,
          ]),
        );
      });
      return { type: "listItem", spread: true, children };
    }),
  };
}

export function reportPresentation() {
  return (root: Node) => {
    let news = false;
    function visit(node: Node, inNews: boolean) {
      if (["code", "inlineCode", "html"].includes(node.type)) return;
      if (node.type === "link") {
        const label = plain(node).trim();
        if (inNews && node.url && httpUrl(node.url) && label === node.url) {
          node.children = [
            text(`Ler notícia em ${new URL(node.url).hostname}`),
          ];
        }
        return; // Preserve descriptive link titles and the exact destination.
      }
      // Free prose may be a title, quotation or source name. Translate only
      // explicit table fields in newsList, never arbitrary words in prose.
      node.children?.forEach((child) => visit(child, inNews));
    }
    root.children = root.children?.map((node) => {
      if (node.type === "heading") {
        const heading = plain(node).trim();
        if (/^Not[ií]cias e fontes$/i.test(heading)) news = true;
        else if ((node.depth ?? 6) <= 3) news = false;
      }
      const output = news && node.type === "table" ? newsList(node) : node;
      visit(output, news);
      return output;
    });
  };
}
