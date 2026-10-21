# TPL_IMPORTACAO_INICIAL_CONTACTOS_PRODUTOS.md

# Template — Importação Inicial de Dados (Contactos e Produtos) + Formação de Faturação · Odoo PT

## Finalidade

Documento reutilizável para preparar, ordenar e executar a **importação inicial de contactos e produtos** num projeto Odoo com localização portuguesa, e para enquadrar a **formação de faturação** ao cliente. Serve simultaneamente de checklist metodológica para a equipa e de base ao documento de *handoff* por projeto (o que está feito, que decisões foram tomadas e o que falta confirmar/pedir ao cliente).

## Tom de Discurso

- Operacional e acionável — orientado a "o que fazer" e "o que pedir ao cliente"

- Preciso — distingue `FACTO OBSERVADO`, `INFERÊNCIA` e `PONTO POR VALIDAR`

- Não assume comportamentos do Odoo nem nomes de registos sem verificação no source/base

- Compreensível por consultor e por cliente

## Instruções para o Agente

1. Confirmar a **versão Odoo** do projeto. Este template assume comportamentos do **Odoo 19**; validar diferenças se a série for outra (especialmente `type`/`is_storable`, categorias raiz e localização PT).

2. Confirmar **edição, ambiente e empresa-alvo** (`company_id`) antes de usar qualquer External ID com prefixo `account.<N>_...`.

3. Substituir todos os `[placeholders]` por dados do projeto (`PG_CONTEXT.md` + contexto da sessão).

4. Consultar sempre o `vendor/odoo_src` da versão ativa **e os módulos custom do repo** antes de assumir nomes de campos, impostos ou posições fiscais.

5. Verificar os **External IDs reais** de impostos e posições fiscais na base do cliente (importador → "Possible Values", ou Definições → Técnico → Identificadores Externos). Nunca assumir os nomes do template base do `l10n_pt`.

6. Versionar o documento a cada revisão significativa.

---

## Estrutura do Documento

---

# [Nome do Projecto] — Importação Inicial e Formação

**Versão:** 1.0 · **Data:** DD/MM/AAAA · **Autor:** [Nome] · **Estado:** Rascunho / Validado

| Item | Valor |
|---|---|
| Cliente / Empresa(s) | [empresa 1] (company_id=[N]) · [empresa 2, se aplicável] |
| Versão / Edição Odoo | [ex.: Enterprise 19.0] · [SaaS / Odoo.sh / on-premise] |
| Localização | Portugal — faturação certificada (séries, ATCUD, QR, SAF-T) |
| Empresa-alvo desta importação | [company_id] |
| Módulos custom relevantes | [ex.: módulo PT de stock/SAF-T, se existir] |

---

## 1. Ordem de importação (regra geral)

Importar **por esta ordem** — cada passo cria as dependências do seguinte:

| # | Conjunto | Modelo | Depende de | Notas |
|---|---|---|---|---|
| 1 | Contactos (empresas + indivíduos) | `res.partner` | — | Base de clientes/fornecedores |
| 2 | Correção de posição fiscal (não nacionais) | `res.partner` (update) | 1 | Ver §3.6 — campo por empresa |
| 3 | Categorias de produto | `product.category` | — | Ver §3.2 e §3.3 |
| 4 | Fornecedores em falta | `res.partner` | — | Só os que não existirem (§3.7) |
| 5 | Produtos | `product.template` | 3, 4 | Referenciam categorias e fornecedores |

> Usar sempre a coluna **`id` (External ID)** para permitir **atualizar sem duplicar** em reimportações. Ficheiros em **UTF-8**, separador vírgula.

---

## 2. Princípio dos External IDs

- Atribuir um External ID estável a cada registo (`[prefixo]_categ_*`, `[prefixo]_prod_<sku>`, etc.) torna a importação **idempotente** (reimportar atualiza, não duplica).
- Para registos **já existentes** na base (criados por importações anteriores ou pela localização), **reutilizar o External ID existente** em vez de criar um novo.

---

## 3. Decisões técnicas e *gotchas* (Odoo 19 PT) — conhecimento reutilizável

> Estas notas são aprendizagens recorrentes; confirmar sempre na versão do projeto.

**3.1 Tipo de produto e stock** — Odoo 19 usa `type = consu` (Goods) ou `service`; **não existe o tipo "product"**. O controlo de inventário passou a ser o booleano **`is_storable`** (módulo stock). "Artigo físico com gestão de stock" → `type=consu` + `is_storable=1`.

**3.2 Categorias raiz** — Odoo 19 **não tem a raiz "All"**; as raízes standard são *Goods / Expenses / Services*. Pendurar as categorias do catálogo sob a raiz adequada (tipicamente `product.product_category_goods`) com hierarquia própria via `parent_id/id`.

**3.3 Marca** — não há campo "Marca" standard. Mapear a marca para **Categoria** (permite listas de preços/relatórios por marca) ou para **Etiquetas de Produto** (`product_tag_ids`). Decidir e documentar.

