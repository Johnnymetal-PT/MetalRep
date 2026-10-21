# Canais Odoo do cliente × Templates documentais

Mapeamento de como os **canais Odoo por projeto** (helper `pg_odoo_client_query.ps1`,
modelo `pg.odoo.connection`) fundamentam a produção documental (`doc_templates/TPL_*`)
com **dados reais**, em vez de memória ou inferência.

## Os quatro canais (recordar)

| Canal | Alvo | Helper | Uso |
|---|---|---|---|
| **Brodoo** | Odoo da Parâmetro Global | `pg_odoo_query.ps1` | gestão de projeto (planeamento, entregáveis, espelho) |
| **Cliente `production`** | Odoo de produção do cliente | `pg_odoo_client_query.ps1 -Purpose production` | análise de **adoção** e estado real (JSON-RPC ou MCP Odoo 19+) |
| **Cliente `brodoo_dev`** | Odoo da branch `brodoo` (Staging) | `pg_odoo_client_query.ps1 -Purpose brodoo_dev` | **desenvolvimento** |
| **Cliente `client_test`** | base de testes/validação do cliente | `pg_odoo_client_query.ps1 -Purpose client_test` | **validação pelo cliente**; destino da promoção de dados vinda do `brodoo_dev` |

Nota de transporte: O `pg_odoo_client_query.ps1` deteta automaticamente se a instância Odoo do cliente usa o protocolo clássico JSON-RPC ou o protocolo nativo MCP (Model Context Protocol, em Odoo 19+ / SaaS 19.4+), garantindo consultas uniformes. Consultas MCP diretas podem também usar `pg_odoo_mcp_query.ps1`.

Nas **escritas** (migração/promoção de dados) a finalidade deixa de ser só uma etiqueta de
leitura: é o que autoriza a escrita. Passa obrigatoriamente por
`scripts/pg_odoo_migration_guard.py` — ver "Migração de dados entre bases Odoo" no
`AGENTS_SHARED.md`.

Regra transversal: `read_mode=api` (caro); preferir sempre primeiro os artefactos
espelhados (`.pg/...`). Acesso sempre **comandado pela equipa**.

## Mapa template × canal × dados

| Template | Canal | Dados reais a injetar | Consulta exemplo |
|---|---|---|---|
| `TPL_LEVANTAMENTO_AMBITO` | production | módulos instalados, empresas, utilizadores, idioma/país | `ir.module.module [state=installed]`; `res.company`; `res.users [share=false]` |
| `TPL_PROPOSTA_TECNICA` | production | módulos instalados (passo 1 vs 2 da ordem de decisão), módulos custom (`pg_*`/não-standard), Studio (`ir.model` custom) | `ir.module.module [state=installed]`; `ir.model [state=manual]` |
| `TPL_STATUS_SEMANAL` | production | métricas de adoção: utilizadores ativos, registos criados por modelo no período | `res.users`; `mail.message`/contagens por modelo-chave |
| `TPL_ORCAMENTO` | production | sinais de complexidade: nº módulos, volumes de dados nos modelos-chave | `search_count` em `sale.order`/`account.move`/`stock.move`… |
| `TPL_IMPORTACAO_INICIAL_CONTACTOS_PRODUTOS` | production / brodoo_dev | estado atual de `res.partner` e `product.template` (contagens, duplicados) | `res.partner search_count`; `product.template search_count` |
| Validação de desenvolvimento | brodoo_dev | config/dados em construção no Staging antes de propor ao cliente | modelos relevantes no build brodoo |

## Notas de método

- A **ordem de decisão obrigatória** (standard já disponível → standard adicional →
  Studio → custom) passa a assentar em **módulos realmente instalados** (canal
  `production`), não em memória. Um módulo `state=installed` é passo 1; um standard
  existente mas não instalado é passo 2.
- Distinguir sempre `FACTO OBSERVADO` (lido do Odoo do cliente via canal) de
  `INFERÊNCIA`. Citar a consulta usada (modelo/método/domínio) como evidência.
- Antes de usar o canal, confirmar que a `pg.odoo.connection` do projeto está
  **válida** (as credenciais podem estar desatualizadas — usar "Testar ligação").

## Estado / próximos passos

- Este documento é o **mapa**; o aprofundamento por template (campos exatos, formato
  de saída) é uma passagem dedicada por template, quando cada um for revisto.
- Higiene de dados: refrescar as `pg.odoo.connection` cujas credenciais estejam
  desatualizadas (verificado: RO-GLUING OK; EPOCA e jmmgroup precisam de refresh).
