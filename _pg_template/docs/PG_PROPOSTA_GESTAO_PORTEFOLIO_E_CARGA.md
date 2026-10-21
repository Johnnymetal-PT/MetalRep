# Proposta — gestão de portefólio e de carga no `_pg_template`

> **Atualização de 2026-10-10 (tarde).** Os números deste documento foram recalculados **só para projetos Odoo** (etiqueta «Odoo») e para o **ano de 2026**; ver as secções 2b e 8.1b. As secções 1, 2 e 8.1 podem ainda citar valores de uma primeira medição (4 semanas, todos os projetos): prevalecem os valores da 2b. Versões para apresentar: Claude Docs «Gestão de projetos às sextas-feiras» e «Manual de sexta-feira para gestores», slides e dashboard «Quadro e carga de projetos».

Estado: **proposta para decisão** (2026-10-10). Nada deste documento está implementado.

Fontes analisadas:
- Curso de Gestão de Projetos da Porto Business School, 62.ª edição (`C:\curso-gestao-projetos-pbs-62`): slides P0–P7, casos, 15 transcrições, biblioteca (PMI, PMO, Prado, Stage-Gate, Standish, HBR, Bosch, EDP X, Amazon) e os A3 do grupo.
- *Implementation Methodology* do Odoo (PDF de 69 páginas, `odoo.com/web/content/17936384`, criado em janeiro de 2020).
- Estado atual do `_pg_template` v2.45.1 (código, scripts, templates e `CHANGELOG`).

Convenção: `FACTO OBSERVADO` está na fonte citada; `INFERENCIA` é conclusão minha; `PONTO POR VALIDAR` precisa de confirmação antes de decidir.

---

## 1. Resumo executivo

1. **O problema principal é que o quadro de tarefas não é mantido.** Metade das tarefas em sprint não é editada há mais de 30 dias; em metade dos projetos com tarefas em sprint não houve uma hora lançada em 4 semanas; e um terço dos projetos com horas não tem tarefa em sprint (secção 2b). O resto desta proposta só funciona se isto for corrigido primeiro.
2. **É um problema de dados e de rotina, não de ferramenta.** O framework espelha tarefas e horas *por projeto* (um repositório por projeto), mas nada junta projetos, pessoas e semanas. `FACTO OBSERVADO`: não existe no repositório nenhuma menção a capacidade, carga, sobre-alocação, PMO ou portefólio.
3. **Nem o curso nem a metodologia Odoo dão números de carga por pessoa.** Não há taxa de utilização-alvo, limite de projetos por gestor nem uma cadência de sexta-feira em nenhuma das duas fontes. Esses parâmetros são decisão da Parâmetro Global (secção 8).
4. **O que as fontes dão é o método:** gestão de capacidade como função do PMO (norma de portefólio do PMI, §5), profundidade de controlo proporcional ao tipo de projeto (A/B/C), reunião curta com informação comum (*War Room*, ≤ 30 min), revisão semanal com relatório de exceções (Amazon), e a regra de que um pedido novo é um projeto novo e passa pela fila de prioridades.
5. **A metodologia Odoo dá o critério do que vigiar:** prazo e orçamento são o que define sucesso; custom e satisfação do cliente não são. Dá também a regra de ouro das alterações: só entram se não afetarem prazo e orçamento, ou se outro requisito sair.
6. **Proposta central:** uma camada de portefólio *fora* dos repositórios de cliente — um comando de revisão de sexta-feira, alimentado por um instantâneo de leitura única ao Odoo da Parâmetro Global (tarefas, horas lançadas, férias, planeamento) — cujo **primeiro passo é limpar o quadro** (mover, fechar ou retirar do sprint cada tarefa sem atividade), mais regras de higiene sem as quais o instantâneo mente.
7. **Antes de construir, há três correções de base** (secção 6, P0). A mais importante: o contrato `PG_EFFORT_SYNC` está partido entre o Odoo e o validador.

---

## 2. Porque é que hoje "não sabemos nada"

| Pergunta de gestão | O que o framework responde hoje | Fonte |
|---|---|---|
| Quantas horas tem cada pessoa nesta semana e nas próximas? | Nada. | Sem leitura de `hr.leave`, `planning.slot`, calendário de recursos. |
| Quem está sobre-alocado? | Nada. | Sem agregação entre projetos. |
| Quanto tempo foi lançado por pessoa, por projeto? | Só por projeto, só quando se abre esse repositório. | `PG_EFFORT_SYNC.json` → `hours_by_employee` (`pg_brodoo/services/project_effort_payload_builder.py:61-98`). |
| Que tarefas abertas não têm dono, horas ou prazo? | Nada verifica. | O template de planeamento *manda* preencher; nenhum código valida. |
| Este projeto está dentro de prazo e orçamento? | Só quando alguém pede um status; o semanal é "a pedido, não agendado". | `TPL_STATUS_SEMANAL_INSTRUCOES.md`. |
| Qual a taxa de execução do portefólio? | Nada. | — |

Um participante da Parâmetro Global disse na Aula 1 (`aula1_parte1`) que tinha "quase 100 projetos no ativo" para 14 colaboradores. A medição seguinte confirma a ordem de grandeza e mostra onde está o problema.

---

## 2b. Medição real ao Odoo da Parâmetro Global (2026-10-10, só projetos Odoo)

`FACTO OBSERVADO` — consulta só de leitura (`pg_odoo_query.ps1`, `read_mode: api`), base `parametro-main-29950773`, janela de 2026-01-01 a 2026-10-09. **Universo: projetos com a etiqueta «Odoo»** (164 ativos e 13 arquivados; 68 em curso). Os projetos PHC, Primavera, Web, BI e internos ficam fora. Os valores por pessoa aparecem com nome nos Claude Docs e no dashboard; aqui ficam só os agregados.