**3.4 Categoria Fiscal AT (comunicação de inventário)** — se o projeto tiver o módulo PT de stock/SAF-T (campo tipo `l10n_pt_legal_categ`), classificar os produtos: `M` Mercadorias, `P` Matérias-primas, `A` Produtos acabados, `S` Subprodutos, `T` Produtos em curso. Para um **distribuidor (compra e revende)** → tudo `M`. O campo na **categoria** serve de *default* herdado pelos produtos — preencher na categoria, não produto a produto (override só nas exceções).

**3.5 Impostos** — em PT os impostos partilham **nome** ("23%", "0%") entre venda e compra → importar por **nome é ambíguo**. Usar **External ID** por empresa (ex.: `account.<N>_iva_pt_sale_normal`, `account.<N>_iva_pt_purchase_normal`, `..._purchase_isenta`). Pré-requisito: plano de contas PT instalado.

**3.6 Posições fiscais** — **verificar os External IDs reais na base** (variam por instalação e por empresa). Não assumir os nomes do template base. Regra de classificação típica:
- Nacional continente → posição "Continente/Nacional"
- UE com NIF de empresa → "Intracomunitário B2B"
- Particular UE sem NIF → "Intracomunitário B2C"
- Fora da UE (inclui Reino Unido, pós-Brexit) → "Extracomunitário"
- Regiões autónomas (Madeira/Açores) e casos especiais (inversão do sujeito passivo) → posições próprias

A posição fiscal (`property_account_position_id`) é **company-dependent** (definida por empresa).

**3.7 Fornecedores** — antes de criar, **procurar variantes do nome** nos contactos já importados (evita duplicados). Reutilizar o existente (mesmo que esteja só como cliente — completar `supplier_rank`/etiqueta). Criar apenas os que faltam e **completar dados fiscais (NIF, morada, país)** antes da 1.ª fatura de compra.

**3.8 Contas na categoria de produto** — com **valorização periódica** (manual), só relevam a *conta de rendimentos* (vendas) e a *conta de gastos* (compras); as contas de stock **não são usadas**. A localização PT já define *defaults* da empresa (income/expense), por isso muitas vezes a categoria pode ficar **sem contas preenchidas**. Só preencher na categoria para separar famílias em contas diferentes. Com **valorização automática**, aí sim configurar as contas de stock.

---

## 4. Multiempresa

- Artigos e contactos com `company_id` **vazio = partilhados** por todas as empresas; preenchido = **exclusivo** dessa empresa.
- Campos *company-dependent* (posição fiscal, contas, impostos) têm valor **por empresa** — a mesma importação só configura a empresa em contexto.
- Decisão de negócio a documentar: **catálogo/contactos partilhados** vs. **separados/preços por empresa**. Atenção a entidades que sejam simultaneamente fornecedor e empresa do grupo.

---

## 5. O que CONFIRMAR / PEDIR AO CLIENTE (checklist)

- [ ] Empresa-alvo (`company_id`) e plano de contas PT instalado
- [ ] External IDs reais de impostos e posições fiscais (verificados na base)
- [ ] Regra de classificação de categorias do catálogo (e reclassificar genéricas/"A classificar")
- [ ] Dados fiscais completos dos fornecedores criados de novo
- [ ] Confirmação de identidade de fornecedores reutilizados (nome ≠ marca)
- [ ] Regra multiempresa: partilhado vs. exclusivo
- [ ] Posições fiscais B2B vs B2C; e necessidade de repetir para outras empresas
- [ ] Séries de faturação registadas/comunicadas à AT antes do go-live
- [ ] Método de valorização de inventário (periódico vs. automático)

---

## 6. Formação de faturação (PT certificada) — guião

1. **Enquadramento PT:** série + numeração sequencial, ATCUD, QR code, cadeia inalterável, SAF-T.
2. **Dados base** que sustentam a fatura (cliente com NIF/país, produto com IVA, série).
3. **Fluxo:** Venda → Confirmar → Criar Fatura → rever rascunho → **Confirmar (publicar)**.
4. **Irreversibilidade:** publicada não se edita nem apaga — corrige-se com **Nota de Crédito**.
5. **Enviar** (email/PDF) e **registar pagamento**.
6. **Compras:** encomenda → receção → fatura de fornecedor.
7. **Relembrar** as pendências de dados (categorias, fornecedores, multiempresa, posições fiscais).
8. **Checklist** final para os utilizadores e canal de suporte.

---

## 7. Pendências típicas pós-importação

- Reclassificar categorias genéricas ("A classificar") na árvore real.
- Completar dados fiscais dos fornecedores novos.
- Confirmar e marcar corretamente fornecedores reutilizados.
- Decidir e aplicar a regra multiempresa.
- Repetir posições fiscais/impostos para a 2.ª empresa, se aplicável.

---

## 8. Validação e referências

- `PG_CONTEXT.md` do projeto
- `vendor/odoo_src/[versão]` (módulos product, stock, l10n_pt) e módulos custom do repo
- Documentação oficial Odoo da versão ativa
- Distinguir `FACTO OBSERVADO` / `INFERÊNCIA` / `PONTO POR VALIDAR` em cada conclusão relevante

_Última atualização do template: AAAA-MM-DD._
