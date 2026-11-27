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


## Verificação após o deploy e ajuste de coerência — 27/11/2026

As capturas fornecidas pelo usuário confirmam o deploy f306747 e a apresentação
em PETR4 de USD 26.113,00 mi (2025) e USD 26.876,00 mi (2024), com fonte F-4.
A interpretação, porém, declarou falta de conciliação do resultado reportado.
A regra compartilhada ainda mencionava o bloqueio sem distinguir o campo legado.

O ajuste separa os dois campos nas instruções e acrescenta ao contexto dos dois
agentes financeiros a disponibilidade por exercício, preservando referências e
períodos indisponíveis. Também permite URLs documentais além dos links de notícias
e orienta a não reproduzir instruções de redação no aviso ao leitor.
Não modifica valores, aprovação, tabelas, métricas ou relatórios já armazenados.

Validação local: 165 testes executados, 162 passaram e 3 de banco ignorados.
Casos cobrem zero disponível, referência divergente, exercício ausente e entrega
do contexto aos dois agentes sem alterar a base original. Sem IA real ou Docker.
O ajuste de instruções não é um verificador determinístico da resposta do modelo.
Após o próximo deploy, gerar novas consultas PETR4 e VALE3 e conferir a coerência
entre tabela e texto. A verificação visual de VALE3 ainda está pendente.


## Validação de PETR4 e VALE3 e ressalva restante — 27/11/2026

O usuário confirmou ed38373 Live e forneceu novas consultas concluídas de PETR4
(02:22 Brasília) e VALE3 (02:30 Brasília). As tabelas mostram os quatro valores
aprovados com fontes F-4/F-3; ambas as interpretações reconhecem sua disponibilidade.
Uma tentativa anterior falhou na etapa CIO (Gemini, unavailable após cerca de 60s);
a tentativa seguinte terminou, sem alteração de configuração pelo assistente.

Permaneceu a justificativa sem suporte de falta de conciliação com outros
demonstrativos ou conciliação contábil completa. O novo ajuste de instruções
separa disponibilidade documental de inferência causal: valores disponíveis podem
ser citados e comparados em exercícios compatíveis, mas isoladamente não provam
eficiência ou causas. Ressalvas de lucro/FCF não devem migrar para essa medida.
A escolha editorial de outros achados não requer inventar uma restrição de uso.

Não há alteração dos valores, registro aprovado, cálculos ou snapshots armazenados.
A validação real do texto permanece pendente de novas consultas após este ajuste;
instruções não constituem verificação determinística da saída do modelo.
