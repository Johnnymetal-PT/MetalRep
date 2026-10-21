# PG_TEMPLATE_USAGE_GUIDE

## Objetivo do guia
Este documento descreve como utilizar o `_pg_template` no dia a dia de projetos Odoo.
O objetivo e ajudar a aplicar o template de forma consistente, desde o bootstrap inicial até a resposta consultiva final.

## Principios fundamentais do template
O template foi desenhado para forçar disciplina consultiva antes de desenvolvimento.
Antes de qualquer recomendação relevante, a decisão deve ser sempre validada contra:
- `PG_CONTEXT.md`
- código do projeto
- `vendor/odoo_src`
- documentação oficial da versão ativa

Para esta validação, `codigo do projeto` e `vendor/odoo_src` incluem também fontes locais relevantes expostas no repo atual por symlink, junction ou atalho estrutural equivalente.

O template não existe para acelerar customização.
Existe para reduzir suposições, melhorar a qualidade consultiva e evitar desenvolvimento desnecessario.

## Fluxo de utilização do template num projeto

### 1. Bootstrap do repositório
Aplicar o template ao repositório com `scripts/pg_bootstrap_repo.ps1`.
Isto copia os ficheiros base do template para o projeto e prepara a estrutura mínima de trabalho.
O bootstrap passa também a criar `PG_SCOPE_INTAKE.yaml` e `.pg/PG_SCOPE_SYNC.json`.
O bootstrap passa também a criar `.pg_framework/`, que e a referência local ao framework partilhado.

### 2. Checkout do source Odoo
Preparar o source Odoo com `scripts/pg_clone_odoo_source.cmd`.
Isto cria `vendor/odoo_src/community` e, quando aplicável, `vendor/odoo_src/enterprise`, permitindo consultar diretamente o source da versão ativa sem instalar o ERP localmente.

Fluxo recomendado:
- `.\scripts\pg_clone_odoo_source.cmd NOME_DO_REPO 19.0 community`
- `.\scripts\pg_clone_odoo_source.cmd NOME_DO_REPO 19.0 enterprise`

O script legado `scripts/pg_link_odoo_core.cmd` continua disponível apenas como compatibilidade.

### Discovery antes do PG_CONTEXT
Se o pedido ainda estiver incompleto, ambiguo ou pouco maduro para decisão, usar primeiro `docs/PG_DISCOVERY_PROMPT.md`.
Este ficheiro ajuda a qualificar o pedido, pedir evidência e confirmar se já existe base suficiente para preencher ou atualizar o `PG_CONTEXT.md`.

### 3. Preenchimento inicial do contexto
Preencher primeiro o `PG_SCOPE_INTAKE.yaml` e depois materializar o `PG_CONTEXT.md`.

Fluxo recomendado:
- inicializar ou rever `PG_SCOPE_INTAKE.yaml`
- correr `scripts/pg_build_pg_context.ps1`
- confirmar no `PG_CONTEXT.md` a informação inicial do projeto

O intake deve concentrar informação como:
- versão do Odoo
- edição
- ambiente
- restrições contratuais
- pedido funcional atual
- processo atual
- problema e impacto no negocio

### 4. Inicio de sessão com o contrato base
Começar a interação com o agente a partir do contrato local do repositório:
- `AGENTS.md`
- `.pg_framework/templates/AGENTS_SHARED.md`
- `PG_CONTEXT.md`

Quando for necessário reforcar discovery, fit-gap ou decisão consultiva, usar também os prompts operacionais presentes em `docs/`.
No repositório do projeto, o `AGENTS.md` local passa a funcionar como wrapper para `.pg_framework/templates/AGENTS_SHARED.md`.
Para Claude Code, o `CLAUDE.md` local importa `AGENTS.md` e o mesmo `AGENTS_SHARED.md`, mantendo paridade com Codex.

### 5. Análise de requisitos
Para cada requisito, analisar primeiro o contexto funcional, o processo atual, o problema real e a evidência disponível.
Se faltar contexto critico, pedir clarificação antes de fechar recomendação.

### 6. Fit-gap framing antes da decisão
Quando o discovery já estiver claro, mas ainda for cedo para fechar recomendação, usar `docs/PG_FIT_GAP_FRAMING_PROMPT.md`.
Esta etapa ajuda a mapear rapidamente o encaixe no Odoo, distinguir fit de gap e perceber se já existe base para passar a decisão consultiva.

### 7. Uso do decision engine quando necessário
Quando a análise for mais sensível, ambigua ou estrutural, usar também `docs/PG_DECISION_ENGINE_PROMPT.md`.
Este ficheiro ajuda a aprofundar a decisão consultiva antes de qualquer proposta final.

