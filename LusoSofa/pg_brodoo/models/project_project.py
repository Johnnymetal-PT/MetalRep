import logging
import re
import unicodedata

from odoo import _, api, fields, models
from odoo.exceptions import ValidationError
from odoo.tools import html2plaintext

from ..services.github_service import GitHubService
from ..services.project_effort_sync_service import ProjectEffortSyncService
from ..services.project_mirror_sync_service import ProjectMirrorSyncService
from ..services.project_mirror_migration_service import ProjectMirrorMigrationService
from ..services.project_scope_sync_service import ProjectScopeSyncService
from ..services.project_sync_quality_review_service import ProjectSyncQualityReviewService

_logger = logging.getLogger(__name__)


YES_NO_UNKNOWN_SELECTION = [
    ('yes', 'Yes'),
    ('no', 'No'),
    ('unknown', 'Unknown'),
]

ODOO_EDITION_SELECTION = [
    ('community', 'Community'),
    ('enterprise', 'Enterprise'),
    ('unknown', 'Unknown'),
]

ODOO_ENVIRONMENT_SELECTION = [
    ('saas', 'SaaS'),
    ('odoo_sh', 'Odoo.sh'),
    ('on_premise', 'On-Premise'),
    ('unknown', 'Unknown'),
]

PROJECT_PHASE_SELECTION = [
    ('discovery', 'Discovery'),
    ('fit_gap', 'Fit-Gap'),
    ('solution_design', 'Solution Design'),
    ('implementation', 'Implementation'),
    ('uat', 'UAT'),
    ('go_live', 'Go-Live'),
    ('hypercare', 'Hypercare'),
    ('support', 'Support'),
]

SCOPE_SYNC_MODE_SELECTION = [
    ('manual', 'Manual'),
    ('event_driven', 'Event Driven'),
]

SCOPE_SYNC_STATUS_SELECTION = [
    ('never', 'Never'),
    ('queued', 'Queued'),
    ('running', 'Running'),
    ('done', 'Done'),
    ('skipped', 'Skipped'),
    ('error', 'Error'),
]

PG_ONBOARDING_STATUS_SELECTION = [
    ('never', 'Never'),
    ('done', 'Done'),
    ('error', 'Error'),
]


