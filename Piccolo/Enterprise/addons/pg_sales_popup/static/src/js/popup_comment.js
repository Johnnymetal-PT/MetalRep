/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { Dialog } from "@web/core/dialog/dialog";

console.log("[PG_POPUP] Script loaded");

patch(FormController.prototype, {
    async saveRecord(recordId) {
        const result = await super.saveRecord(recordId);
        const comment = this.env.context?.show_comment_popup;
        if (comment) {
            Dialog.alert(this, comment, {
                title: "Comentário do Cliente",
            });
        }
        return result;
    },
});
