# PG_CONTEXT - Memória funcional e decisória

> Fonte de verdade do estado funcional, técnico e consultivo do projeto.
> Alguns blocos marcados com `PG_AUTO` podem ser atualizados automaticamente a partir de `PG_SCOPE_INTAKE.yaml`, `.pg/PG_PROJECT_STATUS_SYNC.json` e scripts do template.

## Estado Oficial do Projeto

### Identificação do projeto
<!-- PG_AUTO:IDENTIFICACAO:START -->
Nome do projeto: Waterdetails
Cliente / unidade: Virgin Details, Lda.
Resumo funcional do repositório: Implementação de Odoo Enterprise 19.0 em Odoo.sh para arranque mínimo viável integrado de contactos, produtos, vendas, faturação certificada PT, inventário, compras e multiempresa.
Fase atual do projeto: Comercial
<!-- PG_AUTO:IDENTIFICACAO:END -->

### Parâmetros Odoo ativos
Versão do Odoo: 19.0
Edição: Enterprise
Ambiente: Odoo.sh
Path do core: C:\Users\Utilizador\.pg\odoo_src\19.0\community
Path source Enterprise: C:\Users\Utilizador\.pg\odoo_src\19.0\enterprise
Documentação oficial base: https://www.odoo.com/documentation/19.0/
Documentação Studio: https://www.odoo.com/documentation/19.0/applications/studio.html
Documentação Developer: https://www.odoo.com/documentation/19.0/developer/reference.html
Última sincronização de âmbito: [NAO EXECUTADA]
Fonte do âmbito sincronizado: [PONTO POR VALIDAR]
Última sincronização automática: 2026-10-14 18:00:32 +01:00

### Restrições do projeto
<!-- PG_AUTO:RESTRICOES:START -->
Configuração standard permitida?: Sim
Módulos standard adicionais permitidos?: Sim (Contactos, Produtos, Vendas, Fat...
Odoo Studio permitido?: Restrito / Não prioritário nesta fase
Custom permitido?: Não permitido nesta fase
Restrições contratuais adicionais: Pacote inicial de 40 horas (2800€ + IVA); subscrição do software em nome do cliente; licenciamento de software com prazo de pagamento de 20 dias; 50% adjudicação / 50% a meio das horas.
<!-- PG_AUTO:RESTRICOES:END -->

### Pedido funcional atual
<!-- PG_AUTO:PEDIDO_ATUAL:START -->
Requisito / pedido atual: Realizar a sessão de revisão de âmbito para go-live seguro e arranque assistido do Odoo Enterprise.
Objetivo de negocio: Centralizar a operação da Virgin Details e reduzir a dependência de PHC GO, folhas de Excel e processos paralelos.
Trigger: Decisão de adjudicação de um modelo híbrido com pacote mínimo de 40 horas de consultoria.
Frequência: Diária
Volumes: 6 utilizadores ativos, 2 empresas previstas (Virgin Details, Lda e Starplast SRLE na Fase 3).
Urgência: Urgente
Critérios de aceitação:
- Faturação certificada em Portugal operacional (Plugin AT e SAF-T validados)
- Estrutura base multiempresa configurada
- Fluxos principais de venda-compra-stock-fatura validados
- Dados migrados e limpos importados com sucesso (contactos, produtos, fornecedores, listas de preços)
- Go-live executado com sucesso e acompanhado
<!-- PG_AUTO:PEDIDO_ATUAL:END -->

### Processo atual
<!-- PG_AUTO:PROCESSO_ATUAL:START -->
Processo atual: Faturação efetuada no PHC GO e gestão operacional descentralizada em folhas de Excel para stocks e compras.
Utilizadores / papeis:
- Nuno Magalhães (Diretor Comercial / Comercial)
- Daniela Martins (Administração / SPOC)
- Cláudio Pereira (Consultor / Parâmetro)
- Pedro Coelho (Gestor de Projeto / Parâmetro)
Exceções conhecidas:
- Starplast SRLE entra apenas em fase posterior (Fase 3)
- Exclusão de automatizações avançadas, CRM completo, relatórios complexos ou produção nesta fase inicial
Aprovações:
- Aprovação manual de orçamentos e compras pela gerência
Documentos envolvidos:
- Orçamentos, Encomendas de Venda, Faturas, Faturas-Recibo, Notas de Crédito, Guias de Transporte, Recibos
Integrações:
- Comunicação AT (faturação e guias de transporte)
- Importação de extratos bancários standard
Reporting esperado:
- Vendas por empresa e consolidadas
- Stock disponível e pendentes de compras/vendas
O que já foi tentado ou validado no standard atual:
- Fluxo standard de vendas e faturação validado
Porque foi considerado insuficiente:
- Apenas as exigências da localização e certificação fiscal PT requerem configuração do plugin AT e SAF-T localizados.
<!-- PG_AUTO:PROCESSO_ATUAL:END -->

### Problema / dor
<!-- PG_AUTO:PROBLEMA_DOR:START -->
Problema / necessidade observada: Necessidade de integração de fluxos (venda-compra-stock-fatura) sob estrutura multiempresa com suporte a faturação portuguesa certificada.
<!-- PG_AUTO:PROBLEMA_DOR:END -->

### Impacto no negócio
<!-- PG_AUTO:IMPACTO_NEGOCIO:START -->
Impacto de negocio: Falta de controlo integrado de inventário, margens comerciais e processos manuais passíveis de erro.
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

- [PREENCHER]

### Dependências de refresh e validação

- [PREENCHER]

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
- [PREENCHER]

### Próximos passos
- [PREENCHER]

## Referências e Histórico

### Referências consultadas

#### Documentação Odoo
- [PREENCHER]

#### Core Odoo
- [PREENCHER]

#### Código do projeto
- [PREENCHER]

### Histórico de marcos de decisão

#### YYYY-MM-DD - [Titulo curto]
Contexto:
- [PREENCHER]

Decisão:
- [PREENCHER]

Riscos / pendências:
- [PREENCHER]

Referências:
- [PREENCHER]
