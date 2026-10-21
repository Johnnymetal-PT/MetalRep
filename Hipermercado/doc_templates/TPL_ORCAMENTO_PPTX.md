# TPL_ORCAMENTO_PPTX.md

> Template executavel: gerar um **deck PowerPoint comercial de orcamento** com a

> identidade Parametro Global, a partir do Excel de orcamento ja produzido

> (ver `TPL_ORCAMENTO.md` / `assets/Estrutura Orcamentacao.xlsx`).

> Fonte de verdade deste template: artigo Odoo do workspace `pg_doc_templates`.

> Se for editado localmente, **republicar no Odoo** para nao perder no proximo pull.

## Finalidade

O Excel e a fonte de numeros; este template transforma-o num deck apresentavel ao

cliente. **Nunca inventar valores**: todos os numeros vem do Excel. O agente nao

recalcula esforco nem tarifas — apenas le, organiza e apresenta.

## Quando usar

Disparar quando o utilizador pedir, por exemplo: "faz um orcamento pptx",

"orcamento em powerpoint", "deck/apresentacao do orcamento", "passa o orcamento a slides".

---

## Passo 0 — Localizar o orcamento (Excel) [GATE]

1. Procurar automaticamente o ficheiro Excel do orcamento, por ordem de prioridade:

   - `outputs/**/*[Oo]rcamento*.xlsx`, depois `docs/**/*[Oo]rcamento*.xlsx`, depois raiz.

   - Escolher o **mais recente** (data no nome e/ou `LastWriteTime`); preferir sufixos

     curados como `_CP`/`_final` quando existirem.

2. Se houver **varios candidatos** ambiguos, listar (nome + data) e **perguntar qual usar**.

3. Se **nao existir** nenhum, **pedir ao utilizador** o `.xlsx` do orcamento (ou o path).

4. Confirmar tambem `PG_CONTEXT.md` (cliente, projeto, versao/edicao Odoo, ambiente,

   ambito/exclusoes) para o texto das slides. Converter nomes/datas relativas em absolutas.

## Passo 1 — Extrair dados do Excel (read-only)

- Ler com `openpyxl` em `data_only=True` (le valores em cache; **nao** depende de Excel).

- Abas tipicas do template `Estrutura Orcamentacao.xlsx`:

  - `Resumo` — totais, pressupostos, exclusoes, pontos por validar, margem.

  - `Servicos` — tabela por fase: `Empresa | Fase | Rubrica | H | Valor` + linhas `... Total`.

  - `Cronograma` — dias (`D`) por fase / distribuicao por semana.

  - `Empresa` — totais H/Valor por empresa.

  - `DB` — fonte detalhada (linha a linha) com funcao/tarifa.

  - `tarefas` / `artigos` — fatores e **tarifas horarias** (ex.: consultor 65, gestor 90).

- Derivar e **validar**: `Total servicos`, `Total horas`, `Total dias`, tarifas, e por

  cada **fase**: nome, horas, valor, dias. Confirmar que `soma das fases == total`.

- Detetar o **tipo de orcamento**:

  - **so servicos** (licenciamento/software a 0 ou ausente) — caso base; ou

  - **servicos + software/licenciamento/componentes** (ex.: hardware, controlo de acessos) —

    nesse caso acrescentar slide(s) dedicada(s) e KPIs de "Total 1.o ano" e "Recorrencia anual".

- O que nao estiver no Excel mas for afirmacao comercial (margem, validade) → marcar como

  pressuposto; o que for incerto → `[POR VALIDAR]`.

## Passo 2 — Ambiente tecnico

- `py -3 -m venv .venv_pptx` e instalar `python-pptx openpyxl` (Pillow opcional).

- Gerar via script Python (`python-pptx`). Remover o venv e ficheiros temporarios no fim.

## Passo 3 — Identidade visual Parametro Global (obrigatoria)

- **Logotipo oficial**: `.pg_framework/doc_templates/assets/image.png`

  (wordmark "parametr()" + "Global technology. Local insights.", ratio ~4.556).

  Capa: canto superior esquerdo, largura ~9 cm. Slides de conteudo: canto superior direito

  do cabecalho, largura ~5 cm. **Nunca** substituir por wordmark de texto.

- **Slide**: 16:9, `33.867 cm x 19.05 cm`.

- **Tipo de letra**: `Aptos`.

- **Paleta** (de `assets/create_parametro_powerpoint_template.py`):

  - BLUE `#0094E9` · DARK `#151D2B` · TEXT `#1F2937` · MUTED `#64748B`

  - LIGHT_LINE `#D5E2EE` · LIGHT_BLUE `#EBF7FF` · WHITE · BLACK

  - acentos: GREEN `#16A34A` · ORANGE `#F9731A`

