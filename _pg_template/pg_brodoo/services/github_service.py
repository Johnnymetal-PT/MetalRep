import base64
import logging
import os
import time
from collections import Counter
from urllib.parse import quote

import requests

from odoo import _
from odoo.exceptions import UserError
from odoo.fields import Datetime

_logger = logging.getLogger(__name__)


REPOSITORY_SORT_OPTIONS = {'updated', 'full_name', 'created', 'pushed'}


class GitHubApiError(UserError):
    """UserError com o status HTTP do GitHub, para permitir decidir retries.

    status_code=None significa falha de rede/timeout (sem resposta HTTP).
    """

    def __init__(self, message, status_code=None):
        super().__init__(message)
        self.status_code = status_code


class GitHubService:
    API_URL = 'https://api.github.com'
    DEFAULT_TIMEOUT = 60
    API_VERSION = '2026-03-10'
    PAGE_SIZE = 100
    DEFAULT_REPOSITORY_SORT = 'updated'
    DEFAULT_BRANCH = 'main'

    def __init__(self, env):
        self.env = env
        self.params = env['ir.config_parameter'].sudo()

    def _get_param(self, key, default=None):
        return self.params.get_param(key, default)

    def _get_timeout(self):
        value = self._get_param('pg_github_timeout', self.DEFAULT_TIMEOUT)
        try:
            return max(int(value), 1)
        except (TypeError, ValueError):
            return self.DEFAULT_TIMEOUT

    def _get_repository_sort(self):
        repository_sort = (
            self._get_param('pg_github_repository_sort', self.DEFAULT_REPOSITORY_SORT)
            or self.DEFAULT_REPOSITORY_SORT
        ).strip()
        if repository_sort not in REPOSITORY_SORT_OPTIONS:
            return self.DEFAULT_REPOSITORY_SORT
        return repository_sort

    def _get_default_branch(self):
        return (self._get_param('pg_github_default_branch', self.DEFAULT_BRANCH) or self.DEFAULT_BRANCH).strip()

    def should_autosync_on_search(self):
        value = self._get_param('pg_github_autosync_on_search', 'True')
        return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}

    def should_push_directly_to_selected_branch(self):
        value = self._get_param('pg_ai_push_direct_to_selected_branch', 'True')
        return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}

    def _get_environment_token(self):
        for key in ('PG_GITHUB_TOKEN', 'GITHUB_TOKEN', 'GH_TOKEN'):
            value = (os.environ.get(key) or '').strip()
            if value:
                return value
        return ''

    def _get_resolved_token(self, token=None):
        resolved_token = (
            (token or '').strip()
            or (self._get_param('pg_github_token') or '').strip()
            or self._get_environment_token()
        )
        if not resolved_token:
            raise UserError(_("Configuracao em falta: GitHub Token."))
        return resolved_token

    def _build_headers(self, token=None):
        resolved_token = self._get_resolved_token(token)
        return {
            'Accept': 'application/vnd.github+json',
            'Authorization': f'Bearer {resolved_token}',
            'X-GitHub-Api-Version': self.API_VERSION,
        }

    def _request(self, method, endpoint, token=None, allow_not_found=False, **kwargs):
        try:
            response = requests.request(
                method,
                f'{self.API_URL}{endpoint}',
                headers=self._build_headers(token=token),
                timeout=self._get_timeout(),
                **kwargs,
            )
            if response.status_code == 404 and allow_not_found:
                return False
            if response.status_code >= 400:
                details = response.text
                try:
                    details = response.json().get('message') or details
                except ValueError:
                    pass
                raise GitHubApiError(
                    _("GitHub API devolveu erro em %s: %s") % (endpoint, details),
                    status_code=response.status_code,
                )
            if response.content:
                return response.json()
            return {}
        except requests.exceptions.RequestException as exc:
            _logger.exception("GitHub request failed: %s %s", method, endpoint)
            raise GitHubApiError(_("Falha na comunicacao com GitHub: %s") % exc) from exc

    def _paginate(self, endpoint, token=None, params=None):
        current_page = 1
        records = []
        params = dict(params or {})
        while True:
            payload = self._request(
                'GET',
                endpoint,
                token=token,
                params={**params, 'per_page': self.PAGE_SIZE, 'page': current_page},
            )
            if not payload:
                break
            records.extend(payload)
            if len(payload) < self.PAGE_SIZE:
                break
            current_page += 1
        return records

    def discover_configuration(self, token=None):
        resolved_token = self._get_resolved_token(token)
        user_data = self._request('GET', '/user', token=resolved_token)
        repos = self._paginate('/user/repos', token=resolved_token, params={'sort': self._get_repository_sort()})
        branch_counter = Counter(
            repo.get('default_branch')
            for repo in repos
            if (repo.get('default_branch') or '').strip()
        )
        suggested_default_branch = ''
        if branch_counter:
            suggested_default_branch = branch_counter.most_common(1)[0][0]

        return {
            'token': resolved_token,
            'login': (user_data.get('login') or '').strip(),
            'name': (user_data.get('name') or '').strip(),
            'default_owner': (user_data.get('login') or '').strip(),
            'suggested_default_branch': suggested_default_branch,
            'public_repos': user_data.get('public_repos') or 0,
            'private_repos': user_data.get('total_private_repos') or 0,
        }

    def list_user_repositories(self, token=None):
        return self._paginate('/user/repos', token=token, params={'sort': self._get_repository_sort()})

    def list_repository_branches(self, repository, token=None):
        return self._paginate(f'/repos/{repository.github_owner}/{repository.github_repo}/branches', token=token)

    def sync_user_repositories(self, token=None):
        repositories = self.list_user_repositories(token=token)
        repository_model = self.env['pg.ai.repository'].sudo()
        synced_records = repository_model.browse()
        # Include archived records: the unique (github_owner, github_repo)
        # constraint applies regardless of `active`, so a stale row still blocks
        # a resync even when inactive.
        all_records = repository_model.with_context(active_test=False).search([])
        existing_by_github_id = {
            record.github_id: record
            for record in all_records if record.github_id
        }
        existing_by_owner_repo = {
            (record.github_owner, record.github_repo): record
            for record in all_records if record.github_owner and record.github_repo
        }
        existing_by_full_name = {
            record.full_name: record
            for record in all_records if record.full_name
        }
        # GitHub ids returned in this sync; used to tell a genuinely stale row
        # apart from a live repo that merely appears later in the loop.
        incoming_github_ids = {repo_data.get('id') for repo_data in repositories if repo_data.get('id')}
        sync_time = Datetime.now()

        for repo_data in repositories:
            owner_data = repo_data.get('owner') or {}
            github_id = repo_data.get('id')
            owner = self._repository_model_normalize(owner_data.get('login'))
            repo = self._repository_model_normalize(repo_data.get('name'))
            full_name = (repo_data.get('full_name') or '').strip()
            values = {
                'name': (repo_data.get('name') or '').strip(),
                'github_id': github_id,
                'full_name': full_name,
                'github_owner': owner,
                'github_repo': repo,
                'default_branch': (repo_data.get('default_branch') or '').strip() or self._get_default_branch(),
                'visibility': (repo_data.get('visibility') or 'private').strip(),
                'is_private': bool(repo_data.get('private')),
                'last_sync_at': sync_time,
                'active': True,
            }
            # Identity is the github_id (stable across transfers/renames); fall
            # back to the unique (owner, repo) key and finally to full_name.
            record = (
                existing_by_github_id.get(github_id)
                or existing_by_owner_repo.get((owner, repo))
                or existing_by_full_name.get(full_name)
            )

            # A repository transferred between accounts keeps its github_id, so
            # the matched record may need to move onto an (owner, repo) key still
            # held by a different, stale row. Detach that row first, otherwise the
            # unique constraint aborts the whole sync.
            conflicting = existing_by_owner_repo.get((owner, repo))
            if (
                conflicting
                and conflicting != record
                and conflicting.github_id not in incoming_github_ids
            ):
                self._merge_stale_repository(conflicting, record or repository_model)
                existing_by_owner_repo.pop((owner, repo), None)
                if conflicting.github_id:
                    existing_by_github_id.pop(conflicting.github_id, None)
                if conflicting.full_name:
                    existing_by_full_name.pop(conflicting.full_name, None)

            if record:
                record.write(values)
            else:
                record = repository_model.create(values)

            # Keep the lookup maps coherent for the remaining iterations.
            if github_id:
                existing_by_github_id[github_id] = record
            existing_by_owner_repo[(owner, repo)] = record
            if full_name:
                existing_by_full_name[full_name] = record
            synced_records |= record

        return synced_records.sorted(key=lambda repo: (repo.github_owner.lower(), repo.github_repo.lower()))

    def _repository_model_normalize(self, value):
        return self.env['pg.ai.repository']._normalize_git_value(value)

    def _merge_stale_repository(self, stale, canonical):
        """Detach a stale repository row whose (owner, repo) key is now owned by
        another record (typically after a GitHub transfer that preserves the
        github_id). Project/task links and adoption configuration are migrated to
        the surviving record before the stale row is removed, so the unique
        constraint on (github_owner, github_repo) no longer blocks the resync."""
        if not stale or stale == canonical:
            return
        env = self.env
        if canonical:
            env['project.project'].sudo().search(
                [('pg_repository_id', '=', stale.id)]
            ).write({'pg_repository_id': canonical.id})
            env['project.task'].sudo().search(
                [('ai_repo_id', '=', stale.id)]
            ).write({'ai_repo_id': canonical.id})
            # Reparent Odoo connections to the surviving record (else they would be
            # cascade-deleted when the stale record is unlinked below). Skip any
            # purpose already present on the canonical record (unique constraint).
            canonical_purposes = set(canonical.odoo_connection_ids.mapped('purpose'))
            stale.odoo_connection_ids.filtered(
                lambda connection: connection.purpose not in canonical_purposes
            ).sudo().write({'repository_id': canonical.id})
            _logger.info(
                "Merged stale AI repository %s (%s) into %s (%s) during sync.",
                stale.id, stale.full_name, canonical.id, canonical.full_name,
            )
        # unlink() flushes immediately, so the DELETE runs before the surviving
        # record's UPDATE takes the freed (owner, repo) key.
        stale.unlink()

    def sync_repository_branches(self, repository, token=None):
        branch_model = self.env['pg.ai.repository.branch'].sudo()
        branches = self.list_repository_branches(repository, token=token)
        existing = {branch.name: branch for branch in repository.branch_ids}
        current_names = set()
        sync_time = Datetime.now()
        synced_branches = branch_model.browse()

        for branch_data in branches:
            branch_name = (branch_data.get('name') or '').strip()
            if not branch_name:
                continue
            current_names.add(branch_name)
            values = {
                'repository_id': repository.id,
                'name': branch_name,
                'is_default': branch_name == repository.default_branch,
                'last_sync_at': sync_time,
            }
            branch_record = existing.get(branch_name)
            if branch_record:
                branch_record.write(values)
            else:
                branch_record = branch_model.create(values)
            synced_branches |= branch_record

        stale_branches = repository.branch_ids.filtered(lambda branch: branch.name not in current_names)
        if stale_branches:
            stale_branches.unlink()

        if repository.default_branch and not synced_branches.filtered(lambda branch: branch.name == repository.default_branch):
            synced_branches |= branch_model.create(
                {
                    'repository_id': repository.id,
                    'name': repository.default_branch,
                    'is_default': True,
                    'last_sync_at': sync_time,
                }
            )

        return synced_branches.sorted(key=lambda branch: (not branch.is_default, branch.name.lower()))

    def get_repository_file(self, repository, path, branch=None, token=None):
        owner, repo, resolved_branch = self._get_repository_coordinates(repository, base_branch=branch)
        quoted_path = quote((path or '').lstrip('/'), safe='')
        return self._request(
            'GET',
            f'/repos/{owner}/{repo}/contents/{quoted_path}',
            token=token,
            allow_not_found=True,
            params={'ref': resolved_branch},
        )

    def get_repository_file_text(self, repository, path, branch=None, token=None):
        file_data = self.get_repository_file(repository, path, branch=branch, token=token)
        if not file_data:
            return ''
        if (file_data.get('type') or '').strip() != 'file':
            return ''

        content = file_data.get('content') or ''
        encoding = (file_data.get('encoding') or 'base64').strip().lower()
        if not content:
            return ''
        if encoding == 'base64':
            normalized_content = ''.join(str(content).splitlines())
            return base64.b64decode(normalized_content).decode('utf-8')
        return str(content)

    def upsert_repository_file(self, repository, path, content, message, branch=None, token=None, max_attempts=3):
        owner, repo, resolved_branch = self._get_repository_coordinates(repository, base_branch=branch)
        quoted_path = quote((path or '').lstrip('/'), safe='')
        encoded_content = base64.b64encode((content or '').encode('utf-8')).decode('ascii')

        last_error = None
        for attempt in range(1, max_attempts + 1):
            # O sha e refrescado a CADA tentativa: um 409/422 "does not match"
            # significa que o ficheiro mudou entre o GET e o PUT (escrita
            # concorrente ao mesmo artefacto); repetir com o sha antigo falha sempre.
            existing_file = self.get_repository_file(repository, path, branch=resolved_branch, token=token)
            payload = {
                'message': message,
                'content': encoded_content,
                'branch': resolved_branch,
            }
            if existing_file and existing_file.get('sha'):
                payload['sha'] = existing_file['sha']

            try:
                return self._request('PUT', f'/repos/{owner}/{repo}/contents/{quoted_path}', token=token, json=payload)
            except GitHubApiError as exc:
                last_error = exc
                if attempt >= max_attempts or not self._is_retryable_upsert_error(exc):
                    raise
                _logger.warning(
                    "Upsert de %s em %s/%s falhou (tentativa %s/%s, status %s); a repetir com sha refrescado.",
                    path, owner, repo, attempt, max_attempts, exc.status_code,
                )
                time.sleep(attempt)
        raise last_error

    @staticmethod
    def _is_retryable_upsert_error(exc):
        status = getattr(exc, 'status_code', None)
        if status is None:
            # Falha de rede/timeout sem resposta HTTP.
            return True
        if status >= 500:
            return True
        # Conflito de sha por escrita concorrente (GitHub devolve 409 ou 422).
        return status in (409, 422) and 'does not match' in str(exc)

    def _get_repository_coordinates(self, repository, base_branch=None):
        owner = (repository.github_owner or self._get_param('pg_github_default_owner') or '').strip()
        repo = (repository.github_repo or '').strip()
        resolved_base_branch = (base_branch or repository.default_branch or self._get_default_branch()).strip()
        if not owner or not repo:
            raise UserError(_("O repositorio AI tem de ter owner e repository GitHub configurados."))
        return owner, repo, resolved_base_branch

    def should_create_pull_request(self):
        if self.should_push_directly_to_selected_branch():
            return False
        value = self._get_param('pg_github_create_pr_by_default', 'True')
        return str(value).strip().lower() in {'1', 'true', 'yes', 'on'}

    def get_branch_sha(self, repository, branch_name):
        owner, repo, _base_branch = self._get_repository_coordinates(repository)
        ref_data = self._request('GET', f'/repos/{owner}/{repo}/git/ref/heads/{branch_name}')
        return ref_data.get('object', {}).get('sha')

    def branch_exists(self, repository, branch_name):
        """True se a branch existir no repo. Nao levanta em 404 (usa allow_not_found)."""
        if not (branch_name or '').strip():
            return False
        owner, repo, _base_branch = self._get_repository_coordinates(repository)
        ref_data = self._request(
            'GET',
            f'/repos/{owner}/{repo}/git/ref/heads/{branch_name}',
            allow_not_found=True,
        )
        return bool(ref_data and ref_data.get('object', {}).get('sha'))

    def create_branch(self, repository, branch_name, base_branch=None):
        owner, repo, default_branch = self._get_repository_coordinates(repository, base_branch=base_branch)
        source_branch = (base_branch or default_branch).strip()
        sha = self.get_branch_sha(repository, source_branch)
        if not sha:
            raise UserError(_("Nao foi possivel obter o SHA da branch base %s.") % source_branch)
        payload = {'ref': f'refs/heads/{branch_name}', 'sha': sha}
        return self._request('POST', f'/repos/{owner}/{repo}/git/refs', json=payload)

    def create_commit(self, repository, message, tree_sha, parent_shas):
        owner, repo, _base_branch = self._get_repository_coordinates(repository)
        payload = {
            'message': message,
            'tree': tree_sha,
            'parents': parent_shas,
        }
        return self._request('POST', f'/repos/{owner}/{repo}/git/commits', json=payload)

    def find_open_pull_request(self, repository, branch_name):
        owner, repo, _base_branch = self._get_repository_coordinates(repository)
        payload = self._request(
            'GET',
            f'/repos/{owner}/{repo}/pulls?state=open&head={owner}:{branch_name}',
        )
        return payload[0] if payload else False

    def create_pull_request(self, repository, branch_name, title, body, base_branch=None):
        owner, repo, resolved_base_branch = self._get_repository_coordinates(repository, base_branch=base_branch)
        payload = {
            'title': title,
            'head': branch_name,
            'base': resolved_base_branch,
            'body': body,
            'maintainer_can_modify': True,
        }

        try:
            return self._request('POST', f'/repos/{owner}/{repo}/pulls', json=payload)
        except UserError as exc:
            if 'A pull request already exists' not in str(exc):
                raise
            existing_pr = self.find_open_pull_request(repository, branch_name)
            if existing_pr:
                return existing_pr
            raise

    # --- GitHub Actions secrets & variables -------------------------------

    def get_actions_public_key(self, repository, token=None):
        owner, repo, _base_branch = self._get_repository_coordinates(repository)
        return self._request(
            'GET',
            f'/repos/{owner}/{repo}/actions/secrets/public-key',
            token=token,
        )

    def _encrypt_actions_secret(self, public_key_b64, secret_value):
        """Cifra o valor com a public key do repo (libsodium sealed box).

        A API de secrets do GitHub exige sealed box; ver
        https://docs.github.com/rest/actions/secrets#create-or-update-a-repository-secret
        """
        try:
            from nacl import encoding, public
        except ImportError as exc:  # pragma: no cover - depende do runtime
            raise UserError(_(
                "Dependencia em falta: PyNaCl (nacl) e necessario para cifrar "
                "GitHub Actions secrets. Instale 'pynacl' no ambiente do Odoo."
            )) from exc

        public_key = public.PublicKey(
            (public_key_b64 or '').encode('utf-8'), encoding.Base64Encoder()
        )
        sealed_box = public.SealedBox(public_key)
        encrypted = sealed_box.encrypt((secret_value or '').encode('utf-8'))
        return base64.b64encode(encrypted).decode('utf-8')

    def set_actions_secret(self, repository, name, value, token=None):
        owner, repo, _base_branch = self._get_repository_coordinates(repository)
        key_data = self.get_actions_public_key(repository, token=token)
        if not key_data or not key_data.get('key') or not key_data.get('key_id'):
            raise UserError(_("Nao foi possivel obter a public key de secrets do repositorio %s/%s.") % (owner, repo))
        payload = {
            'encrypted_value': self._encrypt_actions_secret(key_data['key'], value),
            'key_id': key_data['key_id'],
        }
        # 201 (criado) ou 204 (atualizado) -> corpo vazio
        return self._request(
            'PUT',
            f'/repos/{owner}/{repo}/actions/secrets/{quote(name, safe="")}',
            token=token,
            json=payload,
        )

    def set_actions_variable(self, repository, name, value, token=None):
        owner, repo, _base_branch = self._get_repository_coordinates(repository)
        quoted_name = quote(name, safe='')
        existing = self._request(
            'GET',
            f'/repos/{owner}/{repo}/actions/variables/{quoted_name}',
            token=token,
            allow_not_found=True,
        )
        if existing:
            return self._request(
                'PATCH',
                f'/repos/{owner}/{repo}/actions/variables/{quoted_name}',
                token=token,
                json={'name': name, 'value': value or ''},
            )
        return self._request(
            'POST',
            f'/repos/{owner}/{repo}/actions/variables',
            token=token,
            json={'name': name, 'value': value or ''},
        )
