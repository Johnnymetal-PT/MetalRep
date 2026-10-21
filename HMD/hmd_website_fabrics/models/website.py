# -*- coding: utf-8 -*-
from odoo import models
from odoo.osv import expression


class Website(models.Model):
    _inherit = 'website'

    def sale_product_domain(self):
        """Tira da grelha da loja os materiais e os tecidos (#7877).

        Estao publicados de proposito: as paginas /fabrics e /materials e a
        pagina de cada tecido (controllers/main.py) exigem-no. Mas o
        website_sale mostra na /shop todos os artigos publicados, e a 08/10/2026
        os 77 do teste apareciam la misturados com o mobiliario, com preco 1.

        Este dominio so e usado para LISTAR artigos (grelha, pesquisa, sitemap,
        acessorios e alternativas: website_sale 18.0, controllers/main.py e
        models/product_template.py). Nao controla o acesso a pagina de um
        artigo, por isso as paginas dos tecidos continuam a funcionar.

        So actua nos websites com o tema HMD; a intranet nao muda.
        """
        domain = super().sale_product_domain()
        website = self or self.get_current_website()
        hidden = website._hmd_shop_hidden_category_ids()
        if hidden:
            domain = expression.AND([domain, [('public_categ_ids', 'not in', hidden)]])
        return domain

    def _hmd_shop_hidden_category_ids(self):
        """Ids das categorias (e subcategorias) a esconder da loja.

        Vem do parametro de sistema `hmd_website_fabrics.shop_hidden_categories`
        (ids separados por virgula). Ids e nao nomes: os nomes destas
        categorias sao traduzidos e foram criados pela HMD, sem xmlid. Sem o
        parametro nao se esconde nada.
        """
        self.ensure_one()
        # sudo: theme_id e um ir.module.module, que o visitante sem conta nao
        # pode ler. Sem isto a /shop dava 403 a quem nao tem sessao (08/10).
        if self.sudo().theme_id.name != 'theme_hmd_furniture':
            return []
        raw = self.env['ir.config_parameter'].sudo().get_param(
            'hmd_website_fabrics.shop_hidden_categories', '')
        ids = [int(x) for x in raw.split(',') if x.strip().isdigit()]
        if not ids:
            return []
        Categ = self.env['product.public.category'].sudo()
        return Categ.search([('id', 'child_of', ids)]).ids
