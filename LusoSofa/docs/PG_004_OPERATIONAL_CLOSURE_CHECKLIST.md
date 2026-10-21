# PG-004 Operational Closure Checklist

## Objetivo

Fechar operacionalmente o item `PG-004` com critérios verificáveis para:

- templates obrigatórios `TPL_*` publicados no Odoo Knowledge
- credenciais estáveis de execução
- governança contínua `T3/T5/T6` ativa

## Gate de fecho

`PG-004` só passa a `FECHADO` quando todos os blocos abaixo estiverem concluídos.

Estado de execução: `CONCLUIDO EM 2026-05-27`.
Evidência operacional: validação prática executada pelo operador com bootstrap assistido e confirmação visual dos templates/artigos no Odoo Knowledge.

## Bloco A - Templates obrigatórios no Odoo (T3)

Pré-condição: addon `pg_doc_templates` instalado e workspace `PG Framework / Doc Templates` criado.

Checklist:

- [x] `TPL_LEVANTAMENTO_AMBITO` publicado com `pg_template_state = published` e `pg_template_version = 1.0.0` (ou superior)
- [x] `TPL_EMAIL_CLIENTE` publicado com `pg_template_state = published` e `pg_template_version = 1.0.0` (ou superior)
- [x] `TPL_PROPOSTA_TECNICA` publicado com `pg_template_state = published` e `pg_template_version = 1.0.0` (ou superior)
- [x] `TPL_PONTO_SITUACAO` publicado com `pg_template_state = published` e `pg_template_version = 1.0.0` (ou superior)
- [x] `TPL_ORCAMENTO` publicado com attachments esperados e metadados completos
- [x] `TPL_ORCAMENTO_PPTX` publicado com attachments esperados e metadados completos
- [x] `author != reviewer` aplicado nas publicações não-bootstrap
- [x] grupo `pg_doc_templates_reviewer` com mínimo de 2 membros ativos

Evidência mínima:

- export/listagem dos 6 articles com `code`, `state`, `version`, `author`, `reviewer`
- captura de memberships do grupo reviewer

## Bloco B - Credenciais e segredos estáveis (T6)

Checklist:

- [x] conta técnica dedicada criada para pull (`PG Framework Doc Templates Pull`)
- [x] permissões mínimas aplicadas (workspace alvo + leitura de anexos)
- [x] API key emitida para a conta técnica
- [x] política de rotação definida (periodicidade + responsável + procedimento)
- [x] local de armazenamento definido (secret manager corporativo ou GitHub Secrets)
- [x] procedimento de revogação documentado

Segredos operacionais esperados:

- `PG_ODOO_KNOWLEDGE_TOKEN`
- `PG_ODOO_BASE_URL`
- `PG_ODOO_DATABASE`
- `PG_ODOO_LOGIN`
- `PG_ODOO_WORKSPACE_XMLID`

Evidência mínima:

- registo interno da conta técnica
- data da última rotação e owner
- confirmação de presença dos segredos no runtime alvo

## Bloco C - Operação contínua (T5)

Checklist:

- [x] job semanal de drift-check ativo no repositório operativo
- [x] run manual validado sem erro técnico
- [x] cenário de drift validado (falha controlada quando há diff)
- [x] procedimento de resposta a drift documentado e testado

Comando de validação local (manual):

```powershell
.\scripts\pg_pull_doc_templates.ps1 -PythonExe 'py'
```

Sem variáveis de ambiente: a credencial vem de `credentials/brodoo_credentials.json` (ver
[PG_DOC_TEMPLATES_VERSIONING.md](PG_DOC_TEMPLATES_VERSIONING.md), secção "Operação de pull").
Para apontar a outro Odoo ou usar outra conta, definir `$env:PG_ODOO_KNOWLEDGE_TOKEN` e passar
`-BaseUrl`, `-Database` e `-Login`.

Critério de sucesso:

- sem erro no pull
- `doc_templates/MANIFEST.json` coerente com os `TPL_*.md`
- sem alterações inesperadas após pull quando Odoo e snapshot estão alinhados

## Bloco D - Registo de fecho no repo

Checklist:

- [x] atualizar `docs/PG_FRAMEWORK_IMPROVEMENT_BACKLOG.md` para `PG-004 = FECHADO`
- [x] atualizar `docs/PG_CURRENT_WORKING_STATE.md` removendo pendências operacionais de `PG-004`
- [x] registar data de fecho e evidência de execução (link para PR/issue interno)

## Resultado esperado

Com A+B+C+D concluídos:

- Odoo Knowledge torna-se origem editorial efetiva (não apenas intencional)
- `doc_templates/` mantém materialização local auditável
- execução recorrente e gestão de segredos deixam de depender de contexto oral
