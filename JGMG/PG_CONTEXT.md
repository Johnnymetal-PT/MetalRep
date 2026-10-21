# PG_CONTEXT - Memória funcional e decisória

> Fonte de verdade do estado funcional, técnico e consultivo do projeto.
> Alguns blocos marcados com `PG_AUTO` podem ser atualizados automaticamente a partir de `PG_SCOPE_INTAKE.yaml`, `.pg/PG_PROJECT_STATUS_SYNC.json` e scripts do template.

## Estado Oficial do Projeto

### Identificação do projeto
<!-- PG_AUTO:IDENTIFICACAO:START -->
Nome do projeto: JGMG
Cliente / unidade: [PREENCHER]
Resumo funcional do repositorio: [PREENCHER]
Fase atual do projeto: [PONTO POR VALIDAR]
<!-- PG_AUTO:IDENTIFICACAO:END -->

### Parâmetros Odoo ativos
Versão do Odoo: 19.0
Edição: Enterprise
Ambiente: SaaS (odoo.com), versão `saas~19.4` (módulo `base`, FACTO OBSERVADO a 23/09/2026), em período de teste — expira a 06/10/2026 se não for ativada a licença. Nota: o source local (`vendor/odoo_src`) é a branch estável `19.0`; o SaaS 19.4 tem código mais recente — comportamentos novos do 19.x ficam PONTO POR VALIDAR contra a própria base
Base do cliente: https://jose-guimaraes-manuela-guimaraes-lda-2.odoo.com (BD `jose-guimaraes-manuela-guimaraes-lda-2`) — duplicada a 06/10/2026, expira a 22/10/2026 16:38; base original (`…-lda`) abandonada
Idioma da interface: pt_BR para todos os utilizadores (menus e botões aparecem em português do Brasil)
Path do core: C:\Users\Utilizador\.pg\odoo_src\19.0\community
Path source Enterprise: C:\Users\Utilizador\.pg\odoo_src\19.0\enterprise
Documentação oficial base: https://www.odoo.com/documentation/19.0/
Documentação Studio: https://www.odoo.com/documentation/19.0/applications/studio.html
Documentação Developer: https://www.odoo.com/documentation/19.0/developer/reference.html
Última sincronização de âmbito: [NAO EXECUTADA]
Fonte do âmbito sincronizado: [PONTO POR VALIDAR]
Última sincronização automática: 2026-10-14 11:46:21 +01:00

### Restrições do projeto
<!-- PG_AUTO:RESTRICOES:START -->
Configuracao standard permitida?: [PONTO POR VALIDAR]
Modulos standard adicionais permitidos?: [PONTO POR VALIDAR]
Odoo Studio permitido?: [PONTO POR VALIDAR]
Custom permitido?: [PONTO POR VALIDAR]
Restricoes contratuais adicionais: [PONTO POR VALIDAR]
<!-- PG_AUTO:RESTRICOES:END -->

### Pedido funcional atual
<!-- PG_AUTO:PEDIDO_ATUAL:START -->
Requisito / pedido atual: [PREENCHER]
Objetivo de negocio: [PREENCHER]
Trigger: [PREENCHER]
Frequencia: [PREENCHER]
Volumes: [PREENCHER]
Urgencia: [PREENCHER]
Criterios de aceitacao:
- [PREENCHER]
<!-- PG_AUTO:PEDIDO_ATUAL:END -->

### Processo atual
<!-- PG_AUTO:PROCESSO_ATUAL:START -->
Processo atual: [PREENCHER]
Utilizadores / papeis:
- [PREENCHER]
Excecoes conhecidas:
- [PREENCHER]
Aprovacoes:
- [PREENCHER]
Documentos envolvidos:
- [PREENCHER]
Integracoes:
- [PREENCHER]
Reporting esperado:
- [PREENCHER]
O que ja foi tentado ou validado no standard atual:
- [PREENCHER]
Porque foi considerado insuficiente:
- [PREENCHER]
<!-- PG_AUTO:PROCESSO_ATUAL:END -->

