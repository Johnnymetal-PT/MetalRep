# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.
{
    "name": "Email Cc",
    "version": "17.0.1.0.0",
    "author": "Techultra Solutions Private Limited",
    'company': 'TechUltra Solutions Private Limited',
    'website': "https://www.techultrasolutions.com/",
    "category": "Email",
    "summary": "Permite definir destinatarios em CC no compositor de email e no envio de account.move (faturas).",
    "description": """
Email Cc (modulo de terceiros - TechUltra Solutions)
====================================================

a) Origem e estado no projeto Sofmovel
--------------------------------------
[FACTO OBSERVADO] modulo de terceiros (TechUltra Solutions, licenca OPL-1).
Mantido no repositorio para suportar envio de faturas com CC em
`account.move.send` e tambem CC em `mail.compose.message` (usado em varios
fluxos de Odoo).

NAO alterar a logica interna do modulo - alteracoes precisam ser portadas a
cada upgrade do fornecedor original. Patches Sofmovel devem ser feitos em
modulo proprio que herde por cima.

b) Objetivo de negocio (resumo do fornecedor)
---------------------------------------------
- Acrescenta campo "Email CC" no wizard de envio de faturas
  (`account.move.send`) - hereda e injeta o CC nos valores do envio.
- Acrescenta campo "Email CC" e "Additional email" no compositor de email
  (`mail.compose.message`) - injeta CC e forca `email_from` /`reply_to` para
  o utilizador autenticado.
- Override de `mail.thread._notify_thread_by_email` para suportar
  `email_cc` no envio de notificacoes ligadas a mensagens em registos
  (modelos com `mail.thread`).

c) Pre-requisitos
-----------------
- Modulos: `mail`, `account`.
- Licenca OPL-1 valida.
- Configuracao de SMTP funcional no Odoo.

d) Como funciona (resumo)
-------------------------
- `models/email_cc.py`:
  - `AccountMoveeSend (account.move.send)` adiciona campo `email_to`
    ("Email CC") e injeta-o em `_get_wizard_values` e
    `_get_mail_move_values`.
  - `MailComposeMessage (mail.compose.message)` adiciona `email_to`
    ("Email CC") e `additional_email`; em `_prepare_mail_values` substitui
    `email_from`/`reply_to` pelo do utilizador e adiciona o CC se
    preenchido.
  - `MailThreadInherit (mail.thread)` extende `_get_notify_valid_parameters`
    para aceitar `email_cc` e re-implementa
    `_notify_thread_by_email` para propagar `email_cc` e `email_to`
    extras nas notificacoes.

e) Passo a passo de utilizacao (resumo)
---------------------------------------
1. No envio de uma fatura, surge o campo "Email CC" - preencher com emails
   separados por virgula.
2. Em qualquer compositor de email (mensagem em produto, parceiro, SO,
   etc.), surge "Email CC".
3. O CC e respeitado na entrega do email (cabecalho CC) e no log do
   message do registo.

f) FAQ / Resolucao de problemas
-------------------------------
- "Email CC nao chega":
  Validar configuracao SMTP. O CC viaja como cabecalho normal do email.
- "Eu nao quero forcar email_from para o utilizador":
  O override em `_prepare_mail_values` substitui sempre o `email_from`
  pelo do utilizador (com fallback 'catchall@yourdomain.com'). Para
  alterar este comportamento e preciso outro modulo a herdar por cima.

g) Pontos de atencao (Sofmovel)
-------------------------------
- O fallback `email_from = 'catchall@yourdomain.com'` (literal) e do
  fornecedor; se o utilizador nao tiver `email_formatted`, e enviado este
  endereco invalido. Recomenda-se garantir email em todos os utilizadores
  que enviam.
- O modulo e proprietario (OPL-1). Manter o codigo original sem patches
  diretos.
- Convive com outros modulos que estendem `mail.thread`; ordem de carga
  importa.
- Marca-se `application=True` no upstream para aparecer no menu Apps; e
  irrelevante para o uso real.
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
