/** @odoo-module alias=theme_alan.QuickViewDialog **/

import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";

import { Component } from "@odoo/owl";

// ─── Quick View Dialog ─────────────────────────────────────────────────
export class QuickViewDialog extends Component {
    static template = "theme_alan.QuickViewDialog";
    static components = { Dialog };
    static props = {
        productTemplateId: Number,
        body: { type: String, optional: true },
    };
}

export default {
    QuickViewDialog: QuickViewDialog,
}
