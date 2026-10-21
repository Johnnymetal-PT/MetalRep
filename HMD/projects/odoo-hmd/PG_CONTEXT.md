# PG_CONTEXT - Contexto Global do Projeto

> Artefacto derivado exclusivamente do espelho `.pg` publicado a partir do Odoo.
> Serve como contexto consolidado para leitura humana e para agentes AI.

## 1. Contexto Estrutural

- Projeto: Odoo - HMD
- Cliente: HMD INTERIORS- EDIÇÃO PRODUÇÃO DE MOBILIARIO LDA
- Gestor: João Barros
- Repositorio: parametroglobaladmin/HMD
- Branch: brodoo
- Fase atual: N/A
- Etapa atual: In Progress
- Ultimo sync do espelho: 2026-10-21 13:15:12

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

- Total no ambito curado: 288
- Total pendente de curadoria: 0
- Ruido excluido na curadoria: 0
Motivos dominantes de curadoria pendente:
- N/A
- N/A

### Ambito excluido

Migração histórica de dados, integrações externas, alteração do core Odoo/vendor, redesenho completo do website e decisões contratuais ainda não validadas

### Entregaveis

M1 — Sprint Imediato
M2 — Estabilização Comercial & QC
M3 — Funcionalidades Avançadas
M4 — Preparação Upgrade Odoo 19
M5 — Upgrade Produção & Fecho de Projeto

### Restricoes e pressupostos

Restricoes:
Não alterar vendor/odoo_src; confirmar restrições no PG_CONTEXT.md; priorizar standard > módulo standard adicional > desenvolvimento custom versionado; Odoo Studio PROIBIDO (decisão Bruno Pinheiro, 2026-09-11); manter customizações compatíveis com upgrade

Pressupostos:
Odoo 18.0 Enterprise On-Premise; standard, módulos adicionais e custom versionado permitidos conforme onboarding; Odoo Studio proibido desde 2026-09-11 (decisão Bruno Pinheiro, regressão no givachoice); validação funcional feita com HMD/João Barros

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
- Odoo Studio: NÃO PERMITIDO
- Desenvolvimento custom: PERMITIDO
- Restricoes adicionais: Não alterar vendor/odoo_src; confirmar restrições no PG_CONTEXT.md; priorizar standard > módulo standard adicional > desenvolvimento custom versionado; Odoo Studio PROIBIDO (decisão Bruno Pinheiro, 2026-09-11); manter customizações compatíveis com upgrade

## 2. Planeamento

- Total de marcos: 5
- Proxima etapa/marco: M3 — Funcionalidades Avançadas
- Target da proxima etapa: 2026-11-13
- Owner da proxima etapa: N/A
- Tasks abertas no projeto: 23
- Tasks abertas para a proxima etapa: 3

### Marcos planeados

- M1 — Sprint Imediato | estado: planned | owner: N/A | target: 2026-06-15
- M2 — Estabilização Comercial & QC | estado: planned | owner: N/A | target: 2026-09-30
- M3 — Funcionalidades Avançadas | estado: planned | owner: N/A | target: 2026-11-13
- M4 — Preparação Upgrade Odoo 19 | estado: planned | owner: N/A | target: 2027-03-31
- M5 — Upgrade Produção & Fecho de Projeto | estado: planned | owner: N/A | target: 2027-05-31

### O que falta para atingir a proxima etapa

- [DATA] Investigar importação de saldos iniciais e histórico de faturação por cliente (PHC → Odoo) e data de corte | etapa: Sprint Backlog | prioridade: 0 | responsaveis: Sem responsavel
- [FORM] Reunião final de entrega do projeto com demonstração ponta a ponta | etapa: Backlog | prioridade: 0 | responsaveis: Sem responsavel
- [INV] Desenho dos fluxos de inventário e subcontratação com a HMD | etapa: Sprint in Progress | prioridade: 0 | responsaveis: Sem responsavel

### Proximas prioridades abertas

