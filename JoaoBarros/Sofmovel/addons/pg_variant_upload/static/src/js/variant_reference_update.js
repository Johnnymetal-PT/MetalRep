odoo.define('website_sale.variant_reference_update', function (require) {
    'use strict';

    const publicWidget = require('web.public.widget');

    publicWidget.registry.VariantReferenceUpdate = publicWidget.Widget.extend({
        selector: '.o_wsale_product_page',
        events: {
            'change .js_variant_change': '_onVariantChange',
        },

        /**
         * Handle variant change
         */
        _onVariantChange: function (ev) {
            const $select = $(ev.currentTarget);
            const productId = $select.find(':selected').data('product-id');
            const $referenceElement = $('#variant_reference');

            if (productId) {
                this._fetchVariantReference(productId).then(reference => {
                    $referenceElement.text(reference || '');
                });
            }
        },

        /**
         * Fetch the x_studio_referncia_interna for the selected variant
         */
        _fetchVariantReference: function (productId) {
            return this._rpc({
                route: '/product_variant/reference',
                params: { product_id: productId },
            }).then(result => result.reference);
        },
    });

    return publicWidget.registry.VariantReferenceUpdate;
});

