# Plano geral de desenvolvimento do sistema

**Status:** Aprovado como referência.
**Data de aprovação e registro:** 18/10/2026 (Brasília).
**Atualização em 19/10/2026:** escopo técnico do login multiusuário aprovado com Firebase e Neon Free; implementação em andamento, ainda sem homologação. Demais etapas continuam dependendo de aprovação específica.

**Ampliação aprovada em 20/10/2026:** incluir “Entrar com Google” como alternativa a e-mail/senha nesta entrega. Preservar autorização por UID, acesso por convite, isolamento entre usuários e MFA TOTP para administradores. Tratar conflitos entre métodos sem duplicar identidades ou conceder permissões por coincidência de e-mail. Validar integração real no Render; detalhes e critérios em `login-firebase-neon.md`.

A aprovação deste plano não autoriza automaticamente a implementação de todas
as etapas. Cada etapa exige apresentação do escopo e aprovação prévia do usuário.
Este documento preserva o plano consolidado aprovado na conversa; alterações
futuras também dependem de avaliação do usuário e devem ficar no histórico do Git.

Problemas observados e resultados das validações permanecem no registro separado
de [pendências de homologação](pendencias-homologacao.md).

**Ampliação aprovada em 28/10/2026:** provedores de IA configuráveis e medição
por análise, seguidos de integração Gemini em entrega separada. Manter dados,
cálculos e validações independentes da IA; testes no CI e homologação apenas
PETR4/VALE3, com merge/deploy manual pelo usuário. Não autoriza compra de créditos
ou ativação de cobrança. Acompanhar execução no [estado atual](estado-atual.md).

## 1. Direção geral

Desenvolver um sistema de análise de ações que entregue **Business Intelligence de alto valor para apoiar decisões**, transformando dados financeiros e informações de mercado em conclusões relevantes, claras, comparáveis e auditáveis.

O sistema deverá:

- Priorizar insights acionáveis, destacando o que mudou e por que isso importa.
- Explicar as evidências, os fatores determinantes, os riscos e o contexto por trás das conclusões.
- Distinguir fatos, cálculos reproduzíveis e hipóteses não confirmadas.
- Destacar informações relevantes para a decisão e reduzir repetição e ruído.
- Manter dados, fórmulas, fontes e limitações acessíveis para auditoria.
- Declarar quando uma causa não puder ser estabelecida, sem preencher lacunas com explicações inventadas.

### Posição analítica

Para ações com base suficiente, apresentar **COMPRA, VENDA ou MANTER**, segundo metodologia explícita, testada e versionada.

| Posição | Estrutura dos critérios |
|---|---|
| **COMPRA** | Qualidade dos dados aprovada; fundamentos e avaliação atendem aos critérios definidos; retorno potencial estimado supera o mínimo exigido pela metodologia, considerando riscos e horizonte; ausência de condição de invalidação da tese. |
| **VENDA** | Evidências de invalidação da tese, deterioração além dos limites definidos ou avaliação desfavorável segundo o modelo adotado. |
| **MANTER** | Tese permanece válida, mas os critérios de COMPRA ou VENDA não são atingidos; fundamentos, avaliação e riscos permanecem na faixa de manutenção definida. |

Indicadores, pesos, limites numéricos, modelos de avaliação e horizontes **ainda serão definidos e validados**. Esses critérios representam uma estrutura de desenvolvimento, não uma metodologia pronta para uso.

Quando faltarem evidências essenciais, emitir **“posição não emitida — base insuficiente”**, com justificativa. MANTER não será usado como substituto para falta de dados.

Cada posição deverá incluir:

- Justificativa resumida e evidências determinantes.
- Confiança alta, média ou baixa, com critérios explícitos.
- Principais riscos e fatores observáveis que invalidariam a tese.
- Horizonte curto, médio ou longo, acompanhado do intervalo concreto considerado.
- Fontes, datas, premissas e versão da metodologia.
- Aviso de que a análise apoia decisões e não constitui recomendação financeira personalizada.

