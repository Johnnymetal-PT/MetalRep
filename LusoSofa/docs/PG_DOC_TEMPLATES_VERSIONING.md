# PG_DOC_TEMPLATES_VERSIONING

## Finalidade

Definir como são versionados, publicados e revertidos os **templates documentais** (`doc_templates/TPL_*.md` + `assets/`) sob o regime PG-004: Odoo Knowledge como source of truth editorial + materialização local committed via `MANIFEST.json`.

Este documento é distinto de [PG_TEMPLATE_VERSIONING.md](PG_TEMPLATE_VERSIONING.md), que trata da versão do framework `_pg_template` no seu conjunto. As duas linhas de versão são **independentes** — um bump MAJOR num template não força bump do framework, e vice-versa.

Materializa T4 do backlog Codex do plano arquitetural em `C:\Users\Utilizador\.claude\plans\objetivo-iniciar-e-fechar-parallel-donut.md`.

## Esquema de versão

Cada template é versionado independentemente em **semver** `MAJOR.MINOR.PATCH`:

- **MAJOR** — quebra de estrutura: secções renomeadas, removidas ou reordenadas; placeholders renomeados; mudança de tom que invalide consumo automatizado.
- **MINOR** — adição compatível: nova secção opcional, novo placeholder com default seguro, expansão de instruções para o agente sem invalidar prompts existentes.
- **PATCH** — correção que não muda contrato: typos, redação, formatação, exemplos.

A versão vive em duas localizações que **devem coincidir** após pull:
1. Property `pg_template_version` do article correspondente no Odoo Knowledge.
2. Entrada `templates[<code>].version` em `doc_templates/MANIFEST.json`.

## Hash de conteúdo

Cada `TPL_*.md` tem SHA256 registado em `templates[<code>].sha256` no manifest, calculado sobre os
bytes do ficheiro materializado: **UTF-8 sem BOM e LF**.

O LF não é uma escolha estética — é a única que funciona. O `.gitattributes` do framework impõe
`*.md text eol=lf`, pelo que é em LF que os ficheiros materializam em qualquer checkout, em qualquer
sistema. Enquanto o pull escreveu CRLF (corrigido em `v2.16.2`), gravava o hash de bytes que
deixavam de existir no primeiro checkout seguinte, e o `pg_smoke_test_repo.ps1` — que compara com
`Get-FileHash` cru, sem normalizar — acusava `hash mismatch` em todos os projetos.

Os **anexos** (`doc_templates/assets/`) têm o SHA256 dos bytes tal como vêm do Odoo, e por isso estão
marcados `-text` no `.gitattributes`: qualquer conversão de fins de linha no checkout altera-lhes os
bytes e desalinha-os do manifest. Foi o que acontecia até `v2.16.2` com os anexos sem bytes nulos —
o `text=auto` tratava-os como texto e o `pg_sync_shared_assets.ps1` avisava de desfasamento em todos
os projetos.

Permite:
- detectar drift sem comparar texto
- validar integridade pós-cópia em `pg_sync_shared_assets.ps1`
- bloquear commits que alterem o `.md` sem actualizar manifest (Fase 3, pre-commit hook opcional)

Hash não é versão. Dois ficheiros podem ter o mesmo hash em versões diferentes só se forem byte-idênticos.

## Versão do framework vs versão do template

`MANIFEST.json` regista também `framework_version` (ex. `v2.10.0`) — corresponde à versão do `_pg_template` no momento do pull.

Releases do framework no `CHANGELOG.md` devem enumerar as versões de templates publicadas:

```
## v2.10.0 — 2026-MM-DD
- doc_templates: TPL_EMAIL_CLIENTE 1.0.0 → 1.1.0 (nova secção "Anexos")
- doc_templates: TPL_ORCAMENTO 1.0.0 → 1.0.1 (correção de redação)
- ...
```

Não há relação algorítmica entre version bump de templates e version bump do framework — são linhas independentes.

## Estados editoriais

Property `pg_template_state` no Odoo:

