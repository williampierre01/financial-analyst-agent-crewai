# Login multiusuário — Firebase + Neon Free

Status: implementação preparada para CI e homologação; configuração externa realizada manualmente pelo usuário, ainda sem validação integrada no Render.
A aprovação do escopo ocorreu em 19/10/2026. Não executar testes nem iniciar o aplicativo localmente; validar automaticamente no CI e visualmente no Render.

Em 20/10/2026, o usuário confirmou Neon com esquema aplicado, conexão com pooling usando `analista_runtime`, Firebase com Google/e-mail e TOTP habilitados, credencial da conta `analista-render` e variáveis salvas no Render. A captura do Neon confirmou uma conta administrativa ativa em `app_users`. Essas evidências não comprovam o funcionamento do login, a entrega de e-mails ou as permissões efetivas completas. Nenhum segredo deve ser incluído neste guia.

Correções aprovadas: timeout SQL definido dentro de cada transação, compatível com pooling; nova tentativa após falha de configuração Firebase; limpeza da identidade temporária e do cadastro TOTP incompleto após falhas de login. Se a limpeza falhar, a interface exige recarregar a página para descartar o estado em memória. Verificações de regressão de timeout e nova tentativa foram preparadas para CI, sem execução local.

## Arquitetura e limites desta entrega

Confirmação TOTP: `auth/invalid-verification-code` mantém a chave/resolver somente em memória e limpa o código digitado para nova tentativa na mesma tela. Sessão expirada, limite de tentativas, interrupção de rede e demais falhas limpam o estado e mostram orientação específica. Nenhum erro concede sessão no aplicativo. Os testes de interface usam um SDK simulado no navegador do CI; não confirmam a causa de uma recusa real. Para investigar uma recusa no Firebase, recolher somente `error.message` da resposta da requisição `finalize`, sem payload, cabeçalhos, chave ou códigos. Não regenerar a chave a cada código recusado.

Diagnóstico de falhas de login: respostas HTTP 503 incluem uma referência aleatória `incident`, também presente no log `auth_unavailable` do Render. O log contém somente referência, etapa fixa (`firebase_verify`, `database_user_lookup`, `database_denial_audit`, `database_session_create`, `database_previous_session_revoke` ou `request`) e categoria de erro predefinida. Não registrar mensagem original da exceção, traceback, UID, e-mail, cookies, tokens, senha ou URL do banco. Para investigar, reproduzir uma tentativa após deploy e procurar a referência em Render → Logs. A instrumentação identifica a etapa; ela não corrige por si só a dependência indisponível.

Correção de publicação em 21/10/2026: o log do Render mostrou falha de verificação do certificado nas conexões IPv4 com o Neon. A conexão agora aponta explicitamente para o conjunto de autoridades certificadoras do `certifi`, dependência direta e travada no lockfile, preservando `sslmode=verify-full`. O CI verifica a leitura do pacote de certificados e os parâmetros de segurança; a confirmação da conexão TLS real continua dependendo de novo deploy no Render. Não desativar a verificação para contornar falhas de certificado.

Ampliação aprovada em 20/10/2026: login com Google como alternativa a e-mail/senha. O botão usa popup, armazenamento em memória e a mesma autorização por UID no servidor. Cancelamento, popup bloqueado e conflito de provedor possuem mensagens próprias. Não há vinculação manual automática baseada apenas em e-mail nem concessão de acesso pelo domínio da conta Google.

Configuração adicional: habilitar Google no Firebase, selecionar e-mail de suporte e autorizar o domínio do Render. Preservar uma conta por endereço de e-mail. Manter bloqueada a criação de usuários por clientes e validar com uma conta previamente provisionada o fluxo de vinculação do Google ao mesmo UID. Se houver conflito, usar o método original; resolver a vinculação por procedimento autenticado, sem apagar/recriar a identidade ou transferir permissões por e-mail.

Homologação adicional obrigatória no Render: convidado Google mantém seu UID e permissões; conta não convidada é recusada; Google para administrador exige TOTP (inclusive cadastro e novo login); alternar Google/e-mail não perde propriedade das análises; popup cancelado/bloqueado não cria sessão. A verificação em duas etapas da própria conta Google não substitui a exigência TOTP verificada pelo aplicativo. A entrega deste fluxo depende dessas verificações reais.