### 8. Âmbito vindo do Odoo
Quando existir um snapshot atualizado em `.pg/PG_SCOPE_SYNC.json`, validar primeiro com `scripts/pg_validate_scope_sync.ps1` e depois aplicar `scripts/pg_apply_scope_sync.ps1`.
Esta etapa atualiza os blocos auto-geridos de âmbito no `PG_CONTEXT.md`, sem reescrever a memória consultiva.
Nesta snapshot, o contrato operativo do lado Odoo deve ser lido no código e nos testes do addon `pg_brodoo`, em especial payload builders, sync services e smoke tests.

### 9. Consulta de padrões consultivos
Quando o requisito se assemelhar a um caso recorrente, consultar `docs/PG_CONSULTING_DECISION_PATTERNS.md`.
Este ficheiro serve para acelerar triagem e lembrar opções normalmente relevantes.

### 10. Consulta de aprendizagens anteriores
Quando for útil recuperar experiência consultiva previa, consultar `docs/PG_PROJECT_LEARNINGS.md`.
Este ficheiro ajuda a evitar erros repetidos e a reconhecer sinais recorrentes.

### 11. Verificação final antes da resposta
Antes de fechar uma recomendação consultiva importante, aplicar `docs/PG_PRE_RESPONSE_CHECKLIST.md`.
Esta checklist funciona como camada final de prudência antes da resposta.

## Avaliação obrigatória de soluções
Em qualquer requisito, a ordem obrigatória de decisão e:
1. configuração standard existente
2. módulo standard adicional
3. Odoo Studio
4. custom

Esta ordem não deve ser saltada.
Na avaliação de módulo standard adicional, a análise deve considerar também o `vendor/odoo_src` da versão ativa, incluindo módulos novos do Odoo.

## Atualização de contexto
O `PG_CONTEXT.md` deve ser atualizado sempre que houver alteração relevante no entendimento do projeto.

Atualizar quando:
- uma decisão consultiva relevante e tomada
- uma restrição contratual e descoberta ou confirmada
- uma análise funcional importante e concluida
- surgem novos riscos, bloqueios ou próximos passos relevantes

## Registo de aprendizagens
Adicionar entradas em `docs/PG_PROJECT_LEARNINGS.md` quando surgir uma aprendizagem reutilizável com valor para futuros projetos.

Exemplos:
- um módulo standard adicional evitou custom desnecessario
- Studio parecia suficiente mas revelou fragilidade
- o problema real era de processo e não de funcionalidade
- um pedido aparente de custom era apenas preferência operacional

## Registo de tokens por checkpoint
Cada sessão deve registar eventos em `.pg/tokens/consumption.jsonl`:
- `session_open` no arranque da sessão
- `session_progress` em checkpoints intermedios quando houver trabalho material
- `session_close` no fecho da sessão, quando aplicável

Fluxo recomendado:
- `scripts/pg_log_token_consumption.ps1` para append dos eventos
- `scripts/pg_validate_token_consumption.ps1` para validar o ficheiro

Uma sessão interrompida continua valida sem `session_close`, desde que tenha pelo menos `session_open`.

## Quando atualizar cada ficheiro

| Ficheiro | Quando atualizar |
|---|---|
| `PG_CONTEXT.md` | Quando houver nova decisão consultiva, nova restrição, conclusão funcional relevante ou mudança do estado atual do projeto |
| `PG_SCOPE_INTAKE.yaml` | Quando o âmbito inicial, restrições, processo ou input estruturado do projeto mudarem |
| `.pg/PG_SCOPE_SYNC.json` | Quando houver novo snapshot factual de âmbito publicado a partir do Odoo |
| `.pg/PG_EFFORT_SYNC.json` | Quando houver novo snapshot factual agregado de esforco publicado para contexto operacional |
| `.pg/tokens/consumption.jsonl` | Em cada sessão, com checkpoints `session_open`, `session_progress` e `session_close` |
| `PG_PROJECT_LEARNINGS.md` | Quando surgir uma aprendizagem reutilizável observada em projeto real |
| `PG_CONSULTING_DECISION_PATTERNS.md` | Quando um padrão recorrente novo ficar claro e útil para triagem futura |
| `AGENTS.md` | Quando for necessário ajustar regras estruturais de comportamento do agente no template |
| `AGENTS.md` e `.pg_framework/templates/AGENTS_SHARED.md` | Quando for necessário ajustar o contrato base de comportamento do agente |

## Regras importantes
- nunca alterar `vendor/odoo_src`
- nunca recomendar custom sem justificar porque as alternativas anteriores falharam
- separar sempre `FACTO OBSERVADO`, `INFERENCIA` e `PONTO POR VALIDAR`
- nunca fechar recomendação definitiva sem evidência suficiente
- se a evidência for insuficiente, apresentar apenas recomendação preliminar

## Nota sobre versionamento
O template esta atualmente na release fechada `v2.9.1`.
Futuras alterações devem respeitar as regras definidas em `docs/PG_TEMPLATE_VERSIONING.md`.
As evoluções relevantes devem ser registadas em `CHANGELOG.md`.
