# TPL_ORCAMENTO.md

 	​

Objetivo:

Gerar um orcamento comercial e tecnico completo para o projeto atual, com base no contexto real do repositorio, na transcricao/reuniao mais recente e na **validacao obrigatoria do core Odoo da versao ativa em `vendor/odoo_src`**.

## Entradas obrigatorias (nesta ordem)

1. `PG_CONTEXT.md` — em especial: Versao Odoo, Edicao (Community/Enterprise), Ambiente, restricoes contratuais.

2. `.pg/projects/<project_key>/...` quando existir modo multi-projeto (se `project_key` nao estiver claro, perguntar ao utilizador).

3. `docs/` com foco em: transcricao da reuniao mais recente e proposta/levantamento existente (`.docx`, `.md`, `.pdf`).

4. **Estado real do produto/servico quando existir** (ex.: URL do site, base de dados) — analisar antes de assumir que algo nao existe.

5. `doc_templates/assets/Estrutura Orçamentação.xlsx`.

6. **`vendor/odoo_src` da versao ativa — CONSULTA OBRIGATORIA E VERIFICAVEL (ver Bloco A).**

7. Documentacao oficial Odoo da mesma versao.

## BLOCO A — Verificacao obrigatoria do core Odoo (GATE BLOQUEANTE)

> Este bloco corre **antes** de produzir qualquer hora ou valor. Sem ele, o orcamento nao pode ser fechado.

1. **Resolver o source.** Confirmar que `vendor/odoo_src` esta acessivel. Se for symlink/junction/atalho, resolver o alvo real (ex.: `(Get-Item vendor/odoo_src).Target` ou `cmd /c dir vendor`). Se nao estiver acessivel → **PARAR** e pedir relink, sem inventar cobertura.

2. **Confirmar versao e edicao** no `PG_CONTEXT.md` antes de citar modulos. Nunca citar modulo `enterprise/*` se a edicao for Community.

3. **Para CADA requisito**, executar descoberta real no source (glob/grep/dir) e registar os paths encontrados. Exemplos:
   - procurar o modulo por nome: `community/addons/<m>`, `enterprise/<m>`;
   - procurar capacidade por conteudo: campos/metodos em `models/*.py`, vistas em `views/*.xml`.

4. **Aplicar a ordem obrigatoria** (nunca saltar passos), suportada pelos achados do core:
   1. configuracao standard ja disponivel,
   2. **modulo standard adicional** (mesmo que nao instalado — procurar no source),
   3. custom.

5. **Proibido classificar algo como custom** sem antes provar, com path do core, que nenhum modulo standard cobre (total ou parcialmente) o requisito. A "ausencia" de standard e ela propria um `FACTO` que exige a busca feita.

6. **Citacao obrigatoria:** cada item da tabela de cobertura tem de citar pelo menos um path real verificado em `vendor/odoo_src` (ex.: `community/addons/website_sale_stock/models/product_template.py`). Nomes "de memoria" sem path não são aceites.

## Regras de decisao

- Priorizar standard/core Odoo antes de qualquer custom (ver Bloco A).

- Para `Modulo standard adicional`, classificar cobertura como `TOTAL`, `PARCIAL` ou `PARCIAL COM ADAPTACAO DE PROCESSO` e explicar implicacoes de adocao.

- Quando houver incerteza funcional critica, marcar `PONTO POR VALIDAR`.

- Nao inventar valores comerciais sem base; assumir como estimativa e sinalizar premissas (tarifa lida de `artigos`/`tarefas` do Excel).

- Distinguir sempre: `FACTO OBSERVADO` (confirmado no core/codigo/docs) · `INFERENCIA` · `PONTO POR VALIDAR`. Uma classificacao de cobertura so e `FACTO` se verificada em `vendor/odoo_src`.

## Processo obrigatorio de geracao

1. Ler o contexto factual (objetivo comercial, ambito fase 1, exclusoes, dependencias, restricoes contratuais, versao+edicao).