A confiança refletirá a qualidade e suficiência das evidências e a sensibilidade às premissas. Não será apresentada como probabilidade de acerto sem calibração.

O sistema não presumirá que o usuário possui o ativo nem determinará automaticamente quantidades, alocação ou execução de operações.

## 2. Contexto de evolução

O projeto está em fase de aprendizado sobre o mercado financeiro e sobre as necessidades dos usuários.

A solução deverá ser modular, separando coleta, validação, cálculos, metodologia de posição, interpretação, apresentação e armazenamento.

### Decisões ainda abertas

- Público-alvo e decisões que pretende apoiar.
- Público e regras de admissão ao acesso por múltiplos usuários, já definido como próxima entrega.
- Indicadores e comparações prioritários.
- Modelos de avaliação e critérios das posições.
- Horizontes de análise.
- Formato, profundidade e frequência dos relatórios.
- Necessidade de histórico, acompanhamento e notificações.
- Critérios de confiança e sua calibração.

Suposições sobre mercado ou comportamento dos usuários serão identificadas como **hipóteses a validar**.

A pesquisa com usuários avaliará utilidade e compreensão. A metodologia financeira exigirá revisão especializada e testes próprios.

## 3. Frontend — experiência e apresentação

**Objetivo:** ajudar o usuário a compreender a conclusão, suas razões e seus limites, permitindo aprofundamento sem sobrecarregar a leitura inicial.

### Entregas previstas

0. **Login para múltiplos usuários — próxima entrega prioritária**
   - Tela de login acessível, com identificação do usuário e opção de sair.
   - Estados claros de autenticação, sessão expirada e acesso negado.
   - Mensagens de falha que não revelem se uma conta existe.
   - Cadastro e recuperação de acesso conforme o modelo a definir na seção 6.1.

1. **Síntese da análise**
   - Poucos achados relevantes.
   - Destaque para mudanças, riscos e implicações.
   - Redução da repetição dos demonstrativos.

2. **Detalhes auditáveis**
   - Área expansível para cálculos, operandos e referências.
   - Distinção visual entre fatos, cálculos e hipóteses.
   - Limitações específicas próximas dos resultados afetados.

3. **Apresentação padronizada**
   - Moedas, escalas, percentuais e datas consistentes.
   - Precisão de exibição adequada, preservando precisão interna.
   - Português claro, sem campos técnicos desnecessários.

4. **Notícias e contexto**
   - Títulos clicáveis, veículo, data e ressalvas legíveis.
   - Separação entre contexto relevante e resultados pouco relacionados à ação.
   - Identificação do que foi ou não verificado na fonte original.

5. **Posição analítica**
   - Exibição da posição, confiança, horizonte e justificativa.
   - Riscos e fatores de invalidação acessíveis.
   - Estado explícito de base insuficiente.
   - Dependência da aprovação da metodologia no backend.

6. **Fluxo de uso**
   - Progresso coerente com a etapa real.
   - Mensagens claras para falhas, indisponibilidade e expiração.
   - Responsividade e acessibilidade.

7. **Histórico e comparação**
   - Consulta de análises anteriores.
   - Comparação entre resultados com datas, bases e versões identificadas.
   - Dependência da API e da persistência.

### Critério de conclusão

O usuário consegue identificar a conclusão principal, entender sua justificativa e localizar evidências e limitações. A apresentação preserva informações relevantes e funciona nos dispositivos previstos.

## 4. Backend — dados, análise e metodologia

**Objetivo:** produzir resultados reproduzíveis, rastreáveis e consistentes, com tratamento explícito de incerteza e falhas.

### Entregas previstas

0. **Autenticação e autorização — próxima entrega prioritária**
   - Autenticar contas individuais e controlar sessões, expiração e logout.
   - Verificar permissões no servidor em cada operação protegida.
   - Vincular consultas e resultados ao usuário e impedir acesso cruzado, inclusive por identificador direto da análise.
   - Proteger consultas de status, retomada de análises e futuras operações de histórico.
   - Planejar a transição da proteção HTTP Basic atual sem expor rotas ou resultados durante a mudança.

