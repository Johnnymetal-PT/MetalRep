/** @odoo-module **/
// Acrescenta ao cartão do Chão de Fábrica uma classe com a cor do centro de trabalho.
//
// Porque é preciso JavaScript: a cor de cada centro vive nos separadores do topo, atribuída
// pelo Enterprise em `control_panel.xml:14` com `o_workcenter_item_color_{{id % 11}}`. O
// cartão não tem o centro de trabalho no DOM nem qualquer relação de ascendência com o
// separador activo, por isso não há CSS que chegue lá.
//
// Optou-se por estender o getter `cssClass` em vez de herdar o template: se este patch
// falhar, o cartão perde a cor e mais nada. Um `xpath` a um template do Enterprise que
// deixe de casar rebenta a compilação dos assets e leva o backend inteiro com ele.
//
// O índice é `id % 11`, exactamente o mesmo cálculo do Enterprise, para as cores do cartão
// e do separador coincidirem sempre. As cores estão em `scss/shopfloor_ux.scss`, geradas a
// partir da mesma lista `$o-colors`.

import { patch } from "@web/core/utils/patch";
import { MrpDisplayRecord } from "@mrp_workorder/mrp_display/mrp_display_record";

patch(MrpDisplayRecord.prototype, {
    get cssClass() {
        const base = super.cssClass;
        // Os cartões de ordem de fabrico (`mrp.production`) não têm centro de trabalho —
        // só os de ordem de trabalho. Nesse caso devolve-se a classe original.
        const workcenter = this.props.record.data.workcenter_id;
        if (!workcenter || !workcenter.length) {
            return base;
        }
        return `${base} pg_wc_${workcenter[0] % 11}`;
    },
});
