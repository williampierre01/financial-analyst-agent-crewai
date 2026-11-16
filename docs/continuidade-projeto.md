# Continuidade do projeto — 16/11/2026

## Primeiro passo no próximo chat

Ler este arquivo, `estado-atual.md`, `plano-geral-desenvolvimento.md` e
`pendencias-homologacao.md`. Conferir Git e GitHub antes de modificar arquivos.
PR #27 teve merge confirmado em 16/11/2026 às 04:30 (Brasília), commit `ef5bef7`.
Verificar evidência de publicação Live no Render; ela ainda não foi confirmada. O usuário faz
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