### Apps instaladas (Odoo 19)
**Planning** e **Project Planning**, **Time Off**, **Timesheets** (`timesheet_grid`), **Helpdesk** (com Timesheet e Project Helpdesk), Skills e Knowledge. Studio também está instalado (continua proibido criar nele).

### O realizado está lançado; o planeado não existe
- **7 363 h lançadas em 2026 em 127 projetos Odoo; 28 projetos concentram 80 %.** O Odoo é **48 %** das horas lançadas (7 363 de 15 478); a quota desce a 35 % em agosto e setembro.
- Horas por semana: 113 a 258 h; as pessoas com horas Odoo por semana passam de 9–12 (até julho) para 4–6 (semanas 34 a 39).
- Linhas de timesheet sem tarefa: 1 a 8 % por mês, 3 % no ano.
- Planning: 29 *slots* em 2026, nenhum a começar entre outubro e dezembro (1 875 h planeadas contra 24 277 h de capacidade teórica de 13 pessoas, 7,7 %). Time Off: só uma pessoa tem ausências validadas em 2026.

### O quadro de tarefas não reflete o trabalho (o problema principal)
Tarefas abertas em projetos Odoo: **1 039** (679 em Backlog). Em sprint (*Sprint Backlog* e *Sprint in Progress*, 257):

| Medida | Valor |
|---|---|
| Sem edição há mais de 30 dias | **141 (55 %)** |
| Sem edição há mais de 90 dias | 59 (23 %) |
| *Sprint in Progress* (150): na mesma etapa há mais de 90 dias | 64 (43 %) |
| *Sprint Backlog* (107): sem nenhuma hora lançada | 60 (56 %) |
| Com responsável, horas e prazo ao mesmo tempo | 46 (18 %) |
| Com prazo vencido | 34 (13 %) |
| *Sprint Complete* ainda abertas | 61 |

- **Dos 73 projetos com tarefas em sprint, 38 (52 %) não tiveram uma hora lançada nas últimas 4 semanas.** Dos 50 projetos com horas, 15 (30 %) não têm nenhuma tarefa em sprint.
- Ao longo do ano: 3 450 tarefas criadas e 2 590 fechadas; só 447 das fechadas tinham prazo e 40 % dessas fecharam dentro dele; 15 % dos fechos concentram-se em dias com 50 ou mais fechos (limpezas em massa). A idade mediana das abertas é de 73 dias.
- Higiene das 1 039 abertas: 48 % com responsável, 23 % com horas, 19 % com prazo, 13 % com os três.

### Projetos
- Em curso: 68. **17 sem gestor**, 11 sem data de fim, 8 sem horas alocadas, 28 sem uma hora em 4 semanas (13 dos 17 sem gestor estão neste grupo, quase todos do programa Coaching 4.0).
- Consumo de horas (60 com horas alocadas): 31 abaixo de 50 %, 6 entre 50 e 80 %, 4 entre 80 e 100 %, 7 entre 100 e 120 %, **12 acima de 120 %**; 19 acima do orçado, 6 deles em etapa de suporte.
- Concluídos (22 com horas alocadas): mediana efetivas/alocadas de 58 % abaixo de 50 h, 119 % entre 50 e 150 h, 91 % entre 150 e 300 h e 105 % acima de 300 h (amostras pequenas).
- Projetos em curso por gestor: 16, 11, 7, 5, 4, 4 e 4, mais 17 sem gestor.

### As horas já não medem o tempo de uma pessoa (confirmado pela equipa)
Com agentes de IA, cada pessoa trabalha em vários projetos ao mesmo tempo e as horas lançam-se por cliente. A percentagem de dias de pessoa com mais de 7,5 h lançadas foi de **6 a 12 % de janeiro a julho e de 32 a 35 % de agosto a outubro**. Por pessoa e semana, em 2026 (195 pessoas-semana, sem a pessoa com mais horas Odoo): projetos com 4 h ou mais, mediana 2, percentil 75 = 3, percentil 90 = 4; com 1 h ou mais, mediana 4, percentil 90 = 9. A regra do timesheet de 2026-10-09 conta as sessões paralelas uma só vez por cliente, mas não fixa total diário; repetir a medição daqui a 3 ou 4 semanas.

### Suporte
O suporte entra por três portas: Helpdesk (104 pedidos da equipa Odoo em 2026, 47 fora do SLA, tratados por 12 pessoas), projetos em etapa Support (618 h em 10 projetos, 11 pessoas, 408 tarefas criadas) e tarefas dentro de projetos com horas por gastar (só mensurável pelas palavras no nome: 305 h em 25 projetos, com sobreposição). O que se vê soma 720 h, cerca de meia pessoa. Ver a proposta de função de responsável de suporte nos Claude Docs.

### Consequências para a proposta
1. **Ordem de decisão:** o passo 1 (standard já instalado) existe: Planning, Project Planning e Time Off dão carga por pessoa e por semana. O framework acrescenta a **rotina de revisão**, não um painel próprio.
2. **O gargalo é de dados prospetivos:** o realizado é fiável; o planeado não existe.
3. **A segmentação A/B/C é urgente:** 28 projetos fazem 80 % das horas.
4. **A capacidade tem de ser medida em atenção e em projetos simultâneos (WIP), não só em horas.** Os registos de sessões por agente (`.pg/tokens`) dão o tempo à frente do agente e o paralelismo.
5. **Só se vêem projetos Odoo:** 52 % das horas vão para outros projetos, pelo que a carga real de cada pessoa é maior.

