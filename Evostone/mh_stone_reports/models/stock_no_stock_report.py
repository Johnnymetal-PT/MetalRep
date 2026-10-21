from collections import defaultdict

from odoo import api, fields, models


DEFAULT_PAGE_SIZE = 100


class StockNoStockReport(models.AbstractModel):
    _name = 'report.mh_stone_reports.report_stock_no_stock'
    _description = 'Relatório de Artigos sem Stock'

    def _get_report_values(self, docids, data):
        return self._get_report_data(data or {}, 'pdf')

    @api.model
    def get_html(self, data):
        render_values = self._get_report_data(data or {}, 'html')
        html = self.env['ir.qweb']._render(
            'mh_stone_reports.report_stock_no_stock_page',
            render_values,
        )
        return {
            'html': html,
            'total_products': render_values['total_products'],
            'total_groups': len(render_values['groups']),
            'page_size': render_values['page_size'],
        }

    def _get_report_data(self, data, report_type='html'):
        company = self.env.company

        classifications_raw = data.get('classifications') or data.get('classification') or ''
        if isinstance(classifications_raw, list):
            classifications = [c for c in classifications_raw if c]
        else:
            classifications = [c.strip() for c in str(classifications_raw).split(',') if c.strip()]

        classification_sel = dict(self.env['product.template']._fields['product_classification'].selection)
        classifications_labels = [classification_sel.get(c, c) for c in classifications]
        classifications_label = ', '.join(classifications_labels) if classifications_labels else 'Todas'

        supplier_id = data.get('supplier_id')
        supplier_id = supplier_id and int(supplier_id)
        supplier = (
            self.env['res.partner'].browse(supplier_id).exists()
            if supplier_id else False
        )

        warehouse_id = data.get('warehouse_id')
        warehouse_id = warehouse_id and int(warehouse_id)
        warehouse = (
            self.env['stock.warehouse'].browse(warehouse_id).exists()
            if warehouse_id else False
        )

        domain = [
            ('type', '=', 'consu'),
            ('is_storable', '=', True),
            ('active', '=', True),
        ]
        if classifications:
            domain.append(('product_tmpl_id.product_classification', 'in', classifications))

        product_ctx = {}
        if warehouse:
            product_ctx['warehouse'] = warehouse.id

        products = self.env['product.product'].with_context(**product_ctx).search(domain)

        if supplier:
            products = products.filtered(
                lambda p: supplier.id in p.seller_ids.mapped('partner_id').ids
            )

        products = products.filtered(lambda p: (p.qty_available or 0.0) <= 0)

        groups_map = defaultdict(list)
        for p in products:
            last_seller = p.seller_ids[:1]
            classification_value = p.product_tmpl_id.product_classification or ''
            row = {
                'product_id': p.id,
                'product_name': p.display_name,
                'classification_value': classification_value,
                'classification_name': classification_sel.get(classification_value, '— Sem Classificação —'),
                'uom': p.uom_id.name or '',
                'qty_available': p.qty_available or 0.0,
                'last_supplier_id': last_seller.partner_id.id if last_seller else False,
                'last_supplier_name': last_seller.partner_id.display_name if last_seller else '',
                'last_cost': last_seller.price if last_seller else 0.0,
            }
            groups_map[classification_value].append(row)

        page_size = int(data.get('page_size') or DEFAULT_PAGE_SIZE)

        groups = []
        total_products = 0
        for class_value, rows_list in groups_map.items():
            rows_list.sort(key=lambda r: r['product_name'])
            count = len(rows_list)
            total_pages = max(1, (count + page_size - 1) // page_size)
            groups.append({
                'classification_value': class_value,
                'classification_name': classification_sel.get(class_value, '— Sem Classificação —'),
                'rows': rows_list,
                'count': count,
                'total_pages': total_pages,
            })
            total_products += count

        groups.sort(key=lambda g: g['classification_name'])

        return {
            'is_html_type': report_type == 'html',
            'classifications': classifications,
            'classifications_label': classifications_label,
            'supplier': supplier,
            'supplier_label': supplier.display_name if supplier else 'Todos',
            'warehouse': warehouse,
            'warehouse_label': warehouse.display_name if warehouse else 'Todos',
            'groups': groups,
            'total_products': total_products,
            'page_size': page_size,
            'currency': company.currency_id,
            'company': company,
            'report_date': fields.Datetime.context_timestamp(self, fields.Datetime.now()),
            'title': 'Artigos sem Stock',
            'docs': [company],
        }