2. Ler a reuniao/transcricao mais recente e extrair requisitos acionaveis.

3. Analisar o estado real existente (ex.: site em producao) antes de orcar — distinguir "construir" de "reestruturar".

4. **Executar o BLOCO A** e construir a tabela de cobertura com paths verificados.

5. Classificar cada requisito em: coberto por standard / parcial (com adaptacao) / fora de escopo base / opcional.

6. Construir orcamento de servicos por fases (descricao, horas, valor) usando a tarifa do modelo.

7. Construir simulacao de software **apenas quando aplicavel**: se o cliente ja tiver Odoo/licenciamento/certificacao, registar essas rubricas a `0` e indica-lo explicitamente (orcamento "so servicos").

8. Gerar entregaveis:
   - `docs/ORCAMENTO_PRELIMINAR_<PROJETO>_<AAAA-MM-DD>.md`
   - `docs/ORCAMENTO_<PROJETO>_<AAAA-MM-DD>.xlsx`

## Estrutura minima do Markdown final

1. Enquadramento
2. Escopo incluido (fase 1)
3. Escopo excluido
4. Premissas comerciais e tecnicas
5. **Mapa de cobertura core Odoo (com paths verificados em `vendor/odoo_src`)**
6. Orcamento de servicos (horas e valor)
7. Orcamento de software (0 quando ja contratado pelo cliente; indicar)
8. Total 1o ano e total anual recorrente
9. Opcionais fora do valor base (classificados standard/parcial/custom, nunca custom por defeito)
10. Pontos por validar para fecho
11. Referencias consultadas (paths de `vendor/odoo_src` + links doc oficial da versao)

## Regras para Excel

- Manter sempre a estrutura original do template `Estrutura Orçamentação.xlsx`. Nao criar workbook alternativo, nao renomear abas, nao remover formulas/pivots.

- Fluxo: copiar o template → preencher apenas inputs (aba `DB`: Empresa/Fase/Rubrica/tarefa/funcao/horas; e aba `Software`) → `RefreshAll` → validar totais.

- **Validar o modelo de custeio antes de entregar:** confirmar que `Valor = horas x tarifa` corresponde ao esperado. Se a aba `tarefas` tiver multiplicadores (coluna de fator) que dupliquem o valor, confirmar com o utilizador se e margem intencional; caso contrario, por o fator a `1`.

- Orcamento "so servicos": por a `0` os inputs de `Software`/licenciamento/certificacao e o `Apoio Apos Venda` no `Resumo`.

- Se houver bloqueio tecnico numa aba de pivot: nao contornar com novo ficheiro; atualizar a fonte (`DB`) e ativar refresh; se continuar bloqueado, reportar exatamente o bloqueio e os campos em falta.

## Qualidade minima antes de entregar (checklist — falha = nao entregar)

- [ ] **Bloco A executado**: existe pelo menos um path real de `vendor/odoo_src` por cada requisito standard da tabela de cobertura.
- [ ] **Nenhum modulo citado e fantasma**: cada path citado existe no source da versao/edicao ativa.
- [ ] **Nenhum item classificado como custom** sem justificacao da ausencia de standard (com a busca citada).
- [ ] Edicao respeitada (sem `enterprise/*` em Community).
- [ ] Totais batem entre `Serviços`, `Software` e `Resumo` apos `RefreshAll`; modelo de custeio validado (sem duplicacao indevida).
- [ ] Horas e valores sem celulas vazias no escopo incluido.
- [ ] `PG_CONTEXT.md` e reuniao recente refletidos no texto.
- [ ] O que for suposicao esta marcado como `PONTO POR VALIDAR`.
- [ ] Estrutura do Excel preservada (abas, formulas, pivots, layout).

## Formato de resposta do agente ao utilizador

- Indicar ficheiros gerados com path absoluto.
- Resumir: total servicos · total software anual · total 1o ano · total anual recorrente.
- **Listar os modulos core verificados (com path)** que sustentam o orcamento.
- Listar 3 a 8 pontos por validar para fechar a proposta final.