### Problema / dor
<!-- PG_AUTO:PROBLEMA_DOR:START -->
Problema / necessidade observada: [PREENCHER]
<!-- PG_AUTO:PROBLEMA_DOR:END -->

### Impacto no negócio
<!-- PG_AUTO:IMPACTO_NEGOCIO:START -->
Impacto de negocio: [PREENCHER]
<!-- PG_AUTO:IMPACTO_NEGOCIO:END -->

## Artefactos Fatuais Publicados

> Esta camada le snapshots oficiais publicados em `.pg/`.
> Os snapshots continuam a ser a source of truth factual primária; este ficheiro funciona apenas como consolidação derivada de leitura.

### Âmbito factual publicado
<!-- PG_AUTO:SCOPE_ITEMS:START -->
Resumo do scope sincronizado:
- Itens ativos: [PREENCHER]
- Itens validados: [PREENCHER]
- Itens propostos: [PREENCHER]
- Itens diferidos: [PREENCHER]
- Última alteração de task: [PONTO POR VALIDAR]

Itens em âmbito:
- [PREENCHER]
<!-- PG_AUTO:SCOPE_ITEMS:END -->

### Estado operacional factual publicado
<!-- PG_AUTO:STATUS_SYNC:START -->
Schema do snapshot: [PONTO POR VALIDAR]
Última atualização recebida do Odoo: [NAO SINCRONIZADA]
Fase reportada no último sync: [PONTO POR VALIDAR]
Estado geral reportado: [PONTO POR VALIDAR]
Sistema de origem: [PONTO POR VALIDAR]
Modelo Odoo de origem: [PONTO POR VALIDAR]
Record Odoo de origem: [PONTO POR VALIDAR]
URL do record Odoo: [PONTO POR VALIDAR]
Publicado no repositório em: [PONTO POR VALIDAR]
Publicado por: [PONTO POR VALIDAR]
Trigger de sync: [PONTO POR VALIDAR]
Branch de sync: [PONTO POR VALIDAR]
Milestones:
- [PREENCHER]
Bloqueios:
- [PREENCHER]
Riscos operacionais:
- [PREENCHER]
Próximos passos operacionais:
- [PREENCHER]
Decisões pendentes:
- [PREENCHER]
Go-live alvo: [PONTO POR VALIDAR]
Owner atual: [PONTO POR VALIDAR]
Fonte Odoo / referência: [PONTO POR VALIDAR]
<!-- PG_AUTO:STATUS_SYNC:END -->

### Decisões factuais publicadas

Derivado de `.pg/PG_DECISIONS_SYNC.json` quando esse snapshot existir no projeto bootstrapado.
Este bloco continua de leitura e não substitui o snapshot factual.

### Riscos factuais publicados

Derivado de `.pg/PG_RISKS_SYNC.json` quando esse snapshot existir no projeto bootstrapado.
Este bloco continua de leitura e não substitui o snapshot factual.

### Entregáveis, requisitos, plano e budget publicados

Os snapshots `.pg/PG_DELIVERIES_SYNC.json`, `.pg/PG_REQUIREMENTS_SYNC.json`,
`.pg/PG_PROJECT_PLAN_SYNC.json` e `.pg/PG_BUDGET_SYNC.json` continuam a ser os
artefactos factuais primários. A sua integração textual neste contexto deve ser
sempre derivada, curta e explicitamente não canónica.

## Consolidação e Gaps

### Gaps factuais ainda por consolidar

