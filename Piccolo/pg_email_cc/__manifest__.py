# -*- coding: utf-8 -*-
# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.
{
    "name": "Email Cc",
    "version": "17.0.1.0.0",
    "author": "Techultra Solutions Private Limited",
    "company": "TechUltra Solutions Private Limited",
    "website": "https://www.techultrasolutions.com/",
    "category": "Email",
    "summary": "Modulo terceiro (Techultra Solutions, OPL-1) que acrescenta um campo 'Email Cc' no mail composer para enviar copia a multiplas moradas separadas por virgula.",
    "description": """
Email Cc (vendored - terceiro)
==============================

NOTA SOBRE ESTE MODULO
----------------------
- **Origem**: Techultra Solutions Private Limited
  (`https://www.techultrasolutions.com/`).
- **Licenca**: OPL-1 (paga - 10 USD).
- **Status no projeto Piccolo**: vendored - mantemos a versao
  carregada na altura da compra; nao editar o codigo interno
  porque uma re-instalacao do produto sobrescreve as alteracoes.
- O prefixo ``pg_`` no nome da pasta foi acrescentado pela
  Piccolo apenas para co-localizar com os outros modulos; o
  ``name`` interno e ``Email Cc`` (sem prefixo).

a) Objetivo de negocio
----------------------
Permitir que ao enviar emails do Odoo (composer standard) se
adicionem multiplas moradas em Cc (carbon copy) num so campo,
separadas por virgula, em vez de criar varios destinatarios
individuais.

b) Pre-requisitos
-----------------
- Modulos standard ``mail`` e ``account``.
- Licenca paga ativa (OPL-1).

c) Como funciona (resumo, sem detalhe interno)
---------------------------------------------
- Adiciona campo ``email_cc`` no wizard ``mail.compose.message``.
- No envio, parsea o valor por virgula e inclui cada email como
  Cc no MIME final.

d) Passo a passo de utilizacao
------------------------------
1. Instalar.
2. Abrir composer de email (qualquer documento com chatter).
3. Campo "Email Cc" novo - escrever ``a@x.pt, b@y.pt``.
4. Enviar - os destinatarios em Cc recebem copia.

e) Exemplo pratico
------------------
Enviar fatura por email; em Cc colocar a equipa de cobrancas
(``cobrancas@piccolo.pt, contabilidade@piccolo.pt``). Os dois
recebem copia.

f) FAQ / Resolucao de problemas
-------------------------------
- *"Campo nao aparece"* -> validar que o modulo esta instalado
  e que ``mail`` foi recompilado.
- *"Emails nao chegam"* -> mail server pode estar a rejeitar
  Cc - validar logs do MTA.

g) Pontos de atencao / avisos
-----------------------------
- **NAO editar o codigo deste modulo**. Em proxima atualizacao
  da Techultra, alteracoes locais perdem-se. Se for preciso
  customizar, criar um modulo Piccolo separado que herde de
  ``mail.compose.message``.
- A licenca OPL-1 implica que nao se pode redistribuir o codigo
  fora do projeto Piccolo sem comprar licencas adicionais.
""",
    "depends": ["mail", "account"],
    "data": [
        "views/email_cc.xml",
    ],
    "images": [
        "static/description/main_screen.gif",
    ],
    "currency": "USD",
    "price": 10,
    "installable": True,
    "application": True,
    "license": "OPL-1",
}
