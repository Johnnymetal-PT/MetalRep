# -*- coding: utf-8 -*-
{
    "name": "PG Acesso Universal a Anexos",
    "version": "18.0.1.0.0",
    "category": "Tools",
    "summary": "Permite que todos os utilizadores internos vejam todos os anexos, independentemente do acesso ao registo-pai.",
    "description": """
PG Acesso Universal a Anexos (HMD)
==================================

a) Objetivo de negocio
----------------------
Na BD da HMD, sempre que ha atualizacoes ou alteracoes a modulos com
regras de acesso (produtos, vendas, projetos, etc.), reaparecem erros do
tipo "Anexo (ir.attachment) - sem acesso" para utilizadores que deveriam
conseguir consultar anexos no contexto da sua operacao diaria. O cliente
pediu uma solucao definitiva: todos os utilizadores internos passam a
ter acesso a todos os anexos da BD, eliminando o ciclo de "atualiza ->
quebra permissoes -> ajuste manual".

b) Pre-requisitos
-----------------
- Odoo 18.0 Enterprise on-premise (versao ativa registada em
  PG_CONTEXT.md).
- Modulo `base` instalado (dependencia obvia).
- Nenhuma configuracao Studio especifica e exigida.

c) Como funciona (tecnico)
--------------------------
Herda `ir.attachment` e faz override de dois metodos hardcoded no
standard do Odoo
(`vendor/odoo_src/community/odoo/addons/base/models/ir_attachment.py`):

1. `check(mode, values)`: reimplementa toda a logica standard MENOS a
   chamada final `records.check_access(mode)` sobre o registo-pai
   (`res_model` + `res_id`). E precisamente essa chamada que liga o
   acesso ao anexo ao acesso do registo a que ele esta ligado. Mantemos:
     - bloqueio para utilizadores nao internos (delega no standard);
     - anexos publicos em modo `read` passam direto;
     - anexos orfaos (`res_id` vazio) so para criador ou system (delega
       no standard quando este check falha);
     - campos binarios com `res_field.groups=` continuam restritos.

2. `_search(domain, offset, limit, order)`: o `_search` standard
   pos-filtra o resultset removendo anexos cujo registo-pai o
   utilizador nao consegue ler. Para utilizadores internos saltamos
   esse pos-filtro e devolvemos os ids que satisfazem o dominio,
   aplicando apenas ACL/ir.rule do proprio `ir.attachment` e o check
   de groups por campo binario.

Comportamento para portal/publico/superuser fica intacto.

d) Passo a passo de utilizacao
------------------------------
1. Instalar o modulo `pg_attachment_universal_access` na BD HMD.
2. Sem configuracao adicional: o efeito aplica-se a todos os
   utilizadores internos (`base.group_user`) imediatamente.
3. Para desativar: desinstalar o modulo (o standard volta a vigorar).

e) Exemplo pratico
------------------
Antes:
    - Sergio Pinto (id=9), utilizador interno, navega Inventario >
      Artigos.
    - Um anexo ligado a um produto (ou a uma mail.message do produto)
      tem `res_model='product.template'` cujo registo-pai tem uma
      record rule que exclui o Sergio (ex.: empresa diferente ou rule
      custom).
    - `ir.attachment.check('read')` chama
      `records.check_access('read')` sobre o `product.template` ->
      AccessError "Anexo (ir.attachment) sem acesso".

Depois (com este modulo instalado):
    - Mesma navegacao. `check('read')` valida que o Sergio e interno,
      ignora o check ao registo-pai, devolve True. Sergio consegue
      abrir o anexo.

f) FAQ / Resolucao de problemas
-------------------------------
P: Os utilizadores portal passam a ver tudo?
R: Nao. O override delega no standard quando o utilizador nao e
   interno. Portal/publico mantem comportamento Odoo standard mais as
   regras em `pg_web_attach_pdf_view` (se instalado).

P: E os campos binarios com `groups="..."` (ex.: restritos a `base.
   group_system`)?
R: Continuam protegidos. O override mantem o check
   `field.is_accessible(self.env)` (no `check`) e
   `field.groups + has_groups(...)` (no `_search`).

P: Os anexos orfaos (ainda nao ligados a registo) passam a ser visiveis
   por todos?
R: Nao. Continuam visiveis apenas pelo criador ou system, como no
   standard. O bypass aplica-se apenas ao check do registo-pai.

P: Vai partir o upgrade para Odoo 19?
R: Risco baixo a medio. O override e cirurgico (so dois metodos) e nao
   altera schema. Em Odoo 19, ha que reavaliar a assinatura dos metodos
   `check()` e `_search()` em `ir.attachment` e voltar a sincronizar.
   Esta sincronizacao deve ser revista no marco M4 (Preparacao Upgrade
   Odoo 19) - ver PG_CONTEXT.md.

P: Como reverter rapidamente?
R: Desinstalar o modulo. Todos os checks standard voltam a aplicar-se.

g) Pontos de atencao / avisos
-----------------------------
- IMPACTO DE SEGURANCA: este modulo abre intencionalmente o acesso a
  TODOS os anexos para utilizadores internos. Anexos sensiveis (RH,
  notas internas de chatter, documentos contratuais, etc.) ficam
  acessiveis a qualquer utilizador interno. O cliente HMD assumiu este
  risco explicitamente. Documentar em `PG_CONTEXT.md` na proxima
  atualizacao.
- RGPD / Confidencialidade: confirmar com o cliente que nao ha anexos
  contendo dados pessoais protegidos cujo acesso deva ser restrito por
  RH/Contabilidade. Se houver, sera necessario evoluir este modulo
  para uma whitelist/blacklist de `res_model`.
- Mantemos a verificacao de `res_field` para nao expor campos binarios
  marcados pelo programador como restritos a grupos.
- Override depende da assinatura standard dos metodos em Odoo 18. Em
  Odoo 19+ verificar mudancas em
  `vendor/odoo_src/.../ir_attachment.py` antes do upgrade.

Estado e evidencia
------------------
- FACTO OBSERVADO: standard liga o acesso ao anexo ao registo-pai
  (`vendor/odoo_src/community/odoo/addons/base/models/ir_attachment.py`
  linha 512 - `records.check_access(access_mode)`).
- FACTO OBSERVADO: standard tem ACL `access_ir_attachment_group_user`
  para `base.group_user` com RWUD = 1,1,1,1
  (`vendor/odoo_src/community/odoo/addons/base/security/ir.model.access.csv`).
- PONTO POR VALIDAR: existencia de anexos com `res_field` em campos
  sensiveis na BD atual. Caso existam, o override ja os protege.
""",
    "author": "Parametro Global SA",
    "website": "https://parametro.global",
    "license": "LGPL-3",
    "depends": ["base"],
    "data": [],
    "installable": True,
    "application": False,
    "auto_install": False,
}
