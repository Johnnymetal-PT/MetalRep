# PG_CONTEXT - Contexto Global do Projeto

> Artefacto derivado exclusivamente do espelho `.pg` publicado a partir do Odoo.
> Serve como contexto consolidado para leitura humana e para agentes AI.

## 1. Contexto Estrutural

- Projeto: Odoo - Hipermercado
- Cliente: J. V. Oliveira, Lda
- Gestor: Bruno Pinheiro
- Repositorio: parametroglobaladmin/Hipermercado
- Branch: Testing
- Fase atual: N/A
- Etapa atual: In Progress
- Ultimo sync do espelho: 2026-06-26 14:54:41

### Objetivo e pedido atual

Objetivo do projeto: Unificar CRM, vendas, compras e inventário num único ERP Odoo, automatizar a ingestão de catálogos de fornecedores e suportar operação multi-armazém com etiquetagem automática de expedição (GLS / Rhenus / DPD).

Pedido atual: N/A

- N/A

### Ambito incluido

Integração API com fornecedores (catálogo + stock)
Migração do cérebro do PrestaShop (seleção de produtos para o site + importação CSV de fornecedores)
Importação de artigos com pesos e dimensões
Gestão multi-armazém: 2 físicos + lojas + virtual
Geração de etiquetas GLS, Rhenus, DPD
Configuração de CRM, vendas, compras, inventário
Website com download de informação técnica de produto
Substituição do CEGID PHC
Criação de BD de Testes e Máquina Virtual Windows
Integrações atuais e integrar no Odoo Template - Clarico Vega
Importar produtos Artigos com pesos e dimensoes
Importar a 1ª vez Se stock fisico, sobrepoe ao virtual Caminho mais longo por defeito e encurtar manualmente Transportadoras defnidas por peso e codigo postal Saidas, batch e guia Transporte interno

### Itens factuais a curar no Odoo

- Total no ambito curado: 21
- Total pendente de curadoria: 0
- Ruido excluido na curadoria: 0
Motivos dominantes de curadoria pendente:
- N/A
- N/A

### Ambito excluido

- N/A

### Entregaveis

Integração API Fornecedores Contactos / Master Data Rotas / Inventário Localização Faturação (PT) Go Live
Integração API Fornecedores
Contactos, Master Data
Rotas/Inventário
Localização Faturação
Go Live

### Matriz contratual de entregaveis

Integração API Fornecedores Contactos / Master Data Rotas / Inventário Localização Faturação (PT) Go Live

### Restricoes e pressupostos

Restricoes:
Odoo 19 Enterprise em Odoo.sh (sem código fora do que Odoo.sh permite)
Localização Portuguesa de faturação obrigatória
Compatibilidade obrigatória com transportadoras GLS, Rhenus e DPD
Janela de Go-Live alvo 2026-04-15 já vencida — replanear

Pressupostos:
Acesso atempado às APIs / catálogos dos fornecedores
Template Clarico Vega como base de website
Disponibilidade do cliente (J. V. Oliveira) para validações funcionais
Equipa interna do cliente (Comercial, Marketing) disponível para testes

Stakeholders:
J. V. Oliveira, Lda
João Barros
Bruno Pinheiro

### Contrato e Parametros Odoo

> Parametros lidos do Odoo. Os agentes AI devem respeitar estas restricoes em todas as respostas.

- Versao Odoo: 19.0
- Edicao: enterprise
- Ambiente: odoo_sh
- Configuracao standard: PERMITIDO
- Modulos standard adicionais: PERMITIDO
- Odoo Studio: PERMITIDO
- Desenvolvimento custom: PERMITIDO
- Restricoes adicionais: Odoo 19 Enterprise em Odoo.sh (sem código fora do que Odoo.sh permite) Localização Portuguesa de faturação obrigatória Compatibilidade obrigatória com transportadoras GLS, Rhenus e DPD Janela de Go-Live alvo 2026-04-15 já vencida — replanear

## 2. Planeamento

- Total de marcos: 5
- Proxima etapa/marco: Integração API Fornecedores
- Target da proxima etapa: 2026-04-01
- Owner da proxima etapa: N/A
- Tasks abertas no projeto: 3
- Tasks abertas para a proxima etapa: 0

### Marcos planeados

- Integração API Fornecedores | estado: N/A | owner: N/A | target: 2026-04-01
- Contactos, Master Data | estado: N/A | owner: N/A | target: 2026-04-03
- Rotas/Inventário | estado: N/A | owner: N/A | target: 2026-04-10
- Localização Faturação | estado: N/A | owner: N/A | target: 2026-04-13
- Go Live | estado: N/A | owner: N/A | target: 2026-04-15

### O que falta para atingir a proxima etapa

- N/A

### Proximas prioridades abertas

- N/A

## 3. Operacao Atual

- Total de tarefas espelhadas: 12
- Tarefas abertas: 3
- Go-live alvo: N/A

### Resumo operacional

Estado operacional reportado: Project currently in stage In Progress. Open tasks: 3. Next milestone: Integração API Fornecedores.

### Principais tarefas abertas

- Gestão de Projeto | etapa: Sprint in Progress | prioridade: 1 | responsaveis: Bruno Pinheiro
- Desenvolvimento de Core+API Fornecedores | etapa: Sprint in Progress | prioridade: 0 | responsaveis: João Barros
- Auditoria Servidor SH | etapa: Backlog | prioridade: 0 | responsaveis: Nuno Oliveira

## 4. Comunicacoes e Historico Recente

- Mensagens espelhadas: 47
- Mensagens com cliente: 38
- Notas internas: 9
- Anexos espelhados: 2

### Comunicacoes recentes com cliente

- [2026-04-15 14:51:46] João Barros - <p>Aproveito também para enviar em anexo o template de Excel para importação de Contactos para Odoo.</p> | anexos: 1
- [2026-04-15 14:33:25] João Barros - <p>Boa tarde, António,<br><br>Estamos neste momento muito próximos de atingir o milestone de ter o serviço de Crawler a funcionar de forma eficaz e dentro de um tempo de execuçã...

### Notas internas recentes

- [2026-06-26 14:53:32] Nuno Oliveira - <span><a href="/odoo/res.partner/13" class="o_mail_redirect" data-oe-id="13" data-oe-model="res.partner" target="blank">@João Barros</a> <br>Segue em anexo o documento word da a... | anexos: 1

### Metadata de anexos recentes

- Auditoria Armazenamento Odoo SH.docx | tipo: application/vnd.openxmlformats-officedocument.wordprocessingml.document | origem: project.task:6271
- Template de Importação de Contactos.xlsx | tipo: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet | origem: project.task:4621

### Historico simples recente

- [2026-06-26 14:54:47] attachment.updated | Attachment metadata updated and mirrored to the repository context. [ir.attachment:59964] | origem: ir.attachment:59964
- [2026-06-01 16:54:34] project.snapshot_refreshed | Project repository context synchronized manually. [project.project:206] | origem: project.project:206
- [2026-06-03 08:15:40] chatter.message_created | Chatter message created and mirrored to the repository context. [mail.message:501967] | origem: mail.message:501967
- + 4 adicionais
