/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { MrpDisplayAction } from "@mrp_workorder/mrp_display/mrp_display_action";

const EXTRA_PRODUCTION_FIELDS = [
    "origin",
    "x_studio_ficheiro_pdf",
    "x_studio_imagem_estofo",
];

patch(MrpDisplayAction.prototype, {
    get fieldsStructure() {
        const fieldsStructure = super.fieldsStructure;
        const productionFields = [...fieldsStructure["mrp.production"]];
        for (const fieldName of EXTRA_PRODUCTION_FIELDS) {
            if (!productionFields.includes(fieldName)) {
                productionFields.push(fieldName);
            }
        }
        return {
            ...fieldsStructure,
            "mrp.production": productionFields,
        };
    },
});