- Cliente: empresa de design de interiores que, após o projeto, compra os produtos e faz a montagem (reunião de 23/09/2026).
- Apps instaladas na base do cliente (23/09/2026): CRM, Vendas, Compras, Projeto, Faturamento/Contabilidade, Inventário, Código de barras, Planilhas de horas, Planejamento, Conhecimento, Documentos, Assinar, Funcionários, Contatos, Calendário, Compromissos, Pesquisas. Módulos de ligação: sale_project, sale_timesheet, sale_purchase, sale_stock, purchase_stock, project_purchase, sale_crm, l10n_pt.
- Estágios do projeto «Joaquim» (reflete o processo do cliente): Proposta → Desenho técnico → Orçamento → Desenho 3D → Apresentação → Revisões → Acompanhamento de Produção → Instalação / Montagem → Concluido.
- Utilizadores internos: Ricardo Guimarães (ativo), Andreia Rocha, Cristina Moreira, José Correia, Marta Guimarães (convites reenviados a 24/09; estado de ativação a confirmar).
- Uma única empresa na base (JOSÉ GUIMARÃES & MANUELA GUIMARÃES, LDA).

### Dependências de refresh e validação

- Não há ligação registada em `pg.odoo.connection` para a base do cliente; as chaves API usadas foram entregues ad hoc e já não autenticam. Registar uma ligação `production` em Brodoo › Repositório › Ligações Odoo do cliente.
- `odoo_env.json` com `collection.status=unavailable`: inventário de módulos do espelho por recolher.

## Curadoria Assistida e Itens Por Promover

> Drafts, chatter e backlog operacional vivem aqui apenas como apoio a curadoria.
> Nada desta secção deve competir com os campos oficiais ou com os snapshots publicados.

### Drafts e sinais em revisão

- [PREENCHER]

### Itens por promover a oficial

- [PREENCHER]

## Análise Consultiva e Decisão

### Análise de solução

### 1. Standard já existente no projeto
Estado: [NAO ANALISADO]
Factos observados:
- [PREENCHER]
Inferências:
- [PREENCHER]
Pontos por validar:
- [PREENCHER]

### 2. Standard adicional Odoo
Estado: [NAO ANALISADO]
Módulos / funcionalidades a avaliar:
- [PREENCHER]
Cobertura do requisito: [PONTO POR VALIDAR]
Implicações de adoção:
- [PREENCHER]
Factos observados:
- [PREENCHER]
Inferências:
- [PREENCHER]
Pontos por validar:
- [PREENCHER]

### 3. Odoo Studio
Estado: [NAO ANALISADO]
Factos observados:
- [PREENCHER]
Inferências:
- [PREENCHER]
Pontos por validar:
- [PREENCHER]

### 4. Custom
Estado: [NAO ANALISADO]
Escopo mínimo se for necessário:
- [PREENCHER]
Factos observados:
- [PREENCHER]
Inferências:
- [PREENCHER]
Pontos por validar:
- [PREENCHER]

### Decisão atual
Classificação final: [PONTO POR VALIDAR]
Decisão: [PREENCHER]
Justificação: [PREENCHER]

### Riscos
- Faturação certificada AT: a base SaaS 19.4 não tem módulo de certificação PT nem ATCUD (FACTO OBSERVADO 29/09/2026). **Decidido a 29/09 (Pedro Coelho, por indicação do cliente): sem faturação certificada, só Odoo SaaS standard.** PONTO POR VALIDAR: se o cliente emite faturas a clientes no Odoo, confirmar que o faz de forma legalmente válida (ex.: dispensa de software certificado) — responsabilidade do cliente, a deixar registada.
- Ficha da empresa incompleta: sem NIF, morada, telefone e IBAN; email da empresa é it.odoo@parametro.pt (Parâmetro Global).
- Licença: a base SaaS expira a 06/10/2026 se não for ativada com o código de licenciamento (tarefa 7580; alinhar com a 6153, Paula Gomes). Sem ativação perdem-se a base, os dados e os guias.
- Plano do projeto previa multiempresa (interiores + cervejaria) e website da cervejaria (6779, 6787); fora desta fase por decisão de 29/09/2026 — comunicar ao cliente e rever o âmbito do voucher.

### Próximos passos
- 02/10/2026, 14:30 — reunião de acompanhamento com o cliente (agenda enviada a 29/09: licença, dados, cervejaria, datas das formações).
- Importação de dados mestre (6780) quando o cliente enviar inventário e contactos — modelo em `outputs/jgmg/Modelo_Importacao_Odoo_JGMG.xlsx` (contactos antes de artigos).
- Documentos dos projetos a carregar na aplicação Documentos, uma pasta por projeto.
- Formação presencial (6788, prazo 14/10/2026) com os colaboradores e o responsável, apoiada nos guias do Conhecimento.