- Firebase Authentication/Identity Platform identifica o usuário e mantém senhas e MFA.
- PostgreSQL no Neon guarda a autorização por UID Firebase, papel, situação da conta, sessões e eventos mínimos.
- FastAPI no Render verifica cada requisição privada. React conversa com a API na mesma origem.
- Firebase no navegador usa memória, sem persistir tokens no localStorage. Depois do login, o servidor emite um identificador aleatório em cookie HttpOnly, Secure, SameSite=Strict, sem Domain. O banco guarda somente seu hash.
- Sessão: até oito horas e 30 minutos sem requisições privadas. Polling de uma análise conta como atividade. Logout revoga a sessão corrente; bloqueio da conta impede todas as sessões. Cada requisição também consulta o Firebase para detectar conta desativada, removida ou revogação por recuperação de senha.
- Administradores precisam concluir MFA TOTP; o servidor não aceita somente senha para esse papel. O cadastro do autenticador acontece antes da emissão da sessão. O código não envia SMS.
- Administradores não recebem acesso às análises dos outros usuários. A administração inicial usa ferramenta de operador, sem painel de administração público.
- As análises continuam em memória, limitadas a um processo. Reiniciar perde os resultados, inclusive os antigos sem proprietário. Não existe histórico persistente nesta etapa.
- Se Firebase ou PostgreSQL falharem, a API recusa acesso. A tela pública de login não contém dados privados.
- Limites adicionais do aplicativo: 20 chamadas de sessão/logout por minuto por IP e dez inícios de análise por hora por usuário. São limites locais a um processo; a publicação mantém um worker. Login e recuperação diretamente no Firebase também dependem das proteções e quotas do provedor.
- Eventos de login, autorização e bloqueio não contêm senhas ou tokens. Eventos são removidos após 30 dias na criação de novas sessões; planejar manutenção periódica antes de operação comercial.

## 1. Conferir/criar Neon Free

1. Acesse https://console.neon.tech com a conta que pode já ter utilizado; confira se há projeto existente antes de criar outro.
2. Mantenha o plano Free. Crie um projeto de desenvolvimento e escolha região próxima à do Render, conforme disponibilidade.
3. Use apenas PostgreSQL; não precisamos ativar autenticação, IA ou outros produtos do Neon.
4. Guarde a conexão em configuração protegida. Não cole no chat, README ou commits.
5. Execute a migração `backend/security/schema.sql` no SQL Editor do Neon, usando o proprietário do banco. O SQL é transacional quando executado pela ferramenta `python -m backend.security.admin migrate`; no editor, executar dentro de BEGIN/COMMIT.
6. Crie uma credencial de runtime com privilégio mínimo, separada do proprietário/migração. Gere e guarde a senha pelo mecanismo seguro do painel, sem incluí-la em SQL versionado. Essa credencial precisa conectar ao banco, usar o schema public e dos privilégios abaixo:

```sql
-- Substitua analista_runtime pelo nome da role criada; não usar uma role proprietária em produção.
GRANT USAGE ON SCHEMA public TO analista_runtime;
GRANT SELECT ON auth_schema, app_users TO analista_runtime;
GRANT SELECT, INSERT, UPDATE, DELETE ON app_sessions, security_events TO analista_runtime;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO analista_runtime;
```

O administrador precisa de outra conexão para `allow`, `invite` e `disable`. Não conceder alteração de app_users à credencial usada pelo servidor web.
Use conexão com pooling para o runtime. O cliente força TLS com verificação do certificado e da identidade do servidor usando as raízes do sistema. Acesso ao banco nunca é fornecido ao navegador.

Limites consultados em 19/10/2026: 1 GB por projeto, 100 CU-h/mês, 5 GB de transferência pública; suspensão após cinco minutos inativo. Limites esgotados podem interromper operações. Recuperação instantânea de até seis horas ou 1 GB de alterações não substitui backup independente. Conferir novamente no painel antes da configuração.

## 2. Criar Firebase sem cobrança

