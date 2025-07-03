/** @odoo-module **/

import VariantMixin from "@website_sale/js/variant_mixin";
import publicWidget from "@web/legacy/js/public/public_widget";
import { markup } from "@odoo/owl";

VariantMixin._onChangeCombination = function(ev, $parent, combination){
    console.log('Combination changed:', combination);
    
    if(combination['product_variant_desc']){
        console.log('Product Variant Description:', combination['product_variant_desc']);
        $parent.find('.product_variant_product_variant_desc').html(markup(combination['product_variant_desc']));
    } else {
        console.log('No product_variant_desc found, clearing the description.');
        $parent.find('.product_variant_product_variant_desc').empty();
    }
};

publicWidget.registry.WebsiteSale.include({
    _onChangeCombination: function () {
        console.log('WebsiteSale _onChangeCombination triggered.');
        this._super.apply(this, arguments);
        VariantMixin._onChangeCombination.apply(this, arguments);
    },
});

export default VariantMixin;
