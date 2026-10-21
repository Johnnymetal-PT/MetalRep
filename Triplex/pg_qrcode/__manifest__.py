{
    'name': 'QR Code Contact Scanner',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Lê um QR code vCard com a câmara e cria automaticamente o contacto (res.partner)',
    'description': """
QR Code Contact Scanner
=======================

Objetivo de negócio
-------------------
Acelerar a criação de contactos: em vez de digitar os dados de um cartão de visita, basta
ler o QR code (formato vCard) com a câmara e o contacto é criado no Odoo.

Pré-requisitos
--------------
- Módulos: `base`, `web`.
- Biblioteca Python `vobject` instalada no servidor (pip install vobject).
- Acesso ao Odoo em HTTPS (os browsers só permitem usar a câmara em contextos seguros).
- Permissão dada ao site/Odoo para usar a câmara no browser.
- QR codes em formato vCard (extensão .vcf) — formato standard dos cartões de visita digitais.

Como funciona
-------------
- `res.partner.action_open_qr_scanner()`: devolve a ação cliente `open_qr_scanner`.
- Frontend (static/src/js/qr_scanner.js): componente OWL que abre a câmara (biblioteca
  html5-qrcode incluída em static/lib), lê o QR e envia o texto vCard por RPC.
- Controller (controllers/main.py): rota `/create_partner_from_vcard` que faz o parsing do
  vCard com a biblioteca `vobject` e cria o `res.partner` (nome, telemóvel, email, morada,
  função, website). Se o vCard tiver empresa, liga/cria a empresa-mãe (`parent_id`).
- No fim, o frontend redireciona para a ficha do contacto criado.

Passo a passo de utilização
---------------------------
1. Garantir HTTPS no Odoo e `vobject` instalado.
2. Disparar a ação `open_qr_scanner` (botão a ativar nas vistas — está comentado no
   manifesto; ativar a view ou criar uma ação de menu/servidor).
3. Apontar a câmara ao QR vCard do cartão de visita.
4. O contacto é criado automaticamente e o browser abre a respetiva ficha.

Exemplo prático
---------------
QR vCard de "João Silva (Triplex, Director Comercial), telemóvel 912345678, joao@triplex.pt".
Após a leitura, é criada/atualizada a empresa "Triplex" como parent e o contacto João Silva
ligado a ela com os restantes dados preenchidos.

FAQ / Resolução de problemas
----------------------------
- P: A câmara não abre.
  R: O Odoo tem de estar em HTTPS e o browser precisa de permissão para a câmara.
- P: ImportError: No module named 'vobject'.
  R: Instalar `vobject` no Python do servidor.
- P: Não acontece nada após ler o QR.
  R: O QR pode não estar em formato vCard; testar com um QR vCard standard.
- P: Como aceder ao botão se a view está comentada?
  R: Descomentar `views/res_partner_view.xml` no manifesto ou criar uma ação de menu/servidor
     que chame `action_open_qr_scanner`.

Pontos de atenção
-----------------
- Dependência da biblioteca externa `vobject` (parsing vCard) e da `html5-qrcode` (incluída
  em static/lib).
- A view com o botão está comentada no manifesto.
""",
    'depends': ['base', 'web'],
    'data': [
        #'views/res_partner_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pg_qrcode/static/src/js/qr_scanner.js',
            #'https://unpkg.com/html5-qrcode@2.3.7/html5-qrcode.min.js',
            'pg_qrcode/static/lib/html5-qrcode.min.js',
        ],
    },
    'installable': True,
    'application': False,
}

