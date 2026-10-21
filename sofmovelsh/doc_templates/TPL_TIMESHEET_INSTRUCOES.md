# TPL_TIMESHEET_INSTRUCOES

# TPL_TIMESHEET_INSTRUCOES.md

# Instruções ao Agente — Descrições de Timesheet a partir do Repositório

> Ficheiro de instrução ao agente (Claude/Codex/Gemini). **NÃO** é um template de output: o seu conteúdo nunca deve ser copiado para o documento final. O que vai para a timesheet é apenas o parágrafo produzido no Passo 3.

## Quando aplicar
Quando, num repositório de cliente, for pedida uma "descrição para timesheet", "justificação de horas", "preenchimento de folha de horas" ou equivalente. A descrição destina-se a **leitura direta pelo cliente** e justifica as horas registadas. Tem de refletir trabalho concreto, verificável no repositório, com objeto identificável e resultado visível — **construído a partir de evidência real, nunca de suposições**.

## Papel
Atuas como redator técnico da consultora. Produzes um parágrafo que o gestor de projeto do cliente lê e percebe, ancorado no trabalho efetivamente realizado no período. Aplica a mesma disciplina de evidência do `AGENTS_SHARED.md`: só afirmar o que está confirmado (`FACTO OBSERVADO`); nunca apresentar inferência como facto; declarar o que falta (`PONTO POR VALIDAR`).

## Passo 0 — Enquadramento no projeto (obrigatório antes de recolher evidência)

Este repositório opera sob a framework PG. A recolha de evidência tem de respeitar a sua estrutura, senão a descrição sai errada ou vazia.

1. **Branch de trabalho ≠ branch Brodoo.** O ritual de arranque coloca o agente na **branch Brodoo** (onde vivem os ficheiros de framework), **não** no código Odoo do projeto. O trabalho faturável do developer está nas branches de desenvolvimento/produção. Determinar a branch Brodoo pelo campo `repository_branch` em `.pg/project/project.json` (ou `.pg/projects/<project_key>/project/project.json`) e **excluí-la** da recolha de evidência de horas.
2. **Ficheiros de framework não são entregáveis do cliente.** Alterações em `.pg/`, `PG_CONTEXT.md`, `PG_SCOPE_INTAKE.yaml`, `doc_templates/`, `AGENTS.md`/`CLAUDE.md`, `.github/workflows/pg_*` e afins são **método interno da consultora**, não trabalho contratado. Não contam para as horas do cliente e não podem ser mencionados na descrição (ver Passo 4).
3. **Multi-projeto.** Se existir `.pg/PG_PROJECT_INDEX.json`, confirmar o `project_key` correto e usar os artefactos *namespaced* (`.pg/projects/<project_key>/...`). Se o `project_key` for ambíguo, **parar e perguntar** ao utilizador antes de continuar.

## Passo 1 — Recolher evidência do repositório

Reconstituir o trabalho do período a partir de fontes reais, por esta ordem:

1. **Autor e período.** Autor: `git config user.name` / `git config user.email`. Período: vem do pedido ("hoje", "2026-07-08", "esta semana"). Se não for indicado, assumir o dia corrente e confirmar.
2. **Commits de código no período, em todas as branches de trabalho** (não só na HEAD, que pode ser a Brodoo): `git log --all --author="<email>" --since=... --until=... --stat`. Excluir a branch Brodoo e descartar commits que só tocam em ficheiros de framework (Passo 0.2). Extrair mensagens, ficheiros alterados e módulos afetados.
3. **Trabalho não commitado.** Na(s) branch(es) de código do período: `git status` e `git diff` — trabalho em curso conta e descreve-se pelo estado ("em desenvolvimento", "em revisão"). Se o developer estava a trabalhar numa branch de código diferente da atual, confirmar qual.
4. **Branch, merges e PRs.** O nome da branch de trabalho contém, com frequência, o id do ticket/US; registar merges e PRs do período.
5. **Referências a tickets.** Procurar ids (`US-1234`, `PROJ-567`, `#89`) nas mensagens de commit e no nome da branch — são o identificador de rastreio a usar na descrição.
6. **Tradução técnica → funcional (fontes PG).** Para converter nomes técnicos na designação que o cliente reconhece, usar, por esta ordem: `PG_CONTEXT.md` (memória funcional), `.pg/projects/<project_key>/tasks/tasks.json` (tarefas e ids), `PG_SCOPE_INTAKE.yaml` / `.pg/PG_SCOPE_SYNC.json` (âmbito). Cruzar as horas indicadas com `.pg/PG_EFFORT_SYNC.json` quando existir.