1. **Qualidade dos dados**
   - Validar identidade do ativo, moeda, unidade, período e atualidade.
   - Tratar ausências e incompatibilidades sem inferir valores.
   - Conferir amostras frente à fonte original.
   - Distinguir validação técnica de auditoria financeira.

2. **Cálculos determinísticos**
   - Consolidar indicadores calculados pelo código.
   - Documentar fórmulas, convenções e condições de disponibilidade.
   - Preservar operandos e referências.
   - Evitar que arredondamentos de apresentação alterem cálculos.

3. **Análise estruturada**
   - Separar síntese, evidências, cálculos, riscos, notícias e limitações.
   - Definir quais resultados pertencem ao código e quais à interpretação da IA.
   - Verificar estrutura e referências antes de entregar o relatório.
   - Não tratar instruções ao modelo como garantia de correção.

4. **Metodologia de posição**
   - Definir universo de ativos e horizontes atendidos.
   - Selecionar critérios de fundamentos, avaliação e riscos.
   - Definir regras de COMPRA, VENDA, MANTER e abstenção.
   - Estabelecer critérios de confiança e invalidação da tese.
   - Avaliar sensibilidade às premissas e limitações dos modelos.
   - Versionar regras e submeter a revisão especializada e validação antes da disponibilização.

5. **Notícias**
   - Preservar proveniência e datas recebidas.
   - Avaliar relevância, duplicidade e atualidade.
   - Diferenciar metadados da busca de conteúdo verificado na publicação.
   - Não atribuir causalidade sem suporte.

6. **Resiliência e operação**
   - Revisar limites de tempo, tentativas e fallback.
   - Definir comportamento para falhas parciais e reinícios.
   - Registrar duração, erros e provedor utilizado, sem expor credenciais.
   - Medir consumo e latência antes de otimizar.

7. **API**
   - Fornecer contratos claros para análise estruturada, posição e histórico.
   - Manter compatibilidade ou planejar migrações quando os contratos mudarem.
   - Definir controle de acesso conforme o público escolhido.

### Critério de conclusão

Resultados podem ser rastreados até seus dados e regras. Falhas e insuficiências são explícitas. Posições só são emitidas quando os requisitos da metodologia aprovada forem atendidos.

## 5. Banco de dados — persistência e rastreabilidade

**Objetivo:** permitir recuperação, comparação e auditoria das análises sem perder o contexto em que foram produzidas.

Atualmente, as análises ficam temporariamente na memória do servidor. A persistência será uma nova capacidade, cujo escopo deve ser definido antes da escolha da tecnologia. A próxima entrega antecipa o armazenamento necessário a contas e sessões; o histórico completo de análises continua previsto para uma fase posterior.

### Entregas previstas

0. **Contas e sessões — próxima entrega prioritária**
   - Identidade única, estado da conta e permissões mínimas necessárias.
   - Hash seguro de senha ou identificador de um provedor de identidade, conforme a arquitetura escolhida.
   - Estado necessário para expirar e revogar sessões e fluxos de recuperação, quando aplicáveis.
   - Migrações, restrições de unicidade e registro mínimo de eventos de segurança.
   - Separação lógica dos dados por usuário desde a primeira versão, mesmo enquanto as análises permanecerem em memória.

1. **Modelo de armazenamento**
   - Consultas e estado do processamento.
   - Dados financeiros efetivamente utilizados.
   - Notícias e metadados recebidos.
   - Indicadores, operandos e resultados.
   - Relatório, posição e justificativas, quando disponíveis.

2. **Versionamento**
   - Identificar versões das regras, cálculos e metodologia.
   - Registrar modelo/provedor e configuração relevante da geração.
   - Preservar análises anteriores sem reescrevê-las silenciosamente após mudanças.

