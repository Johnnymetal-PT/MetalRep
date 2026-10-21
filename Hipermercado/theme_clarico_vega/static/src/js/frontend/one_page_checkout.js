/** @odoo-module **/

import publicWidget from '@web/legacy/js/public/public_widget';
import OwlMixin from "@theme_clarico_vega/js/frontend/mixins";
import { rpc } from "@web/core/network/rpc";
import { Interaction } from "@web/public/interaction";
import { registry } from "@web/core/registry";
import { Checkout as OriginalCheckout } from '@website_sale/interactions/checkout';
import { PaymentForm } from '@payment/interactions/payment_form';
import { patch } from "@web/core/utils/patch";
import { patchDynamicContent } from '@web/public/utils';

patch(PaymentForm.prototype, {
    async submitForm(ev) {
        ev.preventDefault();
        ev.stopImmediatePropagation();

        const extraForm = document.querySelector("#extra_info_form");
        if (extraForm) {
            const formData = new FormData(extraForm);

            try {
                const result = await fetch(extraForm.action, {
                    method: "POST",
                    body: formData,
                }).then((res) => res.json());

                if (result.error || result.error_fields) {
                    // handle errors (optional)
                    console.error("Extra form submission failed:", result);
                    return;
                }
            } catch (err) {
                console.error("Error submitting extra form:", err);
                return;
            }
        }

        return await super.submitForm(ev);
    },
});

publicWidget.registry.HideAddressCards = publicWidget.Widget.extend({
    selector: '#wrapwrap',
    events: {
        'click #loadMore': '_loadmore',
    },
    start: function () {
        // Show only the first 2 elements with the o_address_card class, hide the rest
        let $deliveryCards = this.$('#delivery_address_list .o_address_card');
        let $billingCards = this.$('#billing_address_list .o_address_card');
        $deliveryCards.each(function(idx, el) {
            if (idx >= 2) {
                $(el).hide();
            } else {
                $(el).show();
            }
        });
        $billingCards.each(function(idx, el) {
            if (idx >= 2) {
                $(el).hide();
            } else {
                $(el).show();
            }
        });
        return this._super.apply(this, arguments);
    },

    _loadmore: function (ev) {
        ev.preventDefault();
        let $deliveryCards = this.$('#delivery_address_list .o_address_card');
        let $billingCards = this.$('#billing_address_list .o_address_card');
        $deliveryCards.show();
        $billingCards.show();
        this.$('#loadMore').hide();
    }
});