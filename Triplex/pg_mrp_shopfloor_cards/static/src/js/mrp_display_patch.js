/** @odoo-module **/
// Ao ler um código de barras no Shop Floor, filtra as ordens pela "origem" (ou "nome"),
// em vez do comportamento standard. Ver o __manifest__.py.

import { patch } from "@web/core/utils/patch";
import { MrpDisplay } from "@mrp_workorder/mrp_display/mrp_display";

patch(MrpDisplay.prototype, {
    async _onProductionBarcodeScanned(barcode) {
        // Procura um filtro de pesquisa por "origin"; se não existir, recorre a "name".
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
