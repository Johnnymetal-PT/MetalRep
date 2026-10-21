/** @odoo-module **/

import { PaymentForm } from '@payment/interactions/payment_form';
import { patch } from '@web/core/utils/patch';

patch(PaymentForm.prototype, {

    PTPaymentCodes() {
        const paymentCodes = super.PTPaymentCodes();
        paymentCodes.push('mbreu');
        paymentCodes.push('mbweu');
        return paymentCodes;
    },

    MultibancoCodes() {
        const mbCodes = super.MultibancoCodes();
        mbCodes.push('mbreu');
        return mbCodes;
    },

    MBWayCodes() {
        const mbwCodes = super.MBWayCodes();
        mbwCodes.push('mbweu');
        return mbwCodes;
    },
});
