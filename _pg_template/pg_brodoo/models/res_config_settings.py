from odoo import fields, models

from ..services.github_service import GitHubService


class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    _GITHUB_REPOSITORY_SORT_SELECTION = [
        ('updated', 'Updated'),
        ('full_name', 'Full Name'),
        ('created', 'Created'),
        ('pushed', 'Pushed'),
    ]
    _SELECTION_PARAM_FIELDS = {
        'pg_github_repository_sort': ('pg_github_repository_sort', 'updated'),
    }
    _TEXT_PARAM_FIELDS = {}

    pg_sync_quality_review_enabled = fields.Boolean(
        string='Enable Pre-Publication Quality Review',
        config_parameter='pg_sync_quality_review_enabled',
        default=False,
    )
    pg_odoo_version = fields.Char(
        string='Odoo Version',
        config_parameter='pg_odoo_version',
        default='19',
    )

    pg_github_token = fields.Char(
        string='GitHub Token',
        config_parameter='pg_github_token',
    )
    pg_github_default_owner = fields.Char(
        string='GitHub Default Owner',
        config_parameter='pg_github_default_owner',
    )
    pg_github_default_branch = fields.Char(
        string='GitHub Default Branch',
        config_parameter='pg_github_default_branch',
        default='main',
    )
    pg_github_timeout = fields.Integer(
        string='GitHub Timeout (s)',
        config_parameter='pg_github_timeout',
        default=60,
    )
    pg_github_repository_sort = fields.Selection(
        _GITHUB_REPOSITORY_SORT_SELECTION,
        string='Repository Sort',
        default='updated',
    )
    pg_ai_push_direct_to_selected_branch = fields.Boolean(
        string='Push Directly To Selected Branch',
        config_parameter='pg_ai_push_direct_to_selected_branch',
        default=True,
    )
    pg_github_create_pr_by_default = fields.Boolean(
        string='Create Pull Request by Default',
        config_parameter='pg_github_create_pr_by_default',
        default=True,
    )
    pg_github_autosync_on_search = fields.Boolean(
        string='Auto Sync Repositories On Search',
        config_parameter='pg_github_autosync_on_search',
        default=True,
    )
    pg_ai_autosync_branches_on_repo_change = fields.Boolean(
        string='Auto Sync Branches On Repo Change',
        config_parameter='pg_ai_autosync_branches_on_repo_change',
        default=True,
    )
    pg_ai_auto_select_default_branch = fields.Boolean(
        string='Auto Select Default Branch',
        config_parameter='pg_ai_auto_select_default_branch',
        default=True,
    )
    pg_github_account_login = fields.Char(
        string='GitHub Account',
        config_parameter='pg_github_account_login',
        readonly=True,
    )
    pg_github_account_name = fields.Char(
        string='GitHub Name',
        config_parameter='pg_github_account_name',
        readonly=True,
    )
    pg_github_repo_count = fields.Integer(string='GitHub Repositories', compute='_compute_github_repo_count')

    def _compute_github_repo_count(self):
        repository_count = self.env['pg.ai.repository'].sudo().search_count([])
        for record in self:
            record.pg_github_repo_count = repository_count

    def _normalize_selection_value(self, field_name, value, default_value):
        normalized_value = (value or '').strip() or default_value

        if field_name == 'pg_github_repository_sort':
            allowed_values = {item[0] for item in self._GITHUB_REPOSITORY_SORT_SELECTION}
            if normalized_value not in allowed_values:
                return default_value

        return normalized_value

    def get_values(self):
        res = super().get_values()
        params = self.env['ir.config_parameter'].sudo()
        for field_name, (param_key, default_value) in self._SELECTION_PARAM_FIELDS.items():
            res[field_name] = self._normalize_selection_value(field_name, params.get_param(param_key), default_value)
        for field_name, (param_key, default_value) in self._TEXT_PARAM_FIELDS.items():
            res[field_name] = params.get_param(param_key, default_value) or default_value
        return res

    def _store_config_values(self, values):
        params = self.env['ir.config_parameter'].sudo()
        for key, value in values.items():
            stored_value = value
            if isinstance(value, bool):
                stored_value = 'True' if value else 'False'
            elif value in (None, False):
                stored_value = ''
            params.set_param(key, stored_value)

    def set_values(self):
        super().set_values()
        params = self.env['ir.config_parameter'].sudo()
        for field_name, (param_key, default_value) in self._SELECTION_PARAM_FIELDS.items():
            params.set_param(param_key, self._normalize_selection_value(field_name, getattr(self, field_name), default_value))
        for field_name, (param_key, _default_value) in self._TEXT_PARAM_FIELDS.items():
            params.set_param(param_key, getattr(self, field_name) or '')

    def _reload_settings(self):
        return {'type': 'ir.actions.client', 'tag': 'reload'}

    def action_import_github_configuration(self):
        self.ensure_one()
        github_service = GitHubService(self.env)
        details = github_service.discover_configuration(token=self.pg_github_token)
        github_service.sync_user_repositories(token=details.get('token'))
        values = {
            'pg_github_token': details.get('token') or '',
            'pg_github_default_owner': details.get('default_owner') or '',
            'pg_github_account_login': details.get('login') or '',
            'pg_github_account_name': details.get('name') or '',
        }
        if details.get('suggested_default_branch'):
            values['pg_github_default_branch'] = details['suggested_default_branch']

        self._store_config_values(values)
        return self._reload_settings()

    def action_sync_github_repositories(self):
        self.ensure_one()
        GitHubService(self.env).sync_user_repositories(token=self.pg_github_token)
        return self._reload_settings()

    def action_open_pg_ai_onboarding_wizard(self):
        self.ensure_one()
        action = self.env.ref('pg_brodoo.action_pg_ai_onboarding_wizard').read()[0]
        action.update({'target': 'new'})
        return action