3. **Histórico e recuperação**
   - Recuperar análises após reinícios.
   - Distinguir recuperação de resultado anterior de nova consulta.
   - Definir se trabalhos interrompidos serão retomados, repetidos ou encerrados.

4. **Retenção e acesso**
   - Definir prazos de armazenamento e exclusão.
   - Separar registros por usuário, se houver múltiplas contas.
   - Evitar armazenamento desnecessário de informações pessoais e credenciais.

5. **Operação**
   - Migrações, backups e procedimentos de restauração.
   - Monitoramento de crescimento e custo do armazenamento.

6. **Cache**
   - Avaliar reaproveitamento com validade explícita.
   - Considerar ativo, período, origem e versão da metodologia.
   - Nunca apresentar resultado antigo como consulta atual.

### Critério de conclusão

Uma análise pode ser recuperada com seus dados, fontes e versões originais. Retenção, acesso, exclusão e recuperação possuem regras definidas e verificáveis.

## 6. Fases de desenvolvimento

As três áreas organizam responsabilidades; a execução seguirá suas dependências.

| Fase | Entrega principal | Dependências e condição de avanço |
|---|---|---|
| **0. Login e acesso seguro — próximo passo** | Tela de login para diferentes usuários, autenticação real, sessões, armazenamento de contas e isolamento de consultas. | Aprovar modelo de cadastro, arquitetura de autenticação, permissões e transição do HTTP Basic; validar critérios da seção 6.1 antes da publicação. |
| **1. Consolidar o sistema atual** | Resolver pendências de legibilidade, validar uso e conferir dados e indicadores. | Registrar evidências, falhas e limites conhecidos. |
| **2. Descoberta e definição** | Pesquisar usuários e estudar a metodologia financeira. | Definir público, decisões apoiadas e hipóteses prioritárias. Pode ocorrer em paralelo à fase 1. |
| **3. Estruturar a análise e sua apresentação** | Separar síntese, evidências, cálculos, riscos e limitações no backend e frontend. | Aprovar o contrato de saída e os critérios de validação. |
| **4. Persistir e recuperar análises** | Implementar armazenamento, rastreabilidade e histórico. | Definir modelo de dados, retenção e acesso. O desenho começa junto da fase 3. |
| **5. Desenvolver e validar posições** | Implementar metodologia, confiança, riscos e invalidação da tese. | Critérios definidos, revisão especializada e testes adequados. Validar antes de disponibilizar posições ao usuário. |
| **6. Evoluir a operação** | Melhorar desempenho, consumo, confiabilidade e funcionalidades priorizadas pela pesquisa. | Usar medições e evidências de uso. Observabilidade básica começa nas fases anteriores. |

### 6.1. Próxima entrega: login e segurança para múltiplos usuários

Esta é a próxima etapa de implementação, antes das demais fases. O objetivo é
autenticação completa e controle de acesso, não apenas uma tela visual.

**Decisões a aprovar antes de implementar:**

- Contas criadas pelo administrador, por convite ou por cadastro aberto; definir identificação e confirmação de contato quando necessárias.
- Autenticação gerenciada por provedor de identidade ou contas mantidas pelo sistema; priorizar componentes consolidados em vez de criptografia própria.
- Papéis e permissões, necessidade de administração e de autenticação multifator, especialmente para contas privilegiadas.
- Fluxo de recuperação de acesso e criação segura da primeira conta administrativa, sem senha padrão no código.
- Duração das sessões, política de revogação, retenção de eventos e dados mínimos de cadastro.
- Escolha do armazenamento, configuração no Render e transição do HTTP Basic atual, incluindo tratamento de análises antigas sem proprietário identificado.

**Requisitos de segurança:**

