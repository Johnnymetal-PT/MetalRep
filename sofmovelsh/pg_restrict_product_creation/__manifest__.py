{
    'name': 'PG Product Creation Blocklist Manager',
    'version': '19.0.1.0.0',
    'author': 'Parametro Global',
    'category': 'Inventory',
    'summary': 'Bloqueia criacao de produtos por utilizadores numa lista negra (gerida via wizard pelos administradores).',
    'description': """
PG Product Creation Blocklist Manager
=====================================

a) Objetivo de negocio
----------------------
Impedir que determinados utilizadores (gestores externos, balcoes, sessoes
partilhadas, etc.) criem produtos. A lista de utilizadores proibidos e gerida
por um wizard exclusivo para administradores e e validada na propria criacao
do `product.template`.

b) Pre-requisitos
-----------------
- Modulo standard `product`.
- Os emails dos utilizadores autorizados a editar a blocklist sao
  hardcoded na constante `ALLOWED_USERS` em
  `models/product_template_inherit.py`:
    - it.odoo@parametro.pt
    - andreiasilva@sofmovel.pt
    - gabrielpereira@sofmovel.pt
    - pessoal@sofmovel.pt
    - joaosilva@sofmovel.pt

c) Como funciona
----------------
- `models/product_forbidden_users.py`:
  - `product.forbidden.users` (lista de emails proibidos). Campo unico:
    `email` (Char unique).
- `models/restrict_product_creation.py`:
  - Override de `product.template.create`:
    - Le `self.env.user.login`.
    - Procura em `product.forbidden.users` por esse email; se encontrar,
      raise UserError("Nao pode alterar a lista de utilizadores bloqueados.").
    [NOTA: a mensagem aparenta ser copy/paste; a accao bloqueada e CRIAR
    PRODUTO, nao alterar a blocklist. Ver FAQ.]
- `models/product_template_inherit.py`:
  - Adiciona `show_forbidden_users_button` (Boolean, computed) em
    `product.template` e em `product.product`. So fica `True` para emails na
    ALLOWED_USERS.
  - Adiciona `action_manage_forbidden_users`: rebenta se o utilizador nao
    esta em ALLOWED_USERS e abre o wizard.
- `models/product_forbidden_users_wizard.py`:
  - `product.forbidden.users.wizard` (TransientModel) com `forbidden_users_ids`
    Many2many; em `default_get` pre-popula com os registos atuais e em
    `action_save` faz diff: remove os que sairam e cria os que entraram.

d) Passo a passo de utilizacao
------------------------------
1. Aceder com um dos utilizadores ALLOWED.
2. Abrir um produto qualquer; deve aparecer o botao "Manage Forbidden Users".
3. Clicar; abre o wizard com a lista atual de emails.
4. Adicionar/remover entradas e guardar.
5. Utilizadores cujo email estiver na lista nao conseguem mais criar
   produtos (recebem UserError).

e) Exemplo pratico
------------------
- "balcao1@sofmovel.pt" deve nao conseguir criar produtos.
- Administrador IT abre o wizard e adiciona esse email.
- Quando balcao1 tentar criar um produto, recebe a mensagem de UserError.

f) FAQ / Resolucao de problemas
-------------------------------
- "Mensagem de erro parece ao contrario":
  A `UserError` diz "Nao pode alterar a lista de utilizadores bloqueados.",
  mas e mostrada ao TENTAR CRIAR um produto. Aparenta copy/paste; corrigir
  para "Nao tem permissao para criar produtos." e ponto a melhorar.
- "Botao 'Manage Forbidden Users' nao aparece":
  Confirmar que o login do utilizador esta listado em `ALLOWED_USERS`. Sem
  isso o `show_forbidden_users_button` fica False e a vista esconde.
- "Quero outro IT a gerir a blocklist":
  Tem de ser adicionado no codigo (`ALLOWED_USERS`). Nao e configuravel via
  UI.

g) Pontos de atencao
--------------------
- A lista `ALLOWED_USERS` esta hardcoded em duas classes (product.template e
  product.product). Manter as duas em sincronia ao atualizar.
- Modelo `product.template` e `product.product` ambos tem
  `ProductTemplateInherit` declarado, o que reutiliza o nome Python para
  duas classes diferentes (legal mas confuso).
- Override de `create` so cobre `product.template`. Criar um `product.product`
  diretamente nao passa por esta validacao - validar se faz diferenca.
- Restricao em `email` na `product.forbidden.users` esta marcada com
  `unique=True` mas Odoo `Char unique` apenas sinaliza UI; para garantir DB
  uniqueness precisa de SQL constraint.
    """,
    'depends': ['product'],
    'data': [
        'security/ir.model.access.csv',
        'views/product_template_views.xml',
        'views/wizard_views.xml',
    ],
    'installable': True,
    'application': False,
}