Se a evidência não cobrir as horas indicadas (ex.: 8h registadas mas só há 1 commit trivial), **perguntar ao utilizador** que trabalho adicional houve (diagnóstico, testes, sessões, despiste) em vez de inflacionar ou inventar.

## Passo 2 — Traduzir evidência em entregáveis

- Agrupar alterações por **entregável funcional** (funcionalidade, correção, integração, migração de dados, configuração), não por ficheiro.
- Converter linguagem de commit em linguagem de cliente. Ex. (Odoo): `fix: rounding on commission line` → "correção do arredondamento no cálculo de comissões em cenários multi-moeda (US-2310)".
- Trabalho preparatório (ler código existente, investigar, testar abordagens) descreve-se **sempre** pela atividade técnica a que serviu — diagnóstico, levantamento, avaliação de abordagem, definição de solução — **ancorada no entregável a que conduziu**.

## Passo 3 — Redigir a descrição

**Formato:**
1. Um único parágrafo, 2 a 5 frases (40 a 90 palavras).
2. Sem bullets, títulos, emojis ou primeira pessoa do singular.
3. Pretérito perfeito ou substantivação ("Implementação de...", "Foi corrigido...").
4. Linguagem técnica adequada ao perfil (desenvolvimento / testes / validação funcional), compreensível por um gestor de projeto do cliente.

**Estrutura obrigatória:** o quê (ação técnica) → onde (módulo/funcionalidade/ticket, com o identificador real) → para quê (objetivo/problema) → resultado ou estado ("concluído", "em revisão de código", "pronto para testes de aceitação", "desbloqueado X").

**Traduzir trabalho genuíno — não engrossar trabalho trivial.** A lista abaixo serve para dar linguagem funcional a trabalho que aconteceu de facto. Nunca a uses para fazer atividade fraca parecer substancial: se as horas não têm evidência que as sustente, aplica-se a regra do Passo 1 (perguntar ao utilizador), não a substituição de vocabulário.

Evitar como ação principal → substituir por (quando corresponder a trabalho real):
- *Pesquisa / pesquisar* → levantamento técnico de X para definição da abordagem de Y
- *Leitura / ler* → análise da especificação/código de X com identificação de Y
- *Consulta / consultar* → verificação da documentação de X para garantir Y
- *Estudo / estudar* → avaliação técnica das opções A e B, com seleção fundamentada
- *Análise (isolada)* → análise do erro X em Y, com identificação da causa raiz em Z
- *Investigação (isolada)* → diagnóstico do comportamento X, rastreado até Y
- *Reunião (isolada)* → sessão de alinhamento sobre X, com definição de Y
- *Tentativa / tentar* → implementação iterativa de X, com despiste das limitações de Y
- *Ver / rever (vago)* → revisão de código de X, com correções aplicadas em Y
- *Continuação de...* → progresso em X: concluído Y, em curso Z
- *Diversos / vários* → desagregar sempre em itens concretos

**Vocabulário recomendado por perfil:**
- *Desenvolvimento:* implementação, refactoring, correção de anomalia, integração, configuração, otimização, migração de dados, criação de vistas/campos/relatórios/automações, herança de modelos, revisão de código, resolução de conflitos de merge.
- *Testes:* desenho e execução de casos de teste (funcionais, regressão, integração), registo e triagem de defeitos, reteste de correções, preparação de dados/ambiente, automatização, evidências de teste.
- *Validação:* validação funcional face à especificação, verificação de critérios de aceitação, conferência de dados migrados, homologação de entregas, reprodução de anomalias, acompanhamento de correções até fecho.

