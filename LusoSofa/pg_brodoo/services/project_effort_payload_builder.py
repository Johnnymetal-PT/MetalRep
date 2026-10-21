import hashlib
import json
from collections import defaultdict

from odoo import fields
from odoo.exceptions import ValidationError

from .text_hygiene import normalize_inline_text


class ProjectEffortPayloadBuilder:
    def __init__(self, env):
        self.env = env
        self.params = env['ir.config_parameter'].sudo()

    def _get_base_url(self):
        return (self.params.get_param('web.base.url') or '').strip().rstrip('/')

    def _normalize_text(self, value, fallback='', max_chars=False):
        return normalize_inline_text(value, fallback=fallback, max_chars=max_chars, drop_placeholders=True)

    def _build_record_url(self, model_name, record_id):
        base_url = self._get_base_url()
        if not base_url or not model_name or not record_id:
            return None
        return f"{base_url}/web#id={record_id}&model={model_name}"

    def _source_record_url(self, project, trigger_model, trigger_record_id):
        if trigger_model and trigger_record_id:
            source_url = self._build_record_url(trigger_model, trigger_record_id)
            if source_url:
                return source_url
        return self._build_record_url('project.project', project.id)

    def _timesheet_domain(self, project):
        return [('project_id', '=', project.id)]

    def _timesheet_lines(self, project):
        if 'account.analytic.line' not in self.env:
            return self.env['project.task']
        return self.env['account.analytic.line'].search(
            self._timesheet_domain(project),
            order='date asc, id asc',
        )

    def _line_to_payload(self, line):
        employee_name = self._normalize_text(
            getattr(line, 'employee_id', False).name if getattr(line, 'employee_id', False) else '',
            fallback='Unknown',
        )
        return {
            'timesheet_line_id': line.id,
            'date': fields.Date.to_string(line.date) if line.date else None,
            'employee': employee_name,
            'task_id': line.task_id.id if line.task_id else None,
            'task_name': self._normalize_text(line.task_id.name if line.task_id else '', fallback=''),
            'hours': float(line.unit_amount or 0.0),
            'description': self._normalize_text(line.name, fallback=''),
        }

    def build_payload(self, project, trigger_type='manual_button', trigger_model='project.project', trigger_record_id=None):
        project.ensure_one()
        lines = self._timesheet_lines(project)
        entries = [self._line_to_payload(line) for line in lines]

        total_hours = sum(entry['hours'] for entry in entries)
        by_employee = defaultdict(float)
        for entry in entries:
            by_employee[entry['employee']] += entry['hours']

        sync_published_at = fields.Datetime.now()
        payload = {
            'schema_version': '1.0',
            'project_name': self._normalize_text(project.name, fallback='Project'),
            'project_id': project.id,
            'effort': {
                'timesheet_line_count': len(entries),
                'total_hours': float(total_hours),
                'hours_by_employee': [
                    {'employee': employee, 'hours': float(hours)}
                    for employee, hours in sorted(by_employee.items(), key=lambda item: item[0].lower())
                ],
                'entries': entries,
            },
            'source_metadata': {
                'source_system': 'odoo_parametro_global',
                'source_model': trigger_model or 'project.project',
                'source_record_id': trigger_record_id or project.id,
                'source_record_url': self._source_record_url(project, trigger_model, trigger_record_id or project.id),
                'sync_trigger': trigger_type or 'manual_button',
                'sync_published_at': fields.Datetime.to_string(sync_published_at),
                'sync_published_by': self.env.user.display_name or 'Odoo',
                'repo_branch': (project.pg_repo_branch or '').strip(),
                'payload_hash': '',
            },
        }
        self.validate_payload(payload)
        return payload

    def validate_payload(self, payload):
        if not isinstance(payload, dict):
            raise ValidationError("PG_EFFORT_SYNC payload must be an object.")
        if not isinstance(payload.get('effort'), dict):
            raise ValidationError("PG_EFFORT_SYNC payload requires effort object.")
        if not isinstance(payload['effort'].get('entries'), list):
            raise ValidationError("PG_EFFORT_SYNC payload requires effort.entries array.")
        return payload

    def build_hashable_payload(self, payload):
        hashable_payload = json.loads(json.dumps(payload))
        source_metadata = hashable_payload.get('source_metadata') or {}
        for key in ('sync_trigger', 'sync_published_at', 'sync_published_by', 'payload_hash'):
            source_metadata[key] = ''
        hashable_payload['source_metadata'] = source_metadata
        return hashable_payload

    def serialize_payload(self, payload):
        return json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + '\n'

    def payload_hash(self, payload):
        self.validate_payload(payload)
        serialized = self.serialize_payload(self.build_hashable_payload(payload))
        return f"sha256:{hashlib.sha256(serialized.encode('utf-8')).hexdigest()}"
