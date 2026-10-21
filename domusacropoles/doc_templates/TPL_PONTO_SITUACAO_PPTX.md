# TPL_PONTO_SITUACAO_PPTX.md

> Template executável: gerar o **deck PowerPoint de Ponto de Situação** com a
> identidade Parâmetro Global, a partir do conteúdo produzido por `TPL_PONTO_SITUACAO.md`.
> Fonte de verdade deste template: artigo Odoo do workspace `pg_doc_templates`.
> Se for editado localmente, **republicar no Odoo** para não perder no próximo pull.

## Finalidade

`TPL_PONTO_SITUACAO.md` é a fonte do **conteúdo** e do **tom de discurso**; este template
define a **forma** e garante que o deck sai igual em todos os clientes e projetos.
O que segue para o cliente é o **PDF** exportado do deck (Passo 6).

O agente **não desenha slides**. Preenche um payload JSON e corre o gerador. A identidade
visual vive em código (`pg_pptx_identity.py`) e não é redesenhada por sessão — foi essa
improvisação que produziu decks diferentes para clientes diferentes.

## Quando usar

Disparar quando o utilizador pedir, por exemplo: "faz o ponto de situação em pptx",
"ponto de situação em PowerPoint", "deck do ponto de situação", "manda o status ao cliente
em slides".

---

## Passo 0 — Conteúdo aprovado [GATE]

1. O deck **não** é o ponto de partida. Produzir primeiro o ponto de situação em texto
   segundo `TPL_PONTO_SITUACAO.md` (secções 1 a 7) e confirmá-lo com o utilizador.
2. Se o texto ainda não existir, produzi-lo e **pedir validação antes de gerar o deck**.
3. Confirmar `PG_CONTEXT.md`: cliente, projeto, versão/edição Odoo, ambiente, interlocutor.
   Converter datas relativas em absolutas ("esta semana" → "27 de julho de 2026").

## Passo 1 — Carga horária (fonte única)

- As horas vêm **exclusivamente** de `.pg/projects/<project_key>/PG_EFFORT_SYNC.json`:
  `effort.total_hours` (total), `effort.hours_by_employee` (por consultor),
  `effort.entries` (por tarefa, agregado por área).
- Em modo multi-projeto usar **sempre** o ficheiro namespaced. Nunca usar
  `.pg/PG_EFFORT_SYNC.json` da raiz nem `effective_hours` de `tasks.json`.
- Se o ficheiro namespaced não existir, **parar e reportar o bloqueio** — não inventar horas
  nem preencher com "a confirmar" no deck.
- Formatar as horas como no texto (`13h15`), nunca em decimal no conteúdo visível.

## Passo 2 — Construir o payload JSON

Escrever um ficheiro temporário (ex.: `.pg/tmp/ponto_situacao_payload.json`) com este schema.
Campos opcionais omitidos simplesmente não geram o bloco correspondente.

```json
{
  "cliente": "RK.AI",
  "projeto": "Implementação Odoo 19 Enterprise (Odoo.sh) — Reckon.ai",
  "descricao": "Fase de descoberta e levantamento de âmbito",
  "data": "27 de julho de 2026",
  "periodo": "1 a 27 de julho de 2026",
  "preparado_por": "Nuno Oliveira",
  "fase": "Levantamento",

  "resumo": {
    "paragrafo": "Secção 1 do template de texto, em 2 a 4 frases.",
    "focos": ["foco principal 1;", "foco principal 2;"],
    "avaliacao": "Frase de avaliação global da evolução do projeto."
  },

  "areas": [
    {
      "nome": "Gestão de projeto e levantamento funcional",
      "contexto": "Uma frase de contextualização da área.",
      "atividades": ["atividade 1;", "atividade 2;"]
    }
  ],

  "horas": {
    "total": "13h15",
    "por_area": [{ "area": "Configuração geral", "horas": "2h45" }],
    "por_consultor": [{ "consultor": "Nuno Oliveira", "horas": "9h45" }]
  },

  "estado_atual": ["ponto de situação 1;", "ponto de situação 2;"],
  "proximos_passos": ["próximo passo 1;", "próximo passo 2;"],

  "riscos": [
    { "titulo": "Qualidade dos dados de origem", "descricao": "Descrição, impacto e mitigação." }
  ],
  "decisoes_pendentes": [
    { "decisao": "Âmbito do website na Fase 1", "impacto": "Condiciona o plano da Fase 2", "prazo": "05/08" }
  ],

  "acoes_fecho": [
    { "titulo": "Validar o presente ponto de situação", "detalhe": "SPOC do cliente · até 05/08/2026" }
  ],
  "mensagem_fecho": "Ficamos disponíveis para qualquer esclarecimento adicional."
}
```

Mapeamento para as secções de `TPL_PONTO_SITUACAO.md`:

| Secção do texto | Campo do payload | Slide |
|---|---|---|
| — | `cliente`, `projeto`, `data`, `periodo`, `preparado_por` | Capa |
| 1. Resumo executivo | `resumo`, `fase` | 1 |
| 2. Trabalhos realizados | `areas[]` | 2 (nova slide a cada 6 áreas) |
| 3. Carga horária | `horas` | 3 |
| 4. Estado atual + 5. Próximos passos | `estado_atual`, `proximos_passos` | 4 |
| 6. Riscos + 7. Decisões pendentes | `riscos`, `decisoes_pendentes` | 5 (omitido se vazio) |
| Fecho de cortesia | `acoes_fecho`, `mensagem_fecho` | 6 |

