# Resultado operacional reportado: integração local

O usuário responsável aprovou explicitamente a revisão final nesta conversa.
O registro `evidencias/operating-review-approval-2026-11-26.json` preserva a frase
recebida, a identificação contextual de William, a hora de registro e os quatro
digests. Não foi presumida verificação externa da identidade. O pacote e o
documento revisados permanecem intactos; a aprovação é armazenada separadamente.

O contrato 3.1 acrescenta `reported_operating_income` e sua referência por período.
O campo legado `operating_income` continua nulo. O adaptador solicita o campo
reportado no mesmo transporte Yahoo já usado pelos demonstrativos. Não busca
valor alternativo nem substitui ausência pelo snapshot documental.

O registro local do servidor exige pacote, alcance e arquivos de evidências com
hashes íntegros e revisão correspondente. O valor recebido deve coincidir
exatamente com empresa, exercício e moeda aprovados. A tolerância documental
serve à revisão original; não autoriza um valor novo, mesmo próximo. Nenhuma
flag de aprovação recebida do cliente ou provedor libera valores.

Interface, relatório local, referências da IA e contrato HTTP apresentam a nova
medida com fonte oficial e ressalva de alcance. A atualidade dos demonstrativos e
a proibição de combinar moedas diferentes continuam separadas da validação.
O validador offline mantém sua regra de não habilitar runtime; a decisão de uso
fica no novo registro confiável do servidor.

Validação local: 163 testes backend executados, 160 aprovados e 3 ignorados;
27 testes operacionais passaram após os ajustes finais. Build e geração do
contrato TypeScript passaram. Testes de apresentação desktop/mobile verificaram
valor, fonte, limitação e período indisponível. A inspeção visual levou a separar
a referência do número e limitar sua largura na tabela.

Limites: não houve teste com Yahoo ou IA reais, Docker ou banco de produção.
O aviso preexistente de configuração `lifespan` e o aviso de bundle acima de
500 kB continuam presentes. A integridade do registro é verificada durante a
normalização de novas consultas; resultados já armazenados são snapshots e não
são reescritos retroativamente. Arquivos de evidência e aprovação devem acompanhar
o deploy; sua ausência bloqueia apenas o indicador. O registro depende do controle
de escrita do repositório/servidor, não de assinatura criptográfica do revisor.

Revisão para PR: os 16 arquivos vinculados por SHA-256 preservam seus bytes
no Git por regras explícitas em `.gitattributes`, evitando conversão de fim de
linha entre Windows e Linux. A comparação entre índice Git e arquivos locais
passou. A suíte backend, contrato HTTP, formatação e build foram reconferidos.
O processo Playwright local precisou ser encerrado durante a limpeza do servidor
no Windows, após as duas verificações de apresentação terem passado.

A publicação deste trabalho em PR não autoriza merge automático. O merge e a
validação do deploy seguem o fluxo manual adotado pelo projeto.