---

## 3. O que a metodologia Odoo ensina (e onde diverge do nosso contrato)

`FACTO OBSERVADO` — páginas impressas do PDF.

### 3.1 A adotar

| Regra Odoo | Página | Como entra no framework |
|---|---|---|
| Sucesso = no prazo e no orçamento; "quando um projeto falha, é sempre porque demorou demasiado ou custou demasiado". | 9 | Os dois semáforos principais da revisão semanal são **prazo** e **horas**. |
| A satisfação do cliente **não** é KPI de projeto; usa-se só para saber que clientes precisam de atenção. | 10 | Fica como sinal de atenção, nunca como semáforo. |
| Fases e peso relativo: GAP 10 %, arranque 5 %, implementação 80 %, go-live 5 % (10–15 % em projetos grandes). Nota: o texto do arranque diz "pelo menos 10 %", em contradição com a tabela. | 23, 26 | Referência de sanidade para o consumo de horas por fase. `PONTO POR VALIDAR`: os nossos orçamentos seguem esta divisão? |
| Papéis: *Project Leader* (gestor + analista + especialista de produto), *Project Director* (só em projetos grandes ou políticos; não é a tempo inteiro; reporta ao comité), *App Expert* (revisão por pares, transversal a projetos, fora da equipa). | 15–18 | Define quem entra na revisão de sexta e a revisão por pares no fecho do GAP. |
| Entregar funcionalidade todas as semanas, com demonstração semanal ao ponto único de contacto do cliente (SPoC). | 17, 30 | Cadência-base: a sexta-feira fecha o ciclo semanal. |
| Alterações: não se aceitam a meio de um ciclo, salvo sem impacto em prazo e orçamento; se tocam num requisito futuro, só com troca por outro requisito. | 32 | Regra de **pedido de alteração** (secção 6, P2). |
| Teste dos quatro filtros para qualquer custom: é mesmo necessário? vale o custo? o ganho é suficiente? há outra via? | 44–46 | Acrescenta-se à ordem de decisão `standard → adicional → custom`. |
| Custo do custom: cerca de 25 % do desenvolvimento **por ano** (≈ 17 % manutenção + ≈ 8 % upgrades); multiplicar o custo inicial por 2–3 em cinco anos. Exemplo: serviço com margem de 35 % passa a perda de 6 % quando as horas derrapam. | 9, 46, 48 | Números a usar em `TPL_PROPOSTA_TECNICA` e `TPL_ORCAMENTO`. |
| Segunda implementação um mês depois do go-live; em geral, 50 % do custom previsto afinal não era necessário. | 34 | Gate de revisão pós-go-live (fase `hypercare` já existe). |
| Disponibilidade e poder de decisão do SPoC condicionam o projeto (caso do CEO indisponível). | 18–20 | Risco a medir desde o arranque: horas por semana do SPoC. |
| Não adiar o go-live; não importar histórico de dados sem justificação. | 33, 41 | Já alinhado com a nossa prática; formalizar no template de janela de manutenção. |

### 3.2 A adaptar

- **"Fewer meetings, less paperwork"** (p. 7): a revisão de sexta tem de ser preparada automaticamente e decidida em poucos minutos por projeto, não um ritual novo de papel.
- **Pontos do percurso do *Project Leader*** (p. 58–60): referência para avaliar maturidade, não para medir pessoas.

### 3.3 A não adotar — e tem de ficar escrito

- **Studio:** a metodologia diz que o *Project Leader* "configura o software, incluindo personalização com a app Studio" (p. 30). **Proibido criar configuração em Studio** em qualquer cliente (decisão de Bruno Pinheiro, 2026-09-11, `AGENTS_SHARED.md`). Ao incorporar a metodologia, esta frase não entra.
- O texto é de 2020 e fala em *Odoo Online* e em versões antigas. `PONTO POR VALIDAR`: se existe versão mais recente do guia.
- O guia descreve a prática da Odoo S.A. (80 *Project Leaders*), não a de um parceiro. **Não diz** quantos projetos simultâneos um gestor deve ter.

---

## 4. O que o curso traz de aplicável

`FACTO OBSERVADO`, com a fonte indicada. Onde o curso não dá número, diz-se.

### 4.1 Capacidade e carga
- A norma de portefólio do PMI (`PMI_Portefolio_Management`, §5.3–5.6, pp. 52–58) trata capacidade em quatro elementos: planeamento, gestão de oferta e procura, otimização da procura, reporte e analítica. Pede lista priorizada de componentes e um **cronograma-mestre de alocação de recursos**, com o objetivo de minimizar tanto a subutilização como a sobreutilização. Identifica **recursos-gargalo** (competências escassas, pedidas por muitos projetos) e a *soft booking* (reservar pessoas pela data de fim esperada de outro projeto, que falha quando há atrasos).
- A mesma norma dá, **como exemplo e não como norma** (Tabela 6-3, p. 72), cadência semanal ou mensal para dashboard do portefólio, riscos e **utilização de recursos**.
- Caso Águas do Porto (`aula2_parte1`, l.13): havia pessoas alocadas a 180 %, 170 % e 150 %, 20 delas acima de 120 %; o problema era "não tinham números". O formador aconselha um **exercício de influência**: perante um novo pedido, mostrar a carga atual.
- Um pedido "já agora" é um novo projeto e deve passar pela qualificação e pela fila de prioridades; sem isso "é ingovernável" (`aula2_parte1`, l.101).
- APDL: 140–150 projetos ativos e 51 % de execução; ProEP: 45–52 % para 75–80 % de execução do portefólio depois de PMO e critérios de capacidade (o formador avisa que não é uma correlação direta). Dado de contexto (HBR 2021): 64 % dos profissionais de projeto acumulam outra função; 85 % viram o número de projetos crescer.
- **O curso não dá**: taxa de utilização-alvo, limite de projetos por pessoa, nem definição de sobre-alocação em %. (Confirmado em todos os relatórios de extração.)

