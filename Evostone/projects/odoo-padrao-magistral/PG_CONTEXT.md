# PG_CONTEXT - Contexto Global do Projeto

> Artefacto derivado exclusivamente do espelho `.pg` publicado a partir do Odoo.
> Serve como contexto consolidado para leitura humana e para agentes AI.

## 1. Contexto Estrutural

- Projeto: Odoo - EVOSTONE
- Cliente: Evostone Archi - Tech Surfaces, Unipessoal, LDA, Rui Rodrigues
- Gestor: Pedro Coelho
- Repositorio: parametroglobaladmin/Evostone
- Branch: brodoo
- Fase atual: N/A
- Etapa atual: In Progress
- Ultimo sync do espelho: 2026-10-08 16:40:54

### Objetivo e pedido atual

Objetivo do projeto: Assegurar a continuidade das operações na nova infraestrutura Odoo.sh gerida pela Parâmetro Global e garantir a conformidade legal e fiscal da faturação junto da Autoridade Tributária (AT).

Pedido atual: N/A

- Unidade do cliente: Evostone Archi - Tech Surfaces (Portugal / Moçambique)

### Ambito incluido

Validação de acessos GitHub (parametroglobaladmin) e Odoo.sh
Provisionamento de branch de Staging e restauro de backup
Auditoria e compatibilização de módulos customizados
Instalação e configuração dos módulos de Certificação PT (l10n_pt, SAF-T, ATCUD)
Configuração fiscal, séries de faturação e validação de layouts
Testes técnicos de encadeamento de hashes e validação de SAF-T
Testes de Aceitação do Utilizador (UAT)
Transição real para produção (Go-Live) e acompanhamento Hypercare
Gestor do projeto. Pode ou não ser definido de acordo com a metodologia de implementação Consultor. A pessoa responsável pela implementação e comunicação com o cliente. Executa a configuração do sistema e controla o d...
Nº de Utilizadores: 6 Custom ou Padrão: Custom Multiempresa: Sim Tempo de Licença Odoo Faturar a (Cliente
Parametro) Dados do Cliente (SPOC) Pain points Departments to work with Odoo Software they were using Main flows Developments/connectors Potential risks First phase timelines Identified expansion opportunities Departm...
Levantamento de requisitos

### Itens factuais a curar no Odoo

- Total no ambito curado: 86
- Total pendente de curadoria: 0
- Ruido excluido na curadoria: 0
Motivos dominantes de curadoria pendente:
- N/A
- N/A

### Ambito excluido

Novos desenvolvimentos fora do âmbito orçamentado; regularização de pendências financeiras com o parceiro anterior.

### Entregaveis

M1 — Acessos e Ambiente de Testes (Staging)
M2 — Análise de Módulos e Certificação PT
M3 — Testes Integrados e Validação Funcional (UAT)
M4 — Transição Real (Go-Live) e Acompanhamento

### Restricoes e pressupostos

Restricoes:
Cumprimento rigoroso das normas da AT; minimização do tempo de inatividade durante o corte de produção.

Pressupostos:
Disponibilização atempada de acessos GitHub e Odoo.sh; envio de backup completo (DB + filestore); disponibilização de dados fiscais/AT; validação atempada de testes em Staging.

Stakeholders:
Rui Rodrigues (CEO / SPOC Cliente — Evostone)
Pedro Coelho (Gestor de Projeto — Parâmetro Global)
Cláudio Pereira (CEO — Parâmetro Global)
Evostone Archi - Tech Surfaces, Unipessoal, LDA, Rui Rodrigues
Pedro Coelho

### Contrato e Parametros Odoo

> Parametros lidos do Odoo. Os agentes AI devem respeitar estas restricoes em todas as respostas.

- Versao Odoo: 18.0
- Edicao: enterprise
- Ambiente: odoo_sh
- Configuracao standard: PERMITIDO
- Modulos standard adicionais: PERMITIDO
- Odoo Studio: PERMITIDO
- Desenvolvimento custom: PERMITIDO
- Restricoes adicionais: Cumprimento rigoroso das normas da AT; minimização do tempo de inatividade durante o corte de produção.
- Urgencia: high

## 2. Planeamento

- Total de marcos: 4
- Proxima etapa/marco: M3 — Testes Integrados e Validação Funcional (UAT)
- Target da proxima etapa: 2026-09-04
- Owner da proxima etapa: N/A
- Tasks abertas no projeto: 17
- Tasks abertas para a proxima etapa: 2

### Marcos planeados

- M1 — Acessos e Ambiente de Testes (Staging) | estado: delivered | owner: N/A | target: 2026-08-21
- M2 — Análise de Módulos e Certificação PT | estado: delivered | owner: N/A | target: 2026-08-28
- M3 — Testes Integrados e Validação Funcional (UAT) | estado: in_progress | owner: N/A | target: 2026-09-04
- M4 — Transição Real (Go-Live) e Acompanhamento | estado: in_progress | owner: N/A | target: 2026-09-11

