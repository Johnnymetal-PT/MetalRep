# PG_TEMPLATE_VERSIONING

## Objetivo do documento
Este documento define uma convenção simples para versionar a evolução do `_pg_template`.
O objetivo e permitir melhorias controladas sem perder coerência, filosofia consultiva nem estabilidade de uso.

## Estado atual do template
- última release fechada: `_pg_template v2.34.0`
- linha operativa dominante: `medicao fiavel do consumo e alinhamento da frota`
- leitura de prontidão atualmente registada: `READY WITH GUARDRAILS`

## Significado das versões
- `v1.0`: primeira versão pronta para uso
- `v1.1`: correções pequenas e melhorias compatíveis
- `v1.x`: melhorias incrementais sem quebra de filosofia
- `v2.0`: mudança estrutural relevante no template
- `v2.x`: melhorias incrementais após a mudança estrutural do template

## Regras para evoluir o template
- manter a filosofia consultiva do template
- evitar alterações desnecessarias fora do objetivo da iteração
- preservar coerência entre templates, docs e configuração
- documentar cada nova versão no `CHANGELOG.md`
- sempre que a evolução mudar comportamento, linguagem ou estrutura de forma relevante, rever o impacto global antes de editar
- seguir a politica operacional definida em `docs/PG_RELEASE_POLICY.md` quando a baseline for promovida a release

## Quando criar nova versão menor
Criar nova versão menor quando houver:
- correções pequenas de texto ou alinhamento documental
- reforcos de clareza sem alterar filosofia do template
- melhorias incrementais compatíveis com a estrutura atual
- nova documentação de apoio que não altera a base do sistema

## Quando criar nova versão maior
Criar nova versão maior quando houver:
- mudança estrutural relevante na organização do template
- alteração significativa da filosofia de decisão consultiva
- substituição ou redefinição de documentos centrais
- quebra de compatibilidade com a forma atual de uso do template

## Boas práticas antes de alterar o template
- analisar primeiro a estrutura atual do repositório
- confirmar o objetivo exato da alteração
- manter o escopo mínimo necessário
- verificar coerência com `README.md`, `templates/AGENTS.md` e restantes docs centrais
- evitar criar burocracia sem ganho real de uso

## Registo da release fechada e da linha operativa atual
- release fechada: `_pg_template v2.34.0`
- estado da release fechada: `READY WITH GUARDRAILS`
- linha operativa atual: `medicao fiavel do consumo e alinhamento da frota`
- estado da linha operativa atual: setup validado em piloto real; adocao depende de servidor persistente e source Odoo local
- resumo da release fechada: framework consultivo Odoo com referência local `.pg_framework/` ao método partilhado, `git clone` do source oficial do Odoo em `vendor/odoo_src`, wrapper local de `AGENTS.md`, intake estruturado do projeto, contratos validados de scope e status sync, troubleshooting operativo documentado, suite automatizada mínima do addon Odoo 19, politica formal de release, smoke test semantico com higiene textual básica, documento operacional dedicado ao addon, `status sync` manual-only explicitado com indicador de stale state, bootstrap assistido, backlog formal da `v2.6` fechado, workflow GitHub para regenerar `PG_CONTEXT.md` a partir dos snapshots `.pg`, drafts factuais de status com aplicação manual ao estado oficial, wizard de onboarding do addon para GitHub e projeto, fluxo consultivo guiado na task para discovery, fit-gap, recomendação final e gate, dashboard operacional centralizado para projetos, runs e tasks com atenção, gate consultivo mínimo antes de AI, classificação final obrigatória `standard -> modulo adicional -> Studio -> custom`, separação explicita entre `approved_scope` e backlog operacional, trilho mínimo de decisão consultiva na task, checklist executável de primeira adoção real para brownfield, runbook A a Z com template de relatório, draft heuristico de enriquecimento de scope na task para `Scope Summary`, `Acceptance Criteria` e `Scope Kind`, geração e aplicação assistida em massa desses drafts ao nível do projeto, dashboard brownfield para consolidação inicial de campos de scope em falta e casos `needs_review`, draft operacional reforcado para brownfield com sinais de backlog operacional, enriquecimento de scope em falta, drafts `needs_review` e runs com erro, pre-preenchimento consultivo assistido na task com sugestoes separadas da decisão final oficial, pipeline de sinais de chatter com filtro, validação, grounding e explainability, apoio LLM controlado apenas para mensagens ambiguas do chatter com JSON estrito, validação forte e fallback deterministico, e backlog da `v2.9` formalmente fechado como release `v2.9.0`
- resumo da linha operativa atual: o medidor de consumo deixou de somar as releituras de cache ao input (v2.22.0), pelo que a métrica-alvo do AUD-03 volta a ser calculável a partir das sessões novas; o histórico anterior fica identificado e fora das médias. Em aberto na mesma linha: a comparação entre espelho e API, por demonstrar com dados da contabilidade nova; o custo por sessão do contrato carregado em todas as sessões; e o alinhamento da frota, hoje com 5 de 32 repositórios na versão corrente
