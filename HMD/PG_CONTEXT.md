# PG_CONTEXT - Contexto Global do Projeto

> Artefacto derivado exclusivamente do espelho `.pg` publicado a partir do Odoo.
> Serve como contexto consolidado para leitura humana e para agentes AI.

## 1. Contexto Estrutural

- Projeto: Odoo - HMD
- Cliente: HMD INTERIORS- EDIÇÃO PRODUÇÃO DE MOBILIARIO LDA
- Gestor: João Barros
- Repositorio: joao-barros-pg/HMD
- Branch: main
- Fase atual: N/A
- Etapa atual: In Progress
- Ultimo sync do espelho: 2026-05-25 16:10:11

### Objetivo e pedido atual

Objetivo do projeto: Consolidar e evoluir adaptações Odoo que ligam venda, compra, produção e publicação web de produtos/projetos, melhorando rastreabilidade e reduzindo operação manual

Pedido atual: N/A

- Unidade do cliente: HMD INTERIORS - EDIÇÃO PRODUÇÃO DE MOBILIARIO LDA

### Ambito incluido

Vendas/orçamentos
cálculo de preço/margem
compras/RFQs
ligação venda-compra-produção
MRP/BOMs/tecidos/consumos
imagens/anexos/PDFs
eCommerce
modelos 3D
CRM/projetos
adiantamentos e descontos
Servidor JLL subscrição /M /
Template de lista de preços meter também a quantidade mínima do produto Inserir os preços das variáveis manualmente - Os preços vão depender de mais do que uma variante Adicionar módulo de campo de CC aos emails

### Itens factuais a curar no Odoo

- Total no ambito curado: 209
- Total pendente de curadoria: 0
- Ruido excluido na curadoria: 0
Motivos dominantes de curadoria pendente:
- N/A
- N/A

### Ambito excluido

Migração histórica de dados, integrações externas, alteração do core Odoo/vendor, redesenho completo do website e decisões contratuais ainda não validadas

### Entregaveis

Repositório HMD ligado ao framework PG; contexto inicial de projeto; catálogo de addons; validação funcional por área; lista de riscos, pendências e próximos passos
M1 — Sprint Imediato
M2 — Estabilização Comercial & QC
M3 — Funcionalidades Avançadas
M4 — Preparação Upgrade Odoo 19
M5 — Upgrade Produção & Fecho de Projeto

### Restricoes e pressupostos

Restricoes:
Não alterar vendor/odoo_src; confirmar restrições no PG_CONTEXT.md; priorizar standard > módulo standard > Studio > custom; manter customizações compatíveis com upgrade

Pressupostos:
Odoo 18.0 Enterprise On-Premise; standard, módulos adicionais, Studio e custom permitidos conforme onboarding; validação funcional feita com HMD/João Barros

Stakeholders:
HMD INTERIORS- EDIÇÃO PRODUÇÃO DE MOBILIARIO LDA
João Barros

### Contrato e Parametros Odoo

> Parametros lidos do Odoo. Os agentes AI devem respeitar estas restricoes em todas as respostas.

- Versao Odoo: 18.0
- Edicao: enterprise
- Ambiente: on_premise
- Configuracao standard: PERMITIDO
- Modulos standard adicionais: PERMITIDO
- Odoo Studio: PERMITIDO
- Desenvolvimento custom: PERMITIDO
- Restricoes adicionais: Não alterar vendor/odoo_src; confirmar restrições no PG_CONTEXT.md; priorizar standard > módulo standard > Studio > custom; manter customizações compatíveis com upgrade

## 2. Planeamento

- Total de marcos: 5
- Proxima etapa/marco: M2 — Estabilização Comercial & QC
- Target da proxima etapa: 2026-06-30
- Owner da proxima etapa: N/A
- Tasks abertas no projeto: 38
- Tasks abertas para a proxima etapa: 13

### Marcos planeados

- M1 — Sprint Imediato | estado: N/A | owner: N/A | target: 2026-06-15
- M2 — Estabilização Comercial & QC | estado: N/A | owner: N/A | target: 2026-06-30
- M3 — Funcionalidades Avançadas | estado: N/A | owner: N/A | target: 2026-09-30
- M4 — Preparação Upgrade Odoo 19 | estado: N/A | owner: N/A | target: 2026-10-31
- M5 — Upgrade Produção & Fecho de Projeto | estado: N/A | owner: N/A | target: 2027-01-15

### O que falta para atingir a proxima etapa

- [W2] Confirmar acerto contratual O365 / alojamento com Cláudio | etapa: Backlog | prioridade: 0 | responsaveis: Sem responsavel
- [P5] Verificar espelhamento item venda → tarefa projeto (1 SOL = 1 task) | etapa: Backlog | prioridade: 0 | responsaveis: Sem responsavel
- [P6] Vista agregada tarefas entre projetos por etapa operacional | etapa: Backlog | prioridade: 0 | responsaveis: Sem responsavel
- [V1] Templates de cotação por linha de produto (sale.order.template) | etapa: Backlog | prioridade: 0 | responsaveis: Sem responsavel
- [V8] Botão IDU — impressão direta única para encomendas e faturas | etapa: Backlog | prioridade: 0 | responsaveis: Sem responsavel
- [Q1] Configurar painel QC com filtros guardados + kanban | etapa: Backlog | prioridade: 0 | responsaveis: Sem responsavel
- [Q2] Criar atalho mobile criação espontânea QC no terreno | etapa: Backlog | prioridade: 0 | responsaveis: Sem responsavel
- [C1] Instalar account_loans + importar empréstimos históricos até 2026 | etapa: Backlog | prioridade: 0 | responsaveis: Sem responsavel
- + 2 adicionais