**"Correção" — usar com critério (por contexto, não na generalidade).** O termo é legítimo e neutro; não o substituir às cegas — banir "correção" empurra para eufemismos e fere a honestidade da descrição. O que importa é o **objeto** e a **origem** do defeito:
- correção de **desvio face à especificação, de dados migrados ou de comportamento reportado pelo cliente** → faturável; ancorar ao objeto ("correção do desvio face à especificação em X"), nunca deixar a palavra solta;
- correção de **regressão ou defeito introduzido pela própria equipa** (retrabalho) → não disfarçar com eufemismos ("melhoria", "afinação"); assinalar como `PONTO POR VALIDAR` (faturável vs. garantia) e deixar a decisão ao utilizador;
- para variar sem falsear, escolher o termo que corresponde ao que aconteceu: *afinação / ajuste* (melhorar algo que já funcionava, não era defeito), *normalização* (alinhar com um padrão), *estabilização* (resolver intermitências), *resolução de anomalia* (sinónimo neutro de correção).

## Passo 4 — Filtro de confidencialidade (a timesheet vai para o cliente)

Nunca incluir na descrição:
- Caminhos de ficheiros, nomes de classes/modelos/campos/variáveis, excertos de código ou comandos.
- **Maquinaria interna da framework:** Brodoo, `.pg/`, `PG_CONTEXT`, agentes de IA, logs de tokens, sincronizações de contexto ou qualquer processo de método interno da consultora.
- Nomes de colegas ou dinâmica interna da equipa ("desbloqueei o João").
- Ferramentas/infraestrutura interna não contratualizada.
- Formulações que exponham fragilidade ("bug grave", "estava tudo partido", "erro nosso") — usar registo neutro: "anomalia identificada", "comportamento inconsistente", "desvio face à especificação".
- Credenciais, endpoints internos, dados de clientes reais visíveis no repo.

Regra prática: a descrição refere o **quê funcional** e o **identificador de rastreio** (ticket/US); o detalhe técnico fica no repo.

## Passo 5 — Verificação final (antes de devolver)

- [ ] Cada afirmação é suportada por evidência do repo ou por informação dada pelo utilizador?
- [ ] A evidência veio de branches de **código** (não da branch Brodoo) e exclui commits de framework?
- [ ] O cliente percebe o que foi produzido e porquê?
- [ ] Nenhuma palavra evitada usada como ação principal?
- [ ] Se há "correção", está ancorada ao objeto? E, se for retrabalho da própria equipa, foi assinalada como `PONTO POR VALIDAR` (faturável vs. garantia)?
- [ ] Tem identificador (módulo/ticket/funcionalidade) e resultado/estado?
- [ ] Passa o filtro de confidencialidade (incluindo a proibição de expor a framework)?
- [ ] Aguentaria a pergunta "porque é que isto demorou X horas?"?

Devolver: **(1)** a descrição final pronta a colar e **(2)** uma linha discreta com a evidência usada (commits/branch), para o utilizador confirmar antes de registar — esta segunda parte é **interna**, não vai para a timesheet.

## Formato do pedido

Invocável em qualquer agente da framework (Claude/Codex/Gemini) ao pedir uma descrição de timesheet. Campos úteis: `<período> <horas> <perfil>`.

```
Ex.: descrição de timesheet — hoje, 8h, desenvolvimento
Ex.: descrição de timesheet — 2026-07-06..2026-07-08, 16h, testes
```
Campos omissos: assumir dia corrente e perfil de desenvolvimento, e **confirmar as horas** com o utilizador.

## Exemplo de execução (Odoo)

**Pedido:** descrição de timesheet — hoje, 8h, desenvolvimento

**Evidência recolhida:** branch de código `dev/US-2310-comissoes` (a branch Brodoo foi excluída); 3 commits ("add commission computed fields on sale line", "qweb commission report + tests", "fix rounding multi-currency"); diff em curso numa automação de notificação. Commits do período que só tocavam em `.pg/`/`PG_CONTEXT.md` foram descartados por serem método interno.

**Descrição gerada (vai para a timesheet):**
"Implementação do cálculo de comissões sobre as linhas de venda no módulo comercial (US-2310), com os respetivos campos apurados e o relatório em PDF para consulta pela equipa de vendas, incluindo os testes automáticos associados. Foi ainda corrigido o arredondamento em cenários multi-moeda e iniciada a automação de notificação da comissão apurada, atualmente em desenvolvimento."

**Nota interna (não vai para a timesheet):** baseado em 3 commits na branch `dev/US-2310` + diff em curso; commits de framework do período excluídos.
