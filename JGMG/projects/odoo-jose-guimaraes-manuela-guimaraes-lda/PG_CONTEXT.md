# PG_CONTEXT - Contexto Global do Projeto

> Artefacto derivado exclusivamente do espelho `.pg` publicado a partir do Odoo.
> Serve como contexto consolidado para leitura humana e para agentes AI.

## 1. Contexto Estrutural

- Projeto: Odoo - JOSÉ GUIMARÃES & MANUELA GUIMARÃES, LDA
- Cliente: JOSÉ GUIMARÃES & MANUELA GUIMARÃES, LDA
- Gestor: Lara Cunha
- Repositorio: parametroglobaladmin/JGMG
- Branch: brodoo
- Fase atual: N/A
- Etapa atual: In Progress
- Ultimo sync do espelho: 2026-10-14 10:18:04

### Objetivo e pedido atual

Objetivo do projeto: Organizar e centralizar no Odoo o fluxo de ponta a ponta — contacto → CRM → venda → pedido de cotação a fornecedores → projeto — com toda a informação ligada ao mesmo projeto e visibilidade de rentabilidade por projeto (quanto se gastou, quanto se recebeu, margem), incluindo a imputação de custos de tempo de desenho/produção. Adoção progressiva do software pelos utilizadores.

Pedido atual: N/A

- Unidade do cliente: JGMG – José Guimarães & Manuela Guimarães, Lda. Unidade principal em âmbito: decoração de interiores, mobiliário e cozinhas. Segunda empresa (cervejaria) incluída apenas como entidade multiempresa para alojar o website simples exigido pelo voucher.

### Ambito incluido

Importação de dados mestre (clientes, fornecedores, artigos) a partir do PHC, via CSV/Excel
CRM (gestão de contactos e oportunidades qualificadas)
Vendas / orçamentação no Odoo (hoje feita sem software)
Pedidos de cotação a fornecedores (RFQ) ligados ao projeto
Gestão de projeto com agregação de toda a informação e rentabilidade por projeto
Imputação de custos de tempo (timesheet) ao projeto
Configuração inicial da base de dados adaptada à realidade da JGMG
Formação (sessão presencial, ~1 dia) e vídeos passo-a-passo de onboarding
Website simples, apenas para cumprir os requisitos do voucher
Configuração multiempresa no Odoo (empresa de interiores + empresa de cervejaria)
Website simples na empresa de cervejaria, apenas para cumprir os requisitos do voucher
Gestor do projeto. Pode ou não ser definido de acordo com a metodologia de implementação Consultor. A pessoa responsável pela implementação e comunicação com o cliente. Executa a configuração do sistema e controla o d...

### Itens factuais a curar no Odoo

- Total no ambito curado: 37
- Total pendente de curadoria: 0
- Ruido excluido na curadoria: 0
Motivos dominantes de curadoria pendente:
- N/A
- N/A

### Ambito excluido

Faturação no Odoo nesta fase (mantém-se no software atual, com licença existente)
Importação de stock do PHC (stock desatualizado; contagem direta no Odoo)
Implementação operacional da empresa de cervejaria (entra só como website de voucher, sem CRM/vendas/projeto/etc.)
Reformulação/migração do website de interiores como prioridade (apenas o mínimo para o voucher)
Desenvolvimento custom (estratégia: standard; quando muito, campos extra via Studio)

### Entregaveis

M1 — Kick-off realizado e macroplaneamento validado
M2 — Ambiente provisionado e dados mestre importados
M3 — Fluxo comercial validado (CRM → Venda → RFQ)
M4 — Projeto com rentabilidade validado
M5 — Website do voucher publicado
M6 — Formação concluída e go-live

### Restricoes e pressupostos

Restricoes:
Multiempresa ativa, mas a segunda empresa (cervejaria) tem âmbito restrito ao website do voucher

Pressupostos:
O âmbito operacional (CRM, vendas, cotações, projeto, rentabilidade) aplica-se apenas à empresa de interiores; a cervejaria limita-se ao website do voucher

Stakeholders:
JOSÉ GUIMARÃES & MANUELA GUIMARÃES, LDA
Lara Cunha

### Contrato e Parametros Odoo

> Parametros lidos do Odoo. Os agentes AI devem respeitar estas restricoes em todas as respostas.

- Versao Odoo: 19.0
- Edicao: enterprise
- Ambiente: saas
- Configuracao standard: PERMITIDO
- Modulos standard adicionais: NÃO PERMITIDO
- Odoo Studio: PERMITIDO
- Desenvolvimento custom: NÃO PERMITIDO
- Restricoes adicionais: Multiempresa ativa, mas a segunda empresa (cervejaria) tem âmbito restrito ao website do voucher
- Urgencia: medium

## 2. Planeamento

- Total de marcos: 6
- Proxima etapa/marco: M1 — Kick-off realizado e macroplaneamento validado
- Target da proxima etapa: 2026-08-06
- Owner da proxima etapa: N/A
- Tasks abertas no projeto: 10
- Tasks abertas para a proxima etapa: 0

### Marcos planeados

