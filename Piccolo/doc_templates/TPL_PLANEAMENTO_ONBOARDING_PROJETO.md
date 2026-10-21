# 
TPL_PLANEAMENTO_ONBOARDING_PROJETO.md

# TPL_PLANEAMENTO_ONBOARDING_PROJETO.md

# Template — Planeamento, Estruturação de Tarefas e Onboarding de Projetos (Brodoo)

## Finalidade
Instrução e modelo operacional para automação de arranque de projeto no Odoo: estruturação de marcos (*milestones*), decomposição analítica de tarefas com horas alocadas, agendamento em Gantt, planeamento de recursos (*planning slots*), registo de *timesheets* de gestão e execução do assistente **Brodoo Onboarding** (`pg.ai.onboarding.wizard`).

## Quando aplicar
Sempre que o utilizador solicitar "faz o planeamento do projeto", "faz o onboarding", "estrutura as tarefas e marcos no Odoo" ou instruir o arranque de um novo projeto a partir de uma proposta, reunião ou levantamento.

---

## Instruções para o Agente AI

### 1. Levantamento e Estruturação de Escopo
1. Identificar o ID e nome do projeto (`project.project`), cliente e gestor de projeto.
2. Analisar o histórico, propostas comerciais ou emails do cliente para extrair:
   - Objetivo de negócio e desencadeador (*trigger*).
   - Versão, Edição (Enterprise/Community) e Alojamento (Odoo.sh, SaaS, On-Premise).
   - Regras contratuais: Standard permitido, Módulos adicionais, Studio e Desenvolvimento Custom.
   - Âmbito incluído, âmbito excluído, pressupostos, restrições e stakeholders.
3. Decompor o projeto em **4 a 6 Milestones principais** e **Tarefas granulares** com estimativa de horas alocadas (`allocated_hours`).

---

### 2. Automação no Odoo via API (XML-RPC / JSON-RPC)

#### A. Criação de Milestones (`project.milestone`)
- Garantir `allow_milestones = True` no `project.project`.
- Criar os registos em `project.milestone` com `name`, `sequence`, `deadline` e `project_id`.

#### B. Criação e Agendamento de Tarefas (`project.task`)
- Criar as tarefas com os campos:
  - `name`: Nome padronizado (ex: `T1.1 — `)
  - `project_id`: ID do projeto
  - `milestone_id`: ID do marco associado
  - `allocated_hours`: Horas estimadas
  - `planned_date_begin` e `date_deadline`: Datas de início e fim no formato `YYYY-MM-DD HH:MM:SS` (para visibilidade no Gantt)
  - `user_ids`: Atribuição ao gestor/técnico responsável
  - `description`: Atividades e critérios de aceitação formatados em HTML
  - `depend_on_ids`: Encadeamento de dependências sequenciais

#### C. Registo no Módulo de Planeamento (`planning.slot`)
- Criar os turnos no modelo `planning.slot` com:
  - `project_id`, `employee_id`, `resource_id`
  - `start_datetime` e `end_datetime` (cobrindo a janela do projeto)
  - `allocated_hours` total correspondente
  - `state = 'published'`

#### D. Registo da Folha de Horas de Gestão (`account.analytic.line`)
- Registar o tempo despendido no planeamento na tarefa de "Gestão de Projeto" (`project.task`):
  - `project_id`, `task_id`, `employee_id`, `user_id`, `date`, `unit_amount`, `name`.

---

### 3. Preenchimento e Execução do Brodoo Onboarding (`pg.ai.onboarding.wizard`)
1. Instanciar o wizard `pg.ai.onboarding.wizard` no contexto do projeto (`active_id = project_id`).
2. Preencher os campos obrigatórios e contextuais:
   - `client_unit`, `odoo_version`, `odoo_edition`, `odoo_environment`, `urgency`
   - `standard_allowed`, `additional_modules_allowed`, `studio_allowed`, `custom_allowed`
   - `trigger_text`, `frequency_text`, `volumes_text`
   - `project_summary`, `project_objective`
   - `scope_included_text` (1 item por linha)
   - `scope_excluded_text` (1 item por linha)
   - `assumptions_text` (1 item por linha)
   - `restrictions_text` (1 item por linha)
   - `stakeholders_text` (1 stakeholder por linha)
   - `milestones_text` (1 marco por linha)
3. Invocar `action_validate_publish_readiness` para validar os acessos GitHub e parâmetros.
4. Invocar `action_apply_onboarding` para aplicar a configuração ao projeto e sincronizar o espelho do repositório.
5. Executar o ritual de checkout/sync da branch `brodoo` para atualizar os artefactos locais (`.pg/`).

---

## Estrutura Padronizada de Milestones e Tarefas (Exemplo de Implementação)

| Milestone | Tarefas Principais | Estimativa Típica |
| :--- | :--- | :---: |
| **M1 — Onboarding, Acessos e Ambiente de Testes (Staging)** | • Validação de acessos GitHub/Odoo.sh
• Provisionamento de branch Staging e restauro de backup | 6h |
| **M2 — Análise de Módulos, Certificação Fiscal & Parametrização** | • Auditoria de código e módulos customizados
• Instalação/configuração de Certificação PT / Legislação
• Parametrização fiscal (Séries, ATCUD, SAF-T)
• Validação de layouts de relatórios/documentos | 14h |
| **M3 — Testes Integrados e Validação Funcional (UAT)** | • Testes técnicos de hashes, encadeamento e SAF-T
• Sessões de aceitação do utilizador (UAT)
• Reunião de fecho e aprovação formal de Go-Live | 8h |
| **M4 — Transição Real (Go-Live) e Acompanhamento** | • Corte final e migração para Produção
• Ativação e verificação de séries oficiais definitivas
• Suporte pós-arranque e acompanhamento (Hypercare) | 8h |

---

## Critérios de Sucesso
- [ ] Projeto configurado com `allocated_hours` global.
- [ ] Milestones criadas com prazos (*deadlines*).
- [ ] Todas as tarefas visíveis no Gantt (datas início/fim, responsáveis e dependências).
- [ ] Planeamento (*Planning Slots*) publicado com as horas globais alocadas.
- [ ] Timesheet de arranque registado na tarefa de Gestão de Projeto.
- [ ] Brodoo Onboarding validado (`done`) e gravado no projeto.
- [ ] Branch `brodoo` sincronizada no repositório local.
