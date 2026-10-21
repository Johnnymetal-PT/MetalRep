# -*- coding: utf-8 -*-
from odoo.addons.pg_website_scroll_scenes.hooks import (
    ASSETS, PARAM_WEBSITE, URL_DEMO, atualizar_pagina_demo, garantir_assets,
    post_init_criar_assets)
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestCenasLigadasAoWebsiteCerto(TransactionCase):

    def setUp(self):
        super().setUp()
        # Começa sem o que a instalação possa já ter criado.
        for sufixo, *_ in ASSETS:
            rec = self.env.ref("pg_website_scroll_scenes.%s" % sufixo,
                               raise_if_not_found=False)
            rec and rec.unlink()
        demo = self.env.ref("pg_website_scroll_scenes.demo_page",
                            raise_if_not_found=False)
        demo and demo.unlink()
        self.env["ir.config_parameter"].sudo().set_param(
            PARAM_WEBSITE, "Website de ensaio PG")

    def _assets(self):
        return self.env["ir.asset"].search(
            [("name", "like", "pg_website_scroll_scenes:%")])

    def test_sem_o_website_nao_se_liga_nada(self):
        """Um asset sem `website_id` vale para todos os websites: pior que não ligar."""
        post_init_criar_assets(self.env)
        self.assertFalse(self._assets())
        self.assertFalse(self.env["website.page"].search([("url", "=", URL_DEMO)]))

    def test_com_o_website_tudo_fica_preso_a_ele(self):
        website = self.env["website"].create({"name": "Website de ensaio PG"})
        outro = self.env["website"].create({"name": "Outro website"})

        post_init_criar_assets(self.env)

        assets = self._assets()
        self.assertEqual(len(assets), len(ASSETS))
        self.assertEqual(assets.mapped("website_id"), website)
        self.assertNotIn(outro, assets.mapped("website_id"))
        paginas = self.env["website.page"].search([("url", "=", URL_DEMO)])
        self.assertEqual(paginas.mapped("website_id"), website)

    def test_o_gsap_vem_antes_do_motor(self):
        """O motor usa window.gsap; carregado antes dele, falha em silêncio."""
        self.env["website"].create({"name": "Website de ensaio PG"})
        post_init_criar_assets(self.env)
        ordenados = self._assets().sorted(lambda a: (a.sequence, a.id))
        caminhos = [a.path.rsplit("/", 1)[-1] for a in ordenados]
        self.assertEqual(
            caminhos,
            ["gsap.min.js", "ScrollTrigger.min.js", "pg_scenes.css", "pg_scenes.js"])

    def test_correr_duas_vezes_nao_duplica(self):
        self.env["website"].create({"name": "Website de ensaio PG"})
        post_init_criar_assets(self.env)
        post_init_criar_assets(self.env)
        self.assertEqual(len(self._assets()), len(ASSETS))
        self.assertEqual(
            self.env["website.page"].search_count([("url", "=", URL_DEMO)]), 1)

    def test_atualizar_repoe_o_conteudo_sem_mexer_no_url(self):
        website = self.env["website"].create({"name": "Website de ensaio PG"})
        post_init_criar_assets(self.env)
        pagina = self.env["website.page"].search(
            [("url", "=", URL_DEMO), ("website_id", "=", website.id)])
        pagina.write({"arch": pagina.arch.replace("data-pg-scene", "data-x-scene")})
        self.assertNotIn("data-pg-scene", pagina.arch)

        atualizar_pagina_demo(self.env)

        self.assertIn("data-pg-scene", pagina.arch)
        self.assertEqual(pagina.url, URL_DEMO)
        self.assertEqual(
            self.env["website.page"].search_count([("url", "=", URL_DEMO)]), 1)

    def test_garantir_assets_recria_o_que_foi_apagado(self):
        """Uma atualização do módulo chegou a apagar os assets: a migração recria-os."""
        self.env["website"].create({"name": "Website de ensaio PG"})
        post_init_criar_assets(self.env)
        self._assets().unlink()
        self.assertFalse(self._assets())

        garantir_assets(self.env)

        self.assertEqual(len(self._assets()), len(ASSETS))

    def test_os_assets_ficam_protegidos_das_atualizacoes(self):
        """`noupdate` evita que o Odoo os apague como registos órfãos ao atualizar."""
        self.env["website"].create({"name": "Website de ensaio PG"})
        post_init_criar_assets(self.env)
        dados = self.env["ir.model.data"].search([
            ("module", "=", "pg_website_scroll_scenes"), ("model", "=", "ir.asset")])
        self.assertEqual(len(dados), len(ASSETS))
        self.assertTrue(all(dados.mapped("noupdate")))
