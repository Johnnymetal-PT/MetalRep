from odoo.tests import TransactionCase, tagged
from psycopg2 import IntegrityError
from odoo.tools import mute_logger

from .common import PgAiDevAssistantTestMixin


@tagged('post_install', '-at_install')
class TestOdooConnection(PgAiDevAssistantTestMixin, TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.repository = cls.create_repository(name='conn_repo')

    def test_two_purposes_coexist_on_same_repo(self):
        prod = self.env['pg.odoo.connection'].create({
            'repository_id': self.repository.id,
            'purpose': 'production',
            'base_url': 'https://cliente.odoo.com',
            'database': 'cliente-main',
            'login': 'it.odoo@parametro.global',
            'api_key': 'k-prod',
        })
        dev = self.env['pg.odoo.connection'].create({
            'repository_id': self.repository.id,
            'purpose': 'brodoo_dev',
            'base_url': 'https://cliente-brodoo-123.dev.odoo.com',
            'database': 'cliente-brodoo',
            'login': 'it.odoo@parametro.global',
            'api_key': 'k-dev',
        })
        self.assertIn(prod, self.repository.odoo_connection_ids)
        self.assertIn(dev, self.repository.odoo_connection_ids)
        # O label da finalidade e acentuado no modelo (regra de redacao em pt-PT);
        # a assercao ficou por actualizar quando os acentos entraram.
        self.assertEqual(prod.name, 'Produção do cliente (adoção) - https://cliente.odoo.com')

    def test_duplicate_purpose_is_rejected(self):
        self.env['pg.odoo.connection'].create({
            'repository_id': self.repository.id,
            'purpose': 'production',
            'base_url': 'https://cliente.odoo.com',
        })
        with self.assertRaises(IntegrityError), mute_logger('odoo.sql_db'):
            self.env['pg.odoo.connection'].create({
                'repository_id': self.repository.id,
                'purpose': 'production',
                'base_url': 'https://outro.odoo.com',
            })
            self.env.flush_all()
