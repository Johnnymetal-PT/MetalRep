# -*- coding: utf-8 -*-
import json
import logging
from odoo import models, fields

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = "product.template"

    def get_variant_count(self):
        for rec in self:
            valid_combination_list = []
            attribute_ids = []
            attribute_display_types = {}
            unavailable_variant_view_type = []

            all_empty = False
            try:
                iterable = rec.with_context(special_call=True)._get_possible_combinations()
                first = next(iterable)
            except StopIteration:
                all_empty = True

            if all_empty:
                for v in rec._get_possible_combinations():
                    val = []
                    for value in v:
                        val.append(value.id)
                        if value.attribute_id.id not in attribute_ids:
                            attribute_ids.append(value.attribute_id.id)
                            attribute_display_types.update({value.attribute_id.id: value.attribute_id.display_type})
                            unavailable_variant_view_type.append(value.attribute_id.unavailable_value_view_type)
            else:
                for v in rec.with_context(special_call=True)._get_possible_combinations():
                    val = []
                    for value in v:
                        val.append(value.id)
                        if value.attribute_id.id not in attribute_ids:
                            attribute_ids.append(value.attribute_id.id)
                            attribute_display_types.update({value.attribute_id.id: value.attribute_id.display_type})
                            unavailable_variant_view_type.append(value.attribute_id.unavailable_value_view_type)
                    valid_combination_list.append(tuple(val))

            valid_comb = set(valid_combination_list)
            value_count_per_attr = []
            attribute_line_ids = self.attribute_line_ids
            if attribute_line_ids:
                for line in attribute_line_ids:
                    value_count_per_attr.append(len(line.value_ids))

            j = 0
            available_variant_values_ids = {}
            all_val = []
            for item in list(valid_comb):
                all_val.extend(list(item))
                available_variant_values_ids[j] = (list(item))
                j += 1
            all_val = list(set(all_val))

            variant_val_child_dict = {}
            for i in range(len(all_val)):
                all_child_items = []
                for item in list(valid_comb):
                    items = list(item)
                    try:
                        offset = items.index(all_val[i])
                    except ValueError:
                        offset = -1
                    if offset == -1:
                        continue
                    child_item = []
                    for j in range(offset, len(items)):
                        child_item.append(items[j])
                    all_child_items.extend(child_item)
                child_list = list(set(all_child_items))
                variant_val_child_dict[all_val[i]] = child_list

            unavailable_variant_dict = {
                "attribute_ids": attribute_ids,
                "attribute_display_types": attribute_display_types,
                "unavailable_variant_view_type": unavailable_variant_view_type,
                "value_to_show": variant_val_child_dict,
                "value_to_show_tuple": list(valid_comb),
                "value_count_per_attr": value_count_per_attr
            }
            return unavailable_variant_dict

    def _get_first_possible_combination(self, parent_combination=None, necessary_values=None):
        """Ensures a recordset is always returned, never None"""
        empty_ptav = self.env['product.template.attribute.value']
        no_variant_attr_val = empty_ptav

        for combination in self._get_possible_combinations(parent_combination, necessary_values):
            filtered_combination = combination.filtered(lambda ptav: ptav.attribute_id.create_variant != 'no_variant')
            variant_id = self._get_variant_for_combination(filtered_combination)
            if variant_id and not variant_id.hide_on_website:
                return combination
        return empty_ptav

    def _is_combination_possible(self, combination, parent_combination=None, ignore_no_variant=False):
        result = super(ProductTemplate, self)._is_combination_possible(combination, parent_combination, ignore_no_variant)
        if result and self._context.get("special_call"):
            no_variant_attr_val = self.env['product.template.attribute.value']
            for ptav in combination:
                if ptav.attribute_id.create_variant == "no_variant":
                    no_variant_attr_val += ptav
            combination -= no_variant_attr_val
            variant_id = self._get_variant_for_combination(combination)
            if variant_id and variant_id.hide_on_website:
                return False
        return result

    def _get_combination_info(self, combination=False, parent_combination=False, add_qty=1, pricelist=False, only_template=False):
        """⚠️ SAFEGUARD: Ensures combination is a recordset, not None"""
        if combination is None:
            combination = self.env['product.template.attribute.value']
        return super()._get_combination_info(combination, parent_combination, add_qty, pricelist, only_template)

    def _get_variant_for_combination(self, combination):
        """⚠️ SAFEGUARD: Prevents crash if combination is None"""
        if not combination:
            return self.env['product.product']
        return super()._get_variant_for_combination(combination)


class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    unavailable_variant_view_type = fields.Selection([('none', 'None'), ('hide', 'Hide')], default='none', string='Unavailable Variant View Type')


class ProductProduct(models.Model):
    _inherit = "product.product"

    hide_on_website = fields.Boolean()

