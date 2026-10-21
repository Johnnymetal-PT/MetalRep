# PG_CURRENT_WORKING_STATE

## Objetivo

Servir como ponto de entrada operativo único para a linha atual do `_pg_template`.

Este documento responde, de forma curta, a três perguntas:

1. qual é a frente dominante atual
2. qual é o bloqueio principal
3. qual é o próximo passo lógico

## O que este documento NÃO diz

**A versão da release fechada não vive aqui.** Vive na primeira entrada do [CHANGELOG.md](../CHANGELOG.md), e está registada em [PG_TEMPLATE_VERSIONING.md](PG_TEMPLATE_VERSIONING.md).

Não é uma omissão: é a correção de um defeito que já se repetiu. Este documento chegou a anunciar `v2.9.1` com o `CHANGELOG` em `v2.21.2` — **doze releases de atraso**, num ficheiro declarado como ponto de entrada operativo único e lido por agentes. O `BLK-000` do backlog existiu precisamente para corrigir essa divergência, foi dado por fechado, e ela regressou.

A causa não foi desleixo: foi guardar o mesmo facto em dois sítios e confiar em que alguém se lembrasse de atualizar os dois. Um facto derivável não se copia. Há um teste que impede a versão de voltar a ser escrita aqui (`scripts/tests/test_pg_docs_coerencia.py`).

O que resta neste documento é o que **não** é derivável: juízo sobre a frente dominante, o bloqueio e o passo seguinte. Esse decai na mesma, por isso vai datado — e a data é o que diz a quem lê se pode confiar nele.

## Estado atual — 2026-09-10

- backlog histórico: [PG_FRAMEWORK_IMPROVEMENT_BACKLOG.md](PG_FRAMEWORK_IMPROVEMENT_BACKLOG.md) (`BLK-000` a `PG-007`, quase todo fechado; `PG-005` adiado, `PG-007` F2 em aberto)
- frente dominante atual: **as conclusões da auditoria de 2026-09-10**, que não estão nesse backlog. A tese: a construção ultrapassou a adoção e a medição — quase todas as rondas terminaram em «implementado e fundido no `_pg_template`», e o valor só existe quando a frota corre a versão, o agente sabe que a capacidade existe, e algo mede o objetivo

Estado das cinco frentes dessa auditoria:

| # | frente | estado |
|---|---|---|
| 1 | medição do consumo | **fechada** — o medidor somava as releituras de cache ao input e inflacionava as sessões em duas a três ordens de grandeza |
| 2 | propagação à frota | **fechada na parte humana** — perímetro honesto, cobertura visível, 25 de 33 repositórios na versão corrente. O gatilho automático continua deliberadamente desligado |
| 3 | custo por sessão do contrato | **aberta, e é a próxima** — o `AGENTS_SHARED.md` são ~11k tokens carregados em todas as sessões de todos os projetos |
| 4 | testar o que tem consequência | **parcial** — o guard de migração passou a ter 30 testes validados por mutação, e as suites Python passaram a ser corridas; restam ~35 `.ps1` sem teste |
| 5 | higiene com dentes | **parcial** — a raiz fechou-se a despejos de consulta; feita a poda dos ramos já fundidos |

## Bloqueio principal

Sem bloqueio técnico ativo no `_pg_template`.

Na frota, oito repositórios não alinham e nenhum deles se resolve com código:

- cinco têm trabalho de outra pessoa por publicar (entre 4 e 228 commits) — um `push` do alinhador levá-lo-ia atrás
- o `ancoravip` tem um documento local que colide com o publicado
- o `domusacropoles` declara a branch `Teste`, que não existe no remoto (há `teste`, `Teste-cap` e `Teste-remote`, e o git em Windows casa com a errada por ser insensível a maiúsculas)
- o `Parametro_Global` é o repositório do addon e não tem branch Brodoo declarada, o que o mantém de fora por construção

## Próximo passo lógico

**Frente 3 — cortar o custo por sessão do contrato.** Separar o que vale sempre (branch, ordem de decisão, redação, fontes de verdade) do que vale numa sessão em vinte (guard de migração, resolução do nome da base, MCP, HTML de email, geração de Word). O mecanismo de carregamento a pedido já existe e já está sincronizado na frota: as *skills*.

É a única frente que paga em todas as sessões futuras, e é também a única onde um erro degrada todas as sessões de todos os projetos ao mesmo tempo — por isso exige plano e validação num repositório piloto antes de propagar.

## Source of truth para trabalho operativo

- [CHANGELOG.md](../CHANGELOG.md) — o que mudou e porquê; é a fonte da versão
- [PG_RELEASE_POLICY.md](PG_RELEASE_POLICY.md) — como se fecha e propaga uma release
- [PG_FRAMEWORK_IMPROVEMENT_BACKLOG.md](PG_FRAMEWORK_IMPROVEMENT_BACKLOG.md) — backlog histórico `BLK-000`..`PG-007`
- [BRODOO_GUIA_OPERACIONAL.md](BRODOO_GUIA_OPERACIONAL.md) e [BRODOO_AGENTES_AI_GUIA.md](BRODOO_AGENTES_AI_GUIA.md)
- [../README.md](../README.md)
- código e testes em `pg_brodoo/`

## Regra sobre conflito

Quando houver conflito entre memória histórica e o estado atual:

- prevalece o código atual
- prevalecem os paths publicados pelo publisher atual
- prevalece este documento para identificar frente dominante e próximo passo lógico — **desde que a data acima seja recente**. Se estiver meses atrasada, este documento é histórico como outro qualquer, e a fonte passa a ser o `CHANGELOG.md`