- Gestão de Projeto | etapa: Sprint Backlog | prioridade: 3 | responsaveis: Sem responsavel

## 3. Operacao Atual

- Total de tarefas espelhadas: 313
- Tarefas abertas: 23

### Principais tarefas abertas

- Gestão de Projeto | etapa: Sprint Backlog | prioridade: 3 | responsaveis: Lara Cunha
- [v19] Upgrade produção Odoo 18→19 + go-live (janela Dez/Jan) | etapa: Backlog | prioridade: 1 | responsaveis: Vitor Costa
- [ART] Modelação de acabamentos, tampos e kits — Too Simple D80, microcimento e variante de variante | etapa: Sprint Backlog | prioridade: 1 | responsaveis: Lara Cunha
- [FORM] Guia e formação do fluxo CRM → Projeto → Inventário | etapa: Sprint Backlog | prioridade: 1 | responsaveis: Sem responsavel
- [W2] Confirmar acerto contratual O365 / alojamento com Cláudio | etapa: Backlog | prioridade: 0 | responsaveis: Sem responsavel
- [v19] Decisão go/no-go upgrade Odoo 18→19 — aprovação cliente | etapa: Backlog | prioridade: 0 | responsaveis: Lara Cunha
- [v19] Clone tenant HMD para ambiente de testes + correr upgrade v19 | etapa: Backlog | prioridade: 0 | responsaveis: Vitor Costa
- [v19] Refactor módulos custom para compatibilidade Odoo 19 | etapa: Backlog | prioridade: 0 | responsaveis: Sem responsavel
- [DATA] Investigar importação de saldos iniciais e histórico de faturação por cliente (PHC → Odoo) e data de corte | etapa: Sprint Backlog | prioridade: 0 | responsaveis: Joao Castro, Lara Cunha
- [FORM] Reunião final de entrega do projeto com demonstração ponta a ponta | etapa: Backlog | prioridade: 0 | responsaveis: Lara Cunha
- + 13 adicionais

## 4. Comunicacoes e Historico Recente

- Mensagens espelhadas: 1499
- Mensagens com cliente: 1012
- Notas internas: 487
- Anexos espelhados: 1063

### Comunicacoes recentes com cliente

- [2026-08-05 17:07:09] HMD INTERIORS- EDIÇÃO PRODUÇÃO DE MOBILIARIO LDA - <div style="font-family:Aptos, Aptos_EmbeddedFont, Aptos_MSFontService, Calibri, Helvetica, sans-serif; font-size:12pt; color:rgb(0, 0, 0)"> Boa tarde Pedro,</div> <div style="f... | anexos: 4
- [2026-08-05 11:32:42] HMD INTERIORS- EDIÇÃO PRODUÇÃO DE MOBILIARIO LDA - <p> </p> <div style="font-family:Aptos, Aptos_EmbeddedFont, Aptos_MSFontService, Calibri, Helvetica, sans-serif; font-size:12pt; color:rgb(0, 0, 0)"> Em relação ainda aos diário... | anexos: 5
- [2026-08-05 11:01:51] HMD INTERIORS- EDIÇÃO PRODUÇÃO DE MOBILIARIO LDA - <div style="font-family:Aptos, Aptos_EmbeddedFont, Aptos_MSFontService, Calibri, Helvetica, sans-serif; font-size:12pt; color:rgb(0, 0, 0)"> Pedro,</div> <div style="font-family... | anexos: 4

### Notas internas recentes

- [2026-10-02 15:08:17] João Barros - <p><strong>Retrato da cadeia CRM → Projeto → Inventário na produção — 02/10/2026</strong></p> <p>FACTO OBSERVADO (leitura da produção HMD a 02/10, sem escrita):</p> <table class...
- [2026-06-23 10:33:56] Bruno Pinheiro - <div data-oe-version="2.0"><a href="/odoo/res.partner/15434" class="o_mail_redirect" data-oe-id="15434" data-oe-model="res.partner" target="blank" style="text-decoration:none; b... | anexos: 5
- [2026-10-14 09:42:03] Lara Cunha - <p>14/10/2026 — sem resposta da HMD desde o pedido de 06/10, por isso o prazo de 16/10 não era cumprível. Prazo passado para 30/10 e responsáveis João (trabalho técnico) e Lara...

