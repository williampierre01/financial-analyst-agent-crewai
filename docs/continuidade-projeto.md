## Situação vigente — 27/11/2026

Este resumo substitui os próximos passos e estados pendentes das entradas
históricas abaixo; essas entradas permanecem como trilha de evolução.

- PRs #33, #34 e #35 incorporados. Último merge: `96b55fe`; CI do PR #35
  aprovado e Live confirmado por captura do usuário.
- Quatro valores operacionais reportados aprovados e exibidos: PETR4 2025/2024
  USD 26.113/26.876 milhões; VALE3 2025/2024 USD 5.897/10.788 milhões.
  Revisão de alcance limitado, sem auditoria; campo normalizado continua bloqueado.
- PETR4 consultada em 27/11 às 02:53 Brasília: tabela e interpretação coerentes
  no recorte observado, sem inventar falta de conciliação; ressalva causal correta.
- Por decisão do usuário para economizar tokens, VALE3 não foi retestada no
  commit 96b55fe. Sua validação anterior no ed38373 é preservada, não extrapolada.
- Correção operacional encerrada neste recorte. Não há garantia determinística
  sobre futuras respostas da IA, nem validação integral de notícias/indicadores.
- Última suíte local: 165 testes, 162 aprovados, 3 de banco ignorados. Sem Docker
  local, banco de produção para testes ou novas chamadas de IA pelo assistente.
- Não editar o pacote documental, seu alcance ou evidências vinculadas por hash.

## Etapa atual: síntese e evidências

Implementação autorizada pelo usuário e preparada para revisão em PR:

- Até três indicadores calculados do exercício mais recente, em ordem fixa:
  ROE sobre patrimônio de encerramento, lucro informado/receita e dívida/patrimônio.
  Ausências não geram destaques artificiais.
- Detalhes expansíveis com fórmula, operandos, exercício, moeda, fonte e limites.
  A API expõe os cálculos existentes; não altera fórmulas nem chama IA novamente.
- Dados e cálculos continuam disponíveis quando a interpretação falha.
- Aviso quando faltam as seções esperadas do relatório, preservando o texto recebido.
  A verificação é estrutural: não certifica fontes, semântica ou correção financeira.
- Esta entrega apresenta indicadores, não uma síntese automática de hipóteses.
  Redução adicional de repetição e refinamento editorial permanecem para outro recorte.

Verificação local: backend 162 aprovados e 3 de PostgreSQL ignorados; interface
66 cenários aprovados na rodada e 2 repetidos com sucesso após conflito de
arquivos temporários entre execuções; integração 3 cenários aprovados; build e
contrato gerado conferidos. Acessibilidade automática do painel aprovada em desktop
e celular. No Windows, os servidores de teste ficaram aguardando encerramento e
foram interrompidos após os resultados; isso não equivale a saída limpa do runner.
A confirmação limpa da suíte fica a cargo do CI. Nenhuma chamada real de IA.

Economia acordada: usar dados simulados nos testes; não repetir consultas reais por
mudanças de apresentação. Uma consulta PETR4 só quando necessária para homologação.

Fora deste recorte: histórico persistente, novas fontes/ativos, conversão cambial,
compra/venda/manter, cobrança e integração de outro provedor. Histórico é a etapa
seguinte do plano: permitirá reabrir resultados sem nova chamada de IA.
Pendências de autenticação (bloqueio, expiração, acesso inverso e cookie revogado)
continuam separadas; o teste anterior de duas contas não é auditoria completa.

## Registro histórico

> Atualização 26/11/2026 — aprovação recebida: William, responsável neste chat, declarou “revisão final aprovada”. Registro separado em `evidencias/operating-review-approval-2026-11-26.json`, vinculado ao pacote exato e seu alcance. Integração local do contrato 3.1 implementada: campo `reported_operating_income`, referência oficial, correspondência exata e revogação por alteração de evidência/aprovação. Campo normalizado legado permanece nulo. Backend: 163 testes executados, 160 aprovados e 3 ignorados. Interface: testes desktop/mobile passaram; build aprovado. Ainda não publicado nem mesclado. Não editar o documento de revisão aprovado: seu hash faz parte do registro.

> Atualização 26/11/2026: preparação do recorte documental concluída, sujeita à aceitação das limitações pelo revisor. O usuário se ofereceu como responsável; ainda não aprovou valores. Pacote `evidencias/operating-review-package-2026-11-26.json` e documento `revisao-final-operacional-2026-11-26.md` prontos. Os quatro resultados continuam `unverified / missing_matching_review`, sem elegibilidade. 23 testes locais passaram. Próxima ação: revisão identificada do pacote; integração runtime depende dela.

