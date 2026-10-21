import hashlib
import json
from copy import deepcopy

from odoo import fields
from odoo.exceptions import ValidationError

from .project_chatter_filter_service import ProjectChatterFilterService
from .project_scope_payload_builder import ProjectScopePayloadBuilder
from .text_hygiene import SCOPE_ITEM_FACTUAL_BUT_NEEDS_CURATION
from .text_hygiene import SCOPE_ITEM_INCLUDED
from .text_hygiene import build_scope_quality_feedback
from .text_hygiene import classify_scope_item
from .text_hygiene import curate_scope_publication_lines
from .text_hygiene import is_low_signal_scope_summary
from .text_hygiene import sanitize_plaintext
from .text_hygiene import scope_classification_reason_label
from .text_hygiene import sanitize_scope_publication_candidate
from .text_hygiene import normalize_inline_text
from .text_hygiene import split_scope_publication_candidates
from .text_hygiene import split_unique_text_lines
from .text_hygiene import strip_inline_email_noise
from .text_hygiene import strip_scope_leading_label_prefix


class ProjectMirrorPayloadBuilder:
    PROJECT_SCHEMA_VERSION = '1.1'
    PLANNING_SCHEMA_VERSION = '1.0'
    TASKS_SCHEMA_VERSION = '1.0'
    CHATTER_SCHEMA_VERSION = '1.0'
    ATTACHMENTS_SCHEMA_VERSION = '1.0'
    EVENTS_SCHEMA_VERSION = '1.0'
    ODOO_ENV_SCHEMA_VERSION = '1.1'
    # Estados do bloco `collection` do M1 (contrato PG-007, decisao D3).
    ODOO_ENV_COLLECTED = 'collected'
    ODOO_ENV_UNAVAILABLE = 'unavailable'
    ODOO_ENV_STALE = 'stale'
    ODOO_ENV_COLLECTION_STATUSES = (ODOO_ENV_COLLECTED, ODOO_ENV_UNAVAILABLE, ODOO_ENV_STALE)
    DELIVERABLES_SCHEMA_VERSION = '1.1'
    def __init__(self, env):
        self.env = env
        self.params = env['ir.config_parameter'].sudo()
        self.chatter_filter = ProjectChatterFilterService(env)
        self.scope_payload_builder = ProjectScopePayloadBuilder(env)

    def _get_base_url(self):
        return (self.params.get_param('web.base.url') or '').strip().rstrip('/')

    def _build_record_url(self, model_name, record_id):
        base_url = self._get_base_url()
        if not base_url or not model_name or not record_id:
            return None
        return f"{base_url}/web#id={record_id}&model={model_name}"

    def _normalize_text(self, value, fallback='', max_chars=False):
        return normalize_inline_text(
            value,
            fallback=fallback,
            max_chars=max_chars,
            drop_placeholders=True,
        )

    def _normalize_lines(self, value, max_items=False, max_line_chars=False):
        return split_unique_text_lines(
            value,
            from_html=True,
            max_items=max_items,
            max_line_chars=max_line_chars,
            strip_email_noise=False,
        )

    def _merge_unique_lines(self, *collections):
        result = []
        for collection in collections:
            if not collection:
                continue
            for value in collection:
                normalized = self._normalize_text(value, max_chars=False)
                if normalized and normalized not in result:
                    result.append(normalized)
        return result

    def _comparable_scope_key(self, value):
        return self._normalize_text(value, max_chars=False).lower().strip(' .,:;!?')

    def _publishable_scope_line(self, raw_value, normalized_value=''):
        return sanitize_scope_publication_candidate(normalized_value or raw_value, max_chars=False)

    def _publishable_scope_lines(self, raw_value):
        classification = classify_scope_item(raw_value, max_chars=False)
        if classification.get('state') != SCOPE_ITEM_INCLUDED:
            return []
        return (classification.get('publication_candidates') or [])[:6]

    def _curated_scope_lines(self, values):
        return curate_scope_publication_lines(values, max_chars=False)

    def _backlog_reason_label(self, reason):
        return scope_classification_reason_label(reason)

    def _build_scope_backlog_entry(
        self,
        classification,
        source_type,
        source_model,
        source_record_id,
        source_label='',
    ):
        cleaned_text = self._normalize_text(classification.get('normalized_item'), max_chars=False)
        if not cleaned_text:
            return False
        reason = classification.get('reason') or 'needs_manual_scope_curation'
        return {
            'item': cleaned_text,
            'reason': reason,
            'reason_label': classification.get('reason_label') or self._backlog_reason_label(reason),
            'source_type': source_type,
            'source_model': source_model,
            'source_record_id': source_record_id,
            'source_record_url': self._build_record_url(source_model, source_record_id),
            'source_label': self._normalize_text(source_label, max_chars=False),
        }

    def _task_scope_candidate(self, task):
        if task.pg_scope_summary:
            return task.pg_scope_summary, 'task_scope_summary'
        description_lines = self.scope_payload_builder._task_description_lines(task, max_items=False, max_line_chars=False)
        if description_lines:
            return ' '.join(description_lines), 'task_description'
        return task.name or '', 'task_name'

    def _collect_scope_publication_buckets(self, project):
        included_scope = []
        included_seen = set()

        def _append_included(candidate):
            key = self._comparable_scope_key(candidate)
            if not key or key in included_seen:
                return
            included_seen.add(key)
            included_scope.append(candidate)

        for raw_line in self._normalize_lines(project.pg_onboarding_scope_included_text):
            normalized = self._normalize_text(raw_line, max_chars=False)
            if normalized:
                _append_included(normalized)

        tasks = self.env['project.task'].search([('project_id', '=', project.id)], order='id asc')
        for task in tasks:
            raw_value, _ = self._task_scope_candidate(task)
            normalized = self._normalize_text(raw_value, max_chars=False)
            if normalized:
                _append_included(normalized)

        return (
            included_scope,
            [],
            {},
            0,
            {},
        )

    def _format_date(self, value):
        return fields.Date.to_string(value) if value else None

    def _format_datetime(self, value):
        return fields.Datetime.to_string(value) if value else None

    def _serialize_payload(self, payload):
        return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + '\n'

    def _build_hashable_payload(self, payload):
        hashable = deepcopy(payload)
        hashable.pop('source_metadata', None)
        return self._strip_volatile_fields(hashable)

    def _strip_volatile_fields(self, value):
        if isinstance(value, dict):
            cleaned = {}
            for key, item in value.items():
                # `collected_at` fora do hash (PG-007, D7): uma recolha nova com o
                # mesmo inventario nao deve gerar commit - so o conteudo conta.
                if key in {'synced_at', 'sync_published_at', 'payload_hash', 'collected_at'}:
                    continue
                cleaned[key] = self._strip_volatile_fields(item)
            return cleaned
        if isinstance(value, list):
            return [self._strip_volatile_fields(item) for item in value]
        return value

    def _payload_hash(self, payload):
        serialized = self._serialize_payload(self._build_hashable_payload(payload))
        return f"sha256:{hashlib.sha256(serialized.encode('utf-8')).hexdigest()}"

    def serialize_payload(self, payload):
        return self._serialize_payload(payload)

    def build_hashable_payload(self, payload):
        return self._build_hashable_payload(payload)

    def _source_metadata(self, project, trigger_type='manual', trigger_model='project.project', trigger_record_id=None):
        published_at = fields.Datetime.now()
        source_record_id = trigger_record_id or project.id
        source_model = trigger_model or 'project.project'
        return {
            'source_system': 'odoo_parametro_global',
            'source_model': source_model,
            'source_record_id': source_record_id,
            'source_record_url': self._build_record_url(source_model, source_record_id),
            'sync_trigger': trigger_type or 'manual',
            'sync_published_at': fields.Datetime.to_string(published_at),
            'sync_published_by': self.env.user.display_name or 'Odoo',
            'repo_branch': (project.pg_repo_branch or '').strip(),
            'payload_hash': '',
        }

    def _project_core(self, project):
        return {
            'odoo_model': 'project.project',
            'odoo_id': project.id,
            'record_url': self._build_record_url('project.project', project.id),
            'synced_at': fields.Datetime.to_string(fields.Datetime.now()),
            'name': self._normalize_text(project.name, max_chars=False),
            'client_name': self._normalize_text(project.partner_id.display_name if project.partner_id else '', max_chars=False),
            'project_manager': self._normalize_text(project.user_id.display_name if project.user_id else '', max_chars=False),
            'phase': project.pg_project_phase or False,
            'stage_name': self._normalize_text(project.stage_id.name if project.stage_id else '', max_chars=False),
            'tag_names': sorted(project.tag_ids.mapped('name')),
            'planned_date_begin': self._format_date(getattr(project, 'date_start', False)),
            'planned_date_end': self._format_date(getattr(project, 'date', False)),
            'allocated_hours': float(
                getattr(project, 'allocated_hours', getattr(project, 'planned_hours', 0.0)) or 0.0
            ),
            'progress': float(getattr(project, 'progress', 0.0) or 0.0),
            'repository_full_name': project.pg_repository_id.full_name if project.pg_repository_id else False,
            'repository_branch': (project.pg_repo_branch or '').strip() or False,
        }

    def _scope_summary_lines(self, project, states=None, exclude_states=None):
        tasks = self.env['project.task'].search([('project_id', '=', project.id)], order='id asc')
        values = []
        for task in tasks:
            state = task.pg_scope_state or False
            if states and state not in states:
                continue
            if exclude_states and state in exclude_states:
                continue
            summary = self.scope_payload_builder._task_scope_summary(task)
            normalized_task_name = self._normalize_text(task.name, max_chars=False)
            summary = self._normalize_text(summary, max_chars=False)
            summary_lines = self._publishable_scope_lines(summary)
            if not summary_lines:
                continue
            if len(summary_lines) == 1 and summary_lines[0] == normalized_task_name:
                if is_low_signal_scope_summary(task.name, summary_lines[0]):
                    continue
                if self.scope_payload_builder._scope_summary_needs_expansion(summary_lines[0]):
                    continue
            for summary_line in summary_lines:
                if summary_line and summary_line not in values:
                    values.append(summary_line)
        return values

    def _project_deliverables(self, project):
        milestones = self.env['project.milestone'].search([('project_id', '=', project.id)], order='sequence asc, id asc')
        values = []
        for milestone in milestones:
            name = self._normalize_text(milestone.name, max_chars=False)
            if name and name not in values:
                values.append(name)
        return values

    def _project_stakeholders(self, project):
        stakeholders = []
        for value in (
            project.partner_id.display_name if project.partner_id else '',
            project.user_id.display_name if project.user_id else '',
        ):
            normalized = self._normalize_text(value, max_chars=False)
            if normalized and normalized not in stakeholders:
                stakeholders.append(normalized)
        return stakeholders

    def _project_scope_governance(self, project):
        return {
            'odoo_version': self._normalize_text(project.pg_odoo_version, max_chars=False),
            'odoo_edition': project.pg_odoo_edition or 'unknown',
            'odoo_environment': project.pg_odoo_environment or 'unknown',
            'standard_allowed': project.pg_standard_allowed or 'unknown',
            'additional_modules_allowed': project.pg_additional_modules_allowed or 'unknown',
            'studio_allowed': project.pg_studio_allowed or 'unknown',
            'custom_allowed': project.pg_custom_allowed or 'unknown',
            'additional_contract_restrictions': self._normalize_text(project.pg_additional_contract_restrictions, max_chars=False),
            'urgency': project.pg_urgency or 'unknown',
            'trigger': self._normalize_text(project.pg_trigger, max_chars=False),
            'frequency': self._normalize_text(project.pg_frequency, max_chars=False),
            'volumes': self._normalize_text(project.pg_volumes, max_chars=False),
        }

    def _task_is_closed(self, task):
        if 'is_closed' in task._fields:
            return bool(task.is_closed)
        return bool(task.stage_id.fold) if task.stage_id else False

    def _milestone_is_pending(self, milestone):
        if not milestone:
            return False
        if milestone.is_reached:
            return False
        if milestone.pg_delivery_state == 'delivered':
            return False
        return True

    def _milestone_open_task_count(self, project, milestone):
        return len(self._milestone_open_tasks(project, milestone))

    def _milestone_selection_key(self, project, milestone):
        open_task_count = self._milestone_open_task_count(project, milestone) if project and milestone else 0
        in_progress = milestone.pg_delivery_state == 'in_progress'
        activity_score = int(in_progress) + int(open_task_count > 0)
        sequence = milestone.sequence if milestone.sequence not in (False, None) else 999999
        deadline = fields.Date.to_string(milestone.deadline) or '9999-12-31'
        return (-activity_score, -int(in_progress), -open_task_count, sequence, deadline, milestone.id)

    def _next_pending_milestone(self, milestones, project=None):
        candidates = milestones.filtered(self._milestone_is_pending)
        if not candidates:
            candidates = milestones.filtered(lambda milestone: milestone.pg_delivery_state != 'delivered')
        if not candidates:
            return candidates
        ranked = sorted(candidates, key=lambda milestone: self._milestone_selection_key(project, milestone))
        return ranked[0] if ranked else candidates[:1]

    def build_project_payload(self, project, trigger_type='manual', trigger_model='project.project', trigger_record_id=None):
        project.ensure_one()
        (
            included_scope,
            factual_scope_backlog,
            backlog_reason_counts,
            excluded_noise_count,
            excluded_noise_reason_counts,
        ) = self._collect_scope_publication_buckets(project)
        onboarding_excluded_scope = self._normalize_lines(project.pg_onboarding_scope_excluded_text)
        onboarding_assumptions = self._normalize_lines(project.pg_onboarding_assumptions_text)
        onboarding_stakeholders = self._normalize_lines(project.pg_onboarding_stakeholders_text)
        scope_quality_review = {
            'included_scope_count': len(included_scope),
            'factual_scope_backlog_count': len(factual_scope_backlog),
            'curation_reason_counts': backlog_reason_counts,
            'excluded_noise_count': excluded_noise_count,
            'excluded_noise_reason_counts': excluded_noise_reason_counts,
        }
        scope_quality_review.update(
            build_scope_quality_feedback(
                scope_quality_review['included_scope_count'],
                scope_quality_review['factual_scope_backlog_count'],
                scope_quality_review['curation_reason_counts'],
                scope_quality_review['excluded_noise_count'],
                scope_quality_review['excluded_noise_reason_counts'],
            )
        )
        payload = {
            'schema_version': self.PROJECT_SCHEMA_VERSION,
            'project': {
                **self._project_core(project),
                'client_unit': self._normalize_text(project.pg_client_unit, max_chars=False),
                'repository_summary': self._normalize_text(project.pg_repository_summary, max_chars=False),
                'objective': self._normalize_text(project.pg_business_goal, max_chars=False),
                'current_request': self._normalize_text(project.pg_current_request, max_chars=False),
                'current_process': self._normalize_text(project.pg_current_process, max_chars=False),
                'problem_or_need': self._normalize_text(project.pg_problem_or_need, max_chars=False),
                'business_impact': self._normalize_text(project.pg_business_impact, max_chars=False),
                'included_scope': included_scope,
                'factual_scope_backlog': factual_scope_backlog,
                'excluded_scope': self._merge_unique_lines(
                    onboarding_excluded_scope,
                    self._scope_summary_lines(project, states={'excluded', 'dropped'}),
                ),
                'deliverables': self._project_deliverables(project),
                'assumptions': onboarding_assumptions,
                'restrictions': self._normalize_lines(project.pg_additional_contract_restrictions),
                'stakeholders': self._merge_unique_lines(
                    onboarding_stakeholders,
                    self._project_stakeholders(project),
                ),
                'governance': self._project_scope_governance(project),
                'scope_quality_review': scope_quality_review,
            },
            'source_metadata': self._source_metadata(
                project,
                trigger_type=trigger_type,
                trigger_model=trigger_model,
                trigger_record_id=trigger_record_id,
            ),
        }
        payload['source_metadata']['payload_hash'] = self._payload_hash(payload)
        self.validate_project_payload(payload)
        return payload

    def _milestone_open_tasks(self, project, milestone):
        domain = [('project_id', '=', project.id), ('active', '=', True)]
        if milestone:
            domain.append(('milestone_id', '=', milestone.id))
        tasks = self.env['project.task'].search(domain, order='priority desc, id asc')
        return tasks.filtered(lambda task: not self._task_is_closed(task))

    def _planning_summary(self, project, milestones):
        next_milestone = self._next_pending_milestone(milestones, project=project)
        open_tasks = self.env['project.task'].search([('project_id', '=', project.id), ('active', '=', True)], order='priority desc, id asc')
        open_tasks = open_tasks.filtered(lambda task: not self._task_is_closed(task))
        open_for_next_milestone = self._milestone_open_tasks(project, next_milestone) if next_milestone else self.env['project.task']

        return {
            'project_stage_name': self._normalize_text(project.stage_id.name if project.stage_id else '', max_chars=False),
            'current_phase': project.pg_project_phase or '',
            'next_milestone_id': next_milestone.id if next_milestone else False,
            'next_milestone_name': self._normalize_text(next_milestone.name if next_milestone else '', max_chars=False),
            'next_milestone_target_date': self._format_date(next_milestone.deadline if next_milestone else False),
            'next_milestone_owner': self._normalize_text(
                next_milestone.pg_delivery_owner_id.display_name if next_milestone and next_milestone.pg_delivery_owner_id else '',
            ),
            'open_task_count': len(open_tasks),
            'open_tasks_for_next_milestone_count': len(open_for_next_milestone),
            'open_tasks_for_next_milestone': [
                {
                    'odoo_model': 'project.task',
                    'odoo_id': task.id,
                    'record_url': self._build_record_url('project.task', task.id),
                    'name': self._normalize_text(task.name, max_chars=False),
                    'stage_name': self._normalize_text(task.stage_id.name if task.stage_id else '', max_chars=False),
                    'priority': task.priority or False,
                }
                for task in open_for_next_milestone[:10]
            ],
            'open_high_priority_tasks': [
                {
                    'odoo_model': 'project.task',
                    'odoo_id': task.id,
                    'record_url': self._build_record_url('project.task', task.id),
                    'name': self._normalize_text(task.name, max_chars=False),
                    'stage_name': self._normalize_text(task.stage_id.name if task.stage_id else '', max_chars=False),
                    'priority': task.priority or False,
                }
                for task in open_tasks.filtered(lambda task: task.priority in {'2', '3'})[:10]
            ],
        }

    def _planning_item_payload(self, milestone):
        return {
            'odoo_model': 'project.milestone',
            'odoo_id': milestone.id,
            'record_url': self._build_record_url('project.milestone', milestone.id),
            'synced_at': fields.Datetime.to_string(fields.Datetime.now()),
            'name': self._normalize_text(milestone.name, max_chars=False),
            'sequence': milestone.sequence,
            'planned_start': self._format_date(milestone.pg_plan_start_date),
            'planned_end': self._format_date(milestone.deadline),
            'status': milestone.pg_delivery_state or False,
            'delivery_state': milestone.pg_delivery_state or False,
            'acceptance_state': milestone.pg_acceptance_state or False,
            'owner': self._normalize_text(milestone.pg_delivery_owner_id.display_name if milestone.pg_delivery_owner_id else '', max_chars=False),
            'dependencies': self._normalize_lines(milestone.pg_plan_dependency_refs),
            'is_reached': bool(milestone.is_reached),
        }

    def _task_description_html(self, task):
        return (task.description or '').strip()

    def _task_description_text(self, task):
        return sanitize_plaintext(
            task.description,
            from_html=True,
            max_chars=False,
            strip_email_noise=False,
        )

    def build_planning_payload(self, project, trigger_type='manual', trigger_model='project.project', trigger_record_id=None):
        project.ensure_one()
        milestones = self.env['project.milestone'].search([('project_id', '=', project.id)], order='sequence asc, deadline asc, id asc')
        milestone_baseline = self._normalize_lines(project.pg_onboarding_milestones_text)
        next_milestone = self._next_pending_milestone(milestones, project=project)
        next_milestone_payload = self._planning_item_payload(next_milestone) if next_milestone else None
        payload = {
            'schema_version': self.PLANNING_SCHEMA_VERSION,
            'project': self._project_core(project),
            'planning': {
                'milestones': [self._planning_item_payload(milestone) for milestone in milestones],
                'milestone_count': len(milestones),
                'milestone_baseline': milestone_baseline,
                'next_milestone': next_milestone_payload,
                'planning_summary': self._planning_summary(project, milestones),
            },
            'source_metadata': self._source_metadata(
                project,
                trigger_type=trigger_type,
                trigger_model=trigger_model,
                trigger_record_id=trigger_record_id,
            ),
        }
        payload['source_metadata']['payload_hash'] = self._payload_hash(payload)
        self.validate_planning_payload(payload)
        return payload

    def _task_payload(self, task):
        return {
            'odoo_model': 'project.task',
            'odoo_id': task.id,
            'record_url': self._build_record_url('project.task', task.id),
            'synced_at': fields.Datetime.to_string(fields.Datetime.now()),
            'name': self._normalize_text(task.name, max_chars=False),
            'description': self._task_description_html(task),
            'description_text': self._task_description_text(task),
            'stage_name': self._normalize_text(task.stage_id.name if task.stage_id else '', max_chars=False),
            'priority': task.priority or False,
            'assignees': sorted(task.user_ids.mapped('display_name')),
            'planned_date_begin': self._format_datetime(getattr(task, 'date_assign', False)),
            'planned_date_end': self._format_datetime(getattr(task, 'date_deadline', False)),
            'allocated_hours': float(getattr(task, 'allocated_hours', 0.0) or 0.0),
            'effective_hours': float(getattr(task, 'effective_hours', 0.0) or 0.0),
            'progress': float(getattr(task, 'progress', 0.0) or 0.0),
            'is_closed': self._task_is_closed(task),
            'is_cancelled': bool(task.active is False),
            'scope_track': task.pg_scope_track or False,
            'scope_state': task.pg_scope_state or False,
            'scope_kind': task.pg_scope_kind or False,
            'scope_summary': self._normalize_text(task.pg_scope_summary, max_chars=False),
            'acceptance_criteria': self._normalize_lines(task.pg_acceptance_criteria_text),
            'child_task_ids': getattr(task, 'child_ids', self.env['project.task']).ids,
        }

    def build_tasks_payload(self, project, trigger_type='manual', trigger_model='project.project', trigger_record_id=None):
        project.ensure_one()
        tasks = self.env['project.task'].search([('project_id', '=', project.id)], order='priority desc, id asc')
        payload = {
            'schema_version': self.TASKS_SCHEMA_VERSION,
            'project': self._project_core(project),
            'tasks': [self._task_payload(task) for task in tasks],
            'task_count': len(tasks),
            'source_metadata': self._source_metadata(
                project,
                trigger_type=trigger_type,
                trigger_model=trigger_model,
                trigger_record_id=trigger_record_id,
            ),
        }
        payload['source_metadata']['payload_hash'] = self._payload_hash(payload)
        self.validate_tasks_payload(payload)
        return payload

    def _message_entry_type(self, message):
        subtype = message.subtype_id
        if subtype and subtype.internal and self._is_internal_message_author(message):
            return 'internal_note'
        return 'customer_message'

    def _is_internal_message_author(self, message):
        author = message.author_id
        if not author:
            return False
        if author.user_ids:
            return True
        company_partner = self.env.company.partner_id.commercial_partner_id
        return author.commercial_partner_id == company_partner

    def _message_author(self, message):
        author = self._normalize_text(message.author_id.display_name if message.author_id else '', max_chars=False)
        if author:
            return author
        return self._normalize_text(message.email_from, max_chars=False)

    def _attachment_metadata(self, attachment):
        return {
            'odoo_model': 'ir.attachment',
            'odoo_id': attachment.id,
            'record_url': self._build_record_url(attachment.res_model, attachment.res_id) if attachment.res_model and attachment.res_id else None,
            'synced_at': fields.Datetime.to_string(fields.Datetime.now()),
            'name': self._normalize_text(attachment.name, max_chars=False),
            'mimetype': attachment.mimetype or False,
            'file_size': int(attachment.file_size or 0),
            'create_date': self._format_datetime(attachment.create_date),
            'create_uid': self._normalize_text(attachment.create_uid.display_name if attachment.create_uid else '', max_chars=False),
            'linked_model': attachment.res_model or False,
            'linked_record_id': attachment.res_id or False,
            'download_url': f"{self._get_base_url()}/web/content/{attachment.id}?download=true" if self._get_base_url() else None,
        }

    def _message_payload(self, message):
        body = self._normalize_text(message.body, max_chars=False)
        if not body:
            return False
        attachments = [self._attachment_metadata(attachment) for attachment in message.attachment_ids]
        return {
            'odoo_model': 'mail.message',
            'odoo_id': message.id,
            'record_url': self._build_record_url(message.model, message.res_id),
            'synced_at': fields.Datetime.to_string(fields.Datetime.now()),
            'entry_type': self._message_entry_type(message),
            'message_type': message.message_type or False,
            'subtype': message.subtype_id.name if message.subtype_id else False,
            'author': self._message_author(message),
            'date': self._format_datetime(message.date or message.create_date),
            'body': body,
            'linked_model': message.model or False,
            'linked_record_id': message.res_id or False,
            'attachments': attachments,
        }

    def _project_message_domain(self, project):
        task_ids = self.env['project.task'].search([('project_id', '=', project.id)]).ids
        return [
            '|',
            '&', ('model', '=', 'project.project'), ('res_id', '=', project.id),
            '&', ('model', '=', 'project.task'), ('res_id', 'in', task_ids or [0]),
        ]

    def build_chatter_payload(self, project, trigger_type='manual', trigger_model='project.project', trigger_record_id=None):
        project.ensure_one()
        message_domain = self._project_message_domain(project)
        messages = self.env['mail.message'].search(message_domain, order='date desc, id desc')
        message_payloads = [payload for payload in (self._message_payload(message) for message in messages) if payload]
        payload = {
            'schema_version': self.CHATTER_SCHEMA_VERSION,
            'project': self._project_core(project),
            'messages': message_payloads,
            'message_count': len(message_payloads),
            'source_metadata': self._source_metadata(
                project,
                trigger_type=trigger_type,
                trigger_model=trigger_model,
                trigger_record_id=trigger_record_id,
            ),
        }
        payload['source_metadata']['payload_hash'] = self._payload_hash(payload)
        self.validate_chatter_payload(payload)
        return payload

    def build_attachments_payload(self, project, trigger_type='manual', trigger_model='project.project', trigger_record_id=None):
        project.ensure_one()
        task_ids = self.env['project.task'].search([('project_id', '=', project.id)]).ids
        messages = self.env['mail.message'].search(self._project_message_domain(project), order='date desc, id desc')
        message_ids = [message.id for message in messages]
        attachment_domain = [
            '|',
            '|',
            '&', ('res_model', '=', 'project.project'), ('res_id', '=', project.id),
            '&', ('res_model', '=', 'project.task'), ('res_id', 'in', task_ids or [0]),
            '&', ('res_model', '=', 'mail.message'), ('res_id', 'in', message_ids or [0]),
        ]
        attachments = self.env['ir.attachment'].search(attachment_domain, order='create_date desc, id desc')
        payload = {
            'schema_version': self.ATTACHMENTS_SCHEMA_VERSION,
            'project': self._project_core(project),
            'attachments': [self._attachment_metadata(attachment) for attachment in attachments],
            'attachment_count': len(attachments),
            'source_metadata': self._source_metadata(
                project,
                trigger_type=trigger_type,
                trigger_model=trigger_model,
                trigger_record_id=trigger_record_id,
            ),
        }
        payload['source_metadata']['payload_hash'] = self._payload_hash(payload)
        self.validate_attachments_payload(payload)
        return payload

    def build_history_event(
        self,
        project,
        event_type,
        entity_model,
        entity_id,
        summary,
        event_data=None,
        trigger_type='manual',
    ):
        project.ensure_one()
        payload = {
            'schema_version': self.EVENTS_SCHEMA_VERSION,
            'timestamp': fields.Datetime.to_string(fields.Datetime.now()),
            'event_type': event_type,
            'trigger_type': trigger_type or 'manual',
            'project': {
                'odoo_model': 'project.project',
                'odoo_id': project.id,
                'record_url': self._build_record_url('project.project', project.id),
                'synced_at': fields.Datetime.to_string(fields.Datetime.now()),
                'name': self._normalize_text(project.name, max_chars=False),
            },
            'entity': {
                'odoo_model': entity_model,
                'odoo_id': entity_id,
                'record_url': self._build_record_url(entity_model, entity_id),
            },
            'summary': self._normalize_text(summary, max_chars=False),
            'author': self.env.user.display_name or 'Odoo',
            'event_data': event_data or {},
        }
        self.validate_history_event(payload)
        return payload

    # ------------------------------------------------------------------
    # M1: ambiente Odoo real do projeto (.pg/project/odoo_env.json)
    # ------------------------------------------------------------------
    def _odoo_env_snapshot(self, project):
        """Inventario do Odoo do CLIENTE, recolhido pelo canal `production`.

        NUNCA inventariar `self.env`: essa e a base onde o pg_brodoo corre - o Odoo
        da Parametro Global - e nao a base do cliente. Foi exactamente isso que este
        metodo fazia ate 2026-08-10, publicando em 13 repositorios de projeto o
        inventario da PG etiquetado com os dados do cliente. Como o odoo_env.json e
        o arbitro do passo 1 (standard ja instalado) contra o passo 2 (standard
        adicional) da ordem obrigatoria de decisao, o efeito era classificar como
        "ja disponivel" o que exige instalar um modulo.

        A recolha real chega na fase F2 do PG-007 (modelo `pg.odoo.env.snapshot`,
        alimentado pelo operador atraves do canal `production`). Ate la nao existe
        fonte legitima e o payload sai `unavailable` - um estado explicito vale mais
        do que uma lista errada.

        Ver: docs/PG_007_ODOO_ENV_COLLECTION_CONTRACT.md
        """
        return None

    def _odoo_env_collection(self, project):
        """Devolve o par (bloco `collection`, lista de modulos) do payload M1."""
        snapshot = self._odoo_env_snapshot(project)
        if not snapshot:
            return {
                'status': self.ODOO_ENV_UNAVAILABLE,
                'unavailable_reason': 'never_collected',
                'purpose': False,
                'base_url': False,
                'database': False,
                'collected_at': False,
                'collected_by': False,
            }, []
        return {
            'status': snapshot['status'],
            'unavailable_reason': False,
            'purpose': snapshot['purpose'],
            'base_url': snapshot['base_url'],
            'database': snapshot['database'],
            'collected_at': snapshot['collected_at'],
            'collected_by': snapshot['collected_by'],
        }, snapshot['installed_modules']

    def build_odoo_env_payload(self, project, trigger_type='manual', trigger_model='project.project', trigger_record_id=None):
        project.ensure_one()
        collection, installed = self._odoo_env_collection(project)
        payload = {
            'schema_version': self.ODOO_ENV_SCHEMA_VERSION,
            'project': self._project_core(project),
            'odoo_env': {
                'odoo_version': project.pg_odoo_version or False,
                'odoo_edition': project.pg_odoo_edition or False,
                'odoo_environment': project.pg_odoo_environment or False,
                'collection': collection,
                'installed_module_count': len(installed),
                'installed_modules': installed,
            },
            'source_metadata': self._source_metadata(
                project,
                trigger_type=trigger_type,
                trigger_model=trigger_model,
                trigger_record_id=trigger_record_id,
            ),
        }
        payload['source_metadata']['payload_hash'] = self._payload_hash(payload)
        self.validate_odoo_env_payload(payload)
        return payload

    # ------------------------------------------------------------------
    # M3: compromisso documental dedicado (.pg/project/deliverables.json)
    # ------------------------------------------------------------------
    def build_deliverables_payload(self, project, trigger_type='manual', trigger_model='project.project', trigger_record_id=None):
        project.ensure_one()
        milestones = self.env['project.milestone'].search(
            [('project_id', '=', project.id)], order='sequence asc, deadline asc, id asc',
        )
        payload = {
            'schema_version': self.DELIVERABLES_SCHEMA_VERSION,
            'project': self._project_core(project),
            'deliverables': {
                'milestones': [self._planning_item_payload(milestone) for milestone in milestones],
                'milestone_count': len(milestones),
            },
            'source_metadata': self._source_metadata(
                project,
                trigger_type=trigger_type,
                trigger_model=trigger_model,
                trigger_record_id=trigger_record_id,
            ),
        }
        payload['source_metadata']['payload_hash'] = self._payload_hash(payload)
        self.validate_deliverables_payload(payload)
        return payload

    def _require_string(self, payload, field_name, label):
        value = payload.get(field_name)
        if not isinstance(value, str) or not value.strip():
            raise ValidationError(f"{label} requires a non-empty string: {field_name}")

    def _require_dict(self, payload, field_name, label):
        value = payload.get(field_name)
        if not isinstance(value, dict):
            raise ValidationError(f"{label} requires an object: {field_name}")
        return value

    def _require_list(self, payload, field_name, label):
        value = payload.get(field_name)
        if not isinstance(value, list):
            raise ValidationError(f"{label} requires an array: {field_name}")
        return value

    def _validate_project_core(self, payload, field_name='project', label='project mirror payload'):
        project_data = self._require_dict(payload, field_name, label)
        for required in ('odoo_model', 'record_url', 'synced_at', 'name'):
            self._require_string(project_data, required, label)
        return project_data

    def _validate_source_metadata(self, payload, label):
        source_metadata = self._require_dict(payload, 'source_metadata', label)
        for required in (
            'source_system',
            'source_model',
            'sync_trigger',
            'sync_published_at',
            'sync_published_by',
            'repo_branch',
            'payload_hash',
        ):
            self._require_string(source_metadata, required, label)
        return source_metadata

    def validate_project_payload(self, payload):
        self._require_string(payload, 'schema_version', 'project payload')
        project_data = self._validate_project_core(payload, 'project', 'project payload')
        self._require_list(project_data, 'included_scope', 'project payload')
        self._require_list(project_data, 'factual_scope_backlog', 'project payload')
        scope_quality_review = self._require_dict(project_data, 'scope_quality_review', 'project payload')
        self._require_string(scope_quality_review, 'scope_signal_feedback', 'project payload')
        self._require_dict(scope_quality_review, 'curation_reason_counts', 'project payload')
        self._require_dict(scope_quality_review, 'excluded_noise_reason_counts', 'project payload')
        self._require_dict(project_data, 'governance', 'project payload')
        self._validate_source_metadata(payload, 'project payload')
        return payload

    def validate_planning_payload(self, payload):
        self._require_string(payload, 'schema_version', 'planning payload')
        self._validate_project_core(payload, 'project', 'planning payload')
        planning = self._require_dict(payload, 'planning', 'planning payload')
        milestones = self._require_list(planning, 'milestones', 'planning payload')
        self._require_list(planning, 'milestone_baseline', 'planning payload')
        for item in milestones:
            if not isinstance(item, dict):
                raise ValidationError('planning payload requires milestone objects.')
            for required in ('odoo_model', 'record_url', 'synced_at', 'name'):
                self._require_string(item, required, 'planning milestone payload')
        planning_summary = self._require_dict(planning, 'planning_summary', 'planning payload')
        for required in ('project_stage_name', 'current_phase'):
            value = planning_summary.get(required)
            if not isinstance(value, str):
                raise ValidationError(f"planning payload requires a string: {required}")
        self._require_list(planning_summary, 'open_tasks_for_next_milestone', 'planning payload')
        self._require_list(planning_summary, 'open_high_priority_tasks', 'planning payload')
        self._validate_source_metadata(payload, 'planning payload')
        return payload

    def validate_tasks_payload(self, payload):
        self._require_string(payload, 'schema_version', 'tasks payload')
        self._validate_project_core(payload, 'project', 'tasks payload')
        tasks = self._require_list(payload, 'tasks', 'tasks payload')
        for task in tasks:
            if not isinstance(task, dict):
                raise ValidationError('tasks payload requires task objects.')
            for required in ('odoo_model', 'record_url', 'synced_at', 'name'):
                self._require_string(task, required, 'task payload')
        self._validate_source_metadata(payload, 'tasks payload')
        return payload

    def validate_chatter_payload(self, payload):
        self._require_string(payload, 'schema_version', 'chatter payload')
        self._validate_project_core(payload, 'project', 'chatter payload')
        messages = self._require_list(payload, 'messages', 'chatter payload')
        for message in messages:
            if not isinstance(message, dict):
                raise ValidationError('chatter payload requires message objects.')
            for required in ('odoo_model', 'record_url', 'synced_at', 'entry_type', 'body'):
                self._require_string(message, required, 'chatter message payload')
        self._validate_source_metadata(payload, 'chatter payload')
        return payload

    def validate_attachments_payload(self, payload):
        self._require_string(payload, 'schema_version', 'attachments payload')
        self._validate_project_core(payload, 'project', 'attachments payload')
        attachments = self._require_list(payload, 'attachments', 'attachments payload')
        for attachment in attachments:
            if not isinstance(attachment, dict):
                raise ValidationError('attachments payload requires attachment objects.')
            for required in ('odoo_model', 'synced_at', 'name'):
                self._require_string(attachment, required, 'attachment payload')
        self._validate_source_metadata(payload, 'attachments payload')
        return payload

    def validate_history_event(self, payload):
        self._require_string(payload, 'schema_version', 'history event payload')
        for required in ('timestamp', 'event_type', 'trigger_type', 'summary', 'author'):
            self._require_string(payload, required, 'history event payload')
        self._validate_project_core(payload, 'project', 'history event payload')
        entity = self._require_dict(payload, 'entity', 'history event payload')
        for required in ('odoo_model', 'record_url'):
            self._require_string(entity, required, 'history event payload')
        event_data = payload.get('event_data')
        if not isinstance(event_data, dict):
            raise ValidationError('history event payload requires an object: event_data')
        return payload

    def validate_odoo_env_payload(self, payload):
        self._require_string(payload, 'schema_version', 'odoo env payload')
        self._validate_project_core(payload, 'project', 'odoo env payload')
        odoo_env = self._require_dict(payload, 'odoo_env', 'odoo env payload')
        modules = self._require_list(odoo_env, 'installed_modules', 'odoo env payload')
        collection = self._require_dict(odoo_env, 'collection', 'odoo env payload')
        status = collection.get('status')
        if status not in self.ODOO_ENV_COLLECTION_STATUSES:
            raise ValidationError(
                'odoo env payload requires collection.status in %s'
                % (', '.join(self.ODOO_ENV_COLLECTION_STATUSES),)
            )
        if status == self.ODOO_ENV_UNAVAILABLE:
            # Sem recolha nao pode haver modulos: uma lista preenchida com estado
            # `unavailable` seria de novo um inventario de origem desconhecida.
            if modules:
                raise ValidationError(
                    'odoo env payload with collection.status=unavailable requires installed_modules empty'
                )
            self._require_string(collection, 'unavailable_reason', 'odoo env payload')
        else:
            # `collected`/`stale` tem de identificar a base inventariada e o momento
            # da recolha - e o que impede o consumidor de assumir a origem.
            for required in ('purpose', 'base_url', 'collected_at'):
                self._require_string(collection, required, 'odoo env payload')
        self._validate_source_metadata(payload, 'odoo env payload')
        return payload

    def validate_deliverables_payload(self, payload):
        self._require_string(payload, 'schema_version', 'deliverables payload')
        self._validate_project_core(payload, 'project', 'deliverables payload')
        deliverables = self._require_dict(payload, 'deliverables', 'deliverables payload')
        self._require_list(deliverables, 'milestones', 'deliverables payload')
        self._validate_source_metadata(payload, 'deliverables payload')
        return payload