class ProjectProject(models.Model):
    _inherit = 'project.project'

    pg_repository_id = fields.Many2one('pg.ai.repository', string='PG Repository', copy=False)
    pg_repo_branch = fields.Char(string='PG Repo Branch', copy=False)
    pg_project_key = fields.Char(
        string='PG Project Key',
        copy=False,
        index=True,
        help=(
            'Unique key identifying this project in the GitHub repository namespace. '
            'Auto-derived from project name as a lowercase slug. '
            'Immutable after first successful publish.'
        ),
    )
    pg_scope_sync_enabled = fields.Boolean(string='Scope Sync Enabled', copy=False)
    pg_effort_sync_enabled = fields.Boolean(string='Effort Sync Enabled', copy=False, default=True)
    pg_scope_sync_mode = fields.Selection(
        SCOPE_SYNC_MODE_SELECTION,
        string='Scope Sync Mode',
        required=True,
        default='event_driven',
        copy=False,
    )
    pg_scope_sync_last_status = fields.Selection(
        SCOPE_SYNC_STATUS_SELECTION,
        string='Last Scope Sync Status',
        default='never',
        readonly=True,
        copy=False,
    )
    pg_scope_sync_last_payload_hash = fields.Char(string='Last Scope Payload Hash', readonly=True, copy=False)
    pg_scope_sync_last_published_at = fields.Datetime(string='Last Scope Published At', readonly=True, copy=False)
    pg_scope_sync_last_message = fields.Text(string='Last Scope Sync Message', readonly=True, copy=False)
    pg_mirror_sync_last_status = fields.Selection(
        SCOPE_SYNC_STATUS_SELECTION,
        string='Last Mirror Sync Status',
        default='never',
        readonly=True,
        copy=False,
    )
    pg_mirror_sync_last_payload_hash = fields.Char(string='Last Mirror Payload Hash', readonly=True, copy=False)
    pg_mirror_sync_last_published_at = fields.Datetime(string='Last Mirror Published At', readonly=True, copy=False)
    pg_mirror_sync_last_message = fields.Text(string='Last Mirror Sync Message', readonly=True, copy=False)
    pg_mirror_sync_quality_review_status = fields.Selection(
        [
            ('ok', 'OK'),
            ('warning', 'Warning'),
            ('blocking', 'Blocking'),
        ],
        string='Mirror Quality Review Status',
        readonly=True,
        copy=False,
    )
    pg_mirror_sync_quality_review_feedback = fields.Text(
        string='Mirror Quality Review Feedback',
        readonly=True,
        copy=False,
    )
    pg_mirror_sync_quality_warning_count = fields.Integer(
        string='Mirror Quality Warning Count',
        readonly=True,
        copy=False,
    )
    pg_mirror_sync_quality_blocking_count = fields.Integer(
        string='Mirror Quality Blocking Count',
        readonly=True,
        copy=False,
    )
    pg_mirror_included_scope_count = fields.Integer(
        string='Mirror Included Scope Count',
        readonly=True,
        copy=False,
    )
    pg_mirror_scope_backlog_count = fields.Integer(
        string='Mirror Factual Scope Backlog Count',
        readonly=True,
        copy=False,
    )
    pg_mirror_scope_backlog_reason_summary = fields.Char(
        string='Mirror Factual Scope Backlog Reasons',
        readonly=True,
        copy=False,
    )
    pg_mirror_scope_backlog_feedback = fields.Text(
        string='Mirror Factual Scope Backlog Feedback',
        readonly=True,
        copy=False,
    )
    pg_mirror_excluded_noise_count = fields.Integer(
        string='Mirror Excluded Noise Count',
        readonly=True,
        copy=False,
    )
    pg_mirror_excluded_noise_reason_summary = fields.Char(
        string='Mirror Excluded Noise Reasons',
        readonly=True,
        copy=False,
    )
    pg_mirror_excluded_noise_feedback = fields.Text(
        string='Mirror Excluded Noise Feedback',
        readonly=True,
        copy=False,
    )
    pg_mirror_scope_signal_feedback = fields.Text(
        string='Mirror Scope Signal Feedback',
        readonly=True,
        copy=False,
    )
    pg_mirror_operational_eligibility_status = fields.Selection(
        [
            ('eligible', 'Eligible'),
            ('eligible_with_warnings', 'Eligible With Warnings'),
            ('not_eligible', 'Not Eligible'),
        ],
        string='Mirror Operational Eligibility',
        compute='_compute_pg_mirror_operational_eligibility',
        readonly=True,
    )
    pg_mirror_operational_eligibility_warning_count = fields.Integer(
        string='Mirror Operational Eligibility Warning Count',
        compute='_compute_pg_mirror_operational_eligibility',
        readonly=True,
    )
    pg_mirror_operational_eligibility_not_eligible_count = fields.Integer(
        string='Mirror Operational Not Eligible Count',
        compute='_compute_pg_mirror_operational_eligibility',
        readonly=True,
    )
    pg_mirror_operational_eligibility_feedback = fields.Text(
        string='Mirror Operational Eligibility Feedback',
        compute='_compute_pg_mirror_operational_eligibility',
        readonly=True,
    )
    pg_scope_sync_quality_review_feedback = fields.Text(
        string='Scope Quality Review Feedback',
        readonly=True,
        copy=False,
    )
    pg_effort_sync_last_status = fields.Selection(
        SCOPE_SYNC_STATUS_SELECTION,
        string='Last Effort Sync Status',
        default='never',
        readonly=True,
        copy=False,
    )
    pg_effort_sync_last_payload_hash = fields.Char(
        string='Last Effort Payload Hash',
        readonly=True,
        copy=False,
    )
    pg_effort_sync_last_published_at = fields.Datetime(
        string='Last Effort Published At',
        readonly=True,
        copy=False,
    )
    pg_effort_sync_last_message = fields.Text(
        string='Last Effort Sync Message',
        readonly=True,
        copy=False,
    )
    pg_client_unit = fields.Char(string='Client Unit')
    pg_repository_summary = fields.Text(string='Repository Summary')
    pg_project_phase = fields.Selection(PROJECT_PHASE_SELECTION, string='Project Phase')
    pg_odoo_version = fields.Char(string='Odoo Version')
    pg_odoo_edition = fields.Selection(ODOO_EDITION_SELECTION, string='Odoo Edition', default='unknown', required=True)
    pg_odoo_environment = fields.Selection(
        ODOO_ENVIRONMENT_SELECTION,
        string='Odoo Environment',
        default='unknown',
        required=True,
    )
    pg_standard_allowed = fields.Selection(
        YES_NO_UNKNOWN_SELECTION,
        string='Standard Allowed',
        default='unknown',
        required=True,
    )
    pg_additional_modules_allowed = fields.Selection(
        YES_NO_UNKNOWN_SELECTION,
        string='Additional Modules Allowed',
        default='unknown',
        required=True,
    )
    pg_studio_allowed = fields.Selection(
        YES_NO_UNKNOWN_SELECTION,
        string='Studio Allowed',
        default='unknown',
        required=True,
    )
    pg_custom_allowed = fields.Selection(
        YES_NO_UNKNOWN_SELECTION,
        string='Custom Allowed',
        default='unknown',
        required=True,
    )
    pg_additional_contract_restrictions = fields.Text(string='Additional Contract Restrictions')
    pg_business_goal = fields.Text(string='Business Goal')
    pg_current_request = fields.Text(string='Current Request')
    pg_current_process = fields.Text(string='Current Process')
    pg_problem_or_need = fields.Text(string='Problem Or Need')
    pg_business_impact = fields.Text(string='Business Impact')
    pg_onboarding_scope_included_text = fields.Text(string='Onboarding Scope Included')
    pg_onboarding_scope_excluded_text = fields.Text(string='Onboarding Scope Excluded')
    pg_onboarding_assumptions_text = fields.Text(string='Onboarding Assumptions')
    pg_onboarding_stakeholders_text = fields.Text(string='Onboarding Stakeholders')
    pg_onboarding_milestones_text = fields.Text(string='Onboarding Milestones')
    pg_onboarding_last_applied_at = fields.Datetime(
        string='Last Onboarding Applied At',
        readonly=True,
        copy=False,
    )
    pg_onboarding_last_status = fields.Selection(
        PG_ONBOARDING_STATUS_SELECTION,
        string='Last Onboarding Status',
        default='never',
        readonly=True,
        copy=False,
    )
    pg_onboarding_last_message = fields.Text(
        string='Last Onboarding Message',
        readonly=True,
        copy=False,
    )
    pg_mirror_migration_last_at = fields.Datetime(
        string='Last Mirror Migration At',
        readonly=True,
        copy=False,
    )
    pg_mirror_migration_last_status = fields.Selection(
        PG_ONBOARDING_STATUS_SELECTION,
        string='Last Mirror Migration Status',
        default='never',
        readonly=True,
        copy=False,
    )
    pg_mirror_migration_last_message = fields.Text(
        string='Last Mirror Migration Message',
        readonly=True,
        copy=False,
    )
    pg_mirror_migration_needed = fields.Boolean(
        string='Mirror Migration Needed',
        compute='_compute_pg_mirror_migration_needed',
    )
    pg_trigger = fields.Char(string='Trigger')
    pg_frequency = fields.Char(string='Frequency')
    pg_volumes = fields.Char(string='Volumes')
    pg_urgency = fields.Selection(
        [
            ('low', 'Low'),
            ('medium', 'Medium'),
            ('high', 'High'),
            ('critical', 'Critical'),
            ('unknown', 'Unknown'),
        ],
        string='Urgency',
        default='unknown',
        required=True,
    )
    pg_scope_sync_run_ids = fields.One2many('pg.project.scope.sync.run', 'project_id', string='PG Scope Sync Runs', copy=False)
    pg_scope_sync_run_count = fields.Integer(string='Scope Sync Runs', compute='_compute_pg_scope_sync_run_count')
    pg_mirror_sync_run_ids = fields.One2many(
        'pg.project.mirror.sync.run',
        'project_id',
        string='PG Mirror Sync Runs',
        copy=False,
    )
    pg_mirror_sync_run_count = fields.Integer(string='Mirror Sync Runs', compute='_compute_pg_mirror_sync_run_count')
    pg_effort_sync_run_ids = fields.One2many(
        'pg.project.effort.sync.run',
        'project_id',
        string='PG Effort Sync Runs',
        copy=False,
    )
    pg_effort_sync_run_count = fields.Integer(
        string='Effort Sync Runs',
        compute='_compute_pg_effort_sync_run_count',
    )

    @api.depends('pg_scope_sync_run_ids')
    def _compute_pg_scope_sync_run_count(self):
        for project in self:
            project.pg_scope_sync_run_count = len(project.pg_scope_sync_run_ids)

    @api.depends('pg_mirror_sync_run_ids')
    def _compute_pg_mirror_sync_run_count(self):
        for project in self:
            project.pg_mirror_sync_run_count = len(project.pg_mirror_sync_run_ids)

    @api.depends(
        'pg_repository_id',
        'pg_repo_branch',
        'pg_onboarding_last_status',
        'pg_mirror_sync_run_ids',
    )
    def _compute_pg_mirror_migration_needed(self):
        migration_service = self._get_pg_mirror_migration_service()
        for project in self:
            project.pg_mirror_migration_needed = migration_service.project_needs_migration(project)

    @api.depends('pg_effort_sync_run_ids')
    def _compute_pg_effort_sync_run_count(self):
        for project in self:
            project.pg_effort_sync_run_count = len(project.pg_effort_sync_run_ids)

    @api.depends(
        'allow_milestones',
        'task_ids.active',
        'task_ids.pg_scope_relevant',
        'task_ids.pg_scope_track',
        'task_ids.pg_scope_state',
        'task_ids.name',
        'task_ids.description',
        'task_ids.pg_scope_summary',
        'task_ids.pg_acceptance_criteria_text',
        'task_ids.milestone_id',
        'task_ids.milestone_id.pg_delivery_owner_id',
        'milestone_ids.active',
        'milestone_ids.pg_delivery_state',
        'milestone_ids.pg_delivery_owner_id',
    )
    def _pg_mirror_task_eligibility_review_safe(self, task):
        review_method = getattr(type(task), '_pg_mirror_task_eligibility_review', None)
        if callable(review_method):
            return review_method(task)

        findings = []
        if not task.active or not task.pg_scope_relevant or (task.pg_scope_track or 'approved_scope') != 'approved_scope':
            return {
                'applies': False,
                'status': 'eligible',
                'findings': [],
                'feedback': _(
                    "Task does not currently apply to mirror operational eligibility."
                ),
            }

        task_name = (task.name or '').strip()
        description = (html2plaintext(task.description or '') or '').strip()
        scope_summary = (task.pg_scope_summary or '').strip()
        if len(task_name.split()) <= 2:
            findings.append(
                {
                    'bucket': 'weak_name',
                    'message': _(
                        "Task name is too weak to support a robust mirror review."
                    ),
                    'evidence': task_name or '[empty]',
                }
            )
        if not description and not scope_summary:
            findings.append(
                {
                    'bucket': 'missing_description',
                    'message': _(
                        "Task still has no usable description or official scope summary."
                    ),
                    'evidence': task_name or '[empty]',
                }
            )
        if self.allow_milestones and task.milestone_id and not task.milestone_id.pg_delivery_owner_id:
            findings.append(
                {
                    'bucket': 'milestone_owner_missing',
                    'message': _(
                        "Linked milestone still has no owner."
                    ),
                    'evidence': task.milestone_id.name or '[missing milestone name]',
                }
            )

        warning_buckets = {finding['bucket'] for finding in findings}
        status = 'eligible'
        if 'missing_description' in warning_buckets and 'weak_name' in warning_buckets:
            status = 'not_eligible'
        elif findings:
            status = 'eligible_with_warnings'

        feedback = _(
            "Mirror task eligibility fallback applied because the task review helper is unavailable in the current build."
        )
        return {
            'applies': True,
            'status': status,
            'findings': findings,
            'feedback': feedback,
        }

    def _compute_pg_mirror_operational_eligibility(self):
        for project in self:
            weak_name_count = 0
            missing_description_count = 0
            compound_item_count = 0
            task_not_eligible_count = 0

            for task in project._pg_mirror_operational_target_tasks():
                review = project._pg_mirror_task_eligibility_review_safe(task)
                if not review.get('applies'):
                    continue
                buckets = {finding['bucket'] for finding in review.get('findings') or []}
                weak_name_count += int('weak_name' in buckets)
                missing_description_count += int('missing_description' in buckets)
                compound_item_count += int('compound_item' in buckets)
                task_not_eligible_count += int(review.get('status') == 'not_eligible')

            milestone_owner_gap_count = len(
                project.milestone_ids.filtered(
                    lambda milestone: milestone.active
                    and milestone.pg_delivery_state != 'delivered'
                    and not milestone.pg_delivery_owner_id
                )
            ) if project.allow_milestones else 0

            total_warning_count = (
                weak_name_count
                + missing_description_count
                + compound_item_count
                + milestone_owner_gap_count
            )

            if task_not_eligible_count:
                status = 'not_eligible'
            elif total_warning_count:
                status = 'eligible_with_warnings'
            else:
                status = 'eligible'

            if not total_warning_count:
                feedback = _(
                    "Operational mirror eligibility is currently clean for the official project layer."
                )
            else:
                lines = [
                    _(
                        "Operational mirror eligibility status: %(status)s."
                    ) % {'status': status},
                    _(
                        "Official tasks reviewed: %(tasks)s. Not eligible tasks: %(not_eligible)s. Warning signals: %(warnings)s."
                    ) % {
                        'tasks': len(project._pg_mirror_operational_target_tasks()),
                        'not_eligible': task_not_eligible_count,
                        'warnings': total_warning_count,
                    },
                ]
                if weak_name_count:
                    lines.append(_("- Weak task names detected: %s.") % weak_name_count)
                if missing_description_count:
                    lines.append(_("- Tasks with missing description after hygiene: %s.") % missing_description_count)
                if compound_item_count:
                    lines.append(_("- Aggregate or contextual tasks still needing split/curation: %s.") % compound_item_count)
                if milestone_owner_gap_count:
                    lines.append(_("- Open milestones without owner: %s.") % milestone_owner_gap_count)
                feedback = '\n'.join(lines)

            project.pg_mirror_operational_eligibility_status = status
            project.pg_mirror_operational_eligibility_warning_count = total_warning_count
            project.pg_mirror_operational_eligibility_not_eligible_count = task_not_eligible_count
            project.pg_mirror_operational_eligibility_feedback = feedback

    def _get_pg_scope_sync_service(self):
        return ProjectScopeSyncService(self.env)

    def _get_pg_mirror_sync_service(self):
        return ProjectMirrorSyncService(self.env)

    def _get_pg_mirror_migration_service(self):
        return ProjectMirrorMigrationService(self.env)

    def _get_pg_effort_sync_service(self):
        return ProjectEffortSyncService(self.env)

    def _get_pg_sync_quality_review_service(self):
        return ProjectSyncQualityReviewService(self.env)

    def _pg_mirror_operational_target_tasks(self):
        self.ensure_one()
        return self.task_ids.filtered(
            lambda task: task.active
            and task.pg_scope_relevant
            and (task.pg_scope_track or 'approved_scope') == 'approved_scope'
            and task.pg_scope_state not in {'excluded', 'dropped'}
        )

    def _is_pg_mirror_sync_enabled(self):
        self.ensure_one()
        return bool(
            self.pg_repository_id
            and (self.pg_repo_branch or '').strip()
            and self.pg_scope_sync_enabled
        )

    @api.model
    def _pg_derive_project_key(self, name):
        """Derive a stable URL-safe slug from a project name (max 48 chars)."""
        normalized = unicodedata.normalize('NFKD', name or '').encode('ascii', 'ignore').decode('ascii')
        slug = re.sub(r'[^a-z0-9]+', '-', normalized.lower())
        slug = re.sub(r'-+', '-', slug).strip('-')
        return slug[:48] or 'project'

    def _pg_resolve_project_key(self):
        """Return the stored project_key, or None if in legacy mode (key not set)."""
        self.ensure_one()
        return (self.pg_project_key or '').strip() or None

    @api.onchange('name')
    def _onchange_name_suggest_project_key(self):
        if self.name and not self.pg_project_key:
            self.pg_project_key = self._pg_derive_project_key(self.name)

    def _pg_get_or_create_project_key(self):
        """Resolve existing key or create one automatically with repo+branch scoped uniqueness."""
        self.ensure_one()
        key = (self.pg_project_key or '').strip()
        if key:
            return key

        base = self._pg_derive_project_key(self.name)
        candidate = base
        suffix_idx = 2

        def _exists(conflict_key):
            return bool(
                self.search_count([
                    ('pg_project_key', '=', conflict_key),
                    ('pg_repository_id', '=', self.pg_repository_id.id),
                    ('pg_repo_branch', '=', self.pg_repo_branch),
                    ('id', '!=', self.id),
                ])
            )

        while _exists(candidate):
            suffix = '-%s' % suffix_idx
            candidate = (base[: max(1, 48 - len(suffix))] + suffix).strip('-')
            suffix_idx += 1

        self.with_context(
            pg_skip_scope_sync_enqueue=True,
            pg_skip_mirror_sync_enqueue=True,
        ).sudo().write({'pg_project_key': candidate})
        return candidate
    def _pg_mirror_sync_relevant_fields(self):
        return {
            'name',
            'partner_id',
            'user_id',
            'stage_id',
            'tag_ids',
            'date_start',
            'date',
            'allocated_hours',
            'progress',
            'allow_milestones',
            'pg_repository_id',
            'pg_repo_branch',
            'pg_project_key',
            'pg_scope_sync_enabled',
            'pg_scope_sync_mode',
            'pg_client_unit',
            'pg_repository_summary',
            'pg_project_phase',
            'pg_business_goal',
            'pg_current_request',
            'pg_current_process',
            'pg_problem_or_need',
            'pg_business_impact',
            'pg_trigger',
            'pg_frequency',
            'pg_volumes',
            'pg_urgency',
            'pg_standard_allowed',
            'pg_additional_modules_allowed',
            'pg_studio_allowed',
            'pg_custom_allowed',
            'pg_additional_contract_restrictions',
            'pg_onboarding_scope_included_text',
            'pg_onboarding_scope_excluded_text',
            'pg_onboarding_assumptions_text',
            'pg_onboarding_stakeholders_text',
            'pg_onboarding_milestones_text',
        }

    def _pg_operational_backlog_tasks(self):
        self.ensure_one()
        return self.task_ids.filtered(
            lambda task: task.active
            and task.pg_scope_relevant
            and (task.pg_scope_track or 'approved_scope') == 'operational_backlog'
            and task.pg_scope_state not in {'excluded', 'dropped'}
        )

    def _pg_scope_sync_relevant_fields(self):
        return {
            'pg_repository_id',
            'pg_repo_branch',
            'pg_project_key',
            'pg_scope_sync_enabled',
            'pg_scope_sync_mode',
            'pg_client_unit',
            'pg_repository_summary',
            'pg_project_phase',
            'pg_odoo_version',
            'pg_odoo_edition',
            'pg_odoo_environment',
            'pg_standard_allowed',
            'pg_additional_modules_allowed',
            'pg_studio_allowed',
            'pg_custom_allowed',
            'pg_additional_contract_restrictions',
            'pg_business_goal',
            'pg_current_request',
            'pg_current_process',
            'pg_problem_or_need',
            'pg_business_impact',
            'pg_trigger',
            'pg_frequency',
            'pg_volumes',
            'pg_urgency',
        }

    @api.constrains('pg_repo_branch', 'pg_odoo_environment')
    def _check_pg_repo_branch_not_main_on_odoo_sh(self):
        for project in self:
            if (
                project.pg_odoo_environment == 'odoo_sh'
                and (project.pg_repo_branch or '').strip().lower() == 'main'
            ):
                raise ValidationError(
                    _("A branch 'main' não pode ser utilizada em projetos com ambiente Odoo.sh. "
                      "Em Odoo.sh a branch 'main' é a branch de produção. "
                      "Configure uma branch de desenvolvimento (ex: dev, staging).")
                )

    @api.onchange('pg_repo_branch', 'pg_odoo_environment')
    def _onchange_pg_repo_branch_odoo_sh_warning(self):
        if (
            self.pg_odoo_environment == 'odoo_sh'
            and (self.pg_repo_branch or '').strip().lower() == 'main'
        ):
            return {
                'warning': {
                    'title': _("Branch 'main' não permitida em Odoo.sh"),
                    'message': _(
                        "Em Odoo.sh a branch 'main' corresponde ao ambiente de produção. "
                        "Utilize uma branch de desenvolvimento ou staging."
                    ),
                }
            }

    @api.constrains('pg_scope_sync_enabled', 'pg_repository_id', 'pg_repo_branch')
    def _check_pg_scope_sync_configuration(self):
        for project in self:
            if project.pg_scope_sync_enabled and (not project.pg_repository_id or not (project.pg_repo_branch or '').strip()):
                raise ValidationError(
                    _("Scope sync requires both a GitHub repository and a repository branch on the project.")
                )

    @api.constrains('pg_project_key')
    def _check_pg_project_key_format(self):
        for project in self:
            key = (project.pg_project_key or '').strip()
            if key and not re.fullmatch(r'[a-z0-9][a-z0-9\-]{0,47}', key):
                raise ValidationError(
                    _("Project key must be a lowercase alphanumeric slug "
                      "(letters, digits and hyphens only, max 48 chars, "
                      "must start with a letter or digit).")
                )

    @api.constrains('pg_project_key', 'pg_repository_id', 'pg_repo_branch')
    def _check_pg_project_key_unique(self):
        for project in self:
            key = (project.pg_project_key or '').strip()
            if not key:
                continue
            existing = self.search(
                [
                    ('pg_project_key', '=', key),
                    ('pg_repository_id', '=', project.pg_repository_id.id),
                    ('pg_repo_branch', '=', project.pg_repo_branch),
                    ('id', '!=', project.id),
                ],
                limit=1,
            )
            if existing:
                raise ValidationError(
                    _("Project key '%s' is already used by another project "
                      "in the same repository and branch.") % key
                )

    @api.constrains('pg_effort_sync_enabled', 'pg_repository_id', 'pg_repo_branch')
    def _check_pg_effort_sync_configuration(self):
        for project in self:
            repo_set = bool(project.pg_repository_id)
            branch_set = bool((project.pg_repo_branch or '').strip())
            if project.pg_effort_sync_enabled and (repo_set != branch_set):
                raise ValidationError(
                    _("Effort sync requires repository and branch to be configured together.")
                )

    def _pg_branch_missing_action(self):
        """Se a branch do espelho ('pg_repo_branch') nao existir no repo, devolve
        a acao do wizard de criacao (escolha explicita da branch base). Caso
        contrario, None.

        Uso interativo (botoes de sync manual): garante que nenhuma branch e
        criada sem o utilizador escolher a base. No fluxo automatico (cron/eventos)
        a guarda equivalente vive nos servicos de sync, que sinalizam erro em vez
        de criar.
        """
        self.ensure_one()
        if not self.pg_repository_id or not (self.pg_repo_branch or '').strip():
            return None
        if GitHubService(self.env).branch_exists(self.pg_repository_id, self.pg_repo_branch):
            return None
        return {
            'type': 'ir.actions.act_window',
            'name': _('Criar branch em falta'),
            'res_model': 'pg.branch.create.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_project_id': self.id,
                'default_repository_id': self.pg_repository_id.id,
                'default_target_branch': self.pg_repo_branch,
            },
        }

    def action_publish_scope_to_repository(self):
        for project in self:
            branch_action = project._pg_branch_missing_action()
            if branch_action:
                return branch_action
            run = project._get_pg_scope_sync_service().queue_project(
                project,
                trigger_type='manual',
                trigger_model='project.project',
                trigger_record_id=project.id,
            )
            if run and run.status == 'queued':
                project._get_pg_scope_sync_service().process_run(run)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_open_pg_onboarding(self):
        self.ensure_one()
        action = self.env.ref('pg_brodoo.action_pg_ai_onboarding_wizard').sudo().read()[0]
        context = dict(self.env.context)
        context.update(
            {
                'active_model': 'project.project',
                'active_id': self.id,
                'default_project_id': self.id,
            }
        )
        action['context'] = context
        return action

    def action_sync_project_mirror_now(self):
        for project in self:
            branch_action = project._pg_branch_missing_action()
            if branch_action:
                return branch_action
            run = project._get_pg_mirror_sync_service().queue_project(
                project,
                trigger_type='manual',
                trigger_model='project.project',
                trigger_record_id=project.id,
            )
            if run and run.status == 'queued':
                project._get_pg_mirror_sync_service().process_run(run)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_force_rebuild_project_artifacts(self):
        for project in self:
            branch_action = project._pg_branch_missing_action()
            if branch_action:
                return branch_action
            run = project._get_pg_mirror_sync_service().queue_project(
                project,
                trigger_type='manual',
                trigger_model='project.project',
                trigger_record_id=project.id,
                force_republish=True,
            )
            if run and run.status == 'queued':
                project._get_pg_mirror_sync_service().process_run(run)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_migrate_legacy_project_mirror(self):
        for project in self:
            project._get_pg_mirror_migration_service().migrate_project(project, process_run=True)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_rebuild_project_context(self):
        for project in self:
            branch_action = project._pg_branch_missing_action()
            if branch_action:
                return branch_action
            run = project._get_pg_mirror_sync_service().queue_project(
                project,
                trigger_type='scheduled_rebuild',
                trigger_model='project.project',
                trigger_record_id=project.id,
            )
            if run and run.status == 'queued':
                project._get_pg_mirror_sync_service().process_run(run)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_view_mirror_sync_runs(self):
        self.ensure_one()
        action = self.env.ref('pg_brodoo.action_pg_project_mirror_sync_run').sudo().read()[0]
        action['domain'] = [('project_id', '=', self.id)]
        action['context'] = {'default_project_id': self.id}
        return action

    def action_publish_effort_to_repository(self):
        for project in self:
            branch_action = project._pg_branch_missing_action()
            if branch_action:
                return branch_action
            run = project._get_pg_effort_sync_service().queue_project(
                project,
                trigger_type='manual_button',
                trigger_model='project.project',
                trigger_record_id=project.id,
            )
            if run and run.status == 'queued':
                project._get_pg_effort_sync_service().process_run(run)
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_view_scope_sync_runs(self):
        self.ensure_one()
        action = self.env.ref('pg_brodoo.action_pg_project_scope_sync_run').read()[0]
        action['domain'] = [('project_id', '=', self.id)]
        action['context'] = {'default_project_id': self.id}
        return action

    def action_view_effort_sync_runs(self):
        self.ensure_one()
        action = self.env.ref('pg_brodoo.action_pg_project_effort_sync_run').read()[0]
        action['domain'] = [('project_id', '=', self.id)]
        action['context'] = {'default_project_id': self.id}
        return action

    @api.model_create_multi
    def create(self, vals_list):
        # A branch Brodoo so faz sentido com um repositorio. Assume-se 'brodoo'
        # ao criar com repositorio; sem repositorio, a branch fica vazia (evita
        # que a branch sozinha dispare as constraints de sync num projeto novo).
        for vals in vals_list:
            if vals.get('pg_repository_id') and not (vals.get('pg_repo_branch') or '').strip():
                vals['pg_repo_branch'] = 'brodoo'
        return super().create(vals_list)

    def write(self, vals):
        # Manter repositorio e branch em sincronia: ao ligar um repositorio a
        # branch Brodoo e assumida; ao remover o repositorio a branch e limpa.
        if 'pg_repository_id' in vals:
            if vals.get('pg_repository_id'):
                if not (vals.get('pg_repo_branch') or '').strip():
                    vals = dict(vals, pg_repo_branch='brodoo')
            elif 'pg_repo_branch' not in vals:
                vals = dict(vals, pg_repo_branch=False)
        should_enqueue_mirror = (
            not self.env.context.get('pg_skip_mirror_sync_enqueue')
            and bool(set(vals) & self._pg_mirror_sync_relevant_fields())
        )
        should_enqueue = (
            not self.env.context.get('pg_skip_scope_sync_enqueue')
            and bool(set(vals) & self._pg_scope_sync_relevant_fields())
        )
        result = super().write(vals)
        if should_enqueue_mirror:
            for project in self:
                project._get_pg_mirror_sync_service().queue_project(
                    project,
                    trigger_type='project_write',
                    trigger_model='project.project',
                    trigger_record_id=project.id,
                )
        if should_enqueue:
            for project in self:
                project._get_pg_scope_sync_service().queue_project(
                    project,
                    trigger_type='project_write',
                    trigger_model='project.project',
                    trigger_record_id=project.id,
                )
        return result