> Atualização 25/11/2026: D3 encerrado como seleção técnica dos 20-F; página 4 da Vale 2T26 recuperada. Pacote provisório com quatro digests preparado, sem aprovação e sem liberação. 21 testes operacionais passaram. C1–C3 ainda exigem conclusão; ver `decisao-fontes-operacionais-2026-11-25.md` e matriz. Integração runtime não implementada nesta atualização.

# Continuidade do projeto — 17/11/2026

> Atualização mais recente — 25/11/2026: pendências consolidadas em
> [matriz-pendencias-operacionais.md](matriz-pendencias-operacionais.md).
> D1 e D2 concluídos nos recortes registrados. Retomar por D3: escolha da fonte Vale. A matriz separa
> verificações concluídas, lacunas de cobertura e requisitos para aprovação.
> Quatro candidatos permanecem sem revisão aprovada e bloqueados.


## Primeiro passo no próximo chat

Última etapa publicada: PR #31, merge `b5a1239`, checks aprovados e Live confirmado
por captura do usuário. Coletor diagnóstico continua separado do aplicativo/MCP/IA;
140 testes locais aprovados, 3 PostgreSQL ignorados conforme decisão sem Docker.
Critérios registrados em `criterios-resultado-operacional.md`: próximo recorte é
um validador offline por observação, com evidência oficial e motivos de bloqueio.
Validador offline implementado localmente: 151 testes aprovados, 3 PostgreSQL ignorados. Implementação revisada e quatro evidências oficiais estruturadas, com hashes e referências. Próximo passo: revisão de versões/reapresentações e revisão documental identificada; nenhuma evidência real foi aprovada. Não liberar campos nem iniciar Docker.
Merge e deploy permanecem manuais.

Atualização: PR #28 incorporado (`a3f8137`), publicação informada pelo usuário.
Homologados acesso do proprietário, bloqueio por ID para outra conta, acesso
negado após logout e manutenção da sessão da outra conta. Ver limites dessas
evidências no estado atual. Correção 503 já publicada pelo PR #29:
uma repetição extra por análise, validada sem testes reais de IA.

Ler este arquivo, `estado-atual.md`, `plano-geral-desenvolvimento.md` e
`pendencias-homologacao.md`. Conferir Git e GitHub antes de modificar arquivos.
PR #27 teve merge confirmado em 16/11/2026 às 04:30 (Brasília), commit `ef5bef7`.
O deploy posterior do PR #29 está confirmado Live. O usuário faz
merge e deploy/configuração manualmente. Não repetir análises só para obter
evidência já disponível.

## Entrega preparada

PR: https://github.com/williampierre01/financial-analyst-agent-crewai/pull/27

- Orientações Quant/CIO preservam o motivo de indisponibilidade: resultado
  operacional bloqueado por falta de conciliação não significa ausente na fonte.
  Valor continua bloqueado; não há novo verificador semântico.
- CI fixado em Ubuntu 24.04 porque Python 3.13.9 não foi encontrado no Ubuntu
  26.04. CI do head final `58a1a0c` aprovado, execução `43822724129`.
- Estado atual registra sucesso real do Gemini em PETR4 e VALE3 em 15/11.
- Testes locais sobre `58a1a0c`: 130 backend, 58 interface e 3 integração aprovados; detalhes e instabilidades da execução no estado atual. Os 3 testes PostgreSQL permanecem pendentes localmente, cobertos pelo CI. O usuário decidiu continuar sem iniciar Docker; não usar Neon de produção para esses testes.

## Serviços e evidências

- App: https://financial-analyst-agent-crewai.onrender.com
- Repositório: https://github.com/williampierre01/financial-analyst-agent-crewai
- IA observada em produção: Gemini `gemini-3.1-flash-lite`; configuração de
  validação sem fallback. DeepSeek/Groq integrados, mas não usados nas duas
  execuções concluídas. NVIDIA ainda não integrada/testada.
- Firebase: identidade e MFA; Neon: permissões e sessões; Render: hospedagem;
  Yahoo Finance: dados financeiros. Histórico persistente de análises pendente.
