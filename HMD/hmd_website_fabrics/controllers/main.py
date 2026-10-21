# -*- coding: utf-8 -*-
from werkzeug.exceptions import NotFound

from odoo import http
from odoo.http import request


class HmdWebsiteFabrics(http.Controller):

    @http.route(
        '/fabrics/<model("product.template"):fabric>',
        type='http',
        auth='public',
        website=True,
        sitemap=False,
        readonly=True,
    )
    def hmd_fabric_detail(self, fabric, **kwargs):
        """Pagina de especificacoes de um tecido.

        Duas condicoes, ambas em 404 e nao em redirect:

          - publicado. E o campo com que a HMD cura o que aparece no site; se
            a rota servisse despublicados, a curadoria dela nao valia nada;
          - ser tecido. Sem esta condicao a rota tornava-se uma segunda pagina
            de produto para o catalogo inteiro, a competir com /shop pelo mesmo
            conteudo.

        Le-se em sudo() porque o publico nao le `product.template` livremente,
        mas so depois de as duas condicoes passarem — a de publicado e
        exatamente a que o Odoo usa para decidir o que e visivel.
        """
        fabric_sudo = fabric.sudo()
        if not fabric_sudo.website_published or not fabric_sudo._hmd_is_fabric():
            raise NotFound()

        return request.render('hmd_website_fabrics.fabric_detail', {
            'fabric': fabric_sudo,
            'swatches': fabric_sudo._hmd_fabric_swatches(),
            'documents': fabric_sudo._hmd_fabric_documents(),
            # O editor do website usa o main_object para o widget de publicacao
            # e para o painel de SEO. Sem ele a Monica nao consegue despublicar
            # o tecido a partir da propria pagina.
            'main_object': fabric_sudo,
        })
