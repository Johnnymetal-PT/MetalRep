from odoo import http
from odoo.exceptions import UserError
from odoo.http import request

from ..services.github_service import GitHubService


class PgAiDevAssistantConfigController(http.Controller):
    def _is_truthy(self, value):
        return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}

    def _serialize_repository(self, repository):
        return {
            'id': repository.id,
            'name': repository.name,
            'full_name': repository.full_name,
            'owner': repository.github_owner,
            'repo': repository.github_repo,
            'default_branch': repository.default_branch,
            'visibility': repository.visibility,
            'is_private': repository.is_private,
        }

    def _serialize_branch(self, branch):
        return {
            'id': branch.id,
            'name': branch.name,
            'is_default': branch.is_default,
            'repository_id': branch.repository_id.id,
        }

    @http.route('/pg_brodoo/config/github/discover', type='jsonrpc', auth='user')
    def github_discover(self, token=None):
        return GitHubService(request.env).discover_configuration(token=token)

    @http.route('/pg_brodoo/config/github/repositories', type='jsonrpc', auth='user')
    def github_repositories(self, refresh=False, token=None):
        github_service = GitHubService(request.env)
        repository_model = request.env['pg.ai.repository'].sudo()
        if self._is_truthy(refresh) or not repository_model.search_count([]):
            repositories = github_service.sync_user_repositories(token=token)
        else:
            repositories = repository_model.search([], order='github_owner, github_repo')
        return {'repositories': [self._serialize_repository(repository) for repository in repositories]}

    @http.route('/pg_brodoo/config/github/branches', type='jsonrpc', auth='user')
    def github_branches(self, repository_id=None, refresh=False, token=None):
        if not repository_id:
            raise UserError('repository_id is required.')
        repository = request.env['pg.ai.repository'].sudo().browse(int(repository_id)).exists()
        if not repository:
            raise UserError('Repository not found.')
        if self._is_truthy(refresh) or not repository.branch_ids:
            branches = GitHubService(request.env).sync_repository_branches(repository, token=token)
        else:
            branches = repository.branch_ids.sorted(key=lambda branch: (not branch.is_default, branch.name.lower()))
        return {'branches': [self._serialize_branch(branch) for branch in branches]}

    @http.route('/pg_brodoo/config/bootstrap', type='jsonrpc', auth='user')
    def bootstrap(self, github_token=None, refresh_repositories=False):
        repository_model = request.env['pg.ai.repository'].sudo()
        payload = {}
        try:
            payload['github'] = GitHubService(request.env).discover_configuration(token=github_token)
        except UserError:
            payload['github'] = False

        if self._is_truthy(refresh_repositories) or not repository_model.search_count([]):
            try:
                repositories = GitHubService(request.env).sync_user_repositories(token=github_token)
            except UserError:
                repositories = repository_model.browse()
        else:
            repositories = repository_model.search([], order='github_owner, github_repo')
        payload['repositories'] = [self._serialize_repository(repository) for repository in repositories]
        return payload