| Estado | Materializado pelo pull? | Significado |
|---|---|---|
| `draft` | Não | Em edição, não consumível por agentes |
| `published` | Sim | Estável, contrato actual |
| `deprecated` | Sim, com aviso | Ainda consumível por compatibilidade; será removido em próximo MAJOR do framework |

Transição `draft → published` requer reviewer — ver workflow editorial em [PG_004_FASE_0_PREPARATION.md](PG_004_FASE_0_PREPARATION.md).

## Publicação (lifecycle)

1. **Editor** edita o **corpo do article** no Odoo Knowledge (ver "Onde vive o conteúdo" abaixo — não é o `pg_template_body_md`), bump da versão conforme natureza da mudança (MAJOR/MINOR/PATCH).
2. **Editor** muda `pg_template_state` para `draft` enquanto edita.
3. **Reviewer** confere, comenta no article ou aprova.
4. **Reviewer** muda `pg_template_state` para `published`.
5. **Operador do framework** corre `scripts/pg_pull_doc_templates.ps1` no clone local de `_pg_template` (ou usa Action manual no GitHub).
6. **Operador** abre PR em `_pg_template` com o diff em `doc_templates/` + `MANIFEST.json`.
7. PR é mergeado; nova versão entra no `CHANGELOG.md` do framework e é tagged.
8. Repos bootstrapados recebem a nova versão na próxima execução de `scripts/pg_sync_shared_assets.ps1`.

## Onde vive o conteúdo do template (e como não o corromper)

Apesar do nome, **`pg_template_body_md` não contém o template**. Em todos os articles publicados esse campo tem apenas um stub do bootstrap inicial ("Template inicial criado automaticamente", 5 a 80 caracteres). O conteúdo real está sempre no **corpo rich-text** do article.

Isto é imposto pelo código do pull, em `scripts/pg_doc_templates_common.py`:

```python
effective_body = native_body or fallback_body   # o corpo do article ganha
```

O corpo só é ignorado quando está vazio. Como todos os articles têm corpo, `pg_template_body_md` nunca é usado — e inverter a precedência partiria todos os templates de uma vez, substituindo-os pelos stubs.

### O problema: o corpo passa por um conversor HTML→markdown com perdas

`_html_to_markdown_like()` faz `re.sub(r"<[^>]+>", "", text)` e converte `</p>` em `\n\n`. Escrever markdown no editor rich-text destrói:

