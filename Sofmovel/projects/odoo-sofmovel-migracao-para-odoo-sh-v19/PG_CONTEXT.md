# PG_CONTEXT - Contexto Global do Projeto

> Artefacto derivado exclusivamente do espelho `.pg` publicado a partir do Odoo.
> Serve como contexto consolidado para leitura humana e para agentes AI.

## 1. Contexto Estrutural

- Projeto: Odoo - Sofmovel (Migração para odoo.sh v19)
- Cliente: Momentos D Argumento, Lda
- Gestor: Bruno Pinheiro
- Repositorio: parametroglobaladmin/Sofmovel
- Branch: brodoo
- Fase atual: N/A
- Etapa atual: In Progress
- Ultimo sync do espelho: 2026-07-10 09:09:22

### Objetivo e pedido atual

Objetivo do projeto: N/A

Pedido atual: N/A

- N/A

### Ambito incluido

Gestão de Projeto
Contexto e histórico Este trabalho tem origem no projeto Odoo — Sofmovel (Phase 1) onde foram registadas duas tarefas relacionadas
Migrar Odoo para odoo.sh: Task Phase 1 — SOFTMOVEL ODOO Versão 19 / SH / Website
Verificar que a subscrição Odoo.sh do cliente está correctamente configurada com 1 branch de produção 2 branches de staging (uma para testes de desenvolvimento contínuo
uma dedicada ao upgrade v19) Confirmar com o cliente que o acerto foi efectuado antes de iniciar qualquer trabalho técnico. Critérios de aceitação Subscrição confirmada com 2 staging branches activas Acesso ao project...
Migrar o ambiente Odoo 17 Enterprise actual (on-premise) para a plataforma Odoo.sh, mantendo a versão 17 em produção. Inclui
Importação da base de dados e filestore para a branch de produção no Odoo.sh Adaptação dos módulos custom (pg_*) ao ambiente Odoo.sh (sem dependências de filesystem local, sem cron externos, sem configurações on-premi...
Importação de produtos testada Fluxos críticos validados pelo cliente (vendas, compras, stock, expedição) Email configurado e a enviar corretamente
Executar o processo de upgrade de versão em branch de staging, com base no backup diário de produção (já em Odoo.sh). Inclui Solicitar upgrade oficial ao Odoo via plataforma Odoo.sh (upgraded database) Adaptar os módu...
Sessão(ões) de validação com o cliente sobre o ambiente staging v19 antes da promoção para produção. O cliente testa os seus fluxos de trabalho diários e confirma que não há bloqueadores. Critérios de aceitação Client...
Janela de indisponibilidade planeada para promoção do ambiente v19 de staging para produção. Inclui Agendamento da janela de manutenção com o cliente Merge/promoção da branch de staging v19 para produção Verificação p...
Coordenar com o cliente e com os seus parceiros informáticos (referenciados nas comunicações de junho 2026) os passos necessários no servidor on-premise antes de o desactivar. Inclui

### Itens factuais a curar no Odoo

- Total no ambito curado: 14
- Total pendente de curadoria: 0
- Ruido excluido na curadoria: 0
Motivos dominantes de curadoria pendente:
- N/A
- N/A

### Ambito excluido

- N/A

### Entregaveis

- N/A

### Restricoes e pressupostos

Restricoes:
- N/A

Pressupostos:
- N/A

Stakeholders:
Momentos D Argumento, Lda
Bruno Pinheiro

### Contrato e Parametros Odoo

> Parametros lidos do Odoo. Os agentes AI devem respeitar estas restricoes em todas as respostas.

- Configuracao standard: Não definido
- Modulos standard adicionais: Não definido
- Odoo Studio: Não definido
- Desenvolvimento custom: Não definido

## 2. Planeamento

- Total de marcos: 0
- Proxima etapa/marco: N/A
- Target da proxima etapa: N/A
- Owner da proxima etapa: N/A
- Tasks abertas no projeto: 10
- Tasks abertas para a proxima etapa: 0

### Marcos planeados

- N/A

### O que falta para atingir a proxima etapa

- N/A

### Proximas prioridades abertas

- Criar Odoo sh v19 standard de testes + Documentação Gap | etapa: Sprint in Progress | prioridade: 3 | responsaveis: Sem responsavel

## 3. Operacao Atual

- Total de tarefas espelhadas: 14
- Tarefas abertas: 10

### Principais tarefas abertas

- Criar Odoo sh v19 standard de testes + Documentação Gap | etapa: Sprint in Progress | prioridade: 3 | responsaveis: Bruno Pinheiro
- 0. SOFTMOVEL ODOO Versão 19 / SH / Website | etapa: Sprint in Progress | prioridade: 0 | responsaveis: Bruno Pinheiro
- Gestão de Projeto | etapa: Sprint in Progress | prioridade: 0 | responsaveis: Bruno Pinheiro
- Migração Odoo — On-Premise v17 → Odoo.sh + Upgrade v19 | etapa: Sprint Backlog | prioridade: 0 | responsaveis: João Barros
- 2. Migração do ambiente on-premise para Odoo.sh (v17) | etapa: Backlog | prioridade: 0 | responsaveis: João Barros
- 3. Upgrade v17 → v19 em Staging (preparação e testes) | etapa: Backlog | prioridade: 0 | responsaveis: João Barros
- 4. Validação funcional com o cliente (staging v19) | etapa: Backlog | prioridade: 0 | responsaveis: João Barros
- 5. Go-live: promoção para produção (v19) | etapa: Backlog | prioridade: 0 | responsaveis: João Barros
- 6. Descomissionamento do servidor on-premise | etapa: Backlog | prioridade: 0 | responsaveis: Vitor Costa
- Permissões Odoo 19 | etapa: Sprint in Progress | prioridade: 0 | responsaveis: Bruno Pinheiro

## 4. Comunicacoes e Historico Recente

- Mensagens espelhadas: 76
- Mensagens com cliente: 48
- Notas internas: 28
- Anexos espelhados: 228

### Comunicacoes recentes com cliente

- [2026-06-19 07:44:23] Momentos D Argumento, Lda, Andreia Silva - <p> </p> <div style="font-family:Calibri, Helvetica, sans-serif; font-size:11pt; color:rgb(0, 0, 0)"> Olá Bruno,&nbsp;</div> <div style="font-family:Calibri, Helvetica, sans-ser... | anexos: 4
- [2026-06-15 14:11:26] Bruno Pinheiro - <div data-oe-version="2.0">Boa tarde Andreia,</div><div><br></div><p style="border-radius:0px; border-style:none; padding:0px; margin:0px 0 16px 0; border-left-color:#e4e4e4; bo... | anexos: 4
- [2026-06-25 14:23:20] andreiasilva@sofmovel.pt - <p> </p> <div style="font-family:Calibri, Helvetica, sans-serif; font-size:11pt; color:rgb(0, 0, 0)"> Preciso de mais acessos para mexer no website.&nbsp;</div> <div id="Signatu... | anexos: 4

### Notas internas recentes

- [2026-06-24 13:14:15] Bruno Pinheiro - <div data-oe-version="2.0"><a href="/odoo/res.partner/15245" class="o_mail_redirect" data-oe-id="15245" data-oe-model="res.partner" target="blank" style="text-decoration:none; b... | anexos: 4
- [2026-06-26 11:11:06] Bruno Pinheiro - <div class="o-paragraph"><a href="/odoo/res.partner/14957" class="o_mail_redirect" data-oe-id="14957" data-oe-model="res.partner" target="blank">@andreiasilva@sofmovel.pt</a> </... | anexos: 4
- [2026-06-25 15:06:18] Bruno Pinheiro - <div class="o-paragraph"><a href="/odoo/res.partner/14957" class="o_mail_redirect" data-oe-id="14957" data-oe-model="res.partner" target="blank">@andreiasilva@sofmovel.pt</a> </... | anexos: 4

### Metadata de anexos recentes

- Captura de ecrã 2026-06-25, às 16.37.12.png | tipo: image/png | origem: project.task:6233
- Captura de ecrã 2026-06-25, às 16.34.41.png | tipo: image/png | origem: project.task:6233
- Outlook-5ym0dm3s.png | tipo: image/png | origem: project.task:5857
- + 3 adicionais

### Historico simples recente

- [2026-07-10 09:09:38] task.updated | Task updated and mirrored to the repository context. [project.task:6380] | origem: project.task:6380
- [2026-06-19 08:20:51] project.updated | Project context updated and mirrored to the repository. [project.project:289] | origem: project.project:289
- [2026-06-19 09:06:39] attachment.created | Attachment metadata created and mirrored to the repository context. [ir.attachment:58596] | origem: ir.attachment:58596
- + 58 adicionais
