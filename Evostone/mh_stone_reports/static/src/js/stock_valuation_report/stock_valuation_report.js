/** @odoo-module **/

import { Component, markup, onWillStart, useEffect, useRef, useState } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { DateTimeInput } from "@web/core/datetime/datetime_input";
import { download } from "@web/core/network/download";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Layout } from "@web/search/layout";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

const { DateTime } = luxon;

export class StockValuationReport extends Component {
    static props = { ...standardActionServiceProps };
    static components = { Layout, DateTimeInput };
    static template = "mh_stone_reports.StockValuationReport";

    setup() {
        this.action = useService("action");
        this.orm = useService("orm");

        this.state = useState({
            date: DateTime.now(),
            products: [],
            selectedProductId: false,
            classifications: [],
            selectedClassification: "",
            accountingFilter: "all",
            html: "",
            totalSvls: 0,
            totalGroups: 0,
            pageSize: 80,
        });

        this.reportRef = useRef("reportContainer");

        onWillStart(async () => {
            const [products, classifications] = await Promise.all([
                this.getProducts(),
                this.getClassifications(),
            ]);
            this.state.products = products;
            this.state.classifications = classifications;
            await this.renderHtml();
        });

        // Após cada renderização, aplica visibilidade inicial da paginação
        useEffect(
            () => {
                this.applyAllPagination();
            },
            () => [this.state.html]
        );
    }

    get isoDate() {
        return this.state.date ? this.state.date.toFormat("yyyy-MM-dd") : "";
    }

    get reportParams() {
        return {
            date: this.isoDate,
            product_id: this.state.selectedProductId || "",
            classification: this.state.selectedClassification || "",
            accounting_filter: this.state.accountingFilter || "all",
            page_size: this.state.pageSize,
        };
    }

    async getProducts() {
        const products = await this.orm.searchRead(
            "product.product",
            [["is_storable", "=", true]],
            ["id", "display_name"]
        );
        const out = products.map((p) => ({ id: p.id, name: p.display_name }));
        out.sort((a, b) => (a.name || "").localeCompare(b.name || ""));
        return out;
    }

    async getClassifications() {
        const res = await this.orm.call(
            "product.template",
            "fields_get",
            [["product_classification"]],
            { attributes: ["selection"] }
        );
        const selection = (res.product_classification && res.product_classification.selection) || [];
        return selection.map(([value, label]) => ({ value, label }));
    }

    onSelectClassification(ev) {
        this.state.selectedClassification = ev.target.value;
        this.renderHtml();
    }

    onSelectAccountingFilter(ev) {
        this.state.accountingFilter = ev.target.value || "all";
        this.renderHtml();
    }

    async renderHtml() {
        const result = await this.orm.call(
            "report.mh_stone_reports.report_stock_valuation",
            "get_html",
            [],
            { data: this.reportParams }
        );
        this.state.html = markup(result.html);
        this.state.totalSvls = result.total_svls;
        this.state.totalGroups = result.total_groups;
        this.state.pageSize = result.page_size;
    }

