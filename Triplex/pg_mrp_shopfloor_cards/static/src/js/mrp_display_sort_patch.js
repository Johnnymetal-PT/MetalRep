/** @odoo-module **/
// Corrige dois problemas de UX do Shop Floor com muitos registos:
//  1) Páginas em branco / OTs na última página: o Shop Floor pagina (40/página) e filtra
//     os cartões pela estação só do lado do cliente. Páginas cujos 40 registos não são da
//     estação ativa ficam vazias. Aumentamos o limite para carregar tudo de uma vez.
//  2) Ordenação baralhada: o comparador original usa `d1 - d2` com objetos de data, o que
//     dá NaN. Reordenamos de forma robusta (estado -> data, datas em branco no fim).
// Ver o __manifest__.py.

import { patch } from "@web/core/utils/patch";
import { MrpDisplay } from "@mrp_workorder/mrp_display/mrp_display";

// Estado: progresso e pronto primeiro (acionáveis), depois os restantes.
const PG_STATE_ORDER = { progress: 0, ready: 1, pending: 2, waiting: 3, finished: 4 };
// Carregar até este nº de registos por página (em vez de 40), para a filtragem por
// estação não deixar páginas em branco. Ajustável se o volume crescer muito.
const PG_SHOPFLOOR_LIMIT = 500;

patch(MrpDisplay.prototype, {
    setup() {
        super.setup(...arguments);
        if (!this.props.action?.context?.limit && this.state.limit < PG_SHOPFLOOR_LIMIT) {
            this.state.limit = PG_SHOPFLOOR_LIMIT;
        }
    },

    defineRelevantRecords() {
        const records = super.defineRelevantRecords(...arguments);
        if (this.state.activeResModel !== "mrp.production" && Array.isArray(records)) {
            const ts = (wo) => {
                const d = wo.data.date_start;
                return d && d.valueOf ? d.valueOf() : Infinity;
            };
            records.sort((a, b) => {
                const va = PG_STATE_ORDER[a.data.state] ?? 9;
                const vb = PG_STATE_ORDER[b.data.state] ?? 9;
                return va - vb || ts(a) - ts(b) || a.resId - b.resId;
            });
            this._relevantRecords = records;
        }
        return this._relevantRecords || records;
    },
});