- Tráfego autenticado por HTTPS; segredos em configuração protegida, nunca no repositório, frontend ou logs.
- Se houver senhas locais, armazenar somente hashes com algoritmo próprio para senhas, salt individual e parâmetros revisados na implementação. Nunca armazenar senhas em texto puro ou criptografia reversível.
- Permitir senhas longas e uso de gerenciadores; definir proteção contra senhas comuns ou comprometidas sem expor a senha a terceiros.
- Proteger sessões contra roubo e fixação: identificadores imprevisíveis, renovação no login, expiração e invalidação no logout. Para sessões em cookies, usar HttpOnly, Secure e SameSite adequado, com proteção contra CSRF nas operações aplicáveis. Não armazenar credenciais persistentes em localStorage.
- Aplicar autorização no backend e privilégio mínimo. Acesso à tela ou posse de um identificador de análise não concede acesso ao resultado de outro usuário.
- Limitar tentativas de login e recuperação, com respostas genéricas e proteção contra enumeração de contas. Definir limites sem permitir bloqueio abusivo de usuários legítimos.
- Caso exista recuperação de senha, usar tokens imprevisíveis, de uso único e validade curta; armazenar representação protegida e invalidar sessões conforme a política aprovada. Nunca enviar a senha atual por mensagem.
- Validar entradas no servidor, usar consultas parametrizadas e preservar proteções contra injeção e XSS; restringir CORS às origens necessárias.
- Evitar cache compartilhado de respostas privadas e remover estado de usuário no logout ou troca de conta, incluindo a retomada de consultas no navegador.
- Registrar eventos relevantes de autenticação e acesso negado sem senhas, tokens ou dados pessoais desnecessários. Definir retenção e acesso aos registros.
- Proteger backups e acessos ao banco; planejar restauração, atualizações de dependências e revisão das configurações de produção.

Esses requisitos orientam o desenho e não substituem uma revisão de segurança.
Parâmetros e tecnologias serão definidos no plano técnico, conforme riscos e
necessidades do projeto, sem pressupor conformidade regulatória automática.

**Critérios de aceitação:**

- Cada usuário consegue entrar e sair; sessão expirada ou revogada perde acesso no servidor.
- Requisições sem autenticação são rejeitadas nas rotas privadas.
- Usuário A não consegue consultar, acompanhar ou recuperar análises do usuário B, inclusive por URL/identificador direto ou troca de conta no mesmo navegador.
- Fluxos de cadastro e recuperação aprovados não revelam contas existentes nem reutilizam tokens expirados ou consumidos.
- Limites de tentativas, permissões e proteções de sessão são cobertos por testes automatizados no CI; a revisão visual será feita no Render.
- A migração não disponibiliza resultados antigos sem proprietário para contas novas, não expõe segredos e possui procedimento de retorno definido.

### 6.2. Decisões de infraestrutura e custos — atualização em 19/10/2026

Esta seção atualiza as decisões em aberto da seção 6.1; os detalhes técnicos ainda dependem de aprovação.

**Aprovado para o desenvolvimento:**

- Usar Firebase Authentication para autenticação e PostgreSQL para armazenamento dos dados da aplicação, conforme escolha explícita em 19/10/2026.
- Desenvolver com Firebase no plano gratuito Spark; a proposta técnica inclui Identity Platform para MFA por aplicativo autenticador. Conferir os requisitos vigentes durante a configuração, sem ativar cobrança automaticamente.
- Usar Neon Free para hospedar PostgreSQL, aprovado em 19/10/2026 junto com o escopo técnico de login, autorização, sessões e isolamento de análises. A implementação não autoriza plano pago nem configuração de serviços com credenciais não fornecidas.
- Vincular os dados da aplicação ao identificador estável do usuário no Firebase; não copiar senhas para PostgreSQL. Detalhar permissões, sessões e migrações no escopo técnico.
- Começar com acesso por convite, sem cadastro público.
- Manter o plano atual do Render, sem presumir qual é sua cobrança vigente.
- Usar serviços gratuitos dentro das respectivas franquias. Contratações, upgrades e recursos pagos exigem aprovação prévia.
- O usuário informou não possuir domínio para envio de e-mails.
- O escopo da primeira implementação foi aprovado: tela de login, recuperação, verificação de e-mail, MFA administrativo, contas autorizadas pelo administrador, PostgreSQL para permissões/sessões/eventos, autorização por proprietário e validações em CI/Render. Histórico persistente de análises permanece fora desta entrega.

