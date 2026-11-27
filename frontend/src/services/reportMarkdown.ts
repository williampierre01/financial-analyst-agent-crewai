/** Repair only the report envelope and known section titles; never rewrite values. */
export function reportMarkdown(source: string): string {
  let text = source;
  const envelope = source
    .trim()
    .match(/^```(?:markdown|md)\s*\n([\s\S]*?)\n```$/i);
  if (envelope) text = envelope[1];
  let fence: string | undefined;
  return text
    .split(/\r?\n/)
    .map((line) => {
      const marker = line.match(/^\s{0,3}(`{3,}|~{3,})/);
      if (marker) {
        if (!fence) fence = marker[1];
        else if (marker[1][0] === fence[0] && marker[1].length >= fence.length)
          fence = undefined;
        return line;
      }
      if (fence || /^( {4}|\t)/.test(line)) return line;
      const heading = line
        .trim()
        .match(
          /^(?:\*\*)?(?:\\?#{1,6}|(?:\\#){1,6})\s*(Leitura dos resultados|Not[ií]cias e fontes|Limita[cç][oõ]es da an[aá]lise)(?:\*\*)?\s*$/i,
        );
      return heading ? `### ${heading[1]}` : line;
    })
    .join("\n");
}

/** Structural check only: headings outside code, not financial or source validation. */
export function missingReportSections(source: string): string[] {
  const expected = [
    "Leitura dos resultados",
    "Notícias e fontes",
    "Limitações da análise",
  ];
  const found = new Set<string>();
  let fence: string | undefined;
  for (const line of reportMarkdown(source).split(/\r?\n/)) {
    const marker = line.match(/^\s{0,3}(`{3,}|~{3,})/);
    if (marker) {
      if (!fence) fence = marker[1];
      else if (marker[1][0] === fence[0] && marker[1].length >= fence.length)
        fence = undefined;
      continue;
    }
    if (fence) continue;
    const heading = line.match(/^### (.+)$/);
    if (heading) found.add(heading[1].trim().toLocaleLowerCase("pt-BR"));
  }
  return expected.filter((name) => !found.has(name.toLocaleLowerCase("pt-BR")));
}
