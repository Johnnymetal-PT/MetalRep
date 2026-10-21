# pg_bd_geral_security

Perfil de acesso restrito para o utilizador **"BD Geral User"** (Odoo 17.0 Enterprise, on-premise).

> Estado: **ESQUELETO / RASCUNHO**. Contém as partes fundamentadas no source
> (`vendor/odoo_src` 17.0). Há pontos que dependem de dados da BD viva e estão
> marcados como `PONTO POR VALIDAR` — **não instalar em produção** antes de os
> resolver. Validar primeiro em **staging**.

## Princípio de desenho

Os ACLs do Odoo são **aditivos (OR)**: um utilizador acumula os direitos de
todos os grupos que tem e **não existe "negar"**. Logo, para os requisitos
"excluir eliminar" e "só visualização" **não se pode** atribuir o grupo standard
e tirar-lhe o `unlink`. A solução é criar grupos `pg_*` com os ACLs exatos e
**não atribuir** o grupo standard que concederia o `unlink`/escrita.

## Mapa requisito → implementação

| # | Requisito | Implementação | Fonte (odoo_src 17.0) |
|---|-----------|---------------|------------------------|
| 1 | BD Geral: acesso total | Atribuir grupo da app custom **BD Geral** | `PONTO POR VALIDAR` — módulo não está neste repo |
| 2 | Vendas total **sem eliminar** | **Config standard**: atribuir `sales_team.group_sale_salesman_all_leads` (e **não** `group_sale_manager`). O salesman já **não** tem `unlink` em `sale.order` | `sale/security/ir.model.access.csv` |
| 3 | Contactos **sem eliminar** | Grupo custom `pg_group_contacts_no_delete` (res.partner 1,1,1,0) | `base` ACL: só `group_partner_manager` dá unlink |
| 4 | Manufatura: só ver OP+OT | Grupo custom `pg_group_mrp_readonly` (mrp.production/workorder/bom read) + expor menus | `mrp` ACL: `group_mrp_user` dá full CRUD; não há read-only nativo |
| 5 | Reparações: só ver | Grupo custom `pg_group_repair_readonly` (repair.order read) + menu | `repair`: só via `stock.group_stock_user` full CRUD |
| 6 | Inventário: ver stock, **excluir Componentes/Defects** | Grupo custom `pg_group_inventory_stock_readonly` + **record rule** em `stock.quant` excluindo as **localizações** `WH/Stock/COMPONENTES` e `WH/Stock/DEFECTS` | `stock` ACL + localizações da BD |
| 7 | Qualidade: ver verificações/instruções + download imagens | Grupo custom `pg_group_quality_readonly` (quality.check/point read). Anexos/imagens seguem o acesso de leitura ao registo pai | `quality` ACL |
| 8 | Projeto: edição **sem eliminar** | **`project.group_project_user`** (menu+canalização+read) **+** `pg_group_project_no_delete` (acrescenta write/create em project.project) **+** view override (`delete="0"`, scoped ao grupo) que esconde o botão. Eliminar de projetos = bloqueio real (ACL) + botão escondido | `project` ACL/menus |
| 9 | Painéis: ver + editar | **Config standard**: `spreadsheet_dashboard.group_dashboard_manager` | `spreadsheet_dashboard` ACL |
| 10 | To-Do, Conhecimento, Documentos: acesso total | **Config standard**: To-Do/Conhecimento via `base.group_user`; Documentos via `documents.group_documents_manager` | `project_todo`, `knowledge`, `documents` |
| 11 | Ocultar Compras, Despesas, Serviço de Campo, CRM, Contabilidade, Shop Floor | Não atribuir os grupos respetivos (menus deixam de aparecer) — **exceto CRM** (ver Riscos) | menus gated por grupo |
| 12 | Aba lateral: criar tarefas e notas | `base.group_user` + módulo `note`/atividades (`PONTO POR VALIDAR` o módulo) | systray |

## Atribuição de grupos ao utilizador (perfil final)

Standard (a marcar no ecrã de Utilizador ou via dados):
- `sales_team.group_sale_salesman_all_leads`
- `spreadsheet_dashboard.group_dashboard_manager`
- `documents.group_documents_manager`
- grupo da app **BD Geral** (a confirmar)

Custom (deste módulo):
- `pg_group_contacts_no_delete`
- `pg_group_mrp_readonly`
- `pg_group_repair_readonly`
- `pg_group_quality_readonly`
- `pg_group_inventory_stock_readonly`
- `pg_group_project_no_delete`

**Não** atribuir: `purchase.*`, `hr_expense.*`, `industry_fsm.*`, `account.*`,
`mrp_workorder.group_mrp_wo_shop_floor`, `group_sale_manager`,
`base.group_partner_manager`, `project.group_project_user/manager`,
`mrp.group_mrp_user`, `stock.group_stock_user/manager`.

