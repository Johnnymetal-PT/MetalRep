import logging

from odoo import api, fields, models

_logger = logging.getLogger(__name__)

# Fonte do "preço antes do desconto", por ordem de preferência. O nativo primeiro:
# é o que a loja online usa no preço riscado, e a etiqueta tem de dizer o mesmo que
# o site. O campo Studio fica como recurso enquanto os dados não convergirem — na
# V17 está preenchido em 6181 artigos contra 1299 do nativo.
CAMPOS_PRECO_ANTERIOR = ('compare_list_price', 'x_studio_preo_antes_desconto')

# Campos de referência interna, na ordem da decisão do projeto: `default_code` é o
# canónico em v19 (ver pg_product_reference) e o campo Studio é só espelho. É o
# inverso da V17 — ver alínea (g) do manifest.
CAMPOS_REFERENCIA = ('default_code', 'x_studio_referncia_interna')

CAMPOS_CODIGO_BARRAS = ('barcode', 'x_studio_cdigo_de_barras')


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    pg_label_type = fields.Selection(
        selection=[
            ('A5', "Etiqueta A5"),
            ('5x8', "Etiqueta 5x8"),
            ('ZPL', "Etiqueta ZPL"),
        ],
        string="Tipo de etiqueta",
        default='ZPL',
        help="Formato usado ao imprimir etiquetas deste artigo a partir de uma "
             "recepção. As etiquetas ZPL saem por impressora térmica via IoT; as "
             "A5 e 5x8 saem em PDF.",
    )

    # -- dados para as etiquetas -------------------------------------------

    def _pg_label_reference(self):
        """Referência a imprimir na etiqueta."""
        self.ensure_one()
        return self._pg_primeiro_valor(CAMPOS_REFERENCIA)

    def _pg_label_barcode(self):
        self.ensure_one()
        return self._pg_primeiro_valor(CAMPOS_CODIGO_BARRAS)

    def _pg_primeiro_valor(self, nomes):
        """Primeiro campo da lista que exista na base e tenha valor.

        A leitura é defensiva porque metade destes campos são Studio: existem na
        base migrada da V17 e não existem numa base v19 limpa. Um `self.campo`
        directo rebentaria o relatório na base de testes.
        """
        self.ensure_one()
        for nome in nomes:
            if nome in self._fields and self[nome]:
                return self[nome]
        return ''

    def _pg_label_compare_price(self):
        """Preço antes do desconto, ou 0.0 quando não há nenhum registado."""
        self.ensure_one()
        for nome in CAMPOS_PRECO_ANTERIOR:
            if nome in self._fields and self[nome]:
                return self[nome]
        return 0.0

    def _pg_label_pricelist(self):
        """Lista de preços a usar na etiqueta.

        A V17 fazia `search([], limit=1)` — a primeira lista que aparecesse.
        Funcionava por acidente, porque só há uma lista activa; com as listas por
        escalão B2B da tarefa 6563 passaria a imprimir o preço de um escalão a
        quem passasse na loja. Aqui a lista vem do contexto (o wizard de impressão
        deixa escolher) e, em falta, da lista por omissão da empresa.
        """
        Pricelist = self.env['product.pricelist']
        do_contexto = self.env.context.get('pg_label_pricelist_id')
        if do_contexto:
            lista = Pricelist.browse(do_contexto).exists()
            if lista:
                return lista
        # A chave False do resultado é a lista de recurso: a primeira sem grupo de
        # países, ou a definida por parâmetro de sistema. É a mesma que o Odoo aplica
        # a um cliente sem lista própria.
        por_pais = Pricelist._get_country_pricelist_multi([])
        return por_pais.get(False) or Pricelist.search(
            [('company_id', 'in', (self.env.company.id, False))], limit=1,
        )

    def _pg_label_prices(self, pricelist=None):
        """Devolve `(preço a cobrar, preço anterior)` para a etiqueta.

        O preço anterior vem a 0.0 quando não há desconto a mostrar: o template
        só o imprime se for **maior** que o preço a cobrar, para nunca aparecer um
        "antes" mais barato do que o "agora".
        """
        self.ensure_one()
        pricelist = pricelist or self._pg_label_pricelist()
        moeda = pricelist.currency_id or self.currency_id
        base = pricelist._get_product_price(self, 1, currency=moeda) if pricelist else 0.0

        # Herdado da V17: um preço de 0 ou 1 na lista significa, na prática, artigo
        # sem regra própria — imprime-se o preço de venda. Mantido para não mudar o
        # que a loja vê hoje; desliga-se com o parâmetro de sistema abaixo.
        if base in (0.0, 1.0) and self._pg_label_fallback_lst_price():
            base = self.list_price

        anterior = self._pg_label_compare_price()
        return base, (anterior if anterior > base else 0.0)

    @api.model
    def _pg_label_fallback_lst_price(self):
        valor = self.env['ir.config_parameter'].sudo().get_param(
            'pg_etiquetas.fallback_lst_price', 'True',
        )
        return str(valor).strip().lower() not in ('false', '0', 'no')

    # -- logótipo ----------------------------------------------------------

    def _pg_label_logo_url(self):
        """URL do logótipo da etiqueta.

        A V17 tinha dois ids de anexo fixos no QWeb (`/web/image/4022059` para os
        artigos Kave e `/web/image/4036491` para os restantes). Ids fixos não
        sobrevivem a uma base diferente — aqui vêm de parâmetros de sistema e, em
        falta, usa-se o logótipo da empresa.
        """
        self.ensure_one()
        Param = self.env['ir.config_parameter'].sudo()
        if self._pg_label_is_kave():
            anexo = Param.get_param('pg_etiquetas.logo_kave_id')
            if anexo:
                return f'/web/image/{anexo}'
        anexo = Param.get_param('pg_etiquetas.logo_id')
        if anexo:
            return f'/web/image/{anexo}'
        return f'/web/image/res.company/{self.env.company.id}/logo'

    def _pg_label_is_kave(self):
        """O artigo é do fornecedor Kave? Decide qual dos dois logótipos sai."""
        self.ensure_one()
        if 'product_tag_ids' not in self._fields:
            return False
        return any(
            'kave' in (nome or '').lower()
            for nome in self.product_tag_ids.mapped('name')
        )

    # -- variantes ---------------------------------------------------------

    def _pg_label_variant_values(self):
        """Pares "Atributo: Valor" a imprimir."""
        self.ensure_one()
        return self.attribute_line_ids.mapped('value_ids')

    # -- acções ------------------------------------------------------------

    def action_pg_print_label_a5(self):
        return self.env.ref('pg_etiquetas.action_report_pg_etiqueta_a5_template').report_action(self)
