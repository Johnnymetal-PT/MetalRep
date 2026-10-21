/** @odoo-module */

import { AccountReport } from "@account_reports/components/account_report/account_report";
import { AccountReportLineCell } from "@account_reports/components/account_report/line_cell/line_cell";

export class CollectionMapLineCell extends AccountReportLineCell {
    static template = "mh_accounting_reports.CollectionMapLineCell";

    get cellClasses() {
        let superCellClasses = super.cellClasses;
        const cell = this.props.cell;

        if (cell.expression_label === 'aging_days' && cell.name) {
            const val = String(cell.name);
            if (val.includes('em atraso')) {
                superCellClasses += ' text-danger fw-bold';
            } else if (val === 'Hoje') {
                superCellClasses += ' text-warning fw-bold';
            } else if (val.includes('A vencer')) {
                superCellClasses += ' text-success';
            }
        }

        return superCellClasses;
    }
}

AccountReport.registerCustomComponent(CollectionMapLineCell);
