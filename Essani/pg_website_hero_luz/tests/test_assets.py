# -*- coding: utf-8 -*-
from odoo.addons.pg_website_hero_luz.hooks import (
    CAMINHO_CSS, PARAM_WEBSITE, SUFIXO_ASSET, garantir_asset,
    post_init_ligar_ao_website)
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestHeroLuzLigadoAoWebsiteCerto(TransactionCase):

    def setUp(self):
        super().setUp()
        # Começa sem o que a instalação possa já ter criado.
        rec = self.env.ref("pg_website_hero_luz.%s" % SUFIXO_ASSET,
                           raise_if_not_found=False)
        rec and rec.unlink()
        self.env["ir.config_parameter"].sudo().set_param(
            PARAM_WEBSITE, "Website de ensaio PG")

    def _assets(self):
        return self.env["ir.asset"].search(
            [("name", "like", "pg_website_hero_luz:%")])

    def test_sem_o_website_nao_se_liga_nada(self):
        """Um asset sem `website_id` vale para todos os websites: pior que não ligar."""
        post_init_ligar_ao_website(self.env)
        self.assertFalse(self._assets())

    def test_com_o_website_fica_preso_a_ele(self):
        website = self.env["website"].create({"name": "Website de ensaio PG"})
        outro = self.env["website"].create({"name": "Outro website"})

        post_init_ligar_ao_website(self.env)

        assets = self._assets()
        self.assertEqual(len(assets), 1)
        self.assertEqual(assets.website_id, website)
        self.assertNotEqual(assets.website_id, outro)
        self.assertTrue(assets.path.endswith(CAMINHO_CSS))

    def test_correr_duas_vezes_nao_duplica(self):
        self.env["website"].create({"name": "Website de ensaio PG"})
        post_init_ligar_ao_website(self.env)
        post_init_ligar_ao_website(self.env)
        self.assertEqual(len(self._assets()), 1)

    def test_garantir_recria_o_que_foi_apagado(self):
        self.env["website"].create({"name": "Website de ensaio PG"})
        post_init_ligar_ao_website(self.env)
        self._assets().unlink()
        self.assertFalse(self._assets())

        garantir_asset(self.env)

        self.assertEqual(len(self._assets()), 1)

    def test_o_asset_fica_protegido_das_atualizacoes(self):
        """`noupdate` evita que o Odoo o apague como registo órfão ao atualizar."""
        self.env["website"].create({"name": "Website de ensaio PG"})
        post_init_ligar_ao_website(self.env)
        dados = self.env["ir.model.data"].search([
            ("module", "=", "pg_website_hero_luz"), ("model", "=", "ir.asset")])
        self.assertEqual(len(dados), 1)
        self.assertTrue(dados.noupdate)
