# -*- coding: utf-8 -*-
from odoo.addons.pg_website_animations.hooks import (
    PARAM_WEBSITE, post_init_criar_assets)
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestAssetsLigadosAoWebsiteCerto(TransactionCase):

    def setUp(self):
        super().setUp()
        # Começa sem os assets que a instalação possa já ter criado.
        for sufixo in ("asset_css", "asset_js"):
            self.env.ref("pg_website_animations.%s" % sufixo,
                         raise_if_not_found=False) and self.env.ref(
                "pg_website_animations.%s" % sufixo).unlink()
        self.env["ir.config_parameter"].sudo().set_param(
            PARAM_WEBSITE, "Website de ensaio PG")

    def _assets(self):
        return self.env["ir.asset"].search(
            [("name", "like", "pg_website_animations:%")])

    def test_sem_o_website_nao_se_liga_nada(self):
        """Um asset sem `website_id` vale para todos os websites: pior que não ligar."""
        post_init_criar_assets(self.env)
        self.assertFalse(self._assets())

    def test_com_o_website_os_assets_ficam_presos_a_ele(self):
        website = self.env["website"].create({"name": "Website de ensaio PG"})
        outro = self.env["website"].create({"name": "Outro website"})

        post_init_criar_assets(self.env)

        assets = self._assets()
        self.assertEqual(len(assets), 2)
        self.assertEqual(assets.mapped("website_id"), website)
        self.assertNotIn(outro, assets.mapped("website_id"))
        self.assertEqual(set(assets.mapped("bundle")), {"web.assets_frontend"})

    def test_correr_duas_vezes_nao_duplica(self):
        self.env["website"].create({"name": "Website de ensaio PG"})
        post_init_criar_assets(self.env)
        post_init_criar_assets(self.env)
        self.assertEqual(len(self._assets()), 2)