### Proximas prioridades abertas

- N/A

## 3. Operacao Atual

- Total de tarefas espelhadas: 222
- Tarefas abertas: 38
- Go-live alvo: N/A

### Resumo operacional

Estado operacional reportado: Project currently in stage In Progress. Open tasks: 38. Next milestone: M2 — Estabilização Comercial & QC.

### Principais tarefas abertas

- [P1+P2+P3] Reformular fases projeto HMD — 3 fases globais + fases tarefa + 4 templates | etapa: Sprint Backlog | prioridade: 1 | responsaveis: Sem responsavel
- [V2] Configurar Spreadsheet Calculator de transportes | etapa: Sprint Backlog | prioridade: 1 | responsaveis: Sem responsavel
- [C5] Reformular template QWeb recibo de adiantamento | etapa: Sprint Backlog | prioridade: 1 | responsaveis: Sem responsavel
- [V3] Levantar pré-requisitos WhatsApp Business (conta Meta + número dedicado) | etapa: Sprint Backlog | prioridade: 1 | responsaveis: Sem responsavel
- [v19] Aprovar instalação WhatsApp enterprise (custos Meta) — decisão cliente | etapa: Sprint Backlog | prioridade: 1 | responsaveis: Sem responsavel
- [v19] Upgrade produção Odoo 18→19 + go-live (janela Dez/Jan) | etapa: Backlog | prioridade: 1 | responsaveis: Sem responsavel
- Pedir Cotação para SH | etapa: Backlog | prioridade: 0 | responsaveis: Cláudio Pereira
- [C6] Gravar vídeo: fluxo pagamentos sem fatura (IRS / IVA / SS) | etapa: Sprint Backlog | prioridade: 0 | responsaveis: Sem responsavel
- [V5] Cleanup contactos PHC vs Odoo — pedir extracção + script matching | etapa: Sprint Backlog | prioridade: 0 | responsaveis: Sem responsavel
- [W2] Confirmar acerto contratual O365 / alojamento com Cláudio | etapa: Backlog | prioridade: 0 | responsaveis: Sem responsavel
- + 28 adicionais

## 4. Comunicacoes e Historico Recente

- Mensagens espelhadas: 607
- Mensagens com cliente: 450
- Notas internas: 157
- Anexos espelhados: 431

### Comunicacoes recentes com cliente

- [2026-05-20 11:19:11] HMD INTERIORS- EDIÇÃO PRODUÇÃO DE MOBILIARIO LDA - <p> </p> <div style="font-family:Aptos, Aptos_EmbeddedFont, Aptos_MSFontService, Calibri, Helvetica, sans-serif; font-size:12pt; color:rgb(0, 0, 0)"> <span style="font-family:Ap... | anexos: 5
- [2026-05-18 08:29:22] João Barros - <p>Bom dia Nina,<br><br>O valor dessa fatura será os 2617.80€ correto?<br>Se for esse o caso, em anexo envio 3 imagens:<br>1- O valor no SAF-T<br>2- O valor na impressão PDF<br>... | anexos: 3
- [2026-05-08 15:06:43] HMD INTERIORS- EDIÇÃO PRODUÇÃO DE MOBILIARIO LDA, Sérgio Pinto - <p> </p> <div> <p><span style='font-size:11.0pt; font-family:"Calibri",sans-serif'>Ok, Obrigado.</span></p> <p><span style='font-size:11.0pt; font-family:"Calibri",sans-serif'>&... | anexos: 5

### Notas internas recentes

- [2026-05-21 10:52:40] João Barros - <span><a href="/odoo/res.partner/15519" class="o_mail_redirect" data-oe-id="15519" data-oe-model="res.partner" target="blank">@Pedro Coelho</a> Está aqui o plano</span> | anexos: 1
- [2026-04-23 10:19:31] João Barros - <a href="/odoo/res.partner/132859" class="o_mail_redirect" data-oe-id="132859" data-oe-model="res.partner" target="blank">@Lara Cunha</a> | anexos: 1
- [2026-04-22 09:55:59] Nuno Oliveira - <span><a href="/odoo/res.partner/15433" class="o_mail_redirect" data-oe-id="15433" data-oe-model="res.partner" target="blank">@HMD INTERIORS- EDIÇÃO PRODUÇÃO DE MOBILIARIO LDA</... | anexos: 1

### Metadata de anexos recentes

- PLANO_2026Q2_HMD.md | tipo: text/markdown | origem: project.task:5572
- HMD_REUNIAO_20_05_26_PG.docx | tipo: application/vnd.openxmlformats-officedocument.wordprocessingml.document | origem: project.task:5572
- Reunião com Parâmetro + João Barros.docx | tipo: application/vnd.openxmlformats-officedocument.wordprocessingml.document | origem: project.task:5572
- + 60 adicionais

### Historico simples recente

- [2026-05-25 16:11:15] task.updated | Task updated and mirrored to the repository context. [project.task:5670] | origem: project.task:5670
- [2026-05-15 09:49:20] project.updated | Project context updated and mirrored to the repository. [project.project:93] | origem: project.project:93
- [2026-05-15 10:51:31] project.updated | Project context updated and mirrored to the repository. [project.project:93] | origem: project.project:93
- + 26 adicionais

Path do core: C:\Users\Utilizador\.pg\odoo_src\18.0\community
Path source Enterprise: C:\Users\Utilizador\.pg\odoo_src\18.0\enterprise