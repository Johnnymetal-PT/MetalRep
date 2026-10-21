# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    hmd_fabric_composition = fields.Text(
        string="Composição",
        help="Composição básica do tecido. Escrita por série: as cores da "
             "mesma série partilham a composição.",
    )

    # Vocabulario fechado, e nao um Many2one aos valores do atributo
    # "CATEGORIA TECIDO" (104) dos moveis. Esses valores incluem lixo — um "-"
    # e um "COM" a duplicar o "C.O.M." — e amarrar o site a eles importava essa
    # desarrumacao para dentro da pagina. A ligacao entre o tecido e o movel e
    # de significado, nao de registo.
    HMD_FABRIC_CATEGORIES = [
        ('cat_1', "CAT I"),
        ('cat_2', "CAT II"),
        ('cat_3', "CAT III"),
        ('cat_4', "CAT IV"),
        ('cat_5', "CAT V"),
        ('com', "C.O.M."),
    ]

    hmd_fabric_category = fields.Selection(
        selection=HMD_FABRIC_CATEGORIES,
        string="Categoria de tecido",
        index=True,
        help="Gama do tecido. Divide as secções da página /fabrics. "
             "C.O.M. é tecido trazido pelo cliente e não acresce ao preço "
             "do móvel.",
    )

    # Pedido do Miguel Guedes (HMD), 24/09/2026, tarefa #7542: um sitio para a
    # imagem das instrucoes de limpeza. E da serie, como a composicao: as cores
    # da mesma serie limpam-se da mesma maneira.
    hmd_fabric_care_image = fields.Image(
        string="Instruções de limpeza",
        max_width=1024,
        max_height=1024,
        help="Imagem com as instruções de limpeza do tecido (os símbolos de "
             "lavagem). Aparece nas especificações do tecido no site.",
    )

    hmd_fabric_family = fields.Char(
        string="Família de tecido",
        compute='_compute_hmd_fabric_family',
        store=True,
        index=True,
        help="Duas primeiras letras do código do tecido. Agrupa as séries na "
             "página /fabrics.",
    )

    @api.depends('name')
    def _compute_hmd_fabric_family(self):
        """As duas primeiras letras do nome, em maiusculas.

        E a convencao que a HMD usa hoje nos codigos: LUDE e LUCO sao a familia
        LU, ALBO/ALCH/ALRC sao AL, IMAI/IMAN sao IM, e assim por diante.

        Calcula-se para TODOS os produtos, nao so para tecidos: um campo
        calculado com dominio condicional obriga a recalcular quando a
        categoria muda, e o valor num sofa nao incomoda ninguem porque so a
        pagina de tecidos o le.
        """
        for template in self:
            name = (template.name or '').strip()
            template.hmd_fabric_family = name[:2].upper() or False

    def _hmd_is_fabric(self):
        """Se este produto esta na arvore da categoria de tecidos.

        Usa-se `child_of` e nao uma comparacao direta para que subcategorias
        ("Tecidos / Lino") contem como tecidos.
        """
        self.ensure_one()
        root = self.env['product.public.category']._hmd_fabrics_root()
        if not root:
            return False
        return bool(self.sudo().search_count([
            ('id', '=', self.id),
            ('public_categ_ids', 'child_of', root.id),
        ]))

    @api.model
    def _hmd_fabric_families(self):
        """Tecidos publicados, agrupados por familia.

        Devolve uma lista de tuplos (chave, titulo, tecidos), por ordem
        alfabetica da chave. A vista do tema consome isto e nao faz
        agrupamento nenhum: logica de dados em Python, marcacao em QWeb.

        O TITULO tem duas origens, por esta ordem:

          1. uma subcategoria da categoria de tecidos cujos produtos coincidam
             com a familia — e a forma de a HMD dar nomes legiveis as familias
             sozinha, criando "Tecidos / <nome>" no Odoo;
          2. na ausencia dela, a propria chave de duas letras.

        Sem isto o cabecalho da seccao seria sempre "LU" ou "AL", que nao diz
        nada a quem visita o site.

        A curadoria e o `website_published` de cada tecido, por decisao da HMD
        a 07/09/2026: nao se inventou campo para isso.
        """
        root = self.env['product.public.category']._hmd_fabrics_root()
        if not root:
            return []

        fabrics = self.sudo().search(
            [
                ('public_categ_ids', 'child_of', root.id),
                ('website_published', '=', True),
            ],
            order='name',
        )
        if not fabrics:
            return []

        # Titulos vindos das subcategorias, quando existirem.
        titles = {}
        for child in root.sudo().child_id:
            child_fabrics = fabrics.filtered(
                lambda f, c=child: c in f.public_categ_ids
            )
            for key in set(child_fabrics.mapped('hmd_fabric_family')):
                titles.setdefault(key, child.name)

        grouped = {}
        for fabric in fabrics:
            grouped.setdefault(fabric.hmd_fabric_family or '', self.browse())
            grouped[fabric.hmd_fabric_family or ''] |= fabric

        return [
            (key, titles.get(key, key), grouped[key])
            for key in sorted(grouped)
        ]

    def _hmd_fabric_swatches(self):
        """Variantes com fotografia, que sao as amostras de cor.

        Sem fotografia a amostra nao tem nada para mostrar, por isso filtra-se
        aqui e nao na vista.
        """
        self.ensure_one()
        return self.sudo().product_variant_ids.filtered(
            lambda variant: variant.active and variant.image_1920
        )

    def _hmd_fabric_documents(self):
        """Fichas tecnicas publicaveis deste tecido.

        A descarga usa a rota do website_sale, que revalida tudo isto do lado
        do servidor; aqui filtra-se apenas para nao desenhar botoes que a rota
        iria recusar.
        """
        self.ensure_one()
        return self.env['product.document'].sudo().search([
            ('res_model', '=', 'product.template'),
            ('res_id', '=', self.id),
            ('shown_on_product_page', '=', True),
        ])

    def _hmd_fabric_url(self):
        """URL da pagina de especificacoes deste tecido.

        Monta-se aqui e nao na vista para o slug vir do mesmo sitio de onde o
        website_sale o tira (`ir.http._slug`) — se um dia mudar, muda num
        ficheiro so.
        """
        self.ensure_one()
        return '/fabrics/%s' % self.env['ir.http']._slug(self)

    def _hmd_fabric_spec_items(self):
        """Linhas de texto das especificacoes do tecido: [(rotulo, valor)].

        Uma so fonte para a pagina do tecido e para a seccao "Specifications"
        da pagina de produto. Ate 24/09/2026 so a pagina do tecido as mostrava:
        a composicao aparecia em /fabrics/<serie> e nao em /shop/<serie>
        (tarefa #7542).
        """
        self.ensure_one()
        fabric = self.sudo()
        items = []
        # A gama (CAT I a CAT V, C.O.M.) e nao a categoria do site: esta dizia
        # "Fabrics" em todos os tecidos. Decisao da HMD, 24/09/2026 (#7542).
        # Sem gama atribuida a linha nao aparece.
        if fabric.hmd_fabric_category:
            items.append(("Category", dict(self.HMD_FABRIC_CATEGORIES)[fabric.hmd_fabric_category]))
        if fabric.hmd_fabric_composition:
            items.append(("Composition", fabric.hmd_fabric_composition))
        return items

    def _hmd_fabric_attributes(self):
        """Linhas de atributo validas, para a tabela de especificacoes.

        E a mesma fonte que a seccao "Specifications" do website_sale usa na
        pagina de produto — nao se reinventa o dado, so se muda a apresentacao.
        """
        self.ensure_one()
        return self.sudo().valid_product_template_attribute_line_ids

    def _hmd_fabric_tags(self):
        """Etiquetas do tecido visiveis no e-commerce.

        As etiquetas vivem nas variantes e nao no template, por isso agregam-se
        a partir delas — e filtra-se por `visible_on_ecommerce`, senao o site
        mostrava etiquetas internas de gestao.
        """
        self.ensure_one()
        return self.sudo().product_variant_ids.all_product_tag_ids.filtered(
            'visible_on_ecommerce'
        )

    @api.model
    def _hmd_fabric_categories(self):
        """Tecidos publicados, agrupados pela categoria de gama.

        Devolve [(chave, titulo, ancora, tecidos), ...] pela ordem do proprio
        campo — CAT I a CAT V e depois C.O.M. — e nao por ordem alfabetica, que
        poria a CAT V antes da CAT I.

        A ancora e estavel e derivada da chave (`cat_1` -> `cat-1`): e para ela
        que a pagina do movel vai apontar quando ligarmos o seletor de
        categoria, e um link que muda de valor nao serve para nada.

        Tecidos sem categoria NAO aparecem. E deliberado: sem categoria nao ha
        seccao onde os por, e uma seccao "outros" numa pagina de cliente e um
        aviso de trabalho por fazer virado para fora.

        A curadoria continua a ser o `website_published` de cada tecido.
        """
        root = self.env['product.public.category']._hmd_fabrics_root()
        if not root:
            return []

        fabrics = self.sudo().search(
            [
                ('public_categ_ids', 'child_of', root.id),
                ('website_published', '=', True),
                ('hmd_fabric_category', '!=', False),
            ],
            order='name',
        )

        grouped = []
        for key, label in self.HMD_FABRIC_CATEGORIES:
            selected = fabrics.filtered(
                lambda f, k=key: f.hmd_fabric_category == k
            )
            if selected:
                grouped.append((key, label, key.replace('_', '-'), selected))
        return grouped

    @api.model
    def _hmd_seed_fabric_categories(self):
        """Atribuicao inicial das categorias, so onde estiverem vazias.

        A HMD pediu uma primeira atribuicao para poder ver a pagina a funcionar,
        e disse que ajusta depois. Esta e essa: NAO tem significado comercial.

        A regra e a unica defensavel sem saber os precos: uma familia inteira
        fica na mesma categoria, porque uma colecao de tecidos costuma ser toda
        da mesma gama; as familias sao distribuidas por CAT I a CAT V pela sua
        ordem alfabetica.

        Nunca escreve por cima de um valor ja preenchido, para poder ser corrida
        outra vez depois de a HMD ter ajustado sem lhe estragar o trabalho.

        :return: numero de tecidos classificados
        """
        root = self.env['product.public.category']._hmd_fabrics_root()
        if not root:
            return 0

        pending = self.sudo().search([
            ('public_categ_ids', 'child_of', root.id),
            ('hmd_fabric_category', '=', False),
        ], order='name')
        if not pending:
            return 0

        keys = [key for key, _label in self.HMD_FABRIC_CATEGORIES if key != 'com']
        families = sorted(set(pending.mapped('hmd_fabric_family')))
        by_family = {
            family: keys[index % len(keys)]
            for index, family in enumerate(families)
        }
        for fabric in pending:
            fabric.hmd_fabric_category = by_family.get(fabric.hmd_fabric_family)
        return len(pending)
