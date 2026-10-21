/** @odoo-module **/
// Mantém o "Fechar produção" visível mas inactivo enquanto houver operações não concluídas.
//
// O pedido do cliente foi explícito quanto a isto: o botão fica **visível e não clicável**,
// não escondido. Esconder deixaria o operador sem saber que o passo existe; desactivado com
// a razão à frente ensina o que falta fazer.

import { patch } from "@web/core/utils/patch";
import { MrpDisplayAction } from "@mrp_workorder/mrp_display/mrp_display_action";
import { MrpDisplayRecord } from "@mrp_workorder/mrp_display/mrp_display_record";

const CAMPOS_ORDEM = ["pg_can_close", "pg_pending_workorders"];

patch(MrpDisplayAction.prototype, {
    get fieldsStructure() {
        const estrutura = super.fieldsStructure;
        const campos = [...(estrutura["mrp.production"] || [])];
        for (const campo of CAMPOS_ORDEM) {
            if (!campos.includes(campo)) {
                campos.push(campo);
            }
        }
        return { ...estrutura, "mrp.production": campos };
    },
});

patch(MrpDisplayRecord.prototype, {
    get pgCloseBlocked() {
        const registo = this.props.record;
        if (registo.resModel !== "mrp.production") {
            return false;
        }
        // Em validação o mesmo botão passa a ser "Anular". Bloqueá-lo aí impediria o
        // operador de desfazer, que é o oposto do que se pretende.
        if (this.state.underValidation) {
            return false;
        }
        return !registo.data.pg_can_close;
    },

    get pgPendingWorkorders() {
        return this.props.record.data.pg_pending_workorders || "";
    },
});