## Referências e Histórico

### Referências consultadas

#### Documentação Odoo
- [PREENCHER]

#### Core Odoo
- [PREENCHER]

#### Código do projeto
- [PREENCHER]

### Histórico de marcos de decisão

#### 2026-09-23 - Reunião de alinhamento (kick-off com o cliente)
Contexto:
- Reunião com o cliente para alinhamento do projeto (tarefa 7534); conta como kick-off (6152 fechada a 29/09).

Decisão:
- A Parâmetro Global prepara guias de formação: orçamentos de clientes, faturas de fornecedores, artigos, Projetos, Vendas, Compras e CRM — publicados no Conhecimento do Odoo do cliente a 23/09 (artigo «Guias de formação Odoo», ids 39–46).
- O cliente envia inventário de artigos, contactos e documentos dos projetos para inserção no Odoo.
- Agendar formações com os funcionários e com o responsável.

Riscos / pendências:
- Guias ainda não percorridos no ecrã nem validados pelo cliente.

Referências:
- Tarefas 7534, 6152, 6788 (Odoo PG, projeto 290).

#### 2026-10-02 - Reunião de acompanhamento e importação de dados
Contexto:
- Reunião por videochamada com Ricardo Guimarães (2 h). O cliente enviou nesse dia os dados da empresa, clientes, fornecedores e inventário.

Decisão:
- Licença: combinado com a Paula Gomes ir duplicando a base de teste até terminar os trabalhos; licenciamento no fim (tarefa 7580). A base atual expira a 09/10/2026, 13:26.
- Fases dos projetos: ficam as do modelo «Geral» criado pela Cristina (Ficha cliente → Orçamentação → Orçamentos fechados → Aditamentos → Financeiro → Encomendas → Entregas → Auditoria); aplicadas a todos os projetos a 06/10.
- Faturas a clientes emitidas no Odoo, sem faturação certificada — decisão do cliente.
- Formação: 16/10/2026, 15:00–18:00; PLM numa sessão à parte.
- Importados: dados da empresa, 664 contactos, 2 241 artigos com stock inicial (6 055,47 un., valorização periódica). PLM e Fabricação instalados na reunião.

Riscos / pendências:
- Cada duplicação muda o endereço e o nome da base: atualizar a ligação no Brodoo e avisar os utilizadores; dados registados na base antiga depois da cópia perdem-se.
- 25 linhas do inventário e 6 NIF de fornecedores a confirmar pelo cliente; documentos dos projetos por receber; perfis dos participantes na formação por confirmar.

Referências:
- Tarefas 7534, 7580, 6779, 6780, 6788 (Odoo PG).

#### 2026-09-29 - Sem faturação certificada
Contexto:
- A base SaaS 19.4 não tem certificação AT (sem ATCUD); a localização certificada ptplus usada noutros projetos exige Odoo.sh.

Decisão:
- Pedro Coelho, 29/09/2026, por indicação do cliente: o cliente não vai ter faturação certificada; fica só com o Odoo SaaS standard. A licença a ativar é a subscrição SaaS.

Riscos / pendências:
- Confirmar com o cliente onde e como emite as faturas a clientes.

Referências:
- Nota na tarefa 6779 (Odoo PG).

#### 2026-09-29 - Cervejaria fora desta fase
Contexto:
- O plano previa configuração multiempresa (interiores + cervejaria) e website da cervejaria.

Decisão:
- Pedro Coelho, 29/09/2026: a cervejaria não entra nesta fase; configuração e importação só para a empresa de design de interiores.

Riscos / pendências:
- Comunicar ao cliente na reunião de 02/10 e rever o impacto no âmbito do voucher (6779, 6787).

Referências:
- Nota na tarefa 6779 (Odoo PG).
