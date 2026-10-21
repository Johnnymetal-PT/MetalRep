# -*- coding: utf-8 -*-
###############################################################################
#
#    Cybrosys Technologies Pvt. Ltd.
#
#    Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#    Author: Cybrosys Techno Solutions (odoo@cybrosys.com)
#
#    You can modify it under the terms of the GNU AFFERO
#    GENERAL PUBLIC LICENSE (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU AFFERO GENERAL PUBLIC LICENSE (AGPL v3) for more details.
#
#    You should have received a copy of the GNU AFFERO GENERAL PUBLIC LICENSE
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
###############################################################################
{
    'name': 'PG Product Multi Attachment',
    'version': '17.0.1.0.0',
    'category': 'Purchases,Sales',
    'summary': 'Vários anexos por produto, herdados nas linhas de venda/compra e juntos ao email',
    'description': """
PG Product Multi Attachment
===========================

Origem
------
Módulo de terceiros (Cybrosys Techno Solutions). Integrado no projeto com prefixo pg_.

Objetivo de negócio
-------------------
Associar vários documentos (fichas, certificados, desenhos) a um produto e fazer com que
esses anexos sigam automaticamente para as linhas de venda/compra e para os emails enviados
ao cliente/fornecedor, sem ter de os anexar manualmente de cada vez.

Pré-requisitos
--------------
- Módulos: `sale_management`, `purchase`.
- Anexar os documentos no produto (campo "Attachments").

Como funciona
-------------
- `product.template` (e `product.product`): campo `attachment_ids` (Many2many para ir.attachment).
- `sale.order.line` e `purchase.order.line`: campo `attachment_ids`; ao escolher o produto
  (onchange), as linhas herdam automaticamente os anexos do produto.
- `mail.template._generate_template_attachments`: ao gerar o email de uma venda/compra,
  junta automaticamente os anexos das linhas ao email.

Passo a passo de utilização
---------------------------
1. Abrir o produto e adicionar os documentos em "Attachments".
2. Criar uma venda/compra e escolher o produto — os anexos aparecem na linha.
3. Enviar o email da venda/compra — os documentos vão anexados automaticamente.

Exemplo prático
---------------
Produto "Cadeira X" com a ficha técnica anexada; ao colocá-lo numa cotação e enviar ao
cliente, a ficha técnica segue no email sem intervenção manual.

FAQ / Resolução de problemas
----------------------------
- P: Os anexos não foram para o email.
  R: Confirmar que estão na LINHA (vieram do produto) e que o email é de sale.order/purchase.order.
- P: Mudei o produto e os anexos antigos ficaram.
  R: O onchange recarrega os anexos do novo produto ao trocar o product_id.

Pontos de atenção
-----------------
- Módulo base de `pg_intercompany_po_so_sync` (que copia estes anexos da compra para a venda intercompany).
- Módulo de terceiros (AGPL-3); atualizações do fornecedor podem sobrepor alterações locais.
""",
    'author': 'Cybrosys Techno Solutions',
    'company': 'Cybrosys Techno Solutions',
    'maintainer': 'Cybrosys Techno Solutions',
    'website': "https://www.cybrosys.com",
    # `pg_product_variant_description_bytesfuel` fornece o campo `product_variant_desc`
    # que a personalização Studio do formulário de venda referencia. Sem esta dependência
    # o upgrade carrega este módulo primeiro e a validação da vista combinada de
    # `sale.order` falha por o campo ainda não estar registado.
    'depends': ['sale_management', 'purchase', 'pg_product_variant_description_bytesfuel'],
    'data': ['views/product_template_views.xml',
             'views/product_product_views.xml',
             'views/purchase_order_views.xml',
             'views/sale_order_views.xml'
             ],
    'images': ['static/description/banner.jpg'],
    'license': 'AGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}