### Metadata de anexos recentes

- Screenshot 2026-10-21 at 11.52.51.png | tipo: image/png | origem: project.task:8379
- Screenshot 2026-10-21 at 11.51.24.png | tipo: image/png | origem: project.task:8379
- Screenshot 2026-10-21 at 11.48.30.png | tipo: image/png | origem: project.task:8379
- + 264 adicionais

### Historico simples recente

- [2026-10-21 13:15:33] chatter.message_created | Chatter message created and mirrored to the repository context. [mail.message:606319] | origem: mail.message:606319
- [2026-05-28 08:41:17] chatter.message_created | Chatter message created and mirrored to the repository context. [mail.message:498098] | origem: mail.message:498098
- [2026-05-28 08:42:29] task.updated | Task updated and mirrored to the repository context. [project.task:5763] | origem: project.task:5763
- + 672 adicionais


## Registo local de execução — tarefa 8113, 13/10/2026

- Autorização: João Barros pediu neste chat ao Codex para retomar os cinco patches de produção preparados pelo Claude. A intervenção é uma correção pontual no mesmo modelo (`ir.ui.view.arch_db`), sem remodelação nem eliminação de registos.
- FACTO OBSERVADO: destino confirmado por leitura como `production`, base `HMD`, Odoo 18.0, website 3 «HMD Furniture 2026». Antes da intervenção, as cinco vistas coincidiam integralmente com o backup do Claude.
- Aplicação via `.pg_framework/scripts/pg_odoo_migration_guard.py`, com dry-run revisto, confirmação de produção e leitura de comparação antes e depois de cada escrita. Portfolio (6814): três figuras estáticas; Fabrics (6811) e Materials (6812): duas zonas editáveis por página; Contacto (6810): retirada dos dois tokens CSRF manuais redundantes; rodapé (6806): retirado `t-ignore`.
- Reconciliação: 5 vistas previstas, 5 gravadas e verificadas, 0 divergências. Segunda simulação sem alterações. XML e herança resolvidos pelo Odoo; patches presentes em `en_GB` (idioma do site), `en_US` e `pt_PT`. Textos e estilos personalizados preservados fora dos fragmentos previstos.
- Plano, backup de cada vista, diff e prova: `data_local/w3_8113_20261013T172641568450Z/` (dados locais, não versionar). Script reproduzível: `scripts/pg_patch_website3_8113.py`. Log de chamadas: `.pg/migration/api_calls.log.jsonl`.
- PONTO POR VALIDAR: comportamento visual no editor e aceitação pela Mónica. A aplicação técnica não equivale a validação do cliente.
- Registo posterior autorizado por João Barros neste chat (13/10/2026): 0,5 h na tarefa 8113, timesheet 45025, em seu nome, com descrição da aplicação dos cinco patches e verificações. Etapa alterada para «Sprint in Progress» (498) e estado para «Aprovado» (`03_approved`), mantendo a tarefa aberta. Próximo passo indicado pelo utilizador: João deixa uma nota à Lara para verificação; prazo por definir. Timesheet, duração, titular, etapa e estado confirmados por leitura após gravação.
- Referências: `theme_hmd_furniture/views/pages.xml`, `theme_hmd_furniture/views/layout.xml`; source consultado via ligação local em `vendor/odoo_src/community/addons/website/models/ir_ui_view.py` (`write`, isolamento entre websites), `vendor/odoo_src/community/odoo/addons/base/models/ir_ui_view.py` (`_check_xml`, validação da herança) e `vendor/odoo_src/community/addons/website/static/src/snippets/s_website_form/000.js` (token CSRF acrescentado pelo widget); documentação oficial https://www.odoo.com/documentation/18.0/developer/howtos/website_themes/layout.html#drop-zone.
