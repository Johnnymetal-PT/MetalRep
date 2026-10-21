# PG_CONTENT_HYGIENE

## Objetivo
Este documento define regras simples para manter coerência semantica e higiene textual nos artefactos factuais da framework.

Não substitui os contratos técnicos dos snapshots.
Serve para reduzir ruido operacional em:
- `PG_CONTEXT.md`
- `.pg/PG_SCOPE_SYNC.json`

## Checklist curta antes de publicar

Antes de publicar `scope sync`, confirmar:

- não existem textos com `Ã`, `Â`, `â€` ou `�`
- não existem placeholders como `[PREENCHER]` ou `[PONTO POR VALIDAR]` em campos que já deviam estar fechados
- o `scope_summary` é um resumo curado e não repete texto bruto da tarefa de origem

## Encoding e line endings

Na baseline atual:
- os scripts que escrevem `markdown`, `yaml` e `json` usam UTF-8 explícito via `scripts/pg_file_io_common.ps1`
- `.editorconfig` e `.gitattributes` devem permanecer sincronizados nos repositórios bootstrapados

Distinção importante (encoding vs redação):
- esta secção cobre apenas mojibake e encoding, ou seja, corrupção de caracteres já acentuados
- a perda de acentos por o agente escrever em ASCII (`decisao` em vez de `decisão`) NÃO é um problema de encoding; é um problema de geração de conteúdo
- a regra que obriga a acentuação correta na redação vive em `.pg_framework/templates/AGENTS_SHARED.md`, secção `Regras de redação em português europeu`, e é verificada em `.pg_framework/docs/PG_PRE_RESPONSE_CHECKLIST.md`

Se aparecer mojibake:
1. corrigir o conteúdo na origem
2. republicar o snapshot no Odoo
3. voltar a correr `pg_refresh_pg_context.ps1`

## Como corrigir conteúdo mal preenchido

### Caso: placeholders após publish real
Correção:
- preencher no Odoo o campo em falta
- publicar novo snapshot
- não editar manualmente o snapshot no Git, salvo exceção controlada

### Caso: texto corrompido no contexto
Correção:
- confirmar que a repo tem `.editorconfig` e `.gitattributes`
- usar os scripts atuais do `_pg_template`
- regenerar o `PG_CONTEXT.md` a partir dos snapshots

## Ligação com o smoke test

O `scripts/pg_smoke_test_repo.ps1` passou a sinalizar:
- mojibake
- portugues escrito em ASCII (acentuação em falta) no `PG_CONTEXT.md`
- placeholders em snapshots publicados
- duplicações semanticas dentro de listas

## Validação de acentuação em documentos gerados

Para verificar (ou corrigir) acentuação de portugues europeu em qualquer documento gerado:
- relatório: `scripts/pg_validate_pt_accents.ps1 -Path <ficheiro-ou-pasta>`
- correção automática das palavras ineqivocas: `scripts/pg_validate_pt_accents.ps1 -Path <...> -Fix`

Regras do validador:
- achados de confianca alta (mapa `scripts/pg_pt_accent_map.tsv`) falham o gate com exit code 1
- achados heuristicos (sufixos tipo `-cao`, `-ncia`, `-avel`) são apenas avisos e nunca corrigidos automaticamente
- ignora blocos de código, spans inline, URLs, identificadores TODO-MAIUSCULOS e a marca `Parametro`
- homografos ambiguos (`esta`, `so`, `e`, `publico`) ficam de fora para evitar correções erradas; rever a mao
- **ficheiros binarios sao sempre ignorados** (`.docx`, `.xlsx`, `.pptx`, `.pdf`, imagens, arquivos),
  mesmo quando o caminho é passado explicitamente: um `.docx` é um ZIP e, lido como texto,
  produz achados falsos a partir de bytes comprimidos
- em scans de pasta o filtro `-Include` tem default `*.md`; aceita vários padrões separados
  por vírgula (`-Include '*.md,*.ps1'`), para funcionar também via `powershell -File`

Cuidado com `-Fix` fora de prosa:
- a regra de redação cobre também **comentários em código e docstrings**, pelo que correr o
  validador sobre `.ps1`/`.py` é legítimo
- mas uma palavra do mapa pode coincidir com um **identificador** (uma variável chamada
  `titulo` viraria `título` e partiria o código). Nesses ficheiros o script avisa e **o diff
  tem de ser revisto**; em `.md`/`.txt`/`.rst`/`.adoc` não há essa reserva

O validador é um auxiliar, não um gate suficiente. O mapa cobre as palavras conhecidas; uma
palavra ausente do mapa passa em silêncio, e por isso a leitura humana continua a ser o último
filtro antes de fechar um documento formal.

Regressão coberta por `scripts/pg_test_pt_accents.ps1`.

## Fins de linha nos artefactos extraídos

Os `.txt`/`.md` de `doc_templates/assets_extracted/` estão sob `*.txt text eol=lf` no
`.gitattributes`, e o extractor (`pg_extract_doc_template_assets.py`) já escreve LF
explicitamente. Mesmo assim, uma árvore de trabalho pode ficar com **CRLF** nesses ficheiros
quando foram materializados por um `git checkout` anterior à entrada da regra `eol=lf`.

Sintomas:
- os ficheiros aparecem permanentemente como `modified` no `git status`, mas `git diff` não
  mostra alteração nenhuma (o git normaliza na comparação, a árvore é que tem outros bytes)
- `pg_sync_shared_assets.ps1` copia byte a byte (`Copy-Item`), pelo que propaga o CRLF para
  todos os projetos bootstrapados
- o `pg_smoke_test_repo.ps1` compara SHA256 dos bytes e passa a avisar
  `doc_templates desfasado do framework partilhado` — um falso positivo com causa real

Diagnóstico e correção:

```
git ls-files --eol            # procurar linhas com w/crlf e attr/...eol=lf
```

Para corrigir, deixar o **git** reescrever os ficheiros (não reescrever à mão, senão o
`status` continua marcado): apagar os ficheiros afetados e voltar a materializá-los com
`git checkout -- <caminhos>`. Confirmar no fim que `git ls-files --eol` não tem nenhum
`w/crlf` com `eol=lf`.
