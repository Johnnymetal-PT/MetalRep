# -*- coding: utf-8 -*-

from ast import literal_eval
from collections import defaultdict
import logging
from textwrap import dedent

from odoo import _, api, fields, models
from odoo.osv import expression


_logger = logging.getLogger(__name__)


SERVER_ACTION_TEMPLATE_CODE = dedent(
    """
    ctx = env.context
    active_ids = ctx.get('active_ids') or []
    if not active_ids and ctx.get('active_id'):
        active_ids = [ctx['active_id']]
    recordset = records
    if not recordset:
        model_name = ctx.get('active_model')
        if model_name == 'product.template':
            recordset = env['product.template'].browse(active_ids)
        elif model_name == 'product.product':
            recordset = env['product.product'].browse(active_ids).product_tmpl_id
        else:
            recordset = env['product.template'].browse(active_ids)
    recordset = recordset.exists()[:1]
    action = recordset.action_view_related_projects() if recordset else {'type': 'ir.actions.act_window_close'}
    """
)


SERVER_ACTION_PRODUCT_CODE = dedent(
    """
    ctx = env.context
    active_ids = ctx.get('active_ids') or []
    if not active_ids and ctx.get('active_id'):
        active_ids = [ctx['active_id']]
    recordset = records
    if not recordset:
        model_name = ctx.get('active_model')
        if model_name == 'product.product':
            recordset = env['product.product'].browse(active_ids)
        elif model_name == 'product.template':
            recordset = env['product.template'].browse(active_ids).product_variant_ids
        else:
            recordset = env['product.product'].browse(active_ids)
    recordset = recordset.exists()[:1]
    if recordset and recordset._name == 'product.template':
        recordset = recordset.product_variant_ids.exists()[:1]
    action = recordset.action_view_related_projects() if recordset else {'type': 'ir.actions.act_window_close'}
    """
)


