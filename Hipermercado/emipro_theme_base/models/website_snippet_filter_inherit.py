# -*- coding: utf-8 -*-
"""Website Snippet Filter Inheritance to Patch Decode Error on Sample Binary/Image Fields."""

from odoo import models, api


class WebsiteSnippetFilterInherit(models.Model):
    """Inherit website.snippet.filter to patch decode error on sample binary/image fields."""

    _inherit = 'website.snippet.filter'

    def _filter_records_to_values(self, records, **options):
        # Use super to get base values
        try:
            values = super()._filter_records_to_values(records, **options)
        except AttributeError:
            # Patch for decode error on sample binary/image fields
            model = self.env[self.model_name or options.get('res_model')]
            meta_data = self._get_filter_meta_data(model)
            values = []
            is_sample = options.get('is_sample')
            for record in records:
                data = {}
                for field_name, field_widget in meta_data.items():
                    field = model._fields.get(field_name)
                    if field and field.type in ('binary', 'image'):
                        value = record[field_name] if field_name in record else None
                        if is_sample:
                            if isinstance(value, bytes):
                                try:
                                    data[field_name] = value.decode('utf8')
                                except Exception:
                                    data[field_name] = '/web/image'
                            else:
                                data[field_name] = '/web/image'
                        else:
                            data[field_name] = self.env['website'].image_url(record, field_name)
                    else:
                        try:
                            data[field_name] = record[field_name]
                        except Exception:
                            data[field_name] = None
                data['call_to_action_url'] = 'website_url' in record and record['website_url']
                data['_record'] = record
                values.append(data)
        return values


    @api.model
    def _prepare_category_list_data(self, parent_id=None):
        res = super()._prepare_category_list_data(parent_id=parent_id)

        # Add products count to each dict
        for cat_dict in res:
            cat_id = cat_dict['id']
            product_count = self.env['product.template'].sudo().search_count([
                ('public_categ_ids', 'in', [cat_id]),
                ('website_published', '=', True),
            ])
            cat_dict['product_count'] = product_count
        return res

