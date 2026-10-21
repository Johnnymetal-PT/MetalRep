# Nota para IT — Correção do erro RPC_ERROR nas Encomendas de Venda (HMD)

> Para: equipa de IT/sistemas da HMD · De: Parâmetro Global · Data: 2026-06-09

## Problema

Os utilizadores recebem **RPC_ERROR / "Odoo Server Error"** (e ecrã em branco /
OwlError) ao abrir ou listar **Encomendas de Venda** (`sale.order`).

Erro no servidor:
```
psycopg2.errors.UndefinedColumn: column sale_order_line.calc_pc1 does not exist
```

## Causa

O módulo **`hmd_sale_price_calculator`** define em `sale.order.line` vários campos
**armazenados** (`calc_pc1..calc_pc4`, `calc_forn1..4`, `calculator_observation`,
`calc_box_cost`, etc.). O **código foi implantado** (e o serviço reiniciado, por
isso o Odoo já "conhece" os campos e inclui-os nas queries), **mas o módulo nunca
foi atualizado** (`upgrade`) — logo a migração de esquema que **cria as colunas**
na base de dados nunca correu.

Resultado: o Odoo gera `SELECT ... sale_order_line.calc_pc1 ...` para colunas que
não existem → erro de SQL → RPC_ERROR no browser.

> Reiniciar o serviço **carrega o código** mas **não cria as colunas**. Só o
> **upgrade do módulo** corre o `ALTER TABLE`.

## Correção

Atualizar (upgrade) o módulo `hmd_sale_price_calculator` na base de dados `HMD`.

> A **versão do módulo no código foi subida** (`18.0.1.0.0 → 18.0.1.0.2`) para
> sinalizar a alteração de esquema. **Importante:** subir a versão **não cria as
> colunas só com um reinício** do serviço — é preciso que o deploy faça o
> **upgrade** do módulo (passo abaixo) ou que o vosso processo atualize módulos
> cuja versão aumentou. O `-u` aplica o esquema de qualquer forma.

### Pré-requisitos (importante)
1. **Backup completo** da base de dados `HMD` antes de qualquer ação.
2. Confirmar que o **código do módulo no servidor** (pasta de addons) é a versão
   atual que contém os campos `calc_*`. Se o servidor tiver código mais antigo,
   **fazer deploy/pull dessa versão primeiro** e só depois o upgrade.
3. Executar em **janela de baixa atividade** — o upgrade recarrega o registry e
   pode interromper sessões ativas.

### Opção A — pela interface (mais simples)
1. Ativar o **modo de programador** (Definições → Ativar modo de programador).
2. Ir a **Apps**, remover o filtro "Apps" da pesquisa, procurar
   **`hmd_sale_price_calculator`** (ou "HMD Sale Price Calculator").
3. No módulo → menu **⋮ / Atualizar (Upgrade)**.

### Opção B — por linha de comandos
No servidor (ajustar caminhos do Python/odoo-bin e do ficheiro de configuração
da instalação Windows em `C:\ProgGest\Odoo18\...`):
```
odoo-bin -c <caminho>\odoo.conf -d HMD -u hmd_sale_price_calculator --stop-after-init
```
Depois, reiniciar o serviço do Odoo.

## Verificação pós-correção
- Abrir uma **Encomenda de Venda** → já **não** deve dar RPC_ERROR.
- (A Parâmetro pode confirmar via XML-RPC que a coluna `calc_pc1` passou a existir
  e que a leitura de `sale.order` deixou de falhar.)

## Notas
- Esta mesma correção **desbloqueia** o novo relatório de controlo de
  adiantamentos (`pg_sale_advance_report`), que falhava pela mesma razão.
- **Recomendação de processo:** sempre que se faz deploy de alterações que mexem
  em campos/modelos, correr o **upgrade do(s) módulo(s) afetado(s)** logo a seguir
  (não basta reiniciar o serviço). Evita exatamente este tipo de erro.
