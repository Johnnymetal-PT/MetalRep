from odoo import api, models

HEADER = "theme_hmd_furniture.template_header_hmd"
FOOTER = "theme_hmd_furniture.footer_hmd"

# Opcoes da loja que o desenho nao tem
SHOP_VIEWS_OFF = [
    "website_sale.products_categories",      # barra lateral de categorias
    "website_sale.products_attributes",      # filtros de atributos
    "website_sale.products_categories_top",  # categorias no topo
    "website_sale.sort",                     # ordenacao
    "website_sale.search",                   # pesquisa dentro da loja
]

# Blocos que o Odoo mostra na pagina de produto e que o desenho da Monica nao
# tem. Confirmado no PDF da pagina do CONGO 110 (28/08/2026). Sao vistas
# opcionais, desligadas por website — nao e preciso tocar em templates.
PRODUCT_VIEWS_OFF = [
    # ATENCAO: duas vistas nativas NAO podem entrar nesta lista, porque o nosso
    # tema herda delas — desactivar a mae faz desaparecer a filha, sem erro
    # nenhum no log:
    #
    #   website_sale_comparison.product_attributes_body
    #     A seccao "Specifications". Fica activa e o nosso
    #     product_specs_only_public_hmd limita-a a quem nao tem sessao
    #     iniciada (decisao da HMD, 01/09/2026).
    #
    #   website_sale.alternative_products
    #     A nossa seccao "Other options" e um xpath que substitui o conteudo
    #     dessa vista. O "OTHER OPTIONS" a mais que se via na pagina nao vinha
    #     dela: vinha de um snippet gravado no website_description dos
    #     produtos, escondido por CSS em static/src/scss/shop.scss.
    # "Terms and Conditions / 30-day money-back guarantee / Shipping: 2-3
    # Business Days" — active="True" no nativo
    "website_sale.product_custom_text",
    # botoes de partilha (Facebook, X, LinkedIn, WhatsApp, Pinterest, email)
    "website_sale.product_share_buttons",
    # aba "Specifications" do acordeao, com a lista de todos os acabamentos
    "website_sale_comparison.accordion_specs_item",
    # aba "More Information"; ja nasce inactiva, fica aqui por seguranca —
    # o acordeao so aparece se uma das duas abas estiver activa
    "website_sale.accordion_more_information",
]


class ThemeUtils(models.AbstractModel):
    _inherit = "theme.utils"

    @api.model
    def _theme_hmd_furniture_post_copy(self, mod):
        """Activa o cabecalho e o rodape do desenho, no website onde o tema
        acabou de ser aplicado.

        O nosso cabecalho substitui ``//header//nav`` e o nosso rodape
        substitui ``//div[@id='footer']`` — exactamente os mesmos nos que os
        templates nativos. Com os dois activos ha dois ``position="replace"``
        sobre o mesmo no: o segundo nao encontra o no, a validacao da vista
        falha e o site devolve HTTP 500 em todas as paginas.

        O Odoo trata cabecalhos e rodapes como conjuntos mutuamente exclusivos
        (``_header_templates`` / ``_footer_templates``). Como os nossos nao
        pertencem a esses conjuntos, garantimos a exclusividade aqui:
        desligamos todos os nativos e so depois ligamos os nossos, que vem do
        tema com ``active="False"`` precisamente para nao colidirem no momento
        da copia.
        """
        for view in self._header_templates:
            self.disable_view(view)
        for view in self._footer_templates:
            self.disable_view(view)

        self.enable_view(HEADER)
        self.enable_view(FOOTER)

        # O desenho nao tem a barra de copyright do Odoo: o aviso da HMD
        # ("HMD FURNITURE(C)2026" + "COOKIE POLICY") ja esta na primeira coluna
        # do rodape, e o selector de lingua vive no cabecalho (EN|PT).
        self.enable_view("website.footer_no_copyright")

        # Botao de carrinho na grelha do catalogo: o Odoo traz esta opcao
        # desligada, e o desenho mostra-o ao lado da wishlist e do comparar.
        self.enable_view("website_sale.products_add_to_cart")

        # Catalogo (Collection.pdf): grelha limpa de 5 colunas sobre fundo
        # cinza — sem barra lateral de categorias, sem filtros de atributos,
        # sem barra de categorias no topo, sem ordenacao e sem caixa de
        # pesquisa dentro da loja (a pesquisa vive no cabecalho).
        for view in SHOP_VIEWS_OFF + PRODUCT_VIEWS_OFF:
            self.disable_view(view)

        website = self.env["website"].get_current_website()
        if website:
            website.write({"shop_ppr": 5, "shop_ppg": 20})

    @api.model
    def enable_view(self, xml_id):
        """Mantem a exclusividade quando alguem escolhe um cabecalho ou rodape
        nativo no construtor de website.

        Sem isto, activar uma variante nativa deixaria a nossa tambem activa
        — e o site voltaria a dar HTTP 500. Usamos as listas do proprio Odoo
        para nao ficarmos desalinhados entre versoes.
        """
        if xml_id in self._header_templates:
            self.disable_view(HEADER)
        elif xml_id in self._footer_templates:
            self.disable_view(FOOTER)
        return super().enable_view(xml_id)
