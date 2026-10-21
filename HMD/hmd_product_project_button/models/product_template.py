# -*- coding: utf-8 -*-

from ast import literal_eval

from odoo import _, fields, models


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    project_usage_count = fields.Integer(
        string='Projetos',
        compute='_compute_project_usage_count',
        compute_sudo=True,
        readonly=True,
    )

    def _compute_project_usage_count(self):
        if not self.ids or 'project.project' not in self.env:
            for template in self:
                template.project_usage_count = 0
            return
        variants = self.mapped('product_variant_ids')
        projects_by_product = self.env['product.product']._map_product_to_project_ids(variants.ids)
        for template in self:
            project_ids = set()
            for variant in template.product_variant_ids:
                project_ids |= projects_by_product.get(variant.id, set())
            template.project_usage_count = len(project_ids)

    def action_view_related_projects(self):
        self.ensure_one()
        variants = self.product_variant_ids
        project_ids = set()
        if variants:
            projects_by_product = self.env['product.product']._map_product_to_project_ids(variants.ids)
            for variant in variants:
                project_ids |= projects_by_product.get(variant.id, set())
        project_ids = list(project_ids)
        action = self.env['ir.actions.actions']._for_xml_id('project.open_view_project_all')
        if project_ids:
            action['domain'] = [('id', 'in', project_ids)]
        else:
            action['domain'] = [('id', '=', False)]
        action['name'] = _('Projetos')
        context = action.get('context')
        if isinstance(context, str):
            context = literal_eval(context)
        sanitized_context = dict(context or {})
        for key in list(sanitized_context):
            if key.startswith('search_default_'):
                sanitized_context.pop(key, None)
        action['context'] = sanitized_context
        return action
