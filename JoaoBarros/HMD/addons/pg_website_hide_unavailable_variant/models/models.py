# -*- coding: utf-8 -*-
import json

from odoo import models, fields
from odoo.http import request

# Inherits from the existing product.template model to extend its functionality.
class ProductTemplate(models.Model):
    _inherit = "product.template"

    # This method is used to get the count and details of available and unavailable variants for a product template.
    def get_variant_count(self):
        for rec in self:
            valid_combination_list = []  # To store valid combinations of attributes.
            attribute_ids = []  # To store the IDs of attributes involved.
            attribute_display_types = {}  # To store the display types of attributes.
            unavailable_variant_view_type = []  # To store how unavailable variants should be displayed.

            all_empty = False
            try:
                # Attempts to get the first possible combination of attributes. If none exist, it catches the StopIteration exception.
                iterable = rec.with_context(special_call=True)._get_possible_combinations()
                first = next(iterable)
            except StopIteration:
                all_empty = True

            if all_empty:
                # If there are no possible combinations, iterates through combinations to populate attribute details.
                for v in rec._get_possible_combinations():
                    val = []
                    for value in v:
                        val.append(value.id)
                        if value.attribute_id.id not in attribute_ids:
                            attribute_ids.append(value.attribute_id.id)
                            attribute_display_types.update({value.attribute_id.id: value.attribute_id.display_type})
                            unavailable_variant_view_type.append(value.attribute_id.unavailable_value_view_type)
            else:
                # If there are possible combinations, iterates through them to populate attribute details and valid combinations.
                for v in rec.with_context(special_call=True)._get_possible_combinations():
                    val = []
                    for value in v:
                        val.append(value.id)
                        if value.attribute_id.id not in attribute_ids:
                            attribute_ids.append(value.attribute_id.id)
                            attribute_display_types.update({value.attribute_id.id: value.attribute_id.display_type})
                            unavailable_variant_view_type.append(value.attribute_id.unavailable_value_view_type)

                    valid_combination_list.append(tuple(val))

            valid_comb = set(valid_combination_list)  # Removes duplicate combinations.
            value_count_per_attr = []  # Counts the number of values per attribute.
            attribute_line_ids = self.attribute_line_ids
            if attribute_line_ids:
                for line in attribute_line_ids:
                    value_count_per_attr.append(len(line.value_ids))

            j = 0
            available_variant_values_ids = {}  # Maps index to available variant value IDs.
            all_val = []  # To store all variant values.
            for item in list(valid_comb):
                all_val.extend(list(item))
                available_variant_values_ids[j] = (list(item))
                j += 1
            all_val = list(set(all_val))  # Removes duplicate values.

            variant_val_child_dict = {}  # Stores child items for each variant value.
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

            # Constructs a dictionary containing details about unavailable variants.
            unavailable_variant_dict = {
                "attribute_ids": attribute_ids,
                "attribute_display_types": attribute_display_types,
                "unavailable_variant_view_type": unavailable_variant_view_type,
                "value_to_show": variant_val_child_dict,
                "value_to_show_tuple": list(valid_comb),
                "value_count_per_attr": value_count_per_attr
            }
            return unavailable_variant_dict

    # Retrieves the first possible combination of attributes, filtering out attributes that do not create variants.
    def _get_first_possible_combination(self, parent_combination=None, necessary_values=None):
        """See `_get_possible_combinations` (one iteration).

        This method return the same result (empty recordset) if no
        combination is possible at all which would be considered a negative
        result, or if there are no attribute lines on the template in which
        case the "empty combination" is actually a possible combination.
        Therefore the result of this method when empty should be tested
        with `_is_combination_possible` if it's important to know if the
        resulting empty combination is actually possible or not.
        """
        # Gets the next possible combination or an empty recordset.
        com = next(self._get_possible_combinations(parent_combination, necessary_values),
                   self.env['product.template.attribute.value'])
        no_variant_attr_val = self.env['product.template.attribute.value']
        for ptav in com:
            if ptav.attribute_id.create_variant == "no_variant":
                no_variant_attr_val += ptav

        for combination in self._get_possible_combinations(parent_combination, necessary_values):
            org_combination = combination
            combination -= no_variant_attr_val
            # Fetches the variant for the given combination.
            variant_id = self._get_variant_for_combination(combination)
            if variant_id and not variant_id.hide_on_website:
                return org_combination

    # Checks if a given combination is possible, considering the context of 'special_call'.
    def _is_combination_possible(self, combination, parent_combination=None, ignore_no_variant=False):
        result = super(ProductTemplate, self)._is_combination_possible(combination, parent_combination,
                                                                       ignore_no_variant)
        if result and self._context.get("special_call"):
            no_variant_attr_val = self.env['product.template.attribute.value']

            for ptav in combination:
                if ptav.attribute_id.create_variant == "no_variant":
                    no_variant_attr_val += ptav
            combination -= no_variant_attr_val
            # Gets the variant for the combination and checks if it should be hidden on the website.
            variant_id = self._get_variant_for_combination(combination)
            if variant_id and self._context.get("special_call"):
                if variant_id.hide_on_website:
                    return False
                else:
                    return True
        return result


# Inherits from the existing product.attribute model to extend its functionality.
class ProductAttribute(models.Model):
    _inherit = "product.attribute"

    # Adds a new field to specify how unavailable variants should be displayed (or hidden) on the website.
    unavailable_value_view_type = fields.Selection([('none', 'None'), ('hide', 'Hide')],
                                                   default='none', string='Unavailable Variant View Type')


# Inherits from the existing product.product model to extend its functionality.
class ProductProduct(models.Model):
    _inherit = "product.product"

    # Adds a new boolean field to indicate if the variant should be hidden on the website.
    hide_on_website = fields.Boolean()