### 4.2 PMO e cadência
- Seis funções do PMO, incluindo "gestão da capacidade, interdependências e sinergias" (P3, sl. 67); três modos: **suporte, controlo, diretivo** (sl. 71); KPIs de PMO (sl. 72): % de projetos com decisão "Go", % no prazo e no orçamento, % de entregas aceites, tempo entre decisão e conclusão.
- *War Room* (Bosch): reuniões de pé, ≤ 30 min, informação comum; duas vezes por semana em projetos curtos, uma nos longos (`aula2_parte4`, l.35–41). Guia Mestre: "ajustar a cadência das reuniões à matéria e às exceções" (🟡 dado de sala).
- Amazon (*Weekly Business Review*): revisão semanal com formato constante, séries de 6 semanas e 12 meses, e **relatório de exceções**; privilegiar métricas de entrada (controláveis) sobre as de saída (desfasadas).
- Aviso de método (Cora, p. 27): reporte "backward-looking" com dados de semanas atrás não serve; é preciso olhar em frente.

### 4.3 Proporcionalidade (A/B/C)
- A classificação em A se **1 dos n critérios** se verificar; critérios típicos: investimento, margem, complexidade, impacto, penalidades por atraso; proporções de referência 25/35/40 %; escalas revistas anualmente (P1, sl. 37–38). "O excesso de burocracia mata os projetos pequenos; a falta de controlo destrói os estratégicos."
- Instrumentos por tipo (formador, `[AULA]`, não nos slides): A = A3, gates, EVM, RACI; B = marcos e plano de riscos simplificado; C = Kanban e lista de tarefas.

### 4.4 Controlo de desempenho
- EVM (`PMI\EVM`): `CV = EV−AC`, `SV = EV−PV`, `CPI = EV/AC`, `SPI = EV/PV`, `EAC = BAC/CPI`, `TCPI = (BAC−EV)/(BAC−AC)`. O padrão **não fixa limiares**: as tolerâncias definem-nas a organização, e a gestão por exceção atua quando são ultrapassadas. O curso dá referências 🟡 de sala (custo −5/+10 %, prazo ±10 %) que **não são norma**.
- Semáforo de desempenho do curso: adiantado e abaixo do custo = verde; um dos dois falhado = amarelo; atrasado e acima do custo = vermelho.
- Precisão das estimativas por fase: ordem de grandeza −25/+50 %, projeto −10/+25 %, realização −5/+10 %; reservas 1–10 % com experiência, 20–60 % em contexto inovador (heurística pedagógica). Esforço ≠ duração.
- Escala de risco do A3: P e I de 1 a 5; verde ≤ 4, vermelho ≥ 12 (os A3 do grupo usam 5–11 como "vigiar"; o curso não define essa zona).

### 4.5 Sucesso e medição (PMI, 2024–2025)
- A alavanca de maior poder preditivo (385 contra 236 da seguinte) é **ter um sistema de medição bem estabelecido**; só 37 % dos projetos têm critérios, sistema e medição ao longo do percurso (NPSS 49 contra 27). Sem causalidade provada.
- Profissionais com mais experiência gerem mais projetos em simultâneo (58 % contra 45 %), mas "cargas excessivas podem diminuir a eficácia e as oportunidades de aprendizagem" (Pulse 2025).
- Standish: a latência de decisão custa cerca de 25 % do custo de um projeto de software; projetos pequenos e iterativos têm muito mais sucesso.

### 4.6 O que o grupo PBS38 aprendeu e vale como regra
"Nenhuma linha sai da reunião sem dono e sem hora"; "uma decisão registada no ledger não se propaga sozinha aos entregáveis já construídos"; relatório de progresso é da reunião, não da proposta. (`07_Simulacao_PBS38`, `12_Revisao_da_Entrega_v2_para_v3.md`.)

### 4.7 Divergências entre fontes do curso — não propagar
Quatro *gates* (Guia Mestre) contra cinco (Glossário); exposição de risco P×I como "valor esperado" (Síntese) contra "só hierarquiza" (Guia Mestre); tolerâncias de desempenho atribuídas ao PMI contra 🟡 de sala. Usar a versão do Guia Mestre.

---

## 5. Estado atual do `_pg_template` (v2.45.1)

`FACTO OBSERVADO` — levantamento com `path:linha`.

**Existe**
- Espelho do Odoo da Parâmetro Global para `.pg/projects/<key>/`: tarefas com `assignees`, `allocated_hours`, `effective_hours`, `progress`, `planned_date_begin/end`, etapa e prioridade (`project_mirror_payload_builder.py:504-529`); marcos com estado de entrega e de aceitação; gestor do projeto (`project_manager`).
- Esforço por colaborador e por linha de timesheet, atualizado no momento do lançamento (`account_analytic_line.py:12-40`).
- Fases de projeto (`discovery … hypercare, support`, `project_project.py:47-56`).
- Templates de ponto de situação, status semanal (semáforo, baseline vs atual, KPIs), orçamento, timesheet (regra do total diário: máximo 7 h 30 por cliente e por dia), RACI, formalização de entregáveis.
- Registo de sessões por agente e operador (`.pg/tokens/consumption.jsonl`); agregação por operador e máquina; ferramentas de frota (`pg_align_fleet_framework.ps1`).
- Canal de dados direto ao Odoo da Parâmetro Global (`pg_odoo_query.ps1`), com chave pessoal por máquina.

