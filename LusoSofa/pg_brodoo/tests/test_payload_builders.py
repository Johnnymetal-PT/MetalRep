from odoo.tests import TransactionCase, tagged

from ..services.project_scope_payload_builder import ProjectScopePayloadBuilder
from .common import PgAiDevAssistantTestMixin


@tagged('post_install', '-at_install')
class TestPayloadBuilders(PgAiDevAssistantTestMixin, TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.set_pg_base_url()
        cls.repository = cls.create_repository()
        cls.project = cls.create_project(cls.repository)
        cls.scope_task = cls.create_task(cls.project, name='Tarefa em ambito')
        cls.create_task(
            cls.project,
            name='Tarefa excluida',
            pg_scope_relevant=False,
            pg_scope_state='excluded',
            pg_scope_summary='Nao deve entrar no payload.',
            pg_acceptance_criteria_text='Nao aplicavel',
        )
        cls.create_task(
            cls.project,
            name='Backlog operacional',
            pg_scope_track='operational_backlog',
            pg_scope_state='proposed',
            pg_scope_summary='Nao deve entrar no snapshot factual de scope.',
            pg_acceptance_criteria_text='Nao aplicavel',
        )
        cls.create_task(
            cls.project,
            name='Nota interna',
            pg_scope_track='internal_note',
            pg_scope_state='proposed',
            pg_scope_summary='Nao deve entrar no snapshot factual de scope.',
            pg_acceptance_criteria_text='Nao aplicavel',
        )
        cls.scope_builder = ProjectScopePayloadBuilder(cls.env)

    def test_scope_payload_uses_task_trigger_url_and_filters_scope_items(self):
        payload = self.scope_builder.build_payload(
            self.project,
            trigger_type='task_write',
            trigger_model='project.task',
            trigger_record_id=self.scope_task.id,
            sync_reason=f'project.task {self.scope_task.id}',
        )

        self.assertEqual(payload['project_name'], 'Projeto Piloto')
        self.assertEqual(payload['project_phase'], 'discovery')
        self.assertEqual(payload['scope_summary']['active_scope_item_count'], 1)
        self.assertEqual(len(payload['scope_items']), 1)
        self.assertEqual(payload['scope_items'][0]['task_name'], 'Tarefa em ambito')
        self.assertEqual(payload['scope_items'][0]['scope_track'], 'approved_scope')
        self.assertEqual(payload['scope_items'][0]['assigned_users'], [self.env.user.display_name])
        self.assertEqual(
            payload['scope_items'][0]['source_url'],
            f'https://example.test/web#id={self.scope_task.id}&model=project.task',
        )
        self.assertEqual(
            payload['source_metadata']['source_record_url'],
            f'https://example.test/web#id={self.scope_task.id}&model=project.task',
        )

    def test_scope_payload_excludes_operational_backlog_and_internal_notes(self):
        payload = self.scope_builder.build_payload(self.project)

        task_names = {item['task_name'] for item in payload['scope_items']}

        self.assertIn('Tarefa em ambito', task_names)
        self.assertNotIn('Backlog operacional', task_names)
        self.assertNotIn('Nota interna', task_names)

    def test_scope_payload_rejects_low_signal_official_summary_and_falls_back_to_description(self):
        task = self.create_task(
            self.project,
            name='Agendamento',
            description='<p>Agendar arranque do Odoo com a equipa comercial.</p>',
            pg_scope_summary=(
                'Bom dia Bruno, Hoje de tarde sempre passas por ca para dar seguimento ao arranque do Odoo? '
                'Com os melhores cumprimentos, Rui Ribeiro Image [7] ANCORA VIP INDUSTRY, LDA. '
                'Tel. +351 255 878 612'
            ),
            pg_scope_sequence=40,
        )

        payload = self.scope_builder.build_payload(self.project)
        payload_task = next(item for item in payload['scope_items'] if item['task_id'] == task.id)

        self.assertEqual(payload_task['scope_summary'], 'Agendar arranque do Odoo com a equipa comercial.')

    def test_scope_payload_derives_acceptance_criteria_from_description_when_official_text_is_placeholder(self):
        task = self.create_task(
            self.project,
            name='Webhook de faturacao',
            description=(
                '<p>Configurar sincronizacao do webhook de faturacao.</p>'
                '<p>O utilizador deve conseguir validar o webhook GitHub antes do go-live.</p>'
                '<p>O processo deve registar erros de integracao para analise posterior.</p>'
            ),
            pg_scope_summary='Configurar sincronizacao do webhook de faturacao.',
            pg_acceptance_criteria_text='[PONTO POR VALIDAR]',
            pg_scope_sequence=45,
        )

        payload = self.scope_builder.build_payload(self.project)
        payload_task = next(item for item in payload['scope_items'] if item['task_id'] == task.id)

        self.assertEqual(
            payload_task['acceptance_criteria'],
            [
                'O utilizador deve conseguir validar o webhook GitHub antes do go-live.',
                'O processo deve registar erros de integracao para analise posterior.',
            ],
        )

    def test_scope_payload_expands_generic_heading_into_factual_summary(self):
        task = self.create_task(
            self.project,
            name='Importacao de encomendas',
            description=(
                '<p>Desenvolvimento</p>'
                '<p>de funcionalidade para importacao de encomendas a partir de ficheiro Excel.</p>'
                '<p>O utilizador deve conseguir validar a importacao antes do go-live.</p>'
            ),
            pg_scope_summary='[PONTO POR VALIDAR]',
            pg_acceptance_criteria_text='[PONTO POR VALIDAR]',
            pg_scope_sequence=46,
        )

        payload = self.scope_builder.build_payload(self.project)
        payload_task = next(item for item in payload['scope_items'] if item['task_id'] == task.id)

        self.assertEqual(
            payload_task['scope_summary'],
            'Desenvolvimento de funcionalidade para importacao de encomendas a partir de ficheiro Excel.',
        )

    def test_scope_payload_skips_url_only_heading_and_uses_next_factual_line(self):
        task = self.create_task(
            self.project,
            name='Projeto na ref interna',
            description=(
                '<p>https://www.parametro.global/mail/message/419786 [1]</p>'
                '<p>Ao importar encomendas em curso criar o projeto com a ref. interna e confirma-la.</p>'
            ),
            pg_scope_summary='[PONTO POR VALIDAR]',
            pg_acceptance_criteria_text='[PONTO POR VALIDAR]',
            pg_scope_sequence=47,
        )

        payload = self.scope_builder.build_payload(self.project)
        payload_task = next(item for item in payload['scope_items'] if item['task_id'] == task.id)

        self.assertEqual(
            payload_task['scope_summary'],
            'Ao importar encomendas em curso criar o projeto com a ref. interna e confirma-la.',
        )

    def test_scope_payload_skips_phone_fragment_and_uses_next_factual_line(self):
        task = self.create_task(
            self.project,
            name='Lista fornecedores e clientes',
            description=(
                '<p>o +351 917 386 336</p>'
                '<p>Sincronizar lista de fornecedores e clientes com validacao deduplicada.</p>'
            ),
            pg_scope_summary='[PONTO POR VALIDAR]',
            pg_acceptance_criteria_text='[PONTO POR VALIDAR]',
            pg_scope_sequence=48,
        )

        payload = self.scope_builder.build_payload(self.project)
        payload_task = next(item for item in payload['scope_items'] if item['task_id'] == task.id)

        self.assertEqual(
            payload_task['scope_summary'],
            'Sincronizar lista de fornecedores e clientes com validacao deduplicada.',
        )

    def test_scope_payload_derives_acceptance_criteria_from_factual_secondary_line(self):
        task = self.create_task(
            self.project,
            name='Importacao de artigos',
            description=(
                '<p>Configurar importacao de artigos a partir de ficheiro Excel.</p>'
                '<p>Pre-visualizacao em grelha antes da confirmacao final pelo utilizador responsavel.</p>'
            ),
            pg_scope_summary='Configurar importacao de artigos a partir de ficheiro Excel.',
            pg_acceptance_criteria_text='[PONTO POR VALIDAR]',
            pg_scope_sequence=49,
        )

        payload = self.scope_builder.build_payload(self.project)
        payload_task = next(item for item in payload['scope_items'] if item['task_id'] == task.id)

        self.assertEqual(
            payload_task['acceptance_criteria'],
            ['Pre-visualizacao em grelha antes da confirmacao final pelo utilizador responsavel.'],
        )

    def test_scope_payload_keeps_full_task_description_fields(self):
        repeated_sentence = 'Validar os registos importados com todos os campos obrigatorios antes da confirmacao.'
        long_text = ' '.join([repeated_sentence for _ in range(30)])
        task = self.create_task(
            self.project,
            name='Descricao completa no scope',
            description=f'<p>{long_text}</p><p>Confirmar os resultados com o cliente.</p>',
            pg_scope_sequence=49,
        )

        payload = self.scope_builder.build_payload(self.project)
        payload_task = next(item for item in payload['scope_items'] if item['task_id'] == task.id)

        self.assertIn(long_text, payload_task['task_description'])
        self.assertIn('Confirmar os resultados com o cliente.', payload_task['task_description_text'])
        self.assertNotIn('...', payload_task['task_description_text'])

    def test_scope_payload_generates_acceptance_criterion_from_factual_summary_when_needed(self):
        task = self.create_task(
            self.project,
            name='Integracao expedicao',
            description='<p>[PONTO POR VALIDAR]</p>',
            pg_scope_summary='Integrar expedicao da transportadora com confirmacao manual antes do fecho.',
            pg_acceptance_criteria_text='[PONTO POR VALIDAR]',
            pg_scope_sequence=50,
        )

        payload = self.scope_builder.build_payload(self.project)
        payload_task = next(item for item in payload['scope_items'] if item['task_id'] == task.id)

        self.assertEqual(
            payload_task['acceptance_criteria'],
            ['O ambito aprovado deve refletir integrar expedicao da transportadora com confirmacao manual antes do fecho.'],
        )

    def test_scope_payload_generates_acceptance_criterion_from_factual_task_name_when_needed(self):
        task = self.create_task(
            self.project,
            name='Importacao de contactos',
            description='<p>[PONTO POR VALIDAR]</p>',
            pg_scope_summary='Importacao de contactos',
            pg_acceptance_criteria_text='[PONTO POR VALIDAR]',
            pg_scope_sequence=50,
        )

        payload = self.scope_builder.build_payload(self.project)
        payload_task = next(item for item in payload['scope_items'] if item['task_id'] == task.id)

        self.assertEqual(
            payload_task['acceptance_criteria'],
            ['O ambito aprovado deve refletir importacao de contactos.'],
        )

    def test_scope_payload_derives_overview_acceptance_criteria_from_scope_items_when_missing_project_line(self):
        repository = self.create_repository(name='scope_overview_repo')
        project = self.create_project(repository, name='Projeto sem linha oficial')
        self.create_task(
            project,
            name='Importacao de contactos',
            description='<p>[PONTO POR VALIDAR]</p>',
            pg_scope_summary='Importacao de contactos',
            pg_acceptance_criteria_text='[PONTO POR VALIDAR]',
            pg_scope_sequence=10,
        )

        payload = self.scope_builder.build_payload(project)

        self.assertEqual(
            payload['scope_overview']['acceptance_criteria'],
            ['O ambito aprovado deve refletir importacao de contactos.'],
        )

    def test_scope_payload_keeps_acceptance_criteria_empty_when_no_factual_source_exists(self):
        task = self.create_task(
            self.project,
            name='Categorias',
            description='<p>[PONTO POR VALIDAR]</p>',
            pg_scope_summary='Categorias',
            pg_acceptance_criteria_text='[PONTO POR VALIDAR]',
            pg_scope_sequence=52,
        )

        payload = self.scope_builder.build_payload(self.project)
        payload_task = next(item for item in payload['scope_items'] if item['task_id'] == task.id)

        self.assertEqual(payload_task['acceptance_criteria'], [])

    def test_scope_hashable_payload_clears_volatile_metadata(self):
        payload = self.scope_builder.build_payload(self.project)
        hashable_payload = self.scope_builder.build_hashable_payload(payload)
        source_metadata = hashable_payload['source_metadata']

        self.assertEqual(source_metadata['sync_trigger'], '')
        self.assertEqual(source_metadata['sync_reason'], '')
        self.assertEqual(source_metadata['sync_published_at'], '')
        self.assertEqual(source_metadata['sync_published_by'], '')
        self.assertEqual(source_metadata['payload_hash'], '')
