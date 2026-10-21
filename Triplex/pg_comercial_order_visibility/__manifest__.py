{
    'name': 'PG Comercial Order Visibility',
    'version': '1.0',
    'summary': 'Comerciais só veem as suas próprias encomendas de venda e compra',
    'description': """
PG Comercial Order Visibility
=============================

Objetivo de negócio
-------------------
Os utilizadores marcados como "comercial" devem ver apenas as encomendas de venda e compra
que lhes pertencem (criadas/atribuídas a si), enquanto os restantes utilizadores continuam
a ver tudo o que as suas permissões permitem.

Pré-requisitos
--------------
- Módulos: `sale`, `purchase`.
- Campo Studio `x_studio_comercial` (Boolean) em `res.users` — tem de estar criado via Odoo
  Studio antes de instalar.
- Os utilizadores "comerciais" devem ter esse campo marcado.

Como funciona
-------------
Não tem código Python — implementa-se por duas regras de registo (`ir.rule`) em
security/pg_comercial_order_rules.xml, uma para `sale.order` e outra para `purchase.order`:
- Se `user.x_studio_comercial` for falso  -> domínio `[(1,'=',1)]` (vê tudo).
- Se `user.x_studio_comercial` for verdadeiro -> domínio `[('user_id','=',user.id)]` (só os seus).
As regras usam `groups eval=[(5,0,0)]` (sem grupos), pelo que se aplicam globalmente.

Passo a passo de utilização
---------------------------
1. Em Studio, garantir que existe o campo `x_studio_comercial` em `res.users`.
2. Em Definições > Utilizadores, marcar o campo nos utilizadores que devem ver apenas as
   suas próprias encomendas.
3. Instalar o módulo (carrega as regras de registo).
4. Esses utilizadores, ao abrir Vendas/Compras, passam a ver só os seus documentos.

Exemplo prático
---------------
A comercial Ana tem `x_studio_comercial = True`. Ao abrir Vendas > Encomendas, vê apenas as
SOs em que `user_id = Ana`. Já o gestor João, sem o campo marcado, continua a ver todas as
encomendas conforme as suas permissões.

FAQ / Resolução de problemas
----------------------------
- P: O admin deixou de ver todas as encomendas.
  R: As regras são globais (sem grupos). Se o admin tem `x_studio_comercial = True`, fica
     também restringido; desmarcar o campo no admin.
- P: As encomendas continuam todas visíveis para um comercial.
  R: Confirmar que `x_studio_comercial` está marcado nesse utilizador e que o módulo está
     instalado/atualizado (regras carregadas).
- P: Quero também esconder cotações que foram atribuídas a outros.
  R: A regra usa `user_id` (vendedor) — já cobre isso.

Pontos de atenção
-----------------
- O campo `x_studio_comercial` em `res.users` é criado via Odoo Studio (fora deste módulo).
- Sendo regra global (sem grupos), aplica-se a TODOS os utilizadores; validar que não colide
  com administradores ou outros perfis que precisem de ver tudo.
- Não afeta vistas de reporting que liam diretamente do BD com cursor — só o ORM com regras.
""",
    'category': 'Sales',
    'author': 'PG',
    'depends': ['sale', 'purchase'],
    'data': [
        'security/pg_comercial_order_rules.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}