- **Elementos**: capa branca com canto superior direito preto (forma PIE, rotacao 270);

  cabecalho com titulo (24pt DARK) + subtitulo (9pt MUTED) + linha LIGHT_LINE; rodape com

  `<DocLabel> | Odoo <versao>` a esquerda e numero de pagina (azul) a direita.

- Cuidado de qualidade: `shape.shadow.inherit = False`; caixas de valores curtas com

  `word_wrap = False` para nao quebrarem (ex.: "25 860,00 EUR").

## Passo 4 — Estrutura de slides (minima)

1. **Capa** — "Orcamento de Implementacao Odoo" + cliente/empresa + linha de ambito (Fase) +

   3 KPIs (Total servicos s/IVA · Horas · Dias) + caption "Versao comercial - <data> ..." +

   "Preparado por Parametro Global" + barra DARK no fundo.

2. **Resumo executivo** — paragrafo de resultado proposto; KPIs laterais; bloco "Decisao

   financeira" (total, tarifas, margem, o que esta fora); fila "Proximos passos" numerada.

3. **Ambito incluido** — cards (3xN) com os componentes por fase; nota de ambito/exclusao chave.

4. **Investimento por fase** — tabela `Fase | Horas | Dias | Valor s/IVA` com linha TOTAL

   destacada; nota do modelo de custeio (Valor = horas x tarifa) e se e "so servicos".

5. **Plano de trabalho** — barras por fase proporcionais aos dias (rotular `Xd - Yh`); total

   e nota de sequencia (fases `[POR VALIDAR]` podem reposicionar o pico de esforco).

6. **Pressupostos, exclusoes e proximos passos** — 4 blocos (Pressupostos · Exclusoes ·

   Pontos por validar · Margem e validade) + faixa de fluxo de aprovacao.

- **Slides adicionais** quando aplicavel: Investimento de software/licenciamento; componente

  especifica (ex.: controlo de acessos/hardware) com a sua cotacao e recorrencia.

## Passo 5 — QA visual (obrigatorio antes de entregar)

- Exportar as slides para PNG e **rever visualmente** (deteta sobreposicoes e quebras):

  via PowerPoint COM em Windows —

  `pp=New-Object -ComObject PowerPoint.Application; $pres=$pp.Presentations.Open(<pptx>,$true,$true,$false); $pres.Export(<dir>,"PNG",1400,788)` —

  ou LibreOffice (`soffice --headless --convert-to pdf`) se existir.

- Corrigir overlaps, textos cortados e numeros que quebram linha; **so entregar apos rever**.

## Passo 6 — Output e limpeza

- Guardar em `outputs/<slug_projeto>/Orcamento_<Projeto>_<AAAA-MM-DD>.pptx`

  (mesma pasta do Excel de origem).

- Remover `.venv_pptx`, pasta de preview PNG e scripts temporarios.

- **Nao** fazer commit/push sem pedido explicito do utilizador.

## Regras de conteudo

- Numeros **exclusivamente** do Excel; coerencia fase-a-fase == total verificada.

- Valores **s/IVA** (indicar). Se "so servicos", dize-lo (sem licenciamento/suporte recorrente).

- Marcar `[POR VALIDAR]` o que nao estiver confirmado (volumes, integracoes, n.o utilizadores...).

- Texto fiel ao `PG_CONTEXT.md`: ambito, exclusoes, pressupostos, stakeholders.

- Tom comercial e sobrio; sem promessas tecnicas nao suportadas pelo orcamento.

## Checklist antes de entregar (falha = nao entregar)

- [ ] Excel de origem identificado (e confirmado pelo utilizador se havia ambiguidade).

- [ ] Totais batem: soma das fases = total de horas e de valor.

- [ ] Logotipo oficial `image.png` presente na capa e em todas as slides de conteudo.

- [ ] Identidade respeitada (paleta, fonte, 16:9, capa com canto preto, rodape numerado).

- [ ] Estrutura minima de 6 slides (+ slides de software/componente quando aplicavel).

- [ ] QA visual feito (PNG revistos; sem overlaps nem textos cortados).

- [ ] Numeros marcados `[POR VALIDAR]` quando incertos; valores s/IVA assinalados.

- [ ] Output nomeado e colocado em `outputs/...`; temporarios removidos.

## Resposta final ao utilizador

- Indicar o path absoluto do `.pptx` gerado.

- Resumir: total servicos · (total software/recorrencia, se aplicavel) · horas · dias.

- Listar o que ficou `[POR VALIDAR]` e perguntar se deve atualizar `PG_CONTEXT.md` (seccao

  de artefactos) e/ou versionar o deck.