class ProductProduct(models.Model):
    _inherit = 'product.product'

    project_variant_usage_count = fields.Integer(
        string='Projetos',
        compute='_compute_project_variant_usage_count',
        compute_sudo=True,
        readonly=True,
    )

    def _compute_project_variant_usage_count(self):
        if not self.ids or 'project.project' not in self.env:
            for product in self:
                product.project_variant_usage_count = 0
            return
        projects_by_product = self._map_product_to_project_ids(self.ids)
        for product in self:
            project_ids = projects_by_product.get(product.id, set())
            product.project_variant_usage_count = len(project_ids)

    @api.model
    def _map_product_to_project_ids(self, product_ids):
        self._ensure_project_server_actions()
        _logger.info('Mapping product IDs to projects: %s', product_ids)
        project_ids_by_product = defaultdict(set)
        if not product_ids:
            _logger.info('No product IDs provided to project mapping.')
            return project_ids_by_product
        if 'project.project' not in self.env:
            _logger.info(
                'Project app not installed, skipping project mapping for products: %s',
                product_ids,
            )
            return project_ids_by_product

        self = self.sudo()
        product_ids_list = [pid for pid in product_ids if isinstance(pid, int)]
        if not product_ids_list:
            _logger.info('No valid integer product IDs after sanitising input: %s', product_ids)
            return project_ids_by_product

        products = self.browse(product_ids_list).exists()
        if not products:
            _logger.info('No product records found for IDs: %s', product_ids_list)
            return project_ids_by_product

        product_id_set = set(products.ids)
        template_to_products = defaultdict(set)
        for product in products:
            if product.product_tmpl_id:
                template_to_products[product.product_tmpl_id.id].add(product.id)
        template_ids = list(template_to_products.keys())
        _logger.info(
            'Project mapping search context: product_ids=%s template_ids=%s',
            sorted(product_id_set),
            sorted(template_ids),
        )

        def _as_id(value):
            if isinstance(value, (list, tuple)):
                return value[0] if value else False
            return value or False

        def _collect_from_lines(line_model_name, order_model_name, label):
            try:
                line_model = self.env[line_model_name]
            except KeyError:
                _logger.info('%s mapping skipped: missing line model %s.', label, line_model_name)
                return
            try:
                order_model = self.env[order_model_name]
            except KeyError:
                _logger.info('%s mapping skipped: missing order model %s.', label, order_model_name)
                return

            line_model = line_model.with_context(active_test=False).sudo()
            order_model = order_model.with_context(active_test=False).sudo()

            domain_terms = []
            if product_id_set:
                domain_terms.append([('product_id', 'in', list(product_id_set))])
            template_term = False
            if template_ids and 'product_template_id' in line_model._fields:
                template_term = ('product_template_id', 'in', template_ids)

            if template_term:
                domain_terms.append([template_term])

            if not domain_terms:
                _logger.info('%s mapping skipped: no domain terms for products/templates.', label)
                return

            domain = domain_terms[0]
            if len(domain_terms) > 1:
                domain = expression.OR(domain_terms)

            lines = line_model.search(domain)
            if not lines:
                _logger.info('%s mapping found no order lines for domain=%s', label, domain)
                return

            line_vals = lines.read(['product_id', 'product_template_id', 'order_id'])
            order_ids = {
                _as_id(vals.get('order_id'))
                for vals in line_vals
                if vals.get('order_id')
            }
            if not order_ids:
                _logger.info('%s mapping found no related orders from lines %s', label, lines.ids)
                return

            orders = order_model.browse(list(order_ids)).exists()
            order_projects = {
                order.id: order.project_id.id
                for order in orders
                if order.project_id
            }
            if not order_projects:
                _logger.info('%s mapping found no orders with project_id among %s', label, order_ids)
                return

            _logger.info(
                '%s mapping: %s lines, %s orders with project_id.',
                label,
                len(line_vals),
                len(order_projects),
            )

            for vals in line_vals:
                order_id = _as_id(vals.get('order_id'))
                project_id = order_projects.get(order_id)
                if not project_id:
                    continue
                product_bucket = set()
                product_value = _as_id(vals.get('product_id'))
                if product_value and product_value in product_id_set:
                    product_bucket.add(product_value)
                template_value = _as_id(vals.get('product_template_id'))
                if template_value and template_value in template_to_products:
                    product_bucket.update(template_to_products[template_value])
                if not product_bucket:
                    continue
                for product_id in product_bucket:
                    project_ids_by_product[product_id].add(project_id)

        _collect_from_lines('sale.order.line', 'sale.order', 'Sale order')
        _collect_from_lines('purchase.order.line', 'purchase.order', 'Purchase order')

        cleaned = defaultdict(set)
        for product_id, project_ids in project_ids_by_product.items():
            if project_ids:
                cleaned[product_id].update(project_ids)
                _logger.info(
                    'Aggregated project IDs for product %s: %s',
                    product_id,
                    sorted(project_ids),
                )

        return cleaned

    @api.model
    def _ensure_project_server_actions(self):
        """Guarantee the smart buttons reference an existing server action."""

        ir_actions_server = self.env['ir.actions.server'].sudo()
        ir_model_data = self.env['ir.model.data'].sudo()

        def _ensure(xml_id, model_name, code):
            module, name = xml_id.split('.')
            action = self.env.ref(xml_id, raise_if_not_found=False)
            model = self.env['ir.model']._get(model_name)
            if action and action.exists():
                missing_code = (action.code or '').strip() != code.strip()
                missing_model = action.model_id.id != model.id
                if missing_code or missing_model:
                    vals = {'code': code}
                    if missing_model:
                        vals['model_id'] = model.id
                    action.write(vals)
                return

            action = ir_actions_server.create(
                {
                    'name': 'Projetos',
                    'model_id': model.id,
                    'state': 'code',
                    'code': code,
                }
            )

            data = ir_model_data.search(
                [('module', '=', module), ('name', '=', name)],
                limit=1,
            )
            if data:
                data.write(
                    {
                        'model': 'ir.actions.server',
                        'res_id': action.id,
                        'noupdate': False,
                    }
                )
            else:
                ir_model_data.create(
                    {
                        'module': module,
                        'name': name,
                        'model': 'ir.actions.server',
                        'res_id': action.id,
                        'noupdate': False,
                    }
                )

        _ensure(
            'hmd_product_project_button.product_template_project_server_action',
            'product.template',
            SERVER_ACTION_TEMPLATE_CODE,
        )
        _ensure(
            'hmd_product_project_button.product_product_project_server_action',
            'product.product',
            SERVER_ACTION_PRODUCT_CODE,
        )

    def action_view_related_projects(self):
        self.ensure_one()
        project_ids = list(self._map_product_to_project_ids(self.ids).get(self.id, set()))
        action = self.env.ref('project.open_view_project_all').read()[0]
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
