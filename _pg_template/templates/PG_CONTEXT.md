# PG_CONTEXT - Memória funcional e decisória

> Fonte de verdade do estado funcional, técnico e consultivo do projeto.
> Alguns blocos marcados com `PG_AUTO` podem ser atualizados automaticamente a partir de `PG_SCOPE_INTAKE.yaml`, `.pg/PG_SCOPE_SYNC.json` e scripts do template.

## Estado Oficial do Projeto

### Identificação do projeto
<!-- PG_AUTO:IDENTIFICACAO:START -->
Nome do projeto: [PREENCHER]
Cliente / unidade: [PREENCHER]
Resumo funcional do repositório: [PREENCHER]
Fase atual do projeto: [PONTO POR VALIDAR]
<!-- PG_AUTO:IDENTIFICACAO:END -->

### Parâmetros Odoo ativos
Versão do Odoo: [PONTO POR VALIDAR]
Edição: [PONTO POR VALIDAR]
Ambiente: [PONTO POR VALIDAR]
Path do core: [PONTO POR VALIDAR]
Path source Enterprise: [NAO CONFIGURADO]
Documentação oficial base: [PONTO POR VALIDAR]
Documentação Studio: [PONTO POR VALIDAR]
Documentação Developer: [PONTO POR VALIDAR]
Última sincronização de âmbito: [NAO EXECUTADA]
Fonte do âmbito sincronizado: [PONTO POR VALIDAR]
Última sincronização automática: [NAO EXECUTADA]

### Restrições do projeto
<!-- PG_AUTO:RESTRICOES:START -->
Configuração standard permitida?: [PONTO POR VALIDAR]
Módulos standard adicionais permitidos?: [PONTO POR VALIDAR]
Odoo Studio ja aplicado no ambiente?: [PONTO POR VALIDAR]
Custom permitido?: [PONTO POR VALIDAR]
Restrições contratuais adicionais: [PONTO POR VALIDAR]
<!-- PG_AUTO:RESTRICOES:END -->

### Pedido funcional atual
<!-- PG_AUTO:PEDIDO_ATUAL:START -->
Requisito / pedido atual: [Descrever o requisito atual com linguagem de negócio.]
Objetivo de negócio: [PREENCHER]
Trigger: [PREENCHER]
Frequência: [PREENCHER]
Volumes: [PREENCHER]
Urgência: [PREENCHER]
Critérios de aceitação:
- [PREENCHER]
<!-- PG_AUTO:PEDIDO_ATUAL:END -->

### Processo atual
<!-- PG_AUTO:PROCESSO_ATUAL:START -->
Processo atual: [Descrever o processo existente, atores, documentos e etapas.]
Utilizadores / papeis:
- [PREENCHER]
Exceções conhecidas:
- [PREENCHER]
Aprovações:
- [PREENCHER]
Documentos envolvidos:
- [PREENCHER]
Integrações:
- [PREENCHER]
Reporting esperado:
- [PREENCHER]
O que já foi tentado ou validado no standard atual:
- [PREENCHER]
Porque foi considerado insuficiente:
- [PREENCHER]
<!-- PG_AUTO:PROCESSO_ATUAL:END -->

### Problema / dor
<!-- PG_AUTO:PROBLEMA_DOR:START -->
Problema / necessidade observada: [Descrever o problema observado ou a necessidade do negócio.]
<!-- PG_AUTO:PROBLEMA_DOR:END -->

### Impacto no negócio
<!-- PG_AUTO:IMPACTO_NEGOCIO:START -->
Impacto de negócio: [Descrever impacto operacional, financeiro, risco, compliance ou UX.]
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

### Esforço factual publicado

Derivado de `.pg/PG_EFFORT_SYNC.json` quando esse snapshot existir no projeto bootstrapado.
Este bloco continua de leitura e não substitui o snapshot factual.

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

### 3. Custom
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

### Odoo Studio existente (diagnóstico, não opção)
**Criar em Studio está proibido** (ver `AGENTS_SHARED.md`). Esta secção existe porque o Studio **já aplicado** muda o que o sistema faz e **não aparece no código nem em diff** — ler o repositório não basta para estabelecer o comportamento atual.
Estado: [NAO ANALISADO]
Vistas, menus, campos `x_` e automações encontrados:
- [PREENCHER]
Impacto observado no comportamento:
- [PREENCHER]
Destino proposto (migrar para standard, migrar para módulo versionado, manter):
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
