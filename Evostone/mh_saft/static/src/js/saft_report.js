/** @odoo-module **/

import { Component, markup, onWillStart, useState } from "@odoo/owl";
import { download } from "@web/core/network/download";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Layout } from "@web/search/layout";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";


export class SaftReport extends Component {
    static props = { ...standardActionServiceProps };
    static components = { Layout };
    static template = "mh_saft.SaftReport";

    setup() {
        this.orm = useService("orm");
        this.state = useState({
            years: [],
            months: [],
            year: null,
            month: null,
            docType: "",
            html: "",
            totalLines: 0,
            totalDocs: 0,
            grandTotal: 0,
        });

        onWillStart(async () => {
            const f = await this.orm.call("report.mh_saft.report", "get_filters", []);
            this.state.years = f.years;
            this.state.months = f.months;
            this.state.year = f.current_year;
            this.state.month = f.current_month;
            await this.renderHtml();
        });
    }

    get reportParams() {
        return {
            year: this.state.year,
            month: this.state.month,
            doc_type: this.state.docType || false,
        };
    }

    async renderHtml() {
        const res = await this.orm.call("report.mh_saft.report", "get_html", [this.reportParams]);
        this.state.html = markup(res.html);
        this.state.totalLines = res.total_lines;
        this.state.totalDocs = res.total_docs;
        this.state.grandTotal = res.grand_total;
    }

    onChangeYear(ev) {
        this.state.year = parseInt(ev.target.value);
        this.renderHtml();
    }

    onChangeMonth(ev) {
        this.state.month = parseInt(ev.target.value);
        this.renderHtml();
    }

    onChangeType(ev) {
        this.state.docType = ev.target.value;
        this.renderHtml();
    }

    async onClickExport() {
        const select = document.getElementById("mh_saft_format");
        const format = select ? select.value : "xlsx";
        await download({
            url: "/mh_saft/export",
            data: {
                report_data: JSON.stringify(this.reportParams),
                export_format: format,
            },
        });
    }
}

registry.category("actions").add("mh_saft.client_action", SaftReport);