Regras de preenchimento:
- **Áreas sem atividade no período não entram** — não criar cartões vazios.
- Máximo de 6 atividades por área (o cartão corta as restantes); se houver mais, agregar.
- `contexto` deve caber em 2 linhas curtas; texto longo desequilibra a grelha de cartões.
- Manter o tom do template de texto: formal, conciso, honesto nos bloqueios.
- Acentuação de português europeu correta em todos os campos.

## Passo 3 — Gerar o deck

```
py -3 -m venv .venv_pptx
.venv_pptx\Scripts\python -m pip install --quiet python-pptx
.venv_pptx\Scripts\python .pg_framework\scripts\pg_build_ponto_situacao_pptx.py ^
    --payload .pg\tmp\ponto_situacao_payload.json ^
    --out outputs\<slug_projeto>\Ponto_Situacao_<Projeto>_<AAAA-MM-DD>.pptx
```

O gerador é determinístico: **mesmo payload, mesmo deck**. Se o resultado não estiver bem,
corrigir o payload — nunca editar o deck à mão nem gerar slides por outra via.

## Passo 4 — Identidade visual (não redesenhar)

A identidade está implementada em `.pg_framework/scripts/pg_pptx_identity.py`, extraída do
ficheiro da marca `doc_templates/assets/Template_Parametro_PowerPoint_Completo 1.pptx`.

O agente **não** define cores, margens, tipos de letra nem capas. Para referência:

- Capa: logótipo em cima à esquerda (8,59 cm), título azul `#0099FF` Aptos Display 32pt,
  subtítulo `#111827` 22pt, bloco de metadados, barra `#111E2D` no fundo. **Sem canto preto** —
  esse elemento não existe no ficheiro da marca.
- Conteúdo: título Aptos Display 21pt `#111827`, subtítulo 6,8pt `#64748B`, régua `#E7EEF5`,
  marca `()` no canto superior direito, rodapé com etiqueta do documento e número azul `#009FE3`.
- Acento: `#009FE3`. Cartões brancos com contorno `#E7EEF5`. Bandas `#F5F9FC`.

Se for preciso um componente que não existe no módulo, **acrescentá-lo ao módulo** (para
todos os templates o passarem a usar), nunca desenhá-lo localmente no gerador.

## Passo 5 — QA visual (obrigatório antes de entregar)

Exportar as slides para PNG e **rever uma a uma** — deteta sobreposições e transbordos:

```powershell
$pp = New-Object -ComObject PowerPoint.Application
$pres = $pp.Presentations.Open("<caminho.pptx>", $true, $true, $false)
$pres.Export("<dir_png>", "PNG", 1600, 900)
$pres.Close(); $pp.Quit()
```

Verificar em cada slide:
- nenhum texto passa o rodapé nem sai do cartão;
- nenhum número quebra linha (`13h15` numa só linha);
- cartões da grelha de áreas equilibrados;
- acentuação correta (sem mojibake).

Se algum bloco transbordar, reduzir o conteúdo do payload (menos bullets, texto mais curto) —
não alterar a geometria da identidade.

## Passo 6 — PDF para o cliente

**O cliente recebe o PDF, nunca o `.pptx`.** O deck é a fonte interna, editável; o anexo do
e-mail é o PDF exportado dele, depois de o deck estar aprovado. Exportar pelo PowerPoint, com o
mesmo nome ao lado do deck (o ficheiro tem de estar fechado no PowerPoint):

```powershell
$pp = New-Object -ComObject PowerPoint.Application
$pres = $pp.Presentations.Open("<caminho.pptx>", $true, $true, $false)
$pres.SaveAs("<caminho.pdf>", 32)   # 32 = ppSaveAsPDF
$pres.Close(); $pp.Quit()
```

Conferir que o PDF tem tantas páginas como o deck tem slides e rever pelo menos a página do
painel executivo. Se o deck mudar depois, voltar a exportar o PDF: os dois têm de dizer o mesmo.

## Passo 7 — Output e limpeza

- Guardar em `outputs/<slug_projeto>/Ponto_Situacao_<Projeto>_<AAAA-MM-DD>.pptx` e `.pdf`.
- Remover `.venv_pptx`, os PNG de pré-visualização e o payload temporário.
- **Não** fazer commit/push sem pedido explícito do utilizador.

## Checklist antes de entregar (falha = não entregar)

- [ ] Conteúdo de texto produzido segundo `TPL_PONTO_SITUACAO.md` e validado.
- [ ] Horas lidas de `PG_EFFORT_SYNC.json` namespaced (nunca estimadas).
- [ ] Total de horas coerente com a soma por área e por consultor.
- [ ] Só áreas com atividade no período.
- [ ] Deck gerado pelo `pg_build_ponto_situacao_pptx.py` (nenhum slide feito à mão).
- [ ] QA visual feito (PNG revistos, sem sobreposições nem transbordos).
- [ ] Acentuação de português europeu correta em todo o deck.
- [ ] PDF exportado do deck aprovado, com o mesmo número de páginas que de slides.
- [ ] Output (`.pptx` e `.pdf`) nomeado e colocado em `outputs/...`; temporários removidos.

## Resposta final ao utilizador

- Indicar o caminho absoluto do **`.pdf` a anexar ao e-mail**, o do `.pptx` e o número de slides.
- Resumir: período · total de horas · nº de áreas · riscos e decisões pendentes assinalados.
- Listar o que ficou `PONTO POR VALIDAR` e perguntar se deve atualizar `PG_CONTEXT.md`
  (secção de artefactos) e/ou versionar o deck e o PDF.
