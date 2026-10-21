/** @odoo-module **/
// Mostra o tempo gasto e o número de pessoas em cada linha de operação do cartão da ordem
// de fabrico — a vista "Todas as OF", onde cada cartão lista os cinco centros de trabalho.
//
// Só aparece quando há tempo registado. Nas operações que ainda não arrancaram, um
// "0:00 · 1 pessoa" em cada linha seria ruído em cinco linhas por cartão.

import { patch } from "@web/core/utils/patch";
import { MrpWorkorder } from "@mrp_workorder/mrp_display/mrp_record_line/mrp_workorder";

patch(MrpWorkorder.prototype, {
    get pgTimeAndPeople() {
        const dados = this.props.record.data;
        // `duration` vem em minutos e é o tempo de relógio acumulado da operação.
        const minutos = dados.duration || 0;
        if (minutos <= 0) {
            return "";
        }
        const pessoas = dados.pg_people_count || 1;
        const horas = Math.floor(minutos / 60);
        const resto = Math.round(minutos % 60);
        const tempo = `${horas}:${String(resto).padStart(2, "0")}`;
        return `${tempo} · ${pessoas} ${pessoas === 1 ? "pessoa" : "pessoas"}`;
    },
});
