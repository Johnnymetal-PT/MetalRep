# PG-004 Fase 0 — Preparação para execução no Odoo Knowledge

## Objetivo

Concentrar tudo o que é necessário para executar a Fase 0 de [PG-004](PG_FRAMEWORK_IMPROVEMENT_BACKLOG.md#pg-004---centralizar-templates-documentais-no-odoo-knowledge-com-source-of-truth-editorial):

1. resolver os PONTOS POR VALIDAR técnicos com recomendações fundamentadas
2. especificar o workspace, properties e articles a criar no Odoo Knowledge da Parâmetro Global
3. fornecer o conteúdo markdown raw dos 6 templates pronto a colar

Plano arquitetural completo: `C:\Users\Utilizador\.claude\plans\objetivo-iniciar-e-fechar-parallel-donut.md`.

## Resolução dos PONTOS POR VALIDAR

Cada ponto está marcado como `RECOMENDAÇÃO FUNDAMENTADA` (decisão técnica defendida com base em conhecimento Odoo até cutoff Janeiro 2026) ou `DECISÃO HUMANA NECESSÁRIA` (governance/negócio).

### #1 Protocolo RPC — `RECOMENDAÇÃO FUNDAMENTADA`

**Decisão:** **JSON-RPC + API key**.

**Fundamentação:**
- JSON-RPC é o protocolo recomendado oficialmente pelo Odoo desde a versão 8; XML-RPC continua a funcionar mas é considerado legado.
- API keys (introduzidas em Odoo 14, refinadas em 17+) substituem password+login para integrações stateless e são revogáveis por utilizador via UI Odoo (Preferences → Account Security → Developer API Keys).
- Permitem rotacionar credencial sem reset de password humana.

**Implicação técnica em T1:** o helper Python usa `requests` HTTP para `/web/dataset/call_kw` ou `/jsonrpc` com header `Authorization: Bearer <api_key>` (ou via parâmetro Odoo equivalente).

### #2 Properties custom — `RECOMENDAÇÃO FUNDAMENTADA`

**Decisão:** **Extender o modelo `knowledge.article` num addon Odoo mínimo `pg_doc_templates`**, em vez de usar `article_properties_definition` nativo.

**Fundamentação:**
- `article_properties_definition` (Odoo 17+) suporta os tipos `char|boolean|integer|float|date|datetime|selection|tags|many2one|many2many|html|separator`. **Não existe tipo "Text" longo.** Apenas `char` (uma linha, ~256) ou `html` (rich text).
- Como queremos markdown raw lossless (decisão fechada em discovery), `char` não chega e `html` reintroduz conversão HTML→MD (que evitámos por design).
- Properties dinâmicas também não dão garantia de presença obrigatória nem validação no Python; ficam definidas por article ou por parent, com risco de drift entre articles irmãos.
- Um addon Odoo mínimo (3 fields + 1 Selection) tem custo marginal e dá:
  - validação no Python
  - migrações controladas
  - search/filter por estado no Knowledge UI
  - constraints (`UNIQUE(pg_template_code)`)

**Implicação:** criar addon `pg_doc_templates` no Odoo da Parâmetro Global, separado de `pg_brodoo` (este é addon de projeto, não de framework).

### #3 Campo `pg_template_body_md` — `RECOMENDAÇÃO FUNDAMENTADA`

**Decisão:** **Field Python `Text` no addon `pg_doc_templates`** (consequência directa de #2).

**Fundamentação:** mesma de #2. O field `Text` em Odoo aceita conteúdo arbitrário multilinha sem limite prático e preserva newlines/encoding como editado.

### #4 Workflow editorial — `FECHADO (2026-05-26)`

**Decisão final:** **2-eyes desde o início** — qualquer alteração a `pg_template_body_md` ou bump de `pg_template_version` exige `author != reviewer` antes de `pg_template_state = published`. Enforced via record rule + group `pg_doc_templates_reviewer` no addon.

**Excepção operacional documentada — bootstrap inicial dos 6 articles v1.0.0:** operador cria e publica directamente nesse acto único; 2-eyes activa a partir do primeiro bump pós-baseline. Não é relaxamento da regra: é a impossibilidade lógica de aplicar 2-eyes ao acto que carrega o conteúdo inaugural.

**Pré-requisito operacional:** grupo `pg_doc_templates_reviewer` tem de ter **mínimo 2 membros** antes da 1ª edição pós-bootstrap; caso contrário a regra fica logicamente inaplicável.

**Risco residual aceite:** 2-eyes para PATCH trivial (typo) pode degenerar em rubber-stamp se o volume editorial crescer. Mitigação: cultura de revisão crítica; reviewer não-autor declina rever quando o motivo é insuficiente.

### #5 Assets binários — `RECOMENDAÇÃO FUNDAMENTADA`

**Decisão:** **Attachments do article que os referência.**

**Fundamentação:**
- `Template PPTX.pptx` → attachment de `TPL_ORCAMENTO_PPTX`
- `Odoo Orçamentação Estrutura.xlsx` → attachment de `TPL_ORCAMENTO`
- `parametrologo.png` → attachment de `TPL_ORCAMENTO_PPTX` (e referenciado por path no body se outros templates o usarem)

**Justificação:** autoria coerente — o editor do article é o dono do asset. Article dedicado "Assets" partilhado introduz problemas de versionamento independente.

### #6 Frequência editorial — `FECHADO (2026-05-26)`

**Decisão final:** **ad-hoc com drift-check semanal**.

- **Edição:** ad-hoc, sempre que houver necessidade real identificada por editor ou consumidor (consultor/agente).
- **Drift técnico:** cron semanal (Fase 3 do plano) detecta hash mismatch entre Odoo e snapshot committed e abre/atualiza issue.

**Risco residual aceite:** drift-check técnico não detecta drift **conceptual** (templates ficam stale face à prática actual sem que ninguém edite). Mitigação: editores e consultores são responsáveis por sinalizar desactualização sempre que encontrada no uso real. Se este risco se concretizar de forma material, abrir item de backlog para introduzir revisão calendarizada.

### #7 Política de breaking changes — `RECOMENDAÇÃO FUNDAMENTADA`

**Decisão:** **single source of truth — sempre sobrescrever em repos bootstrapados.**

**Fundamentação:** o framework não suporta múltiplas versões coexistindo de um template no mesmo projeto. Bump MAJOR é documentado no `CHANGELOG.md` do framework e nas release notes; projetos bootstrapados recebem-no na próxima sincronização (`pg_sync_shared_assets.ps1`). Quem precisar de manter cópia local não-sincronizada usa override local explícito (fora do contrato do framework).

## Spec do addon Odoo `pg_doc_templates`

Endereço esperado no Odoo Parâmetro Global: módulo a instalar na mesma base que aloja o Knowledge.

### Modelo (`pg_doc_templates/models/knowledge_article.py`)

```python
from odoo import fields, models

class KnowledgeArticle(models.Model):
    _inherit = "knowledge.article"

    pg_template_code = fields.Char(
        string="PG Template Code",
        help="Código único do template (ex. TPL_EMAIL_CLIENTE). Vazio se o article não é um template PG.",
        copy=False, index=True,
    )
    pg_template_version = fields.Char(
        string="PG Template Version",
        help="Semver MAJOR.MINOR.PATCH (ex. 1.0.0).",
        copy=False,
    )
    pg_template_state = fields.Selection(
        selection=[
            ("draft", "Draft"),
            ("published", "Published"),
            ("deprecated", "Deprecated"),
        ],
        string="PG Template State",
        copy=False, index=True,
    )
    pg_template_body_md = fields.Text(
        string="PG Template Body (Markdown)",
        help="Conteúdo markdown raw do template, exatamente como será materializado em doc_templates/.",
        copy=False,
    )

    _sql_constraints = [
        ("pg_template_code_unique",
         "UNIQUE(pg_template_code)",
         "Já existe um article PG template com este código."),
    ]
```

### Security (`pg_doc_templates/security/pg_doc_templates_security.xml`)

- Group `pg_doc_templates_author` — pode editar `pg_template_body_md` e bump version mas não publicar.
- Group `pg_doc_templates_reviewer` — pode mudar `pg_template_state` para `published` (subset de admin Knowledge ou grupo dedicado).
- Record rule: editar requer ser author do article OU membro de `pg_doc_templates_reviewer`.

### Manifest (`pg_doc_templates/__manifest__.py`)

```python
{
    "name": "PG Doc Templates",
    "version": "19.0.1.0.0",
    "category": "Knowledge",
    "summary": "Markdown raw templates source-of-truth para PG Framework",
    "depends": ["knowledge"],
    "data": [
        "security/pg_doc_templates_security.xml",
        "views/knowledge_article_views.xml",
    ],
    "license": "LGPL-3",
}
```

**Nota:** versão `19.0.1.0.0` se a instância Odoo PG é Odoo 19. Caso a instância seja outra versão, ajustar prefixo. (`PONTO POR VALIDAR` operacional, não arquitetural — depende da instância concreta.)

## Spec do workspace e articles

**Workspace:** criar manualmente no Odoo Knowledge.
- Nome: `PG Framework / Doc Templates`
- Visibilidade: interna à Parâmetro Global (não pública).
- XML ID sugerido (se carregado por data file no addon): `pg_doc_templates.workspace_doc_templates`.

**Articles a criar — 6 no total. Versão inicial `1.0.0`, estado `published`:**

| `pg_template_code` | Nome do article | Versão | Estado | Body source |
|---|---|---|---|---|
| `TPL_LEVANTAMENTO_AMBITO` | TPL_LEVANTAMENTO_AMBITO | 1.0.0 | published | conteúdo de [doc_templates/TPL_LEVANTAMENTO_AMBITO.md](../doc_templates/TPL_LEVANTAMENTO_AMBITO.md) |
| `TPL_EMAIL_CLIENTE` | TPL_EMAIL_CLIENTE | 1.0.0 | published | conteúdo de [doc_templates/TPL_EMAIL_CLIENTE.md](../doc_templates/TPL_EMAIL_CLIENTE.md) |
| `TPL_PROPOSTA_TECNICA` | TPL_PROPOSTA_TECNICA | 1.0.0 | published | conteúdo de [doc_templates/TPL_PROPOSTA_TECNICA.md](../doc_templates/TPL_PROPOSTA_TECNICA.md) |
| `TPL_PONTO_SITUACAO` | TPL_PONTO_SITUACAO | 1.0.0 | published | conteúdo de [doc_templates/TPL_PONTO_SITUACAO.md](../doc_templates/TPL_PONTO_SITUACAO.md) |
| `TPL_ORCAMENTO` | TPL_ORCAMENTO | 1.0.0 | published | conteúdo de [doc_templates/TPL_ORCAMENTO.md](../doc_templates/TPL_ORCAMENTO.md) + attachment `Odoo Orçamentação Estrutura.xlsx` |
| `TPL_ORCAMENTO_PPTX` | TPL_ORCAMENTO_PPTX | 1.0.0 | published | conteúdo de [doc_templates/TPL_ORCAMENTO_PPTX.md](../doc_templates/TPL_ORCAMENTO_PPTX.md) + attachments `Template PPTX.pptx`, `parametrologo.png` |

**Para cada article:**
1. Criar article filho do workspace `PG Framework / Doc Templates`.
2. Preencher `name` com o código (ex. `TPL_EMAIL_CLIENTE`).
3. Preencher `pg_template_code`, `pg_template_version=1.0.0`, `pg_template_state=draft` inicialmente.
4. Copiar o ficheiro `doc_templates/TPL_*.md` na íntegra para `pg_template_body_md`. Preservar newlines.
5. Anexar binários do `doc_templates/assets/` que correspondam.
6. Validar visualmente que o conteúdo é igual ao ficheiro fonte (diff zero).
7. Mudar `pg_template_state` para `published`.

## Checklist de fecho da Fase 0

- [ ] Addon `pg_doc_templates` desenvolvido e instalado na instância Odoo PG
- [ ] Workspace `PG Framework / Doc Templates` criado
- [ ] 6 articles criados, com properties preenchidas e estado `published`
- [ ] Attachments binários anexados nos 2 articles aplicáveis
- [ ] API key gerada para a conta de serviço que vai correr o pull (guardada em local seguro, NÃO committed)
- [x] PONTO POR VALIDAR #4 (workflow editorial) — `FECHADO 2026-05-26`: 2-eyes desde o início; excepção operacional só para bootstrap dos 6 articles v1.0.0; ≥2 membros no grupo reviewer pré-requisito
- [x] PONTO POR VALIDAR #6 (frequência editorial) — `FECHADO 2026-05-26`: ad-hoc com drift-check semanal
- [ ] Versão Odoo da instância PG confirmada (impacta versão do manifest do addon)
- [ ] Capacidade de invocar `knowledge.article` via JSON-RPC validada com curl ou Postman a partir de fora da rede Odoo
- [ ] Bruno Pinheiro confirma fecho da Fase 0 e libera T1–T2 do backlog Codex

## Próximo passo após Fase 0

Com a Fase 0 fechada, Codex executa **T1 → T2 → (T3, T4, T5, T6 em paralelo)**, conforme [backlog do plano](../../../../../.claude/plans/objetivo-iniciar-e-fechar-parallel-donut.md). T4 (documentação) já tem draft em [PG_TEMPLATE_VERSIONING.md](PG_TEMPLATE_VERSIONING.md) — adiantado nesta sessão como trabalho paralelizável.