1. Acesse https://console.firebase.google.com e crie um projeto no Spark. Não ativar Blaze, SMS ou uma conta de faturamento automaticamente.
2. Registre um aplicativo Web para obter `apiKey`, `authDomain` e `projectId` públicos. Não são a chave privada da conta de serviço.
3. Ative Authentication com Identity Platform e o provedor e-mail/senha. Se o painel exigir faturamento para algum recurso, interromper essa configuração e discutir a condição antes de prosseguir.
4. Nas configurações de Identity Platform, desative criação de usuários por clientes (`Enable create / sign-up`). A ferramenta administrativa continua criando contas. Ative proteção contra enumeração de e-mails e configure política de senhas longas; não dependa da ausência do botão de cadastro.
5. Adicione `financial-analyst-agent-crewai.onrender.com` aos domínios autorizados. Use inicialmente as páginas padrão do Firebase para ações de e-mail; não é necessário domínio próprio.
6. Configure templates em português, verificação e recuperação de senha. Não habilite login por link nesta entrega.
7. Ative TOTP no projeto seguindo a [documentação oficial](https://firebase.google.com/docs/auth/web/totp-mfa#enable_totp_mfa). A configuração pode ser feita pela API administrativa em ambiente confiável, com credencial de operador e sem expor seu token. Escolha uma janela adjacente pequena (proposta: 1 intervalo de 30 segundos). Nunca colocar tokens em logs ou scripts versionados.
8. Habilite MFA também na conta Google que administra o projeto.

A conta de serviço do runtime precisa verificar tokens e consultar usuários: use permissão de leitura de Firebase Authentication, sem papel Owner/Editor. Credencial administrativa para criar contas/configurar MFA fica separada. Tokens de sessão não são aceitos em modo emulador pela aplicação.

## 3. Preparar Render antes do merge

| Configuração | Conteúdo |
|---|---|
| APP_ORIGIN | https://financial-analyst-agent-crewai.onrender.com |
| FIREBASE_PROJECT_ID | ID do projeto Firebase |
| FIREBASE_WEB_API_KEY | apiKey do aplicativo Web Firebase |
| FIREBASE_AUTH_DOMAIN | authDomain indicado pelo Firebase |
| GOOGLE_APPLICATION_CREDENTIALS | Caminho do arquivo secreto da conta de serviço no Render |
| DATABASE_URL | Conexão PostgreSQL da credencial de runtime no Neon |

Armazene o JSON privado como Secret File, por exemplo `/etc/secrets/firebase-service-account.json`, e aponte GOOGLE_APPLICATION_CREDENTIALS para esse caminho. Nunca use variável VITE_* para credenciais privadas. Preserve as chaves dos provedores de IA já configuradas.

A aplicação usa `backend.web:app`, frontend compilado e exatamente um worker. A API isolada também exige autenticação; não há fallback público. APP_ORIGIN deve ser a origem HTTPS exata, sem caminho. A proxy do Render deve ser a única entrada; não expor diretamente o servidor que confia em cabeçalhos encaminhados. Restringir origens e manter HTTPS na plataforma.

Não remover WEB_USERNAME/WEB_PASSWORD até concluir a validação, pois podem ser necessárias para voltar à versão anterior. A versão nova não as utiliza. Não habilitar uma chave de desenvolvimento para contornar autenticação.

## 4. Criar a primeira conta e convidar usuários

Usar um ambiente de operador confiável com as dependências instaladas, GOOGLE_APPLICATION_CREDENTIALS administrativo, FIREBASE_PROJECT_ID e DATABASE_URL administrativo configurados de modo protegido. Isso é provisionamento, não execução de testes locais. Os comandos abaixo são instruções; não foram executados nesta tarefa.

```powershell
# Cria conta sem senha temporária e autoriza no PostgreSQL.
.venv/Scripts/python.exe -m backend.security.admin invite SEU_EMAIL --role admin
# Demais usuários:
.venv/Scripts/python.exe -m backend.security.admin invite EMAIL_DO_CONVIDADO --role user
```

Comunicar manualmente à pessoa o endereço do aplicativo e pedir que use “Esqueci minha senha / Primeiro acesso”. O Firebase envia o link para ela escolher a senha. Não compartilhar senha ou chave de MFA. No primeiro login sem e-mail verificado, a tela solicita confirmação pelo e-mail; após confirmar, entrar novamente. Administradores então cadastram o autenticador e fazem novo login com senha e código. Não há envio automático de convites personalizados.

Se a conta já existe no Firebase, copie o UID no painel e autorize:

```powershell
.venv/Scripts/python.exe -m backend.security.admin allow UID_FIREBASE --role user
# Bloqueia no banco e revoga tokens Firebase:
.venv/Scripts/python.exe -m backend.security.admin disable UID_FIREBASE
```

Autorizar ou mudar papel revoga sessões anteriores. Se uma criação falhar parcialmente, conferir o Firebase e usar allow pelo UID; a existência da conta no Firebase sem autorização no banco não libera o aplicativo.

Perda do autenticador administrativo: confirmar identidade por procedimento de operador, bloquear acesso e revogar sessões antes de remover o fator no Firebase. Reautorizar somente após a verificação; no próximo acesso, o sistema exigirá novo cadastro TOTP. Não existe atalho web para ignorar MFA.

## 5. CI e homologação no Render

O CI prepara testes de API, autorização, cookies, revogação, MFA, isolamento, interface e banco PostgreSQL descartável. Nenhum teste usa credenciais Firebase ou Neon reais. Não colocar esses segredos no CI. A cobertura simulada não comprova configuração nem entrega real dos provedores.

Antes do merge: conferir CI, projeto Firebase, TOTP, banco migrado, papéis, conta administrativa e variáveis do Render. A publicação continua manual conforme o fluxo do usuário; Auto-Deploy do Render pode iniciar após merge.

Após deploy, verificar no Render:

- Primeiro acesso, confirmação de e-mail e recuperação, com mensagem genérica para endereço inexistente.
- Login de administrador exige código TOTP; senha sozinha não libera dados.
- Duas contas distintas: A não acessa URL/status/resultado de B; mesmo comportamento para administrador.
- Logout limpa resultados, revoga a sessão e bloqueia outras abas; troca de conta não retoma a análise anterior.
- Sessão expirada, conta bloqueada e senha recuperada perdem acesso no servidor.
- Ausência de cadastro público, proteção de origem, mensagens de falha, desktop e celular.
- Configuração incorreta ou banco indisponível não libera dados.
- Inspecionar consumo no Neon e no Firebase durante homologação.

## 6. Backup, retorno e limites operacionais

Antes de mexer em permissões ou migrar uma base com usuários, exportar um backup PostgreSQL em formato custom (`pg_dump --format=custom`), com credenciais fornecidas de modo protegido e armazenamento criptografado fora do repositório. Restaurar em banco separado com pg_restore para verificar o procedimento antes de depender dele. Backup das tabelas da aplicação não inclui as contas Firebase: manter procedimento separado de exportação/recuperação de identidades, protegido e validado antes da operação comercial.

Para voltar à versão anterior: interromper novas entradas, revogar sessões e reimplantar o commit anterior com HTTP Basic e suas variáveis. Essa versão compartilha resultados entre quem possui a credencial; restringir novamente ao grupo de desenvolvimento e não deixá-la disponível a clientes multiusuário. Não apagar tabelas para efetuar rollback. Reinício perde análises temporárias.

Pendências externas: validar conexão protegida e permissões efetivas, primeiro acesso administrativo com verificação de e-mail e TOTP, vinculação Google, e-mails reais (incluindo redefinição de senha), backup/restauração e validação visual. Também verificar falhas durante envio de confirmação e cadastro TOTP: nenhum dado privado deve aparecer e a nova tentativa deve começar sem cadastro incompleto. Sem essas evidências, esta entrega não deve ser descrita como homologada ou pronta para clientes.

Fontes: [Neon Free](https://neon.com/pricing), [limites Neon](https://neon.com/docs/introduction/plans), [Firebase MFA](https://firebase.google.com/docs/auth/web/totp-mfa), [controle de criação de contas](https://docs.cloud.google.com/identity-platform/docs/concepts-manage-users), [limites Firebase](https://firebase.google.com/docs/auth/limits).
