/** @odoo-module **/

import paymentForm from "@payment/js/payment_form";
import {rpc, RPCError} from "@web/core/network/rpc";
import {_t} from "@web/core/l10n/translation";

paymentForm.include({
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
        if (!providerCode.startsWith("mbw")) {
            return this._super(...arguments);
        }
        const phone_number = document.getElementById("phone_number").value;
        const company_id = document.getElementById("company_id").value;
        const currency = document.getElementById("currency").value;
        console.log(currency);
        const route = providerCode.endsWith("if") ? "ifthenpay" : "eupago";

        return rpc("/payment/" + route + "/mbway/feedback", {
            reference: processingValues.reference,
            amount: processingValues.amount,
            currency: currency,
            company_id: company_id,
            phone_number: phone_number,
        })
            .then(() => {
                window.location = "/payment/status";
            })
            .catch((error) => {
                if (error instanceof RPCError) {
                    this._displayErrorDialog(
                        _t("Payment processing failed"),
                        error.data.message
                    );
                    this._enableButton?.(); // This method doesn't exists in Express Checkout form.
                } else {
                    return Promise.reject(error);
                }
            });
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
        if (providerCode.startsWith("mbw")) {
            this._setPaymentFlow("direct");
            return;
        } else {
            return this._super(...arguments);
        }
    },
});
