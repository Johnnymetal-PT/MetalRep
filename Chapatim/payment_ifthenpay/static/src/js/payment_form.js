/** @odoo-module **/

import { PaymentForm } from '@payment/interactions/payment_form';
import { patch } from '@web/core/utils/patch';

patch(PaymentForm.prototype, {

    PTPaymentCodes() {
        const paymentCodes = super.PTPaymentCodes();
        paymentCodes.push('mbrif');
        paymentCodes.push('mbwif');
        return paymentCodes;
    },

    MultibancoCodes() {
        const mbCodes = super.MultibancoCodes();
        mbCodes.push('mbrif');
        return mbCodes;
    },

    MBWayCodes() {
        const mbwCodes = super.MBWayCodes();
        mbwCodes.push('mbwif');
        return mbwCodes;
    },
});