**Não existe** (procurado em `pg_brodoo/`, `scripts/`, `templates/`, `docs/`, `doc_templates/`)
- Capacidade, carga, sobre-alocação, utilização, PMO, portefólio, visão entre projetos.
- Leitura de férias (`hr.leave`) ou de planeamento (`planning.slot`). O template de onboarding manda *criar* `planning.slot`, mas nada o lê. Backlog: "Odoo 5864 — disponibilidade da equipa (Planning + Time Off)" (`docs/PG_FRAMEWORK_IMPROVEMENT_BACKLOG.md:73`), por fazer.
- Caminho crítico, EVM, burn rate, baseline congelada de datas e horas, registo persistente de riscos (removido em v2.10.0), lições aprendidas de projeto, encerramento de projeto.
- Qualquer agendamento: o único *workflow* não tem `schedule`; o status semanal é a pedido.
- Agentes ou comandos próprios do framework: só existe uma *skill* (`pg-odoo-navigator`).
- Relatórios, vistas gráficas ou dashboards no `pg_brodoo` (só `form` e `list`; sem JS).

**Defeitos encontrados na análise** (verificados por mim)
1. `PG_EFFORT_SYNC`: o template (`templates/.pg/PG_EFFORT_SYNC.json`) e o validador (`scripts/pg_effort_sync_common.ps1`) exigem `summary.planned_hours_total`, `logged_hours_total`, `remaining_hours_total`, `variance_hours_total` e `workstreams`; o builder do Odoo só emite `effort.total_hours`, `hours_by_employee` e `entries`. O ficheiro publicado não passa o validador.
2. `TPL_STATUS_SEMANAL_INSTRUCOES.md` descreve uma "Secção 12 — Adoção Odoo" e um *workflow* `pg_weekly_status_adoption.yml` que foram cortados em 2026-07-01.
3. `BRODOO_GUIA_OPERACIONAL.md` descreve um "Dashboard Brodoo" cujo modelo foi removido; `MANIFEST.json` traz `framework_version` v2.9.1.

**Dados já disponíveis para calibrar** (memória do projeto, 2026-10-09): projetos industriais e de mobiliário ficam 10–50 % acima do orçado (Triplex 500→677 h, JMM 497→549, HMD 338→511, EPOCA 384→417); os pequenos estouram por múltiplos (CST 84→270, Private-Label 75→449). O mecanismo de fator de risco do Excel de orçamentação nunca tinha sido usado antes de Granatur e Jantes Xavier.

---

## 6. Alterações propostas

Ordem: o que desbloqueia tudo primeiro. Cada item diz o que muda e onde.

### P0 — Fundações (antes de qualquer relatório)

| # | Alteração | Onde |
|---|---|---|
| 0.1 | Alinhar `PG_EFFORT_SYNC` entre builder, template e validador (decidir qual é a fonte: recomendo ajustar o validador ao que o Odoo realmente publica e acrescentar o que falta ao builder só se for usado). | `pg_brodoo/services/project_effort_payload_builder.py`, `scripts/pg_effort_sync_common.ps1`, `templates/.pg/PG_EFFORT_SYNC.json` |
| 0.2 | Limpar documentação desatualizada (secção 12 do status, guia do dashboard, `framework_version` do manifest, specs PG_005 com artefactos removidos). | `doc_templates/` (origem no Knowledge), `docs/` |
| 0.0 | **Limpeza única do quadro** antes de ligar qualquer rotina: por projeto em curso, cada tarefa em sprint ou em curso sem edição há mais de 30 dias é movida, fechada ou devolvida ao *Backlog*; as 66 *Sprint Complete* abertas fecham-se; os projetos sem horas há 4 semanas passam a "Parado" (secção 8.1b). Medir antes e depois com o instantâneo. | Odoo (dados), com lista gerada pelo instantâneo |
| 0.3 | **Definição de pronto de uma tarefa**: toda a tarefa aberta tem responsável, `allocated_hours`, prazo e etapa; toda a pessoa lança horas diariamente. Escrever como regra obrigatória e medir (percentagem de tarefas sem dono/horas/prazo). Sem isto a carga calcula-se sobre o vazio. | `templates/AGENTS_SHARED.md` + medição na secção 6, P1 |
| 0.4 | Exportar para o espelho o que falta para planear: `remaining_hours`, `depend_on_ids`, `parent_id`, `milestone_id`, data de última mudança de etapa (envelhecimento). `PONTO POR VALIDAR`: nomes dos campos em `vendor/odoo_src` v19. | `project_mirror_payload_builder.py:504-529` |

### P1 — Camada de portefólio (o pedido principal)

