{
    "name": "PG Account Journal Access",
    "summary": "Whitelist de utilizadores por diario contabilistico (ver, criar, editar, lancar) + acesso a ir.attachment para internos.",
    "version": "18.0.1.0.1",
    "author": "Parametro Global",
    "website": "https://www.parametroglobal.com",
    "category": "Accounting",
    "license": "LGPL-3",
    "description": """
PG Account Journal Access (HMD)
===============================

a) Objetivo de negocio
----------------------
Em equipas de contabilidade, ha diarios sensiveis (salarios,
pagamentos a fornecedores estrategicos, lancamentos de fecho) que
nao devem ser visiveis a TODA a equipa, apesar de todos os
contabilistas terem o grupo Accountant standard. O Odoo standard
permite restringir diarios apenas por GRUPO (group_id no journal),
o que e um martelo demasiado grosso. Este modulo introduz uma
whitelist por UTILIZADOR no diario:
  - se a lista esta vazia, o diario continua aberto a todos os
    contabilistas (comportamento default seguro);
  - se a lista tem utilizadores, apenas esses podem ver, criar,
    editar e lancar nesse diario (e respetivos movimentos e
    rubricas);
  - ao restringir pela primeira vez, todos os Administradores de
    Contabilidade sao pre-preenchidos automaticamente (para nao
    deixar a chefia fora por engano), mas podem ser removidos.

b) Pre-requisitos
-----------------
- Odoo 18.0 Enterprise (versao ativa em PG_CONTEXT.md).
- Modulo `account`.
- Grupo `account.group_account_manager` (Administrador de
  Contabilidade) existente.

c) Como funciona (tecnico)
--------------------------
1. `account.journal` (`models/account_journal.py`):
   - `pg_allowed_user_ids` (Many2many a `res.users`, filtrado a
     `share=False` para nao incluir users portal): whitelist.
   - `pg_access_seeded` (Boolean): flag tecnica - marca se ja
     foram pre-preenchidos os admins (impede re-adicao apos
     remocao deliberada).
   - `_onchange_pg_allowed_user_ids`: quando a lista comeca a ter
     utilizadores (e nao houve seed previo), adiciona os
     `account.group_account_manager` internos. Quando a lista
     volta a vazio, o seed flag e resetado para que da proxima
     vez o seed ocorra de novo.

2. `security/journal_access_rules.xml`:
   - `pg_journal_access_rule` (em `account.journal`): regra GLOBAL
     (sem `groups`) com dominio
     `pg_allowed_user_ids = False OR user.id in pg_allowed_user_ids`.
     Globais sao combinadas em AND com todas as outras regras -
     funcionam como restricao adicional (e nao OR como regras de
     grupo, que nunca restringiriam).
   - `pg_move_journal_access_rule` (em `account.move`): mesmo
     dominio mas via `journal_id.pg_allowed_user_ids`.
   - `pg_move_line_journal_access_rule` (em `account.move.line`):
     idem via `move_id.journal_id.pg_allowed_user_ids`. Usa-se
     `move_id.journal_id` em vez do related/store `journal_id` da
     rubrica para nao depender do timing de computacao da linha
     durante a criacao da fatura. Sem isto, criar fatura de
     fornecedor a partir de `purchase.order` pode falhar (rubricas
     nao podem ser criadas).
   - `pg_ir_attachment_internal_user_rule`: regra cosmica em
     `ir.attachment` para `base.group_user`, perm RWUD = 1,1,1,1
     com dominio `(1,=,1)`. Coexistencia com
     `pg_attachment_universal_access`: ambos coincidem na intencao
     "internos podem ver anexos".

3. `security/ir.model.access.csv`: ACL standard para o modelo de
   journal (manter inalterado a menos que se mexa no schema).

4. View (`views/account_journal_views.xml`): aba "Configuracao
   Avancada" do journal, secao "Acesso por Utilizador (PG)",
   visivel so a `account.group_account_manager`.

d) Passo a passo de utilizacao
------------------------------
1. Instalar `pg_account_journal_access`.
2. Contabilidade > Configuracao > Diarios > abrir um diario
   sensivel.
3. Aba "Configuracao Avancada" > seccao "Acesso por Utilizador (PG)".
4. Adicionar os utilizadores que devem ter acesso. Ao adicionar o
   primeiro, os Administradores de Contabilidade entram
   automaticamente.
5. Remover os que nao devem ter acesso (incluindo admins, se for o
   caso).
6. Salvar. A partir daqui, so esses utilizadores veem este diario,
   os seus movimentos e rubricas.

e) Exemplo pratico
------------------
Diario "Salarios" (`HR-PAY`):
  - Antes: visivel a todos os 12 contabilistas.
  - Operacao: adicionar "Maria (RH)" a `pg_allowed_user_ids`.
    Auto-seed adiciona tambem "Joao (admin contab.)" e
    "Ana (admin contab.)". Remover "Ana" - ficam Maria + Joao.
  - Resultado: apenas Maria e Joao veem `HR-PAY`, os move.lines
    desse diario e o diario em si.

Tentar (sem permissao): outro contabilista abre Contabilidade >
Diarios -> nao ve `HR-PAY`. Tenta abrir um movimento por URL ->
AccessError.

f) FAQ / Resolucao de problemas
-------------------------------
P: O diario continua visivel a todos.
R: A lista ainda esta vazia (default = aberto). Adicionar pelo
   menos um utilizador.

P: Quando faco fatura de fornecedor a partir da PO, da erro de
   acesso em `account.move.line`. Resolver?
R: A regra `pg_move_line_journal_access_rule` para `account.move.line`
   deve estar ativa e o dominio deve usar `move_id.journal_id` -
   verificar Settings > Technical > Record Rules.

P: Removi todos os admins da lista por engano. Como recuperar?
R: Como admin do sistema (`base.group_system`), as record rules
   ainda sao bypassed. Reabrir o diario e voltar a por-se na
   lista.

P: A pre-seed re-acontece quando volto a esvaziar e re-encher?
R: Sim. O `pg_access_seeded` reset quando a lista fica vazia.

P: Esta regra cobre `account.payment`?
R: Nao diretamente. account.payment liga a `account.move` via
   `move_id` - a regra em account.move ja restringe (move com
   diario X so visivel para os whitelisted).

g) Pontos de atencao / avisos
-----------------------------
- REGRAS GLOBAIS: as 3 primeiras regras nao tem grupos definidos.
  Aplicam-se a TODOS os utilizadores (incluindo Accountant manager).
  Apenas `base.group_system` bypassa.
- Sem `perm_unlink`: ninguem (com estas regras) pode apagar
  movimentos via fluxo standard. Apagar exige user `group_system`.
- O `pg_ir_attachment_internal_user_rule` interfere com qualquer
  outra regra de attachment - validar interacao com
  `pg_attachment_universal_access` ou `pg_web_attach_pdf_view`.
- O domain `(1,=,1)` em ir.attachment para internos e o oposto do
  standard (que liga ao registo-pai). Convive com
  `pg_attachment_universal_access` - mesma filosofia.
- Em upgrade Odoo 19, validar que `account.group_account_manager`
  continua a existir com o mesmo XID.
""",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "security/journal_access_rules.xml",
        "views/account_journal_views.xml",
    ],
    "installable": True,
    "application": False,
}
