from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPhcHistory(TransactionCase):

    def test_merge_sums_phc_history(self):
        """Fundir dois contactos duplicados soma o volume histórico e não perde o n.º PHC."""
        Partner = self.env["res.partner"]
        dst = Partner.create({"name": "Cliente PHC", "phc_history_amount": 1000.0})
        src = Partner.create({"name": "Cliente PHC (dup)", "phc_history_amount": 250.5, "phc_customer_number": "4021"})
        wizard = self.env["base.partner.merge.automatic.wizard"].create({})
        wizard._merge((dst + src).ids, dst)
        self.assertFalse(src.exists())
        self.assertAlmostEqual(dst.phc_history_amount, 1250.5)
        self.assertEqual(dst.phc_customer_number, "4021")

    def test_history_is_searchable(self):
        """O volume histórico é pesquisável e ordenável, ao contrário do total faturado standard."""
        Partner = self.env["res.partner"]
        big = Partner.create({"name": "Grande", "phc_history_amount": 50000.0})
        Partner.create({"name": "Pequeno", "phc_history_amount": 10.0})
        found = Partner.search([("phc_history_amount", ">=", 1000)], order="phc_history_amount desc")
        self.assertEqual(found[:1], big)