| # | Alteração | Onde |
|---|---|---|
| 1.1 | **Instantâneo de portefólio** (só leitura, canal Brodoo): por gestor, projetos ativos (`project.project.user_id`), tarefas abertas com horas e prazo, horas lançadas nas últimas semanas por pessoa, férias e planeamento. Regista `read_mode: api`. Fica **fora** dos repositórios de cliente. | novo `scripts/pg_portfolio_snapshot.*` |
| 1.2 | **Comando/skill de revisão de sexta-feira** que corre o instantâneo, aplica o protocolo da secção 7 e devolve o resumo e as ações. Seguir o padrão da *skill* existente e a regra de compatibilidade Codex ↔ Claude (`CLAUDE.md`). | `templates/.agents/skills/pg-revisao-semanal/` + equivalente Claude |
| 1.3 | **Template do documento** (`TPL_REVISAO_SEMANAL_PORTEFOLIO` e instruções), com a lista de exceções, a tabela de carga e a de decisões. Nota: os templates nascem na app Knowledge da Parâmetro Global e são sincronizados por `pg_pull_doc_templates.ps1`; criar primeiro lá. | `doc_templates/` |
| 1.4 | **Secção nova no contrato partilhado**: papel de gestor de projeto, cadência, definições e responsabilidade de manter os dados. Faz o agente comportar-se como gestor também dentro de um repositório de projeto (alerta no arranque da sessão: tarefas vencidas, sem horas, horas gastas contra alocadas, próximo marco). | `templates/AGENTS_SHARED.md` |
| 1.6 | **Medida de atenção e paralelismo** por operador: união dos intervalos de sessão entre repositórios, sobreposição máxima e média, projetos com sessão por dia. Estende `pg_report_token_consumption.ps1`; os dados já são recolhidos pelos hooks. | `scripts/pg_report_token_consumption.ps1` |
| 1.5 | **Histórico de instantâneos** (só acrescenta) para ver tendência e medir a taxa de execução. Onde guardar: decisão 3 da secção 8. | a decidir |

### P2 — Controlo de projeto e do método

| # | Alteração | Onde |
|---|---|---|
| 2.1 | **Segmentação A/B/C** por projeto (campo versionado no `pg_brodoo`, nunca em Studio), que define a profundidade da revisão: A item a item, B por exceção, C por lista. Critérios a definir (secção 8). | `pg_brodoo` (campo + vista) |
| 2.2 | **Baseline congelada** no fecho do GAP/arranque (datas de marcos e horas por fase). Sem baseline não há `SPI`. | `pg_brodoo` ou `.pg/…/baseline.json` |
| 2.3 | **Medidas de saúde do projeto** por semana: horas consumidas contra alocadas e contra o peso da fase (10/5/80/5 como referência), marcos no prazo, previsão de fim, dias de tarefas vencidas. `PONTO POR VALIDAR`: o campo `progress` do Odoo parece calcular-se por horas (INFERENCIA); se assim for, não serve de *earned value* e é preciso um percentual de conclusão por marco. | instantâneo (P1.1) |
| 2.4 | **Regra de pedidos de alteração** com troca obrigatória e teste dos quatro filtros; "estacionamento" pós-go-live. | `templates/AGENTS_SHARED.md`, `TPL_STATUS_SEMANAL` |
| 2.5 | **Disponibilidade do SPoC** (horas por semana) registada no arranque e seguida como risco; reutilizar a coluna "Disponibilidade" que já existe nos templates de âmbito e proposta. | `TPL_LEVANTAMENTO_AMBITO`, `TPL_FORMALIZACAO_CONTRATUAL` |
| 2.6 | **Revisão por pares** no fecho do GAP e antes de enviar proposta ou fit-gap (equivale ao *App Expert*); o modo challenger existente fica como primeira passagem. | `docs/PG_CHALLENGER_PROMPT.md`, contrato |
| 2.7 | **Escala de risco única** (1–5, ≤ 4 verde, 5–11 amarelo, ≥ 12 vermelho) e **top-5 de riscos** na revisão, reutilizando tarefas etiquetadas em vez de recriar o registo removido em v2.10.0. | templates de status |

### P3 — Aprender com cada projeto

| # | Alteração | Onde |
|---|---|---|
| 3.1 | **Fecho de projeto** (A3 de avaliação e fecho do curso: lições, objetivos e sustentabilidade, encerramento com aceitação formal) e **revisão aos 30 dias** do go-live (p. 34 da metodologia). | novo `TPL_ENCERRAMENTO_PROJETO` |
| 3.2 | **Calibração de orçamentos** como processo: horas orçadas contra realizadas por categoria no fecho; preencher o fator de risco do Excel com os dados da frota; linha explícita de gestão de projeto no orçamento ("é gratuito?"); intervalos de precisão por fase na proposta. | `TPL_ORCAMENTO` |
| 3.3 | **Lições de projeto** num registo próprio, separado de `PG_PROJECT_LEARNINGS.md` (hoje só técnico). | `docs/` |
| 3.4 | **Verificação de cumprimento de timesheet**: dias com sessões de agente e sem horas lançadas (reutiliza `.pg/tokens` e a regra do total diário já escrita). Opcional e de baixa prioridade. | instantâneo |

---

## 7. A revisão de sexta-feira

**Regra (decisão da direção, 2026-10-10): todas as sextas-feiras, cada pessoa pára e gere os seus projetos.** É um bloco protegido na agenda, não uma boa prática opcional. Sem ele o quadro volta ao estado de hoje (secção 2b) e os atrasos descobrem-se quando o cliente reclama.

Duas camadas, no mesmo bloco:

| Parte | Quem | Duração-alvo | Conteúdo |
|---|---|---|---|
| **A. O meu quadro** | **todas as pessoas** que trabalham em projetos | 45 min | atualizar as próprias tarefas: dono, horas, prazo, etapa; fechar o que está feito; retirar do sprint o que não vai ser feito; lançar horas em falta |
| **B. Os meus projetos** | **cada gestor de projeto**, sobre os projetos que gere | 45 a 60 min | semáforos, previsão de fim, bloqueios, pedidos de alteração, decisões e escalamentos |

Custo: 90 a 105 min por pessoa e por semana, cerca de 4 a 5 % das 37,5 h. Com 11 pessoas, cerca de 17 a 19 h semanais da equipa. `INFERENCIA`: é o preço da visibilidade que hoje não existe; deve comparar-se com o custo de um atraso descoberto pelo cliente. As **duas primeiras sextas** (limpeza do quadro, item 0.0) pedem 2 a 3 h por pessoa.

