# -*- coding: utf-8 -*-
from odoo import api, models


class ProductPublicCategory(models.Model):
    _inherit = 'product.public.category'

    @api.model
    def _hmd_fabrics_root(self):
        """Categoria raiz dos tecidos.

        Ha UMA via de resolucao, de proposito: o nome, com "Tecidos" por
        omissao e o parametro de sistema `hmd_website_fabrics.category_name`
        para o mudar sem tocar em codigo.

        Nao se usa o id fixo (24 na base HMD_TESTE) porque um id nao sobrevive
        a passagem para outra base, e nao se usa xmlid porque a categoria foi
        criada pela HMD e nao por nos — nao temos onde o declarar.

        :rtype: recordset de product.public.category, vazio se nao existir
        """
        name = self.env['ir.config_parameter'].sudo().get_param(
            'hmd_website_fabrics.category_name', 'Tecidos',
        )
        Categoria = self.sudo()

        root = Categoria.search([('name', '=', name)], limit=1)
        if root:
            return root

        # O `name` da categoria e um campo TRADUZIDO, e a procura acontece
        # sempre no idioma do contexto. O site novo esta em en_GB, onde esta
        # categoria se chama "Fabrics" — a procura por "Tecidos" nao devolvia
        # nada e a pagina caia na rede de seguranca, mostrando as imagens de
        # maqueta com os tecidos todos carregados por tras.
        #
        # Diagnosticado a 16/09/2026, reproduzindo o pedido web: no shell
        # (pt_PT) devolvia a categoria, no pedido (en_GB) devolvia vazio.
        #
        # Procura-se em cada idioma instalado, para o parametro poder ser
        # escrito em qualquer um deles.
        for codigo, _etiqueta in self.env['res.lang'].sudo().get_installed():
            root = Categoria.with_context(lang=codigo).search(
                [('name', '=', name)], limit=1,
            )
            if root:
                return root

        return Categoria.browse()
