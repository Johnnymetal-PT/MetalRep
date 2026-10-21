import re
import logging

from odoo import _, api, fields, models

from ..services.project_scope_sync_service import ProjectScopeSyncService
from ..services.text_hygiene import is_compound_scope_summary
from ..services.text_hygiene import is_low_signal_scope_summary
from ..services.text_hygiene import normalize_inline_text
from ..services.text_hygiene import sanitize_plaintext
from ..services.text_hygiene import split_unique_text_lines

_logger = logging.getLogger(__name__)

PG_SCOPE_TRACK_SELECTION = [
    ('approved_scope', 'Oficial'),
    ('operational_backlog', 'Backlog'),
    ('internal_note', 'Nota Interna'),
]

PG_SCOPE_KIND_SELECTION = [
    ('requirement', 'Requirement'),
    ('process', 'Process'),
    ('integration', 'Integration'),
    ('report', 'Report'),
    ('data', 'Data'),
    ('migration', 'Migration'),
    ('training', 'Training'),
    ('technical', 'Technical'),
]

PG_REQUIREMENT_STATUS_SELECTION = [
    ('approved', 'Approved'),
    ('deferred', 'Deferred'),
]

PG_REQUIREMENT_PRIORITY_SELECTION = [
    ('low', 'Low'),
    ('medium', 'Medium'),
    ('high', 'High'),
    ('critical', 'Critical'),
]