Preparação automática e sessão de decisão curta, no estilo *War Room*. Quem não fez a Parte A **não entra** na Parte B: o semáforo de um projeto cujo quadro está por atualizar não vale nada.

0. **Preparação (automática, sexta de manhã):** instantâneo com tudo o que se segue.
1. **Higiene (10 min):** fechar tarefas sem dono, horas ou prazo; confirmar que as horas da semana estão lançadas. O instantâneo marca esses itens como **"carga desconhecida"**, nunca como zero (a mesma regra do `odoo_env.json`: vazio é "não sei").
2. **Carga própria e da equipa (15 min):** horas por semana nas próximas 4 semanas contra a capacidade disponível; semanas e pessoas acima do limite; recursos-gargalo. Decisões: adiar, redistribuir, pedir apoio, recusar entrada de pedido novo (exercício de influência).
3. **Projetos (30–50 min, por tipo):** A todos; B só amarelos e vermelhos; C por lista. Por projeto: semáforo de prazo e de horas, previsão de fim, bloqueios, pedidos de alteração pendentes, disponibilidade do SPoC, próximo marco.
4. **Decisões e escalamentos (10 min):** cada linha sai com **dono e hora**; fica registada no projeto (nota no chatter por `pg_odoo_post_chatter.py`, com o conversor correto de markdown).
5. **Saída:** resumo por projeto para o *chatter* e uma síntese do gestor. À segunda, síntese entre gestores para a direção: carga por pessoa, projetos em vermelho, taxa de execução, pedidos novos à espera de prioridade.

Porque sexta-feira: fecha o ciclo semanal da metodologia Odoo (demonstração e entrega semanais) e é o último dia para lançar horas da semana.

---

## 8. Modelo de carga e decisões em aberto

### 8.1 Definições adotadas e modelo proposto

**Decisão da direção (2026-10-10):** as horas lançadas no Odoo medem **trabalho feito para o cliente**, não tempo de pessoa. O **tempo de pessoa é de 7 h 30 por dia** (o horário), ou 37,5 h por semana, menos ausências.

Daqui saem dois livros que **não se misturam**:

| | Horas de cliente (HC) | Tempo de pessoa (TP) |
|---|---|---|
| O que mede | trabalho entregue por projeto e cliente | tempo da pessoa, fixo |
| Valor por dia | **sem teto**: com agentes pode passar de 7,5 h | **7,5 h** |
| Onde está | timesheet (`account.analytic.line`) | calendário de recursos e Time Off; sessões em `.pg/tokens` para a repartição |
| Serve para | orçamento, faturação, desvio de horas por projeto | capacidade, dispersão, ausências |

**Alavancagem** = HC ÷ TP (`INFERENCIA`, indicador novo). Na janela de 4 semanas, sem descontar ausências: **cerca de 2,4 para uma pessoa e cerca de 0,9 para as outras dez** (entre 0,7 e 1,0 de HC por hora de TP). Isto lê-se assim: a maioria lança menos de 7,5 h de cliente por dia, o resto do tempo é interno, comercial, reuniões ou por lançar. **Uma alavancagem acima de 1 não é um alarme por si só**; é o ganho de trabalhar com agentes. O alarme está na dispersão e nos prazos.

Modelo de carga, em dois eixos:

1. **Compromisso (em HC):** soma, por tarefa aberta atribuída, das `remaining_hours` repartidas entre hoje e o prazo (tarefas vencidas carregam sobre a semana corrente), contra o orçado e prometido. Mede se o que prometemos cabe nas datas. Tarefas sem horas ou sem prazo entram numa coluna "desconhecida", com contagem. Não se divide por 37,5 h: o teto de HC por pessoa **não é** o horário.
2. **Atenção (em TP):**
   - **projetos com trabalho ativo por pessoa e por semana** (WIP) e **projetos no mesmo dia**, a partir do timesheet;
   - **repartição do tempo de pessoa por projeto**: o tempo real de sessão de cada operador (união dos intervalos entre repositórios, `.pg/tokens`) dividido pelas sessões simultâneas. É uma estimativa, não uma medição; reuniões e deslocações vêm declaradas pelo utilizador (já previsto no Passo 1A do timesheet);
   - **decisões e revisões pendentes** (tarefas à espera de resposta).
3. **Limites** (WIP por pessoa, decisões pendentes, tolerâncias): o curso e a metodologia **não dão valores**; são decisão da direção. Ponto de partida: hoje 3 a 26 projetos por pessoa em 4 semanas e 2 a 10 projetos por dia.

### 8.1b Valores iniciais propostos (para discussão)

`INFERENCIA`. Calibrados pelo que a equipa faz hoje (percentis 75 e 90, projetos Odoo, 2026), **não pelo ideal**: descrevem o ponto de partida. Convém apertá-los depois de 4 a 8 semanas de revisão.

| Medida | Hoje | Proposta |
|---|---|---|
| Projetos com 4 h ou mais na semana, por pessoa | mediana 2, p90 4 | meta 3, teto 4 |
| Projetos por pessoa e por dia | mediana 2, p90 5 | meta 2, alerta acima de 4 |
| Projetos em curso por gestor | de 4 a 16; 17 sem gestor | meta 12, teto 15; sem gestor 0 |
| Horas consumidas ÷ alocadas | 12 projetos acima de 120 % | verde até 80 %, amarelo até 110 %, vermelho acima de 110 % |
| Tarefas em sprint com responsável, horas e prazo | 18 % | 55 % às 4 semanas, 90 % às 8 |
| Tarefas em sprint com prazo vencido | 13 % | 8 % às 4 semanas, 5 % às 8 |
| Projetos «Parados» (sem horas há 4 semanas) | 28 | decisão mensal |

