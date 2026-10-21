/** @odoo-module **/
// Acrescenta campos extra (origem + ficheiros Studio) aos dados das ordens carregados
// pelo Shop Floor, para depois poderem ser usados nos cartões. Ver o __manifest__.py.

import { patch } from "@web/core/utils/patch";
import { MrpDisplayAction } from "@mrp_workorder/mrp_display/mrp_display_action";

const EXTRA_PRODUCTION_FIELDS = [
    "origin",
    "x_studio_ficheiro_pdf",
    // Endereço da imagem do cartão, já resolvido no servidor por precedência (imagem
    // manual da ordem > foto da linha de venda > imagem de catálogo do produto). Ver
    // `models/mrp_production.py`. Substituiu a leitura direta do `x_studio_imagem_estofo`,
    // que era só uma das três origens.
    "pg_card_image_url",
    // Tecido da peça, procurado nos componentes da ordem e, na falta deles, nos materiais
    // escritos na descrição da venda. Ver `models/mrp_production.py`.
    "pg_fabric_label",
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
