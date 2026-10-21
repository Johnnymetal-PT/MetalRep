{
    "name": "PG CRM Project Opportunities",
    "summary": "Liga CRM opportunities a projects com smart button bidirecional.",
    "version": "18.0.1.0.0",
    "author": "Parametro Global",
    "license": "LGPL-3",
    "description": """
PG CRM Project Opportunities (HMD)
==================================

a) Objetivo de negocio
----------------------
A HMD trabalha por projeto (1 cliente, 1 obra). Para gerir bem o
pipeline comercial, e util ver no projeto que oportunidades CRM o
originaram e, inversamente, ver na oportunidade a que projeto ela ja
deu origem. O standard nao tem esse linker. Este modulo adiciona:
  - campo `pg_project_id` em `crm.lead` (oportunidade) - ligacao
    manual ao projeto;
  - smart button "CRM Opportunities" no projeto, contando
    oportunidades ligadas pelo campo acima PLUS oportunidades
    indiretamente ligadas via sale.order (fallback automatico).

b) Pre-requisitos
-----------------
- Odoo 18.0 Enterprise (versao ativa em PG_CONTEXT.md).
- Modulos `crm`, `project`, `sale_crm`, `sale_project`.
- Para ver o smart button, o utilizador tem de pertencer ao grupo
  `sales_team.group_sale_salesman` (vendedor).

c) Como funciona (tecnico)
--------------------------
1. `crm.lead` (`models/pg_crm_lead.py`): adiciona `pg_project_id`
   Many2one a `project.project`. View injeta o campo na form do
   lead (depois do tipo).

2. `project.project` (`models/pg_project_project.py`):
   - `pg_crm_opportunity_count` (Integer, computed, compute_sudo).
   - `_pg_get_opportunity_ids_per_project()`:
       a) procura `crm.lead` com `pg_project_id` in self.ids e
          `type=opportunity` -> ligacao direta;
       b) usa `_fetch_sale_order_items_per_project_id()` (helper do
          `sale_project`) para obter sale.order.lines por projeto,
          depois pega os `opportunity_id` dos respetivos sale.orders
          -> ligacao indireta.
   - `action_pg_view_crm_opportunities`: abre `crm.crm_lead_opportunities`
     com dominio restrito aos opportunity_ids agregados; se for
     so 1, abre direto em form.
   - `_get_stat_buttons` override: adiciona o botao na barra de
     stat buttons (sequence 29) - aparece so para users sales.

3. Views (`views/pg_crm_lead_views.xml`,
   `views/pg_project_project_views.xml`): adicionam o campo na lead
   form e o botao smart no projeto.

d) Passo a passo de utilizacao
------------------------------
1. Instalar `pg_crm_project_opportunities`.
2. CRM > abrir/criar uma oportunidade. Aparece o campo "Project" -
   selecionar o projeto correspondente. Salvar.
3. Project > abrir o projeto. Smart button "CRM Opportunities"
   mostra a contagem (1, neste caso).
4. Clicar -> abre a oportunidade.

e) Exemplo pratico
------------------
Projeto P-100 "Cliente A renovacao".
  - CRM O01 (opportunidade) tem `pg_project_id = P-100`.
  - CRM O02 originou SO S010, e S010 tem `project_id = P-100` e
    `opportunity_id = O02`.

Botao no P-100 -> mostra O01 e O02 (uniao dos dois caminhos).

f) FAQ / Resolucao de problemas
-------------------------------
P: O botao smart nao aparece. Porque?
R: O utilizador atual nao tem o grupo
   `sales_team.group_sale_salesman`. Adicionar.

P: Contagem 0 mas eu sei que ha oportunidades.
R: A oportunidade nao tem `pg_project_id` definido e a venda dela
   tambem nao tem `project_id`. Definir uma das duas ligacoes.

P: O campo "Project" em CRM nao aparece.
R: A view foi mal carregada. Atualizar o modulo.

g) Pontos de atencao / avisos
-----------------------------
- O fallback via sale.order depende de `sale_project` (campo
  `project_id` em SO). Se nao estiver instalado, so a ligacao
  manual funciona.
- O `_get_stat_buttons` adiciona o botao na lista standard - se
  outro modulo tambem mexer, validar a ordem.
- `compute_sudo=True` para que o sales user veja a contagem mesmo
  sem ACL plena nas SOs.
""",
    "depends": ["crm", "project", "sale_crm", "sale_project"],
    "data": [
        "views/pg_crm_lead_views.xml",
        "views/pg_project_project_views.xml",
    ],
    "installable": True,
    "application": False,
}