**Semáforo de prazo:** não é possível calibrar (11 projetos em curso sem data de fim, sem baseline). Regra provisória: amarelo até 10 dias úteis de atraso na previsão, vermelho acima de 10 dias úteis ou com o go-live em risco. **Decisões pendentes por pessoa:** sem dados; medir 4 semanas com uma etiqueta «aguarda decisão» antes de fixar limite. **Alavancagem (horas de cliente ÷ tempo de pessoa):** sem limite; rever a pessoa quando for superior a 2 e tiver mais de 4 projetos relevantes na semana.

**Função de suporte (proposta):** quem a ocupa dedica 30 a 35 % do tempo a suporte e tem meta 2 e teto 3 projetos relevantes, contra 3 e 4 para os restantes.

---

### 8.2 Decisões de que precisamos

1. **Onde corre e onde se guarda a revisão?** Opções: (a) repositório interno "PMO" bootstrapado como projeto da framework (histórico versionado, sessões contadas); (b) pasta de trabalho declarada com `pg_init_work_folder.ps1`; (c) tudo em Odoo (nota por projeto e artigo no Knowledge). Recomendo (a) com publicação das notas em Odoo.
2. ~~Horas de cliente ou tempo de pessoa~~ — **decidido**: horas lançadas = trabalho para o cliente; tempo de pessoa = 7 h 30 por dia. Ficam por decidir os **limites**: projetos com trabalho ativo por pessoa por semana (WIP), decisões pendentes por pessoa, e tolerâncias de prazo e de horas para os semáforos.
3. **Critérios A/B/C** (investimento, horas orçadas, risco, fase próxima do go-live, cliente estratégico) e quem classifica.
4. ~~Que apps estão instaladas~~ — **respondido na secção 2b**: Planning, Project Planning, Time Off e Timesheets estão instalados. Fica a decisão de **adotar o Planning standard como fonte da carga prospetiva** (e quem passa a mantê-lo), em vez de calcular a carga só a partir de horas de tarefas.
5. **Quem é o "Project Director"** nos projetos A e quem faz de *App Expert*.
6. **Função de responsável de suporte Odoo** (secção 2b, Suporte): quem a ocupa, com que percentagem de tempo (proposta: 30 a 35 %), com que limite de projetos próprios (meta 2, teto 3), com que SLA e onde entram os pedidos (Helpdesk da equipa Odoo ou tarefa de projeto de suporte, sempre com horas).

### 8.3 Pontos por validar

- Qualidade dos dados de origem: percentagem de tarefas abertas com responsável, horas e prazo, e de pessoas com horas lançadas por dia. **É o primeiro risco do plano.** Sugiro que a Fase 0 seja medir isto.
- Se `progress` de `project.task` é por horas (INFERENCIA).
- Nomes de campos v19 para o P0.4.
- Se `read_mode: api` em massa (todos os projetos, todas as semanas) é aceitável como custo do canal Brodoo, e a dependência dos endpoints `/jsonrpc` que saem no Odoo 22 (issue #56).
- A chave da Brodoo é lida por qualquer utilizador de projeto até o `pg_brodoo` 19.0.1.15.0 ser instalado; o instantâneo só lê, mas cruza dados de todos os clientes.

---

## 9. Plano por fases

| Fase | Conteúdo | Resultado |
|---|---|---|
| 0 — Medir (**feita em 2026-10-10**, secção 2b) | Apps instaladas; percentagem de tarefas com dono, horas e prazo; cobertura de timesheet; horas por pessoa. Por fazer: associação empregado→calendário e esclarecer a anomalia de horas. | Primeira fotografia real. |
| 1 — Fundações | P0.1 a P0.4. | Contrato de esforço coerente e regras de higiene escritas. |
| 2 — Revisão manual assistida | P1.1 a P1.4, com um gestor-piloto e 5 a 10 projetos. | Primeira sexta-feira com instantâneo e protocolo. |
| 3 — Escala e controlo | P2.1 a P2.7; extensão a todos os gestores; síntese de segunda-feira. | Carga e saúde de todos os projetos, por exceção. |
| 4 — Agendar e aprender | Agendamento da preparação; P3.1 a P3.4. | Rotina sem intervenção, calibração de orçamentos, fecho de projetos. |

---

## 10. Referências

- Curso: `01_Aulas`, `_kb\txt\CGP_vf_P1–P6`, `04_Entregaveis\Guia_Mestre_Gestao_Projetos.md`, `06_Audio\Transcricoes\aula1_parte1–5`, `aula2_parte1–6`, `aula3_parte1–4`, `_kb\txt\PMI\PMI_Portefolio_Management`, `PMI\EVM`, `PMO\next-generation-pmo`, `PMI_Sucess`, `PMI_Pulse`, `HBR-Project-Management-Research`, `EndlessModernization`, `Stage_Gate_Framework\PDI_Idea-to-Launch`, `brief-summary-of-working-backwards`, `07_Simulacao_PBS38`.
- Odoo: *Implementation Methodology* (PDF, 69 páginas), `https://www.odoo.com/web/content/17936384`.
- Framework: `templates/AGENTS_SHARED.md`, `pg_brodoo/services/*`, `doc_templates/TPL_STATUS_SEMANAL_V1.md`, `TPL_TIMESHEET_INSTRUCOES.md`, `TPL_ORCAMENTO.md`, `docs/PG_FRAMEWORK_IMPROVEMENT_BACKLOG.md`, `CHANGELOG.md`.