- **tabelas** — o `<table>` é desmontado e as células ficam texto corrido sem `|`;
- **blocos de código** — as cercas ``` perdem-se e cada linha fica separada por linha em branco;
- **listas aninhadas** — todos os `<li>` colapsam para um nível.

É esta a causa das tabelas partidas nos templates antigos (linha em branco entre cada linha da tabela, o que impede a renderização como tabela).

### A solução: envolver o markdown num `<pre>`

Gravar o corpo como um único elemento `<pre>` com o markdown **HTML-escaped** lá dentro. O conversor remove as etiquetas, o `html.unescape()` repõe os caracteres, e as quebras de linha dentro do `<pre>` sobrevivem intactas — o markdown volta byte a byte igual ao original.

```powershell
$md   = [System.IO.File]::ReadAllText("doc_templates\TPL_<CODIGO>.md")
$body = "<pre>" + [System.Net.WebUtility]::HtmlEncode($md) + "</pre>"
$payload  = @{ body = $body } | ConvertTo-Json -Depth 5 -Compress
$argsJson = '[[<article_id>],' + $payload + ']'
& .\scripts\pg_odoo_query.ps1 -Model knowledge.article -Method write -ArgsJson $argsJson
```

O `HtmlEncode` é obrigatório: sem ele, sequências como `<project_key>` são interpretadas como etiquetas e removidas pelo strip de tags.

Validar sempre o round-trip antes de dar por publicado:

```python
import sys; sys.path.insert(0, "scripts")
from pg_doc_templates_common import _normalize_native_body
assert _normalize_native_body(body_lido_do_odoo) == local.replace("\r\n", "\n").strip()
```

`PONTO POR VALIDAR`: os restantes templates continuam gravados como rich-text e mantêm as tabelas partidas. Republicá-los com esta técnica corrige-os, mas é uma alteração a `pg_template_body_md`/corpo e cai na regra 2-eyes.

## Rollback

### Rollback de um pull mal-formado (antes de PR)
Apagar `doc_templates/` e `MANIFEST.json` no clone local e fazer `git checkout HEAD -- doc_templates/`.

### Rollback de uma versão já mergeada
- `git revert <commit-do-pull>` no `_pg_template`. Novo PR, smoke test confirma snapshot anterior.
- Repos bootstrapados recebem rollback na próxima sincronização.

### Rollback editorial no Odoo (sem alterar framework)
Nova edição que reverte o conteúdo no Odoo Knowledge, com bump de PATCH ou MAJOR consoante o impacto. Não há "delete version" — versão errada fica no histórico do article.

## Compatibilidade backwards

Templates marcados `deprecated`:
- Continuam materializados pelo pull (não desaparecem do `doc_templates/`).
- `MANIFEST.json` regista `state: "deprecated"`; o pull avisa em log.
- São removidos do pull (e por consequência do `doc_templates/`) só em release MAJOR do framework, com nota explícita no `CHANGELOG.md`.

Nunca eliminar `TPL_*.md` em uso sem deprecation prévia documentada.

## Single source of truth — política de override

O Odoo Knowledge é a única origem editorial. Repos bootstrapados não devem editar `doc_templates/TPL_*.md` à mão. Edição manual neste path é detectada pelo:
- smoke test em `scripts/pg_smoke_test_repo.ps1` — hash mismatch entre ficheiro e manifest.
- cron drift-check (Fase 3) — diff entre Odoo e snapshot committed.

Override local legítimo (caso de exceção):
- Criar `doc_templates/overrides/<TPL_CODE>.md` no projeto bootstrapado (fora do contrato do framework).
- Documentar no `PG_CONTEXT.md` do projeto.
- Não esperar que sobreviva a `pg_sync_shared_assets.ps1` se o override for em `doc_templates/TPL_*.md` directamente.

## Mudança de MAJOR — política de breaking changes

Bump MAJOR significa que prompts/automações que assumiam estrutura antiga vão partir-se.

Procedimento:
1. Article com `pg_template_state = published` mantém versão antiga acessível no histórico do Odoo.
2. Nova versão MAJOR substitui no pull; framework version bumps MINOR ou MAJOR conforme impacto agregado.
3. `CHANGELOG.md` do framework dedica entrada à mudança, incluindo:
   - razão da quebra
   - diff conceptual entre versões
   - migration notes para consumidores
4. Repos bootstrapados sobrescrevem na próxima sincronização — não há flag para "ficar na versão antiga". Quem precisar de versão antiga usa override local conforme secção anterior.

## Referências

- Plano arquitetural: `C:\Users\Utilizador\.claude\plans\objetivo-iniciar-e-fechar-parallel-donut.md`
- Preparação Fase 0: [PG_004_FASE_0_PREPARATION.md](PG_004_FASE_0_PREPARATION.md)
- Versão do framework (linha distinta): [PG_TEMPLATE_VERSIONING.md](PG_TEMPLATE_VERSIONING.md)
- Backlog: [PG_FRAMEWORK_IMPROVEMENT_BACKLOG.md](PG_FRAMEWORK_IMPROVEMENT_BACKLOG.md)
- Snapshot operativa: [PG_CURRENT_WORKING_STATE.md](PG_CURRENT_WORKING_STATE.md)

## Operação de pull (T1/T2)

Com a Fase 0 concluida, correr:

```powershell
.\scripts\pg_pull_doc_templates.ps1 -PythonExe 'py'
```

### Credencial (cascata)

A credencial é resolvida por esta ordem, e o script diz em `INFO:` qual usou:

1. `$env:PG_ODOO_KNOWLEDGE_TOKEN` — override por sessão; é também o caminho do CI (secret). Com o
   token no ambiente, `-BaseUrl`, `-Database` e `-Login` valem o que o chamador passar (ou os
   defaults do script).
2. `credentials/brodoo_credentials.json` — segredo partilhado do utilizador de serviço Brodoo, que
   vive no `_pg_template` privado. Daqui vêm `api_key`, `login`, `url` e `db` **em conjunto**, para
   não misturar a chave de uma conta com o login de outra; qualquer parâmetro passado
   explicitamente na linha de comando vence o ficheiro.

Nenhuma das duas disponível → o script falha **antes** de tentar os endpoints, com uma mensagem
única que indica as duas vias de resolução.

O passo 2 existe porque `pg_bootstrap_repo.ps1` chama este script no arranque de cada projeto novo.
Depender só da variável de ambiente fazia o onboarding falhar em qualquer máquina que não fosse a de
quem definiu o token — e o Brodoo já tem leitura no workspace da Knowledge (`FACTO OBSERVADO`:
`knowledge.article` com `pg_template_code`, `pg_template_body_md` e anexos lidos com esta credencial).

### Idempotência (desde `v2.16.2`)

Um pull que não traga alterações **não toca em ficheiro nenhum**. Isto é obrigatório, não uma
conveniência: o pull corre no bootstrap de cada projeto novo, e um pull que sujasse a árvore a cada
onboarding convidava a commits vazios — ou, pior, a commitar um manifest inválido.

Três garantias, e as três estão cobertas por teste ou verificadas com um pull real:

1. **os `TPL_*.md` saem em LF**, alinhados com o `.gitattributes` (ver "Hash de conteúdo");
2. **o `MANIFEST.json` é serializado por `pg_json_canonical.py`**, não pelo `ConvertTo-Json`. O do
   Windows PowerShell 5.1 e o do PowerShell 7 formatam de maneira diferente (indentação cumulativa,
   dois espaços depois de `:`, arrays vazios em três linhas), e o ficheiro era reescrito de ponta a
   ponta consoante o shell de quem corria o pull. A forma passa a depender do conteúdo, não do shell.
   Testes: `scripts/tests/test_pg_json_canonical.py`;
3. **`generated_at` só muda quando o snapshot muda.** Se o manifest gerado for igual ao que está em
   disco à parte do timestamp, preserva-se o timestamp anterior e o promote fica um no-op (o script
   diz `INFO: snapshot sem alteracoes`). Semântica do campo: **quando o snapshot mudou**, não quando
   o pull correu. O `sha256` de cada template cobre todo o conteúdo, pelo que "manifest igual"
   implica "snapshot igual".

Critério de aceitação, verificável a qualquer momento: correr o pull duas vezes seguidas numa árvore
alinhada e `git status doc_templates/` sair vazio nas duas.

Nota operacional:
- Em Odoo 19, o helper usa autenticação JSON-2 com bearer API key e `X-Odoo-Database`, mantendo fallback JSON-RPC para compatibilidade.
- O refresh a partir do Odoo **não é bloqueante no bootstrap**: falhando, o bootstrap avisa e segue
  com a cópia versionada em `doc_templates/`, que é a que o sync partilhado leva para o projeto.

### Drift-check semanal (T5)

Workflow partilhado: `templates/.github/workflows/pg_doc_templates_drift_check.yml`.

`PONTO POR VALIDAR` (2026-07-30): **este ficheiro não existe no `_pg_template`**. O único workflow em
`templates/.github/workflows/` é o `pg_refresh_pg_context.yml`. Confirmar se o drift-check vive num
repositório consumidor, se foi removido, ou se nunca chegou a ser criado — e, em qualquer dos casos,
corrigir esta secção. Enquanto não estiver confirmado, não contar com o drift-check semanal como rede
de segurança do desalinhamento entre a Knowledge e o snapshot.

Secrets esperados no repo consumidor:
- `PG_ODOO_KNOWLEDGE_TOKEN`
- `PG_ODOO_BASE_URL`
- `PG_ODOO_DATABASE`
- `PG_ODOO_LOGIN`
- `PG_ODOO_WORKSPACE_XMLID`

O job falha quando há diff em `doc_templates/` após pull, sinalizando drift entre Odoo e snapshot committed.