- M1 — Kick-off realizado e macroplaneamento validado | estado: planned | owner: N/A | target: 2026-08-06
- M2 — Ambiente provisionado e dados mestre importados | estado: planned | owner: N/A | target: 2026-08-21
- M3 — Fluxo comercial validado (CRM → Venda → RFQ) | estado: planned | owner: N/A | target: 2026-09-18
- M4 — Projeto com rentabilidade validado | estado: planned | owner: N/A | target: 2026-10-02
- M5 — Website do voucher publicado | estado: planned | owner: N/A | target: 2026-10-09
- M6 — Formação concluída e go-live | estado: planned | owner: N/A | target: 2026-10-23

### O que falta para atingir a proxima etapa

- N/A

### Proximas prioridades abertas

- N/A

## 3. Operacao Atual

- Total de tarefas espelhadas: 26
- Tarefas abertas: 10

### Principais tarefas abertas

- Licença Odoo — duplicar a base antes de expirar (09/10/2026) e licenciar no fim dos trabalhos | etapa: Sprint Backlog | prioridade: 1 | responsaveis: Lara Cunha
- Kick Off interno | etapa: Sprint in Progress | prioridade: 0 | responsaveis: Sem responsavel
- Licenciamento Odoo | etapa: Sprint in Progress | prioridade: 0 | responsaveis: Paula Gomes
- Gestão de Projeto | etapa: Sprint in Progress | prioridade: 0 | responsaveis: Sem responsavel
- Vendas — orçamentação e listas de preços | etapa: Backlog | prioridade: 0 | responsaveis: João Barros, Lara Cunha
- Timesheets — imputação de custos de tempo | etapa: Sprint Backlog | prioridade: 0 | responsaveis: Lara Cunha
- Rentabilidade por projeto — analítica e relatórios de margem | etapa: Sprint Backlog | prioridade: 0 | responsaveis: Lara Cunha
- Formação presencial (1 dia) | etapa: Sprint Backlog | prioridade: 0 | responsaveis: Lara Cunha
- Vídeos passo-a-passo de onboarding | etapa: Backlog | prioridade: 0 | responsaveis: Lara Cunha
- Go-live e acompanhamento pós-arranque | etapa: Backlog | prioridade: 0 | responsaveis: Lara Cunha

## 4. Comunicacoes e Historico Recente

- Mensagens espelhadas: 133
- Mensagens com cliente: 56
- Notas internas: 77
- Anexos espelhados: 9

### Comunicacoes recentes com cliente

- [2026-09-28 07:59:56] Cristina Moreira - <div dir="ltr"><br><div><p>Olá, bom dia</p><p>Recebi um email para redefinição da minha senha de acesso, mas infelizmente foi parar à caixa de spam e deixei passar o prazo para... | anexos: 1
- [2026-10-12 17:31:56] Lara Cunha - <p>Boa tarde, Sr. Ricardo,</p> <p>Antes da formação de sexta-feira, 16 de outubro, envio em anexo o ponto de situação do projeto.</p> <p>O Odoo está configurado e com os vossos... | anexos: 1
- [2026-10-02 16:57:21] Lara Cunha - <p>Boa tarde, Sr. Ricardo,</p> <p>Obrigada pelos ficheiros. Já estão carregados no Odoo e podem começar a usá-los:</p> <ul><li><strong>Dados da empresa</strong> — NIF, morada, t... | anexos: 1

### Notas internas recentes

- [2026-10-06 16:39:52] Lara Cunha - <p><strong>Prazos revistos a 06/10/2026</strong> (formação a 16/10, go-live 23/10): CRM (6781), Vendas (6782), Compras (6783) e Gestão de projeto (6784) até <strong>15/10</stron...
- [2026-10-06 16:39:51] Lara Cunha - <p><strong>Prazos revistos a 06/10/2026</strong> (formação a 16/10, go-live 23/10): CRM (6781), Vendas (6782), Compras (6783) e Gestão de projeto (6784) até <strong>15/10</stron...
- [2026-10-06 16:39:51] Lara Cunha - <p><strong>Prazos revistos a 06/10/2026</strong> (formação a 16/10, go-live 23/10): CRM (6781), Vendas (6782), Compras (6783) e Gestão de projeto (6784) até <strong>15/10</stron...

### Metadata de anexos recentes

- Ponto_Situacao_JGMG_2026-10-12.pdf | tipo: application/pdf | origem: project.task:6155
- Inventario_Linhas_a_Confirmar.xlsx | tipo: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet | origem: project.task:7534
- logo_so.png | tipo: image/png | origem: project.task:7534
- + 6 adicionais

### Historico simples recente

- [2026-10-14 10:18:14] task.updated | Task updated and mirrored to the repository context. [project.task:3467] | origem: project.task:3467
- [2026-06-19 15:30:20] project.updated | Project context updated and mirrored to the repository. [project.project:290] | origem: project.project:290
- [2026-06-19 15:51:43] task.updated | Task updated and mirrored to the repository context. [project.task:6153] | origem: project.task:6153
- + 77 adicionais
