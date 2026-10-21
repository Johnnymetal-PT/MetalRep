/** @odoo-module **/

import { Component, markup, onWillStart, useRef, useState } from "@odoo/owl";
import { DateTimeInput } from "@web/core/datetime/datetime_input";
import { download } from "@web/core/network/download";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Layout } from "@web/search/layout";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

const { DateTime } = luxon;


export class StockAtDateReport extends Component {
    static props = { ...standardActionServiceProps };
    static components = { Layout, DateTimeInput };
    static template = "mh_stock_at_date.StockAtDateReport";

    setup() {
        this.orm = useService("orm");
        this.action = useService("action");
        this.state = useState({
            date: DateTime.now(),
            locations: [],
            products: [],
            classifications: [],
            selectedLocationId: false,
            selectedProductId: false,
            selectedClassification: "",
            html: "",
            totalGroups: 0,
            totalLines: 0,
            grandTotal: 0,
        });
        this.reportRef = useRef("reportContainer");

        onWillStart(async () => {
            const [locations, products, classifications] = await Promise.all([
                this.orm.call("report.mh_stock_at_date.report", "get_locations", []),
                this.orm.call("report.mh_stock_at_date.report", "get_products", []),
                this.orm.call("report.mh_stock_at_date.report", "get_classifications", []),
            ]);
            this.state.locations = locations;
            this.state.products = products;
            this.state.classifications = classifications;
            await this.renderHtml();
        });
    }

    get isoDate() {
        return this.state.date ? this.state.date.toFormat("yyyy-MM-dd") : "";
    }

    get reportParams() {
        return {
            date: this.isoDate,
            location_id: this.state.selectedLocationId || false,
            product_id: this.state.selectedProductId || false,
            classification: this.state.selectedClassification || "",
        };
    }

    async renderHtml() {
        const result = await this.orm.call(
            "report.mh_stock_at_date.report",
            "get_html",
            [this.reportParams]
        );
        this.state.html = markup(result.html);
        this.state.totalGroups = result.total_groups;
        this.state.totalLines = result.total_lines;
        this.state.grandTotal = result.grand_total;
    }

    onChangeDate(value) {
        this.state.date = value;
        this.renderHtml();
    }

    onChangeLocation(ev) {
        const val = ev.target.value;
        this.state.selectedLocationId = val ? parseInt(val) : false;
        this.renderHtml();
    }

    onSelectProduct(ev) {
        const typed = (ev.target.value || "").trim();
        if (!typed) {
            this.state.selectedProductId = false;
            this.renderHtml();
            return;
        }
        let match = this.state.products.find((p) => p.name === typed);
        if (!match) {
            const low = typed.toLowerCase();
            match = this.state.products.find((p) => (p.name || "").toLowerCase().includes(low));
        }
        this.state.selectedProductId = match ? match.id : false;
        this.renderHtml();
    }

    onTypeProduct(ev) {
        if (!ev.target.value) {
            this.state.selectedProductId = false;
            this.renderHtml();
        }
    }

    onSelectClassification(ev) {
        this.state.selectedClassification = ev.target.value;
        this.renderHtml();
    }

    async onClickPrint() {
        const select = document.getElementById("stock_at_date_format");
        const format = select ? select.value : "pdf";
        await download({
            url: "/stock_at_date/export/",
            data: {
                report_data: JSON.stringify(this.reportParams),
                export_format: format,
            },
        });
    }

    onClickReport(ev) {
        // Link para registo (produto)
        const link = ev.target.closest("a.o_action");
        if (link) {
            ev.preventDefault();
            const model = link.dataset.model;
            const resId = parseInt(link.dataset.resId, 10);
            if (!model || !resId) return;
            this.action.doAction({
                type: "ir.actions.act_window",
                res_model: model,
                res_id: resId,
                views: [[false, "form"]],
                target: "current",
            });
            return;
        }
        // Click numa localização — expande/colapsa todo o bloco
        const locHeader = ev.target.closest(".o_loc_header");
        if (locHeader) {
            const block = locHeader.closest(".o_loc_block");
            if (block) block.classList.toggle("collapsed");
            return;
        }
        // Click num produto clicável — expande/colapsa lotes desse produto
        const prodHeader = ev.target.closest(".o_prod_header.o_clickable");
        if (prodHeader) {
            const block = prodHeader.closest(".o_loc_block");
            if (!block) return;
            // Identificar o produto pelo position (próximas tr até próximo o_prod_header)
            const allRows = Array.from(block.querySelectorAll("tr"));
            const idx = allRows.indexOf(prodHeader);
            for (let i = idx + 1; i < allRows.length; i++) {
                const row = allRows[i];
                if (row.classList.contains("o_prod_header")) break;
                if (row.classList.contains("o_prod_detail")) {
                    row.classList.toggle("collapsed-prod");
                }
            }
            // Toggle chevron
            const chev = prodHeader.querySelector(".o_prod_chevron");
            if (chev) chev.classList.toggle("expanded");
        }
    }
}

registry.category("actions").add("mh_stock_at_date.client_action", StockAtDateReport);