    onChangeDate(date) {
        this.state.date = date || DateTime.now();
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
            match = this.state.products.find((p) =>
                (p.name || "").toLowerCase().includes(low)
            );
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

    async onClickPrint() {
        const select = document.getElementById("stock_valuation_format");
        const format = select ? select.value : "pdf";
        const params = {
            date: this.isoDate,
            product_id: this.state.selectedProductId || "",
            classification: this.state.selectedClassification || "",
            accounting_filter: this.state.accountingFilter || "all",
        };
        await download({
            url: "/stock_valuation/export/",
            data: {
                report_data: JSON.stringify(params),
                export_format: format,
            },
        });
    }

    // ───────────────── Paginação por grupo (client-side) ─────────────────

    applyAllPagination() {
        const root = this.reportRef.el;
        if (!root) return;
        // Inverter ordem DOM (mais recente primeiro) e re-indexar antes de paginar
        root.querySelectorAll("tbody.o_group_block").forEach((block) => {
            const rows = Array.from(block.querySelectorAll("tr.o_group_row"));
            if (rows.length > 1) {
                rows.reverse().forEach((row, idx) => {
                    row.dataset.rowIndex = String(idx);
                    block.appendChild(row);
                });
            }
            this.applyGroupPage(block);
        });
        // Estado inicial: classificações colapsadas → esconder os blocos de
        // produto de cada classificação marcada como o_class_collapsed.
        root.querySelectorAll("tbody.o_classification_block.o_class_collapsed").forEach((classBlock) => {
            let sib = classBlock.nextElementSibling;
            while (sib && !sib.classList.contains("o_classification_block")) {
                if (sib.classList.contains("o_group_block")) {
                    sib.style.display = "none";
                }
                sib = sib.nextElementSibling;
            }
        });
    }

    applyGroupPage(block) {
        const pageSize = parseInt(block.dataset.pageSize || "80", 10);
        const currentPage = parseInt(block.dataset.currentPage || "1", 10);
        const svlCount = parseInt(block.dataset.svlCount || "0", 10);
        const start = (currentPage - 1) * pageSize;
        const end = start + pageSize;

        block.querySelectorAll("tr.o_group_row").forEach((row) => {
            const idx = parseInt(row.dataset.rowIndex || "0", 10);
            row.style.display = idx >= start && idx < end ? "" : "none";
        });

        const rangeEl = block.querySelector(".o_page_range");
        if (rangeEl) {
            const last = Math.min(end, svlCount);
            rangeEl.textContent = `${start + 1}–${last}`;
        }
        const cur = block.querySelector(".o_current_page");
        if (cur) cur.textContent = String(currentPage);

        const totalPages = parseInt(block.dataset.totalPages || "1", 10);
        const prev = block.querySelector(".o_page_prev");
        const next = block.querySelector(".o_page_next");
        if (prev) prev.classList.toggle("disabled", currentPage <= 1);
        if (next) next.classList.toggle("disabled", currentPage >= totalPages);
    }

    onClickReport(ev) {
        // Link para registo
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

        // Paginação
        const pageBtn = ev.target.closest(".o_page_prev, .o_page_next");
        if (pageBtn) {
            ev.preventDefault();
            if (pageBtn.classList.contains("disabled")) return;
            const block = pageBtn.closest("tbody.o_group_block");
            if (!block) return;
            const current = parseInt(block.dataset.currentPage || "1", 10);
            const total = parseInt(block.dataset.totalPages || "1", 10);
            const next = pageBtn.classList.contains("o_page_next")
                ? Math.min(current + 1, total)
                : Math.max(current - 1, 1);
            block.dataset.currentPage = String(next);
            this.applyGroupPage(block);
            return;
        }

        // Expand/collapse de CLASSIFICAÇÃO — esconde/mostra todos os blocos
        // de produto até à próxima classificação.
        const classHeader = ev.target.closest("tr.o_classification_header");
        if (classHeader) {
            const classBlock = classHeader.closest("tbody.o_classification_block");
            if (classBlock) {
                const collapsing = !classBlock.classList.contains("o_class_collapsed");
                classBlock.classList.toggle("o_class_collapsed", collapsing);
                const chevron = classHeader.querySelector(".o_class_chevron");
                if (chevron) {
                    chevron.classList.toggle("fa-chevron-down", !collapsing);
                    chevron.classList.toggle("fa-chevron-right", collapsing);
                }
                let sib = classBlock.nextElementSibling;
                while (sib && !sib.classList.contains("o_classification_block")) {
                    if (sib.classList.contains("o_group_block")) {
                        sib.style.display = collapsing ? "none" : "";
                    }
                    sib = sib.nextElementSibling;
                }
            }
            return;
        }

        // Expand/collapse de PRODUTO
        const header = ev.target.closest("tr.o_group_header");
        if (header) {
            const block = header.closest("tbody.o_group_block");
            if (block) {
                block.classList.toggle("collapsed");
                const chevron = header.querySelector(".o_group_chevron");
                if (chevron) {
                    chevron.classList.toggle("fa-chevron-right");
                    chevron.classList.toggle("fa-chevron-down");
                }
            }
        }
    }
}

registry
    .category("actions")
    .add("generate_stock_valuation_report", StockValuationReport);
