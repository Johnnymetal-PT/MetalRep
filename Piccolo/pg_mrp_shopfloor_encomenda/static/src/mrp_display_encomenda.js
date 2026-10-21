/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { MrpDisplayAction } from "@mrp_workorder/mrp_display/mrp_display_action";
import { MrpDisplayRecord } from "@mrp_workorder/mrp_display/mrp_display_record";

// 1) Carregar `origin` (Nº de Encomenda) e `pg_client_order_ref`
//    (Referencia do Cliente) da mrp.production no Shop Floor.
//    O getter devolve um objeto novo a cada chamada, por isso o push
//    nao acumula entre chamadas.
patch(MrpDisplayAction.prototype, {
    get fieldsStructure() {
        const structure = super.fieldsStructure;
        const moFields = structure["mrp.production"];
        if (moFields) {
            for (const fName of ["origin", "pg_client_order_ref"]) {
                if (!moFields.includes(fName)) {
                    moFields.push(fName);
                }
            }
        }
        return structure;
    },
});

// 2) Expor o Nº de Encomenda e a Referencia do Cliente ao cartao.
//    - Cartao de Ordem de Trabalho: le do MO-pai (props.production).
//    - Cartao de Ordem de Producao: le do proprio registo.
patch(MrpDisplayRecord.prototype, {
    get pgEncomenda() {
        return this.props.production?.data?.origin || this.record?.origin || "";
    },
    get pgClientOrderRef() {
        return (
            this.props.production?.data?.pg_client_order_ref ||
            this.record?.pg_client_order_ref ||
            ""
        );
    },
});