### O que falta para atingir a proxima etapa

- T3.2 — Testes de Aceitação do Utilizador (UAT) | etapa: Sprint in Progress | prioridade: 0 | responsaveis: Sem responsavel
- T3.3 — Aprovação Formal de Go-Live | etapa: Backlog | prioridade: 0 | responsaveis: Sem responsavel

### Proximas prioridades abertas

- N/A

## 3. Operacao Atual

- Total de tarefas espelhadas: 78
- Tarefas abertas: 17

### Principais tarefas abertas

- Gestão de Projeto | etapa: Sprint Complete | prioridade: 0 | responsaveis: Sem responsavel
- Criar Prototipo | etapa: Backlog | prioridade: 0 | responsaveis: Sem responsavel
- Criar Orçamento | etapa: Backlog | prioridade: 0 | responsaveis: Sem responsavel
- T3.2 — Testes de Aceitação do Utilizador (UAT) | etapa: Sprint in Progress | prioridade: 0 | responsaveis: Pedro Coelho
- T3.3 — Aprovação Formal de Go-Live | etapa: Backlog | prioridade: 0 | responsaveis: Pedro Coelho
- T4.3 — Suporte e Acompanhamento Pós Go-Live (Hypercare) | etapa: Backlog | prioridade: 0 | responsaveis: Pedro Coelho
- Enviar listagem de pendentes de conta corrente de clientes e fornecedores | etapa: Sprint Backlog | prioridade: 0 | responsaveis: Bruno Pinheiro
- Responder a cliente sobre se as taxas de cambio são atualizadas automaticamente | etapa: Sprint Backlog | prioridade: 0 | responsaveis: Bruno Pinheiro
- Verifivar em odoo a nivel de compra e venda como é classificado o mercado | etapa: Sprint Backlog | prioridade: 0 | responsaveis: Bruno Pinheiro
- Configurar emails ligar com cliente alojado em odoo.sh | etapa: Sprint Backlog | prioridade: 0 | responsaveis: Hugo Ferreira
- + 7 adicionais

## 4. Comunicacoes e Historico Recente

- Mensagens espelhadas: 286
- Mensagens com cliente: 217
- Notas internas: 69
- Anexos espelhados: 238

### Comunicacoes recentes com cliente

- [2026-08-25 14:20:11] Bruno Pinheiro - <div data-oe-version="2.0">Boa tarde Sr. Rui,</div><div><br></div><div>De momento não vou conseguir atender pois vou ter uma consulta médica agora mesmo. Não é do meu conhecimen... | anexos: 4
- [2026-08-25 14:21:56] Evostone Archi - Tech Surfaces, Unipessoal, LDA - <div><p><span style="font-size:11.0pt">Ok certo.</span></p><p><span style="font-size:11.0pt">Então peço para me ligar assim que lhe for possível 917500268.</span></p><p><span st...
- [2026-08-25 14:13:22] Evostone Archi - Tech Surfaces, Unipessoal, LDA - <div><p><span style="font-size:11.0pt">Boa tarde Sr Bruno</span></p><p><span style="font-size:11.0pt">&nbsp;</span></p><p><span style="font-size:11.0pt">Junto envio o link para...

### Notas internas recentes

- [2026-09-03 15:28:46] Bruno Pinheiro - <div data-oe-version="2.0"><a href="/odoo/res.partner/133286" class="o_mail_redirect" data-oe-id="133286" data-oe-model="res.partner" target="blank" style="text-decoration:none... | anexos: 4
- [2026-08-25 09:06:22] Bruno Pinheiro - <p data-oe-version="2.0" style="border-radius:0px; border-style:none; padding:0px; margin:0px 0 16px 0; border-left-color:#e4e4e4; border-bottom-color:#e4e4e4; border-right-colo... | anexos: 4
- [2026-10-02 13:25:50] Pedro Coelho - <span><a href="/odoo/res.partner/133356" class="o_mail_redirect" data-oe-id="133356" data-oe-model="res.partner" target="blank">@Maria Dias</a> Boa tarde,<br><br>Já fiz as devid... | anexos: 1

### Metadata de anexos recentes

- EMPRESAS (Feira) - marmomacplus.xlsx | tipo: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet | origem: project.task:8017
- Scanner_20261002.png | tipo: image/png | origem: project.task:7761
- Fatura Odoo.pdf | tipo: application/pdf | origem: project.task:7761
- + 21 adicionais

### Historico simples recente

- [2026-10-08 16:41:09] task.created | Task created and mirrored to the repository context. [project.task:8019] | origem: project.task:8019
- [2026-07-22 10:56:06] project.snapshot_refreshed | Project repository context synchronized manually. [project.project:316] | origem: project.project:316
- [2026-07-22 10:59:51] project.updated | Project context updated and mirrored to the repository. [project.project:316] | origem: project.project:316
- + 203 adicionais
