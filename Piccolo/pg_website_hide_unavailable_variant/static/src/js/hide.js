/** @odoo-module **/
import { jsonrpc } from "@web/core/network/rpc_service"; // Importing the jsonrpc service for making JSON-RPC calls.

import { WebsiteSale } from '@website_sale/js/website_sale'; // Importing the WebsiteSale module.
var id_tuples = undefined; // Variable to store the data related to product variants.

WebsiteSale.include({
    // Overriding the willStart method to fetch data before the module starts.
    willStart: async function () {
        var proms;
        const _super = this._super.apply(this, arguments); // Calling the original method.
        
        var $parent = $('.js_product'); // Selecting the product element.
        var product_tmpl_id = parseInt($parent.find('.product_template_id').val()); // Getting the product template ID.
        if (product_tmpl_id) {
            // Fetching product variant data via a JSON-RPC call.
            proms = jsonrpc('/get_product_variant_data_website', {
                'product_tmpl_id': product_tmpl_id,
            }).then((data) => {
                id_tuples = data; // Storing the fetched data in id_tuples.
            });
        }
        return Promise.all([this._super(...arguments), proms]); // Ensuring the original method and the data fetch complete before proceeding.
    },

    // Overriding the start method to manipulate the DOM after the module starts.
    start: function () {
        var self = this;
        var def = this._super.apply(this, arguments); // Calling the original start method.
        
        setTimeout(function () {
            var $parent = $("#product_details").find('.js_product'); // Selecting the product details element.
            var combination = self.getSelectedVariantValues($parent); // Getting the selected variant values.
            var checked_val_list = combination;

            if (id_tuples && Object.keys(id_tuples).length) {
                // If id_tuples is defined and has data, proceed to handle variants display.
                var value_to_show = id_tuples['value_to_show'];
                var unavailable_variant_view_type = id_tuples['unavailable_variant_view_type'];
                var z = $('.js_add_cart_variants').find("input[type='radio']");
                var selection_options = $('.js_add_cart_variants').find("select option");

                // If there are selection options, merge them with the radio inputs.
                if (selection_options.length) {
                    $.each(selection_options, function (i, element) {
                        if ($(element).val() != '0') {
                            z = $.merge(z, $(element));
                        }
                    });
                }

                // Loop through each variant option and decide whether to show or hide it.
                for (var i = 0; i < z.length; i++) {
                    if (!value_to_show.hasOwnProperty($(z[i]).val())) {
                        if (unavailable_variant_view_type[0] == 'none') { }
                        else if (unavailable_variant_view_type[0] == 'hide') {
                            if ($(z[i]).is("option")) {
                                $(z[i]).css({ "display": "none" });
                            } else {
                                $(z[i]).parent().css({ "display": "none" });
                            }
                        }
                    }
                }

                // Additional logic to handle visibility of other attributes based on selected variant.
                var attribute_ids = id_tuples['attribute_ids'];
                var unavailable_variant_view_type = id_tuples['unavailable_variant_view_type'];
                var all_attrs_childs = $('.js_product').find(".js_add_cart_variants").children();
                var value_to_show_tuple = id_tuples['value_to_show_tuple'];
                var new_checked_list = [];

                for (var vals2 = 0; vals2 < checked_val_list.length; vals2++) {
                    var clicked_on_variant_id = parseInt(checked_val_list[vals2]);
                    new_checked_list.push(clicked_on_variant_id);

                    if (clicked_on_variant_id) {
                        var checked_attr_val_list = new_checked_list;
                        var exact_show = [];

                        // Determine which variants to show based on the selected attributes.
                        for (var com_no = 0; com_no < value_to_show_tuple.length; com_no++) {
                            var result = checked_attr_val_list.every(val => value_to_show_tuple[com_no].includes(val));
                            if (result) {
                                if (exact_show.length > 0) {
                                    exact_show = exact_show.concat(value_to_show_tuple[com_no]);
                                } else {
                                    exact_show = value_to_show_tuple[com_no];
                                }
                            }
                        }

                        var unique_set = new Set(exact_show);
                        var list = Array.from(unique_set);

                        // Loop through each attribute and variant option to set visibility.
                        for (var i = 0; i < all_attrs_childs.length; i++) {
                            var variant_list = $(all_attrs_childs[i]).find('ul').children();
                            if (variant_list.length == 0) {
                                variant_list = $(all_attrs_childs[i]).find('select').children();
                            }
                            for (var j = 0; j < variant_list.length; j++) {
                                var variant_value = $(variant_list[j]).find('label').find('input');
                                if (variant_value.length == 0) {
                                    var value_id = parseInt($(variant_list[j]).data('value_id'));
                                } else {
                                    var value_id = parseInt(variant_value.attr("data-value_id"));
                                }

                                if (value_id == clicked_on_variant_id) {
                                    var att_id = parseInt($(all_attrs_childs[i]).attr("data-attribute_id"));
                                    var iterate_from = attribute_ids.indexOf(att_id);
                                    var attr_index = iterate_from;

                                    for (var z = iterate_from + 1; z < all_attrs_childs.length; z++) {
                                        var attr_var_list = $(all_attrs_childs[z]).find('ul').children();
                                        if (attr_var_list.length == 0) {
                                            attr_var_list = $(all_attrs_childs[z]).find('select').children();
                                        }
                                        for (var x = 0; x < attr_var_list.length; x++) {
                                            var $input = $(attr_var_list[x]).find('label').find('input');
                                            var $label = $(attr_var_list[x]).find('label').find('label');
                                            var $option;
                                            if ($input.length == 0) {
                                                $option = $(attr_var_list[x]);
                                            }
                                            var variant_value_id = $input.val();
                                            if (!variant_value_id) {
                                                variant_value_id = $(attr_var_list[x]).data("value_id");
                                            }
                                            if (list.indexOf(parseInt(variant_value_id)) != -1) { } else {
                                                if (unavailable_variant_view_type[attr_index] == 'none') {

                                                }
                                                else if (unavailable_variant_view_type[attr_index] == 'hide') {
                                                    $(attr_var_list[x]).css({ "display": "none" });
                                                }
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }, 1); // Timeout of 1ms to ensure DOM is ready.

        return def; // Returning the original start method's return value.
    },

    // Overriding the onChangeVariant method to handle changes in variant selection.
    onChangeVariant: function (ev) {
        this._super.apply(this, arguments); // Calling the original onChangeVariant method.
        
        var $parent = $(ev.target).closest('.js_product'); // Getting the closest product element.
        if (id_tuples && Object.keys(id_tuples).length) {
            var variants = id_tuples;
            var value_to_show_tuple = variants.value_to_show_tuple;
            var attribute_ids = variants.attribute_ids;
            var value_count_per_attr = variants.value_count_per_attr;
            var attribute_display_types = variants.attribute_display_types;
            var clicked_on_variant_id = parseInt($(ev.target).attr('data-value_id'));

            if (!clicked_on_variant_id) {
                clicked_on_variant_id = parseInt($(ev.target).val());
            }

            var unavailable_variant_view_type = variants.unavailable_variant_view_type;
            var all_attrs_childs = $parent.find(".js_add_cart_variants").children();

            // Iterates over all attributes and their values to manage visibility.
            for (var i = 0; i < all_attrs_childs.length; i++) {
                if (['radio', 'color', 'select', 'button', 'pills'].indexOf(attribute_display_types[$(all_attrs_childs[i]).data("attribute_id")]) > -1) {
                    var variant_list = $(all_attrs_childs[i]).find('ul').children();
                    if (variant_list.length == 0) {
                        variant_list = $(all_attrs_childs[i]).find('select').children();
                    }

                    for (var j = 0; j < variant_list.length; j++) {
                        var variant_value = $(variant_list[j]).find('label').find('input');
                        if (variant_value.length == 0) {
                            var value_id = parseInt($(variant_list[j]).data('value_id'));
                        } else {
                            var value_id = parseInt(variant_value.attr("data-value_id"));
                        }

                        if (value_id == clicked_on_variant_id) {
                            var att_id = parseInt($(all_attrs_childs[i]).attr("data-attribute_id"));
                            var iterate_from = attribute_ids.indexOf(att_id);
                            var attr_index = iterate_from;

                            for (var z = iterate_from + 1; z < all_attrs_childs.length; z++) {
                                var attr_var_list = $(all_attrs_childs[z]).find('ul').children();
                                if (attr_var_list.length == 0) {
                                    attr_var_list = $(all_attrs_childs[z]).find('select').children();
                                }

                                for (var x = 0; x < attr_var_list.length; x++) {
                                    if (value_count_per_attr[z] > 1) {
                                        $(attr_var_list[x]).find('label').find('input').prop('checked', false);
                                        $(attr_var_list[x]).prop('selected', false);
                                        $(attr_var_list[x]).removeClass("active");
                                    }
                                }
                            }
                        }
                    }
                }
            }

            if (clicked_on_variant_id) {
                var checked_attr_val = $('.js_add_cart_variants').find("input:checked[type='radio']");
                var selected_attr_val = $('.js_add_cart_variants').find("select option:selected");

                if (selected_attr_val.length) {
                    $.each(selected_attr_val, function (i, element) {
                        if ($(element).val() != '0') {
                            checked_attr_val = $.merge(checked_attr_val, $(element));
                        }
                    });
                }

                var checked_attr_val_list = [];
                for (var i = 0; i < checked_attr_val.length; i++) {
                    checked_attr_val_list.push(parseInt($(checked_attr_val[i]).val()));
                }

                var exact_show = [];
                for (var com_no = 0; com_no < value_to_show_tuple.length; com_no++) {
                    var result = checked_attr_val_list.every(val => value_to_show_tuple[com_no].includes(val));
                    if (result) {
                        exact_show = exact_show.concat(value_to_show_tuple[com_no]);
                    }
                }

                var unique_set = new Set(exact_show);
                var list = Array.from(unique_set);
                var $first_attr_value = false;

                for (var i = 0; i < all_attrs_childs.length; i++) {
                    if (['radio', 'color', 'select', 'button', 'pills'].indexOf(attribute_display_types[$(all_attrs_childs[i]).data("attribute_id")]) > -1) {
                        var variant_list = $(all_attrs_childs[i]).find('ul').children();
                        if (variant_list.length == 0) {
                            variant_list = $(all_attrs_childs[i]).find('select').children();
                        }

                        for (var j = 0; j < variant_list.length; j++) {
                            var variant_value = $(variant_list[j]).find('label').find('input');
                            if (variant_value.length == 0) {
                                var value_id = parseInt($(variant_list[j]).data('value_id'));
                            } else {
                                var value_id = parseInt(variant_value.attr("data-value_id"));
                            }

                            if (value_id == clicked_on_variant_id) {
                                var att_id = parseInt($(all_attrs_childs[i]).attr("data-attribute_id"));
                                var iterate_from = attribute_ids.indexOf(att_id);
                                var attr_index = iterate_from;
                                var first_value = 0;

                                for (var z = iterate_from + 1; z < all_attrs_childs.length; z++) {
                                    var attr_var_list = $(all_attrs_childs[z]).find('ul').children();
                                    if (attr_var_list.length == 0) {
                                        attr_var_list = $(all_attrs_childs[z]).find('select').children();
                                    }

                                    for (var x = 0; x < attr_var_list.length; x++) {
                                        var $input = $(attr_var_list[x]).find('label').find('input');
                                        if (value_count_per_attr[z] > 1) {
                                            $(attr_var_list[x]).find('label').find('input').prop('checked', false);
                                            $(attr_var_list[x]).prop('selected', false);
                                            $(attr_var_list[x]).removeClass("active");
                                        }

                                        var variant_value_id = $input.val();
                                        if (!variant_value_id) {
                                            variant_value_id = $(attr_var_list[x]).data("value_id");
                                        }

                                        if (list.includes(parseInt(variant_value_id))) {
                                            if (first_value == 0) {
                                                $first_attr_value = $input;
                                                if ($input.length == 0) {
                                                    $first_attr_value = $(attr_var_list[x]);
                                                }
                                                first_value = 1;
                                            }
                                            if (unavailable_variant_view_type[attr_index] == 'hide') {
                                                if ($(attr_var_list[x]).hasClass("list-inline-item")) {
                                                    $(attr_var_list[x]).css({ "display": "inline-block" });
                                                } else {
                                                    $(attr_var_list[x]).css({ "display": "list-item" });
                                                }
                                            }
                                        } else {
                                            if (unavailable_variant_view_type[attr_index] == 'hide') {
                                                $(attr_var_list[x]).css({ "display": "none" });
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }

                if ($first_attr_value && $($first_attr_value).is("input")) {
                    $first_attr_value.prop('checked', true);
                    $first_attr_value.change();
                    $first_attr_value.closest('li').addClass("active");
                } else if ($first_attr_value && $($first_attr_value).is("option")) {
                    $first_attr_value.prop('selected', true);
                    $first_attr_value.parent().trigger("change");
                }
            }
            $parent.find("p.css_not_available_msg").remove();
        }
    }
});
