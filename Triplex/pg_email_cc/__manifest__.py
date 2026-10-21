# Part of Odoo. See COPYRIGHT & LICENSE files for full copyright and licensing details.
{
    "name": "Email Cc",
    "version": "17.0.1.0.0",
    "author": "Techultra Solutions Private Limited",
    "company": "TechUltra Solutions Private Limited",
    "website": "https://www.techultrasolutions.com/",
    "category": "Email",
    "summary": "Campo 'Email CC' no compositor de email e no envio de faturas, para enviar cópia a vários destinatários",
    "description": """
Email Cc
========

Origem
------
Módulo de terceiros (Techultra Solutions). Integrado no projeto com prefixo pg_.

Objetivo de negócio
-------------------
Permitir enviar emails (incluindo o envio de faturas) com endereços em cópia (CC), sem ter
de criar contactos nem enviar emails separados. Os endereços CC são escritos num campo,
separados por vírgula.

Pré-requisitos
--------------
- Módulos: `mail`, `account`.
- Nada a configurar: após instalar, o campo "Email CC" aparece nos ecrãs de envio.

Como funciona
-------------
- `account.move.send` (envio de faturas) e `mail.compose.message` (compositor): acrescentam
  o campo `email_to` ("Email CC") e propagam-no para os valores do email a enviar.
- `mail.thread._notify_thread_by_email`: override do método standard de notificação por
  email para, quando vem um `email_cc`, o incluir nos valores do `mail.mail` criado.

Passo a passo de utilização
---------------------------
1. Abrir o envio de um email/fatura (botão "Enviar" / "Enviar e Imprimir").
2. Preencher o campo "Email CC" com um ou mais endereços separados por vírgula.
3. Enviar — os destinatários em CC recebem cópia.

Exemplo prático
---------------
Ao enviar a fatura a "cliente@exemplo.pt", preencher Email CC com
"contabilidade@triplex.pt, gestor@triplex.pt" para que ambos recebam cópia.

FAQ / Resolução de problemas
----------------------------
- P: Pus vários emails e só um recebeu.
  R: Confirmar que estão separados por vírgula e sem espaços/typos.
- P: O CC não aparece no envio de faturas.
  R: O campo está no wizard de envio (account.move.send); confirmar que o módulo está instalado.
- P: É de terceiros — posso alterar?
  R: Sim, mas atualizações do fornecedor podem sobrepor alterações locais; documentar bem.

Pontos de atenção
-----------------
- Faz override de um método central de notificação (`_notify_thread_by_email`); uma
  atualização major do Odoo pode exigir reconciliar este override com o standard.
- Módulo proprietário (licença OPL-1).
""",
    "depends": ["mail", "account"],
    "data": [
        "views/email_cc.xml",
    ],
    "assets": {
        "web.assets_frontend": [
            "pg_email_cc/static/src/scss/fonts.scss",  # Your custom font-face declarations
        ],
    },
    "images": [
        "static/description/main_screen.gif",
    ],
    "currency": "USD",
    "price": 10,
    "installable": True,
    "application": True,
    "license": "OPL-1",
}