class ProjectTask(models.Model):
    _inherit = 'project.task'

    pg_scope_track = fields.Selection(
        PG_SCOPE_TRACK_SELECTION,
        string='Camada Brownfield',
        required=True,
        default='approved_scope',
        copy=False,
        tracking=True,
    )
    pg_scope_relevant = fields.Boolean(string='Scope Relevant', default=True, copy=False)
    pg_scope_state = fields.Selection(
        [
            ('proposed', 'Proposed'),
            ('validated', 'Validated'),
            ('deferred', 'Deferred'),
            ('excluded', 'Excluded'),
            ('dropped', 'Dropped'),
        ],
        string='Scope State',
        required=True,
        default='proposed',
        copy=False,
    )
    pg_scope_kind = fields.Selection(
        PG_SCOPE_KIND_SELECTION,
        string='Scope Kind',
        copy=False,
    )
    pg_scope_summary = fields.Text(string='Scope Summary', copy=False)
    pg_acceptance_criteria_text = fields.Text(string='Acceptance Criteria', copy=False)
    pg_requirement_status = fields.Selection(
        PG_REQUIREMENT_STATUS_SELECTION,
        string='Requirement Status',
        copy=False,
    )
    pg_requirement_priority = fields.Selection(
        PG_REQUIREMENT_PRIORITY_SELECTION,
        string='Requirement Priority',
        copy=False,
    )
    pg_requirement_owner_id = fields.Many2one(
        'res.users',
        string='Requirement Owner',
        copy=False,
    )
    pg_requirement_traceability_refs = fields.Text(string='Requirement Traceability Refs', copy=False)
    pg_out_of_scope_reason = fields.Text(string='Out Of Scope Reason', copy=False)
    pg_scope_sequence = fields.Integer(string='Scope Sequence', default=10, copy=False)
    pg_scope_curation_feedback = fields.Text(
        string='Scope Curation Feedback',
        compute='_compute_pg_scope_curation_feedback',
        store=True,
        readonly=True,
        copy=False,
    )
    pg_mirror_task_eligibility_status = fields.Selection(
        [
            ('eligible', 'Eligible'),
            ('eligible_with_warnings', 'Eligible With Warnings'),
            ('not_eligible', 'Not Eligible'),
        ],
        string='Mirror Task Eligibility',
        compute='_compute_pg_mirror_task_eligibility',
        readonly=True,
    )
    pg_mirror_task_eligibility_warning_count = fields.Integer(
        string='Mirror Task Eligibility Warning Count',
        compute='_compute_pg_mirror_task_eligibility',
        readonly=True,
    )
    pg_mirror_task_eligibility_feedback = fields.Text(
        string='Mirror Task Eligibility Feedback',
        compute='_compute_pg_mirror_task_eligibility',
        readonly=True,
    )
    def _get_pg_scope_sync_service(self):
        return ProjectScopeSyncService(self.env)

    def _pg_scope_sync_relevant_fields(self):
        return {
            'name',
            'description',
            'project_id',
            'stage_id',
            'state',
            'priority',
            'date_assign',
            'date_deadline',
            'allocated_hours',
            'effective_hours',
            'progress',
            'milestone_id',
            'parent_id',
            'tag_ids',
            'user_ids',
            'active',
            'pg_scope_relevant',
            'pg_scope_track',
            'pg_scope_state',
            'pg_scope_kind',
            'pg_scope_summary',
            'pg_acceptance_criteria_text',
            'pg_scope_sequence',
        }

    def _pg_scope_official_fields(self):
        return {
            'pg_scope_kind',
            'pg_scope_summary',
            'pg_acceptance_criteria_text',
        }

    @api.depends(
        'active',
        'pg_scope_relevant',
        'pg_scope_track',
        'pg_scope_state',
        'pg_scope_kind',
        'pg_scope_summary',
        'pg_acceptance_criteria_text',
    )
    def _compute_pg_scope_curation_feedback(self):
        field_labels = {
            'pg_scope_kind': _('Scope Kind'),
            'pg_scope_summary': _('Scope Summary'),
            'pg_acceptance_criteria_text': _('Acceptance Criteria'),
        }
        for task in self:
            if not task.active:
                task.pg_scope_curation_feedback = _(
                    "This task is archived. It does not participate in official scope curation or publication."
                )
                continue
            if not task.pg_scope_relevant:
                task.pg_scope_curation_feedback = _(
                    "This task is marked as not scope relevant. It stays outside the official scope curation path."
                )
                continue
            if (task.pg_scope_track or 'approved_scope') != 'approved_scope':
                task.pg_scope_curation_feedback = _(
                    "This task is currently outside the official layer. It stays in backlog or note mode until it is manually reclassified."
                )
                continue
            if task.pg_scope_state in {'excluded', 'dropped'}:
                task.pg_scope_curation_feedback = _(
                    "This task is marked as %(state)s and is excluded from official scope publication."
                ) % {'state': dict(task._fields['pg_scope_state'].selection).get(task.pg_scope_state, task.pg_scope_state)}
                continue

            missing_fields = [
                field_labels[field_name]
                for field_name in task._pg_scope_official_fields()
                if not getattr(task, field_name)
            ]
            if missing_fields:
                task.pg_scope_curation_feedback = _(
                    "The following official scope fields are still empty and will not feed publications until filled: %s."
                ) % ', '.join(missing_fields)
            else:
                task.pg_scope_curation_feedback = _(
                    "The official scope fields are filled. Only official scope fields feed scope and requirement publications."
                )

    def _pg_is_in_official_mirror_scope(self):
        self.ensure_one()
        return bool(
            self.active
            and self.pg_scope_relevant
            and (self.pg_scope_track or 'approved_scope') == 'approved_scope'
            and self.pg_scope_state not in {'excluded', 'dropped'}
        )

    def _pg_mirror_task_eligibility_review(self):
        self.ensure_one()
        if not self._pg_is_in_official_mirror_scope():
            return {
                'applies': False,
                'status': 'eligible',
                'findings': [],
                'feedback': _(
                    "This task does not currently feed the official mirror path, so the minimum mirror eligibility checks do not apply."
                ),
            }

        findings = []

        normalized_name = normalize_inline_text(self.name, fallback='', max_chars=220, drop_placeholders=True)
        normalized_name_tokens = [
            token.strip()
            for token in re.split(r'[\W_]+', normalized_name.lower())
            if token.strip()
        ]
        if (
            not normalized_name
            or is_low_signal_scope_summary(self.name, normalized_name)
            or len(normalized_name_tokens) <= 2
        ):
            findings.append(
                {
                    'bucket': 'weak_name',
                    'message': _(
                        "Task name is still too weak or generic for mirror publication."
                    ),
                    'evidence': normalized_name or '[empty]',
                }
            )

        normalized_description = sanitize_plaintext(
            self.description,
            from_html=True,
            max_chars=1200,
            strip_email_noise=True,
        )
        if not normalized_description:
            findings.append(
                {
                    'bucket': 'missing_description',
                    'message': _(
                        "Task description is empty or collapses after hygiene filtering."
                    ),
                    'evidence': '[empty]',
                }
            )

        compound_source_raw = self.pg_scope_summary or self.description or self.name or ''
        compound_source_clean = (
            normalize_inline_text(self.pg_scope_summary, fallback='', max_chars=False, drop_placeholders=True)
            if self.pg_scope_summary
            else normalized_description
        )
        if compound_source_clean and is_compound_scope_summary(compound_source_raw, compound_source_clean):
            findings.append(
                {
                    'bucket': 'compound_item',
                    'message': _(
                        "Task still looks aggregate or contextual and should be split or curated before relying on it for the mirror."
                    ),
                    'evidence': compound_source_clean[:120] or '[aggregate]',
                }
            )

        if self.milestone_id and not self.milestone_id.pg_delivery_owner_id:
            findings.append(
                {
                    'bucket': 'milestone_owner_missing',
                    'message': _(
                        "Linked milestone still has no owner."
                    ),
                    'evidence': self.milestone_id.name or '[missing milestone name]',
                }
            )

        warning_buckets = {finding['bucket'] for finding in findings}
        status = 'eligible'
        if 'missing_description' in warning_buckets and (
            'weak_name' in warning_buckets or 'compound_item' in warning_buckets
        ):
            status = 'not_eligible'
        elif findings:
            status = 'eligible_with_warnings'

        if not findings:
            feedback = _(
                "Task is currently eligible for the mirror minimum contract."
            )
        else:
            lines = [
                _(
                    "Mirror task eligibility status: %(status)s. Warning signals: %(count)s."
                )
                % {'status': status, 'count': len(findings)}
            ]
            for finding in findings:
                lines.append(
                    "- %(bucket)s: %(message)s Evidence: %(evidence)s."
                    % {
                        'bucket': finding['bucket'],
                        'message': finding['message'],
                        'evidence': finding['evidence'],
                    }
                )
            feedback = '\n'.join(lines)

        return {
            'applies': True,
            'status': status,
            'findings': findings,
            'feedback': feedback,
        }

    @api.depends(
        'active',
        'pg_scope_relevant',
        'pg_scope_track',
        'pg_scope_state',
        'name',
        'description',
        'pg_scope_summary',
        'pg_acceptance_criteria_text',
        'milestone_id',
        'milestone_id.pg_delivery_owner_id',
    )
    def _compute_pg_mirror_task_eligibility(self):
        for task in self:
            review = task._pg_mirror_task_eligibility_review()
            task.pg_mirror_task_eligibility_status = review['status']
            task.pg_mirror_task_eligibility_warning_count = len(review['findings'])
            task.pg_mirror_task_eligibility_feedback = review['feedback']

    def _queue_scope_sync_for_projects(self, projects, trigger_type):
        for project in projects.exists():
            self._get_pg_scope_sync_service().queue_project(
                project,
                trigger_type=trigger_type,
                trigger_model='project.task',
                trigger_record_id=self[:1].id if self else False,
            )

    def _queue_mirror_sync_for_projects(self, projects, trigger_type):
        for project in projects.exists():
            project._get_pg_mirror_sync_service().queue_project(
                project,
                trigger_type=trigger_type,
                trigger_model='project.task',
                trigger_record_id=self[:1].id if self else False,
            )

    @api.model_create_multi
    def create(self, vals_list):
        tasks = super().create(vals_list)
        if not self.env.context.get('pg_skip_scope_sync_enqueue'):
            tasks._queue_scope_sync_for_projects(tasks.mapped('project_id'), 'task_create')
        if not self.env.context.get('pg_skip_mirror_sync_enqueue'):
            tasks._queue_mirror_sync_for_projects(tasks.mapped('project_id'), 'task_create')
        return tasks

    def write(self, vals):
        old_projects = self.mapped('project_id')
        should_enqueue = (
            not self.env.context.get('pg_skip_scope_sync_enqueue')
            and bool(set(vals) & self._pg_scope_sync_relevant_fields())
        )
        should_enqueue_mirror = (
            not self.env.context.get('pg_skip_mirror_sync_enqueue')
            and bool(set(vals) & self._pg_scope_sync_relevant_fields())
        )
        result = super().write(vals)
        if should_enqueue:
            self._queue_scope_sync_for_projects(old_projects | self.mapped('project_id'), 'task_write')
        if should_enqueue_mirror:
            self._queue_mirror_sync_for_projects(old_projects | self.mapped('project_id'), 'task_write')
        return result

    def unlink(self):
        old_projects = self.mapped('project_id')
        trigger_record_id = self[:1].id if self else False
        result = super().unlink()
        if not self.env.context.get('pg_skip_scope_sync_enqueue'):
            scope_sync_service = ProjectScopeSyncService(self.env)
            for project in old_projects:
                scope_sync_service.queue_project(
                    project,
                    trigger_type='task_unlink',
                    trigger_model='project.task',
                    trigger_record_id=trigger_record_id,
                )
        if not self.env.context.get('pg_skip_mirror_sync_enqueue'):
            for project in old_projects:
                project._get_pg_mirror_sync_service().queue_project(
                    project,
                    trigger_type='task_unlink',
                    trigger_model='project.task',
                    trigger_record_id=trigger_record_id,
                )
        return result

