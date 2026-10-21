/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { MrpDisplay } from "@mrp_workorder/mrp_display/mrp_display";

patch(MrpDisplay.prototype, {
    async _onProductionBarcodeScanned(barcode) {
        const searchItems = Object.values(this.env.searchModel.searchItems);
        const searchItem =
            searchItems.find((item) => item.fieldName === "origin") ||
            searchItems.find((item) => item.fieldName === "name");
        if (!searchItem) {
            return;
        }
        const autocompleteValue = {
            label: barcode,
            operator: "=",
            value: barcode,
        };
        this.env.searchModel.addAutoCompletionValues(searchItem.id, autocompleteValue);
    },
});
