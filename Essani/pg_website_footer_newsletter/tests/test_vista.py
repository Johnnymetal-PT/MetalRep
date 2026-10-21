# -*- coding: utf-8 -*-
from odoo.addons.pg_website_footer_newsletter.hooks import (
    CHAVE, MODULO, NOME_XMLID, PARAM_WEBSITE, garantir_vista, post_init_criar_vista)
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestRodapeNewsletter(TransactionCase):

    def setUp(self):
        super().setUp()
        antiga = self.env.ref("%s.%s" % (MODULO, NOME_XMLID), raise_if_not_found=False)
        antiga and antiga.unlink()
        self.env["ir.config_parameter"].sudo().set_param(PARAM_WEBSITE, "Website de ensaio PG")

    def _vistas(self):
        return self.env["ir.ui.view"].search([("key", "=", CHAVE)])

    def test_sem_o_website_nao_se_cria_nada(self):
        """Uma vista sem `website_id` valeria para todos os websites: pior que não criar."""
        post_init_criar_vista(self.env)
        self.assertFalse(self._vistas())

    def test_com_o_website_fica_presa_a_ele(self):
        website = self.env["website"].create({"name": "Website de ensaio PG"})
        outro = self.env["website"].create({"name": "Outro website"})
        post_init_criar_vista(self.env)
        vistas = self._vistas()
        self.assertEqual(len(vistas), 1)
        self.assertEqual(vistas.website_id, website)
        self.assertNotEqual(vistas.website_id, outro)

    def test_correr_duas_vezes_nao_duplica(self):
        self.env["website"].create({"name": "Website de ensaio PG"})
        garantir_vista(self.env)
        garantir_vista(self.env)
        self.assertEqual(len(self._vistas()), 1)

    def test_a_vista_fica_protegida_das_atualizacoes(self):
        self.env["website"].create({"name": "Website de ensaio PG"})
        garantir_vista(self.env)
        dados = self.env["ir.model.data"].search([
            ("module", "=", MODULO), ("model", "=", "ir.ui.view")])
        self.assertEqual(len(dados), 1)
        self.assertTrue(dados.noupdate)

    def test_o_texto_aparece_em_cada_lingua(self):
        self.env["website"].create({"name": "Website de ensaio PG"})
        garantir_vista(self.env)
        vista = self._vistas()
        esperado = {
            "en_US": "Stay up to date",
            "pt_PT": "Fique a par das novidades",
            "es_ES": "Manténgase al día",
        }
        for lingua, texto in esperado.items():
            arch = vista.with_context(lang=lingua).arch_db
            self.assertIn(texto, arch, lingua)
        # e o inglês nao fica com português
        self.assertNotIn("Fique a par", vista.with_context(lang="en_US").arch_db)
