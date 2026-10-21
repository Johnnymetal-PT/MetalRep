from unittest.mock import patch

from odoo import fields
from odoo.fields import Command

from ..services.github_service import GitHubService


class PgAiDevAssistantTestMixin:
    def setUp(self):
        super().setUp()
        # Por defeito, nos testes a branch alvo do espelho existe. Evita chamadas
        # reais ao GitHub na guarda de branch dos servicos de sync (process_run).
        # Testes especificos da guarda fazem patch local para return_value=False.
        branch_patcher = patch.object(GitHubService, 'branch_exists', return_value=True)
        branch_patcher.start()
        self.addCleanup(branch_patcher.stop)

    @classmethod
    def set_pg_base_url(cls, base_url='https://example.test'):
        cls.env['ir.config_parameter'].sudo().set_param('web.base.url', base_url)

    @classmethod
    def create_repository(cls, name='brodoo_v2', default_branch='teste'):
        return cls.env['pg.ai.repository'].create(
            {
                'name': name,
                'full_name': f'bruno-pinheiro-pg/{name}',
                'github_owner': 'bruno-pinheiro-pg',
                'github_repo': name,
                'default_branch': default_branch,
                'visibility': 'private',
                'is_private': True,
            }
        )

    @classmethod
    def create_repository_branch(cls, repository, name='teste', is_default=True):
        return cls.env['pg.ai.repository.branch'].create(
            {
                'repository_id': repository.id,
                'name': name,
                'is_default': is_default,
            }
        )

    @classmethod
    def create_project(cls, repository, **overrides):
        values = {
            'name': 'Projeto Piloto',
            'pg_repository_id': repository.id,
            'pg_repo_branch': repository.default_branch,
            'pg_scope_sync_enabled': True,
            'pg_scope_sync_mode': 'event_driven',
            'pg_client_unit': 'Consulting',
            'pg_repository_summary': 'Repositorio piloto para validar sync factual.',
            'pg_project_phase': 'discovery',
            'pg_odoo_version': '19.0',
            'pg_odoo_edition': 'community',
            'pg_odoo_environment': 'on_premise',
            'pg_standard_allowed': 'yes',
            'pg_additional_modules_allowed': 'yes',
            'pg_studio_allowed': 'yes',
            'pg_custom_allowed': 'yes',
            'pg_additional_contract_restrictions': 'Sem restricoes extra',
            'pg_business_goal': 'Validar framework consultiva.',
            'pg_current_request': 'Testar scope e status sync.',
            'pg_current_process': 'Analise e publicacao factual.',
            'pg_problem_or_need': 'Garantir contexto factual no repositorio.',
            'pg_business_impact': 'Melhorar disciplina consultiva.',
            'pg_trigger': 'Pedido do utilizador',
            'pg_frequency': 'Semanal',
            'pg_volumes': '5',
            'pg_urgency': 'medium',
        }
        values.update(overrides)
        project = cls.env['project.project'].with_context(
            pg_skip_scope_sync_enqueue=True,
            pg_skip_mirror_sync_enqueue=True,
        ).create(values)
        return project.with_env(cls.env)

    @classmethod
    def create_task(cls, project, name='Tarefa teste', **overrides):
        values = {
            'name': name,
            'project_id': project.id,
            'description': '<p>Descricao funcional da tarefa.</p>',
            'priority': '1',
            'pg_scope_relevant': True,
            'pg_scope_track': 'approved_scope',
            'pg_scope_state': 'proposed',
            'pg_scope_kind': 'requirement',
            'pg_scope_summary': 'Resumo funcional de teste.',
            'pg_acceptance_criteria_text': 'Criterio A\nCriterio B',
            'pg_requirement_status': 'approved',
            'pg_requirement_priority': 'medium',
            'pg_requirement_owner_id': cls.env.user.id,
            'pg_requirement_traceability_refs': 'FIT-001\nSTEERING-REQ-001',
            'pg_scope_sequence': 10,
            'user_ids': [Command.set([cls.env.user.id])],
        }
        values.update(overrides)
        task = cls.env['project.task'].with_context(
            pg_skip_scope_sync_enqueue=True,
            pg_skip_mirror_sync_enqueue=True,
        ).create(values)
        return task.with_env(cls.env)

    @classmethod
    def create_project_milestone(cls, project, name='Entrega teste', **overrides):
        if not project.allow_milestones:
            project.write({'allow_milestones': True})

        values = {
            'project_id': project.id,
            'name': name,
            'deadline': fields.Date.today(),
            'pg_delivery_state': 'planned',
            'pg_delivery_owner_id': cls.env.user.id,
            'pg_acceptance_state': 'pending',
            'pg_delivery_source_reference': 'Plano de entregas do projeto',
            'pg_plan_start_date': fields.Date.today(),
            'pg_plan_dependency_refs': '',
        }
        values.update(overrides)
        milestone = cls.env['project.milestone'].with_context(pg_skip_mirror_sync_enqueue=True).create(values)
        return milestone.with_env(cls.env)

    @classmethod
    def create_chatter_message(
        cls,
        model_name,
        record_id,
        body,
        message_type='comment',
        subtype_xmlid='mail.mt_note',
        author_partner=False,
    ):
        subtype = cls.env.ref(subtype_xmlid)
        return cls.env['mail.message'].create(
            {
                'model': model_name,
                'res_id': record_id,
                'body': body,
                'message_type': message_type,
                'subtype_id': subtype.id,
                'author_id': (author_partner or cls.env.user.partner_id).id,
            }
        )

    @classmethod
    def create_attachment(cls, record, name='anexo.txt', mimetype='text/plain'):
        return cls.env['ir.attachment'].create(
            {
                'name': name,
                'type': 'binary',
                'datas': 'dGVzdA==',
                'mimetype': mimetype,
                'res_model': record._name,
                'res_id': record.id,
            }
        )