## Estado / pontos em aberto

**Resolvido (fundamentado no source e implementado):**
- ✅ **CRM**: re-gate global de `crm.crm_menu_root` → `pg_group_crm_visible`, com
  `post_init_hook` que migra os utilizadores que hoje veem CRM (ver `hooks.py` e
  a sequência de deploy). Decisão do cliente: re-gate global.
- ✅ **Menus read-only**: `mrp.menu_mrp_root`, `mrp.menu_mrp_workorder_todo`,
  `repair.menu_repair_order`, `quality_control.menu_quality_root`,
  `stock.menu_stock_root` expostos aos grupos `pg_*` (xmlids confirmados).
- ✅ **Componentes** (item 6): domínio real `bom_line_ids` + `purchase_ok`.
- ✅ **Model ids de Qualidade**: `quality.model_quality_{check,point}`.
- ✅ **BD Geral**: modelo Studio `x_bd_geral`, **grupo Studio dedicado** — atribui-se
  no ecrã de Utilizador (xmlid lido na instância).

- ✅ **Despesas**: re-gate de `hr_expense.menu_hr_expense_root` (estava **sem grupo**,
  visível a todos) → `pg_group_expenses_visible`, com migração de todos os
  empregados no `post_init_hook`. Decisão do cliente: re-gate global.
- ✅ **Inventário/Products**: `stock.menu_stock_inventory_control` ("Products") não
  tem grupo → fica visível via o root exposto. A lista de Produtos mostra o stock
  on-hand. "Reporting" (manager-only) fica oculto de propósito.

- ✅ **Grupo BD Geral**: grupo Studio **"BD GERAL"** id `107` (xmlid `__custom__.group_107`).
  Atribuir ao utilizador via ecrã de Utilizador. NÃO referenciar no módulo: os
  xmlids `__custom__.*` do Studio não são portáveis entre bases de dados.

- ✅ **Componentes E Defects** (item 6): confirmado na BD que **ambos são localizações
  de stock** (`WH/Stock/COMPONENTES` e `WH/Stock/DEFECTS`). O record rule em
  `stock.quant` exclui as duas por `complete_name`. As restantes localizações
  (FABRIC COM, FABRIC PROVIDED…, IMOBILIZADOS, PROTOTIPAGEM, SAMPLES) ficam visíveis.

**Decisão menor em aberto:**
1. A regra é a nível de `stock.quant` (vista de stock por localização). A **lista de
   Produtos** (Inventário → Produtos) mostra produtos com on-hand agregado e **não**
   filtra por localização — logo um produto que só exista em COMPONENTES/DEFECTS ainda
   aparece nessa lista (com a sua quantidade). Confirmar se isto é aceitável ou se se
   deve **também** ocultar esses produtos da lista (exigiria critério a nível de produto,
   ex.: categoria/marca dos componentes — a definir).

**Verificação em staging:** `groups_id` das *actions* de produto (Inventário) e
confirmar que o menu do Inventário não foi alterado por Studio.

## ⚠️ Menus standard re-gated manualmente nesta BD (Studio)

Esta BD tem menus standard **re-gated manualmente** (campo *Visibilidade* / Studio),
ao contrário do standard. Caso conhecido:
- **Conhecimento** (`knowledge.knowledge_menu_root`): no standard **não tem grupos**
  (visível a todos os internos); nesta BD estava restrito a **"Administração / Admin"**.
  Resolveu-se acrescentando o grupo **"BD GERAL"** à aba *Visibilidade* do menu
  (alteração **manual** na BD — não está neste módulo; recriar a BD perde-a).

Implicação: ao validar apps que "não aparecem", verificar sempre o campo *Grupos*
do menu em **Técnico → Interface do Utilizador → Menus** antes de assumir bug do perfil.
Se quisermos tornar isto reproduzível, podemos capturar estas exposições de menu no
módulo (à semelhança de Contactos/Projeto) — a decidir.

## Parâmetro de deploy obrigatório (exclusão do utilizador-alvo)

Antes de instalar/atualizar, definir em **Definições > Técnico > Parâmetros do Sistema**:

```
pg_bd_geral_security.excluded_user_logins = <login do BD Geral User>
```

Os logins aqui listados ficam **fora** da migração CRM/Despesas — é assim que o
BD Geral User deixa de ver CRM e Despesas, enquanto os restantes mantêm acesso.
Se ficar vazio, ninguém é excluído (o hook regista um aviso).

## Instalação (staging)

```
# (servidor on-premise / staging)
./odoo-bin -d <db_staging> -u pg_bd_geral_security --stop-after-init
```
Depois atribuir os grupos ao utilizador "BD Geral User" e validar caso a caso.