- PETR4: 4 chamadas/4 sucessos; entrada 13.856, saída 3.623 tokens; 82,709 s.
- VALE3: 4 chamadas/4 sucessos; entrada 13.911, saída 3.561 tokens; 52,882 s.
- Os logs medem uso reportado, não cobrança ou garantia de gratuidade. Capturas
  validam funcionamento e coerência observada, não auditoria integral financeira.

## Sequência alinhada com o usuário

1. Validar multiusuário com duas contas: isolamento inclusive por ID direto,
   acesso negado e revogação de sessão. Antes de convidar outros usuários.
2. Consolidar qualidade dos dados de PETR4/VALE3: reconciliar resultado
   operacional e esclarecer definições dos indicadores. Não liberar números
   ou combinar BRL/USD sem validação.
3. Estruturar análise e síntese: poucos achados, mudanças e riscos, detalhes
   auditáveis acessíveis e verificação de estrutura/referências.
4. Persistir histórico: dados utilizados, notícias, cálculos, relatório, modelo
   e versões; recuperação após reinícios e leitura sem nova chamada de IA.
5. Definir e validar metodologia de compra/venda/manter/abstenção. Ainda não
   implementada nem aprovada como metodologia pronta; exige escopo próprio.

Apresentar o escopo de cada etapa antes de implementar. O alinhamento da ordem
não autoriza executar todas de uma vez. Próxima proposta: roteiro enxuto para
validação entre duas contas, minimizando novas chamadas de IA.

## Regras de trabalho

- Em 16/11/2026, o usuário autorizou testes locais. Executar testes automatizados e builds com serviços simulados, mantendo o CI como validação adicional. Testes reais de provedores ou produção continuam separados; merge/deploy permanecem manuais.
- Homologação real restrita a Petrobras e Vale para economizar tokens.
- Acumular ajustes de baixo impacto: repetição de ressalvas, moedas, percentuais
  e espaçamento. Não confundir erro de conteúdo/dados/autorização com cosmética.
- Não contratar serviços, comprar créditos ou ativar cobrança sem autorização.
- Não registrar senhas, chaves, cookies ou segredos MFA em documentos/logs/chat.
- Não abrir novo chat automaticamente: este documento prepara a retomada.

## Revisão documental — 17/11/2026

PR #32 incorporado em `c6dc4eb`, checks aprovados e Live confirmado por captura.
Levantamento SEC e comparação Vale 2024 registrados em
[revisão de versões](revisao-versoes-operacionais.md). Checagem de reapresentações
ainda parcial; quatro candidatos não aprovados. Nenhuma alteração em produção.

### Retomada em 24/11/2026

Concluída a coleta das 114 imagens dos três releases Vale 4T25 e a conferência
das páginas diferentes. A segunda emenda apresenta divergências entre texto e
imagem nas páginas 2 e 25; a correção segmentada de 195 para 287 milhões foi
confirmada visualmente. Detalhes e limites em `revisao-versoes-operacionais.md`.
Não repetir a coleta completa: hashes e comparação estão em
`evidencias/vale-release-image-hashes.json`, agora com estado `complete`.
Referências anuais selecionadas: 20-F SEC Petrobras (F-4) e Vale (F-3), ambos de
2025 com comparativo 2024. Os quatro valores foram corroborados; arquivos e hashes
registrados em `evidencias/annual-source-verification-2026-11-24.json`.
Inventário SEC atualizado em `evidencias/sec-submissions-check-2026-11-24.json`.
Triagem textual posterior concluída: 193/193 documentos primários coletados;
14 com ocorrências de correção tiveram os trechos examinados. Manifesto em
`evidencias/subsequent-filings-triage-2026-11-24.json`. Não repetir a coleta.
Próximo passo: identificar os 12 documentos predominantemente visuais, conferir
remissões de sustentabilidade e conciliar apresentações de streaming relevantes.
Lista e limites na última seção da revisão. Os quatro candidatos seguem sem aprovação.

### Avanço documental em 24/11/2026

Identificadas e conferidas as 12 capas pendentes. Conciliação de streaming da
Vale verificada em quatro períodos trimestrais/acumulados, com resíduo zero.
Remissões GRI examinadas: a página 5 da Petrobras não detalha reapresentações;
conferência de indicadores/ESG Datasheet permanece pendente. Ver o último bloco
de `revisao-versoes-operacionais.md` para alcance e evidências. Próximo passo:
revisar as páginas financeiras das apresentações Vale 1T26, 2T26 e 3T26.
Resultado operacional continua sem liberação; candidatos e código inalterados.
