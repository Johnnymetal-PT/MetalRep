/** @odoo-module **/

import { Component, markup, onWillStart, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { download } from "@web/core/network/download";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Layout } from "@web/search/layout";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

export class StonePricelistReport extends Component {
    static props = { ...standardActionServiceProps };
    static components = { Layout };
    static template = "mh_stone_reports.StonePricelistReport";

    setup() {
        this.action = useService("action");
        this.orm = useService("orm");

        const ctx = this.props.action.context || {};
        this.activeIds = ctx.active_ids || [];

        this.state = useState({
            displayPricelistTitle: false,
            html: "",
            products: [],
            selectedProductId: false,
            pricelists: [],
            selectedPricelistId: false,
        });

        onWillStart(async () => {
            this.state.products = await this.getProductsFromStones();
            this.state.pricelists = await this.getPricelists();
            await this.renderHtml();
        });
    }

    get reportParams() {
        return {
            active_ids: this.activeIds,
            display_pricelist_title: this.state.displayPricelistTitle,
            product_id: this.state.selectedProductId || "",
            pricelist_id: this.state.selectedPricelistId || "",
        };
    }

    async getPricelists() {
        return this.orm.searchRead("product.pricelist", [], ["id", "name"]);
    }

    onSelectPricelist(ev) {
        const value = ev.target.value;
        this.state.selectedPricelistId = value ? parseInt(value, 10) : false;
        this.renderHtml();
    }

    async getProductsFromStones() {
        if (!this.activeIds || !this.activeIds.length) {
            return [];
        }
        const stones = await this.orm.searchRead(
            "stone.stock",
            [["id", "in", this.activeIds]],
            ["product_id"]
        );
        const seen = new Set();
        const products = [];
        for (const s of stones) {
            if (!s.product_id) continue;
            const [pid, pname] = s.product_id;
            if (seen.has(pid)) continue;
            seen.add(pid);
            products.push({ id: pid, name: pname });
        }
        products.sort((a, b) => (a.name || "").localeCompare(b.name || ""));
        return products;
    }

    async renderHtml() {
        const html = await this.orm.call(
            "report.mh_stone_reports.report_stone_pricelist",
            "get_html",
            [],
            { data: this.reportParams }
        );
        this.state.html = markup(html);
    }

    onSelectProduct(ev) {
        const typed = (ev.target.value || "").trim();
        if (!typed) {
            this.state.selectedProductId = false;
            this.renderHtml();
            return;
        }
        // Procurar por nome exacto primeiro, depois por inclusão (case-insensitive)
        let match = this.state.products.find((p) => p.name === typed);
        if (!match) {
            const low = typed.toLowerCase();
            match = this.state.products.find((p) =>
                (p.name || "").toLowerCase().includes(low)
            );
        }
        this.state.selectedProductId = match ? match.id : false;
        this.renderHtml();
    }

    onTypeProduct(ev) {
        // Quando o utilizador apaga tudo, limpa filtro imediatamente
        if (!ev.target.value) {
            this.state.selectedProductId = false;
            this.renderHtml();
        }
    }

    onToggleDisplayTitle() {
        this.state.displayPricelistTitle = !this.state.displayPricelistTitle;
        this.renderHtml();
    }

    async onClickPrint() {
        const select = document.getElementById("stone_pricelist_format");
        const format = select ? select.value : "pdf";
        await download({
            url: "/stone_stock/export/pricelist/",
            data: {
                report_data: JSON.stringify(this.reportParams),
                export_format: format,
            },
        });
    }

    onClickLink(ev) {
        const target = ev.target.closest("a.o_action");
        if (!target) return;
        ev.preventDefault();
        const model = target.dataset.model;
        const resId = parseInt(target.dataset.resId, 10);
        if (!model || !resId) return;
        this.action.doAction({
            type: "ir.actions.act_window",
            res_model: model,
            res_id: resId,
            views: [[false, "form"]],
            target: "current",
        });
    }
}

registry
    .category("actions")
    .add("generate_stone_pricelist_report", StonePricelistReport);