**E-mails e proposta para a primeira validação:**

- Usar os fluxos de verificação de endereço e recuperação de senha do Firebase, dentro das franquias gratuitas, sem exigir compra de domínio nesta etapa.
- O envio desses e-mails não equivale a um serviço geral de convites personalizados. Proposta inicial: admissão controlada pelo administrador e comunicação manual dos convites; detalhar e aprovar esse fluxo antes da implementação.
- Validar acesso, recuperação e isolamento com contas distintas, sem conceder acesso administrativo ao projeto Firebase para testadores.
- Impedir acesso de pessoas não autorizadas no servidor; apenas esconder a tela de cadastro não implementa acesso por convite.
- Não desativar confirmação de contato nem expor links ou tokens em logs para contornar a ausência de serviço de e-mail.
- Não considerar a etapa multiusuário concluída antes de verificar o isolamento entre contas e os fluxos de acesso aprovados.

**Custos e limites a acompanhar:**

- Conferir limites do Firebase e do futuro provedor PostgreSQL, incluindo armazenamento, conexões, suspensão por inatividade, retenção e backups. Definir recuperação adequada antes de armazenar dados cuja perda seja inaceitável.
- Hospedagem, consumo de IA e eventual registro de domínio são custos separados. Não prometer custo total zero para o aplicativo.
- Conferir preços e limites novamente antes de qualquer contratação; medir consumo antes de ampliar capacidade.

**Histórico da decisão:** Supabase havia sido escolhido em 18/10/2026. Após comparar alternativas e considerar a ausência de domínio para e-mails, o usuário substituiu essa escolha por Firebase e PostgreSQL em 19/10/2026. Nenhuma migração de implementação foi realizada nesta decisão de planejamento.

**Implementação iniciada em 19/10/2026:** após aprovação de Neon Free e do escopo, código e instruções estão sendo preparados. Nenhum serviço externo foi provisionado, nenhum teste local foi executado e nenhuma homologação foi concluída. Consultar [o guia de configuração e publicação do login](login-firebase-neon.md) antes de publicar.

Fontes oficiais consultadas na comparação de 18/10/2026; reconferir durante a configuração:

- [Firebase Authentication e Identity Platform](https://firebase.google.com/docs/auth).
- [Firebase: limites de autenticação e e-mails](https://firebase.google.com/docs/auth/limits).
- [Firebase: MFA por aplicativo autenticador](https://firebase.google.com/docs/auth/web/totp-mfa).
- [Firebase: cookies de sessão](https://firebase.google.com/docs/auth/admin/manage-cookies).

## 7. Regras de execução

- Apresentar o plano de cada etapa e aguardar aprovação antes de agir.
- Separar funcionalidades implementadas, propostas e hipóteses a validar.
- Apresentar correções encontradas na revisão antes de editar.
- Manter commit, PR, merge e publicação sob o processo manual escolhido pelo usuário.
- Conforme autorização de 16/11/2026, executar também testes locais e builds com serviços simulados, além do CI. A autorização não altera o merge/deploy manual nem autoriza cobrança de provedores.
- Fazer avaliação visual no Render após publicação.
- Não considerar uma entrega validada apenas porque compilou ou porque a IA seguiu uma instrução em uma consulta.
- Revisar prioridades conforme a pesquisa e os resultados, preservando o histórico das decisões.

## 8. Próximas definições do planejamento

Antes de detalhar prazos ou escolher tecnologias:

0. Aprovar as decisões da seção 6.1 e o escopo técnico do login seguro para múltiplos usuários, próximo passo prioritário.

1. Definir o público e o propósito da próxima versão.
2. Priorizar as entregas da fase 1.
3. Definir como pesquisar as necessidades dos usuários.
4. Estabelecer o escopo inicial da metodologia financeira.
5. Definir o nível de histórico e rastreabilidade necessário.
