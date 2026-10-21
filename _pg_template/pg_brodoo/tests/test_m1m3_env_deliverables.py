from odoo.tests import TransactionCase, tagged

from odoo.addons.pg_brodoo.services.project_mirror_payload_builder import ProjectMirrorPayloadBuilder

from .common import PgAiDevAssistantTestMixin


@tagged('post_install', '-at_install')
class TestM1M3EnvDeliverables(PgAiDevAssistantTestMixin, TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_pg_base_url('https://example.test')
        cls.repository = cls.create_repository()
        cls.project = cls.create_project(cls.repository)
        cls.builder = ProjectMirrorPayloadBuilder(cls.env)

    # M1 -----------------------------------------------------------------
    def test_odoo_env_payload_never_publishes_the_local_module_list(self):
        """Prova anti-regressao (PG-007): o M1 descreve o Odoo do CLIENTE.

        Ate 2026-08-10 o payload inventariava `self.env` - a base onde o pg_brodoo
        corre, que e o Odoo da Parametro Global - e o teste anterior consagrava-o ao
        exigir `pg_brodoo` na lista. Publicava-se assim, em 13 repositorios, o
        inventario da PG etiquetado com os dados do cliente, invertendo o passo 1
        contra o passo 2 da ordem obrigatoria de decisao.
        """
        payload = self.builder.build_odoo_env_payload(self.project)
        self.assertEqual(payload['schema_version'], ProjectMirrorPayloadBuilder.ODOO_ENV_SCHEMA_VERSION)
        env = payload['odoo_env']
        self.assertEqual(env['odoo_version'], self.project.pg_odoo_version)
        self.assertEqual(env['odoo_edition'], self.project.pg_odoo_edition)
        names = [m['name'] for m in env['installed_modules']]
        self.assertNotIn('pg_brodoo', names)
        # payload_hash presente e nao-vazio
        self.assertTrue(payload['source_metadata']['payload_hash'].startswith('sha256:'))

    def test_odoo_env_payload_declares_unavailable_without_collection(self):
        """Sem recolha no cliente, o artefacto diz que nao sabe.

        `unavailable` tem de ser distinguivel de "nada instalado": e o que impede o
        agente de fechar a ordem de decisao sobre um espelho vazio.
        """
        payload = self.builder.build_odoo_env_payload(self.project)
        collection = payload['odoo_env']['collection']
        self.assertEqual(collection['status'], ProjectMirrorPayloadBuilder.ODOO_ENV_UNAVAILABLE)
        self.assertEqual(collection['unavailable_reason'], 'never_collected')
        self.assertEqual(payload['odoo_env']['installed_modules'], [])
        self.assertEqual(payload['odoo_env']['installed_module_count'], 0)

    def test_odoo_env_payload_identifies_the_collected_database(self):
        """Quando ha recolha, o payload identifica a base inventariada."""
        snapshot = {
            'status': ProjectMirrorPayloadBuilder.ODOO_ENV_COLLECTED,
            'purpose': 'production',
            'base_url': 'https://cliente.odoo.com',
            'database': 'cliente-main-12345678',
            'collected_at': '2026-08-11 09:00:00',
            'collected_by': 'Operador',
            'installed_modules': [{
                'name': 'sale',
                'shortdesc': 'Sales',
                'installed_version': '19.0.1.0',
                'application': True,
                'author': 'Odoo S.A.',
            }],
        }
        self.patch(self.builder, '_odoo_env_snapshot', lambda _project: snapshot)
        payload = self.builder.build_odoo_env_payload(self.project)
        collection = payload['odoo_env']['collection']
        self.assertEqual(collection['status'], ProjectMirrorPayloadBuilder.ODOO_ENV_COLLECTED)
        self.assertEqual(collection['base_url'], 'https://cliente.odoo.com')
        self.assertEqual(collection['database'], 'cliente-main-12345678')
        self.assertEqual(payload['odoo_env']['installed_module_count'], 1)
        self.assertEqual([m['name'] for m in payload['odoo_env']['installed_modules']], ['sale'])

    def test_odoo_env_hash_ignores_collection_timestamp(self):
        """PG-007 D7: recolher de novo o mesmo inventario nao gera commit."""
        base = {
            'status': ProjectMirrorPayloadBuilder.ODOO_ENV_COLLECTED,
            'purpose': 'production',
            'base_url': 'https://cliente.odoo.com',
            'database': 'cliente-main-12345678',
            'collected_by': 'Operador',
            'installed_modules': [],
        }
        self.patch(self.builder, '_odoo_env_snapshot',
                   lambda _project: dict(base, collected_at='2026-08-11 09:00:00'))
        h1 = self.builder.build_odoo_env_payload(self.project)['source_metadata']['payload_hash']
        self.patch(self.builder, '_odoo_env_snapshot',
                   lambda _project: dict(base, collected_at='2026-08-12 18:30:00'))
        h2 = self.builder.build_odoo_env_payload(self.project)['source_metadata']['payload_hash']
        self.assertEqual(h1, h2)

    def test_odoo_env_hash_is_stable_across_builds(self):
        """Prova anti-regressao (incidente AUD-04): sem campos volateis no hash ->
        dois builds seguidos produzem o MESMO payload_hash -> nao ha commit repetido."""
        h1 = self.builder.build_odoo_env_payload(self.project)['source_metadata']['payload_hash']
        h2 = self.builder.build_odoo_env_payload(self.project)['source_metadata']['payload_hash']
        self.assertEqual(h1, h2)

    # M3 -----------------------------------------------------------------
    def test_deliverables_payload_includes_milestones_and_commitment(self):
        milestone = self.create_project_milestone(self.project, name='Kick-Off deliverable')
        payload = self.builder.build_deliverables_payload(self.project)
        self.assertEqual(payload['schema_version'], ProjectMirrorPayloadBuilder.DELIVERABLES_SCHEMA_VERSION)
        deliverables = payload['deliverables']
        self.assertIsInstance(deliverables['milestones'], list)
        milestone_ids = [m['odoo_id'] for m in deliverables['milestones']]
        self.assertIn(milestone.id, milestone_ids)
        target = next(m for m in deliverables['milestones'] if m['odoo_id'] == milestone.id)
        self.assertEqual(target['delivery_state'], milestone.pg_delivery_state)
        self.assertEqual(target['acceptance_state'], milestone.pg_acceptance_state)

    def test_deliverables_hash_is_stable_across_builds(self):
        self.create_project_milestone(self.project, name='Entrega estavel')
        h1 = self.builder.build_deliverables_payload(self.project)['source_metadata']['payload_hash']
        h2 = self.builder.build_deliverables_payload(self.project)['source_metadata']['payload_hash']
        self.assertEqual(h1, h2)
