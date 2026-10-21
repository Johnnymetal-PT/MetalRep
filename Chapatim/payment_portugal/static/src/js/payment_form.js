/** @odoo-module **/

import { PaymentForm } from '@payment/interactions/payment_form';
import {rpc, RPCError} from "@web/core/network/rpc";
import {_t} from "@web/core/l10n/translation";
import { patch } from '@web/core/utils/patch';

patch(PaymentForm.prototype, {
    PTPaymentCodes() {
        return []
    },

    MultibancoCodes() {
        return []
    },

    MBWayCodes() {
        return []
    },

    /**
     * Simulate a feedback from a payment provider and redirect the customer to the status page.
     *
     * @override method from payment.payment_form
     * @private
     * @param {string} providerCode - The code of the selected payment option's provider.
     * @param {number} paymentOptionId - The id of the selected payment option.
     * @param {string} paymentMethodCode - The code of the selected payment method, if any.
     * @param {object} processingValues - The processing values of the transaction.
     * @return {void}
     */
    async _processDirectFlow(
        providerCode,
        paymentOptionId,
        paymentMethodCode,
        processingValues
    ) {
        if (!this.PTPaymentCodes().includes(providerCode)) {
            return super._processDirectFlow(...arguments);
        }

        if (this.MultibancoCodes().includes(providerCode)) {
            window.location = "/payment/status";
        }
        else if (this.MBWayCodes().includes(providerCode)) {
            const phone_number = document.getElementById("phone_number").value;
            rpc('/payment/mbway', {
                'reference': processingValues.reference,
                'provider_code': providerCode,
                'phone_number': phone_number,
            }).then(() => {
                window.location = '/payment/status';
            }).catch(error => {
                if (error instanceof RPCError) {
                    // These methods don't exist in Express Checkout.
                    this._displayErrorDialog?.(_t("Payment processing failed"), error.data.message);
                    this._enableButton?.();
                } else {
                    return Promise.reject(error);
                }
            });
        }

    },

    /**
     * Prepare the inline form of Demo for direct payment.
     *
     * @override method from @payment/js/payment_form
     * @private
     * @param {number} providerId - The id of the selected payment option's provider.
     * @param {string} providerCode - The code of the selected payment option's provider.
     * @param {number} paymentOptionId - The id of the selected payment option
     * @param {string} paymentMethodCode - The code of the selected payment method, if any.
     * @param {string} flow - The online payment flow of the selected payment option.
     * @return {void}
     */
    async _prepareInlineForm(
        providerId,
        providerCode,
        paymentOptionId,
        paymentMethodCode,
        flow
    ) {
        if (providerCode in ['mbrif', 'mbwif']) {
            await super._prepareInlineForm(...arguments);
        } else {
            this._setPaymentFlow('direct');
        }
    },
});
