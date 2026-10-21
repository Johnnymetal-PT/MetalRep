/** @odoo-module **/
// Diálogo que pergunta quantas pessoas estão a trabalhar na operação.
//
// Desenho orientado ao mesmo público do restante trabalho de acessibilidade: operadores de
// oficina, em tablet, alguns com pouca prática de tecnologia. Daí as três decisões:
//   1. um toque resolve — escolher o número confirma e fecha, sem botão "Confirmar";
//   2. números em botões grandes, não um campo de texto com teclado;
//   3. o valor actual vem destacado, para se perceber o que está em vigor.

import { Component } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";

export class PgPeopleCountDialog extends Component {
    static template = "pg_mrp_people_count.PeopleCountDialog";
    static components = { Dialog };
    static props = {
        current: { type: Number, optional: true },
        onSelect: Function,
        close: Function,
    };
    static defaultProps = { current: 1 };

    // Oito chega para as secções da oficina. Acima disso escreve-se no back office, que é
    // situação rara e não vale um teclado neste ecrã.
    get options() {
        return [1, 2, 3, 4, 5, 6, 7, 8];
    }

    get title() {
        return _t("Quantas pessoas estão a trabalhar?");
    }

    select(numero) {
        this.props.onSelect(numero);
        this.props.close();
    }
}
