/** @odoo-module **/

import { Component, markup, onMounted, onWillStart, onWillUnmount, useEffect, useRef, useState } from "@odoo/owl";
import { download } from "@web/core/network/download";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Layout } from "@web/search/layout";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";

export class StockNoStockReport extends Component {
    static props = { ...standardActionServiceProps };
    static components = { Layout };
    static template = "mh_stone_reports.StockNoStockReport";

    setup() {
        this.action = useService("action");
        this.orm = useService("orm");

        this.state = useState({
            classifications: [],
            suppliers: [],
            warehouses: [],
            selectedClassifications: [],
            selectedSupplierId: false,
            selectedWarehouseId: false,
            classificationDropdownOpen: false,
            html: "",
            totalProducts: 0,
            pageSize: 100,
        });

        this.reportRef = useRef("reportContainer");

        onWillStart(async () => {
            const [classifications, suppliers, warehouses] = await Promise.all([
                this.getClassifications(),
                this.getSuppliers(),
                this.getWarehouses(),
            ]);
            this.state.classifications = classifications;
            this.state.suppliers = suppliers;
            this.state.warehouses = warehouses;
            await this.renderHtml();
        });

        useEffect(
            () => {
                this.applyAllPagination();
            },
            () => [this.state.html]
        );

        this._onDocumentClick = (ev) => {
            if (!this.state.classificationDropdownOpen) return;
            const dropdown = document.querySelector(".o_stock_no_stock_report .o_classification_dropdown");
            if (dropdown && !dropdown.contains(ev.target)) {
                this.state.classificationDropdownOpen = false;
            }
        };
        onMounted(() => {
            document.addEventListener("click", this._onDocumentClick);
        });
        onWillUnmount(() => {
            document.removeEventListener("click", this._onDocumentClick);
        });
    }

    get reportParams() {
        return {
            classifications: this.state.selectedClassifications.join(","),
            supplier_id: this.state.selectedSupplierId || "",
            warehouse_id: this.state.selectedWarehouseId || "",
            page_size: this.state.pageSize,
        };
    }

    get classificationButtonLabel() {
        const n = this.state.selectedClassifications.length;
        if (n === 0) return "— Todas —";
        if (n === 1) {
            const v = this.state.selectedClassifications[0];
            const c = this.state.classifications.find((x) => x.value === v);
            return c ? c.label : v;
        }
        return `${n} seleccionadas`;
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

    async getSuppliers() {
        const rows = await this.orm.searchRead(
            "res.partner",
            [["supplier_rank", ">", 0]],
            ["id", "display_name"]
        );
        const out = rows.map((r) => ({ id: r.id, name: r.display_name }));
        out.sort((a, b) => (a.name || "").localeCompare(b.name || ""));
        return out;
    }

    async getWarehouses() {
        const rows = await this.orm.searchRead(
            "stock.warehouse",
            [],
            ["id", "name"]
        );
        const out = rows.map((r) => ({ id: r.id, name: r.name }));
        out.sort((a, b) => (a.name || "").localeCompare(b.name || ""));
        return out;
    }

    toggleClassificationDropdown() {
        this.state.classificationDropdownOpen = !this.state.classificationDropdownOpen;
    }

    toggleClassification(value) {
        const idx = this.state.selectedClassifications.indexOf(value);
        if (idx >= 0) {
            this.state.selectedClassifications.splice(idx, 1);
        } else {
            this.state.selectedClassifications.push(value);
        }
        this.renderHtml();
    }

    clearClassifications() {
        this.state.selectedClassifications = [];
        this.renderHtml();
    }

    onSelectSupplier(ev) {
        const typed = (ev.target.value || "").trim();
        if (!typed) {
            this.state.selectedSupplierId = false;
        } else {
            let m = this.state.suppliers.find((s) => s.name === typed);
            if (!m) {
                const low = typed.toLowerCase();
                m = this.state.suppliers.find((s) => (s.name || "").toLowerCase().includes(low));
            }
            this.state.selectedSupplierId = m ? m.id : false;
        }
        this.renderHtml();
    }

    onSelectWarehouse(ev) {
        this.state.selectedWarehouseId = ev.target.value ? parseInt(ev.target.value, 10) : false;
        this.renderHtml();
    }

    onTypeBlank(ev, key) {
        if (!ev.target.value) {
            if (key === "supplier") this.state.selectedSupplierId = false;
            this.renderHtml();
        }
    }

    async renderHtml() {
        const result = await this.orm.call(
            "report.mh_stone_reports.report_stock_no_stock",
            "get_html",
            [],
            { data: this.reportParams }
        );
        this.state.html = markup(result.html);
        this.state.totalProducts = result.total_products;
        this.state.pageSize = result.page_size;
    }

    async onClickPrint() {
        const select = document.getElementById("stock_no_stock_format");
        const format = select ? select.value : "pdf";
        await download({
            url: "/stock_no_stock/export/",
            data: {
                report_data: JSON.stringify(this.reportParams),
                export_format: format,
            },
        });
    }

    applyAllPagination() {
        const root = this.reportRef.el;
        if (!root) return;
        root.querySelectorAll("tbody.o_group_block").forEach((block) => {
            const rows = Array.from(block.querySelectorAll("tr.o_group_row"));
            rows.forEach((row, idx) => { row.dataset.rowIndex = String(idx); });
            this.applyGroupPage(block);
        });
    }

    applyGroupPage(block) {
        const pageSize = parseInt(block.dataset.pageSize || "100", 10);
        const currentPage = parseInt(block.dataset.currentPage || "1", 10);
        const rowCount = parseInt(block.dataset.rowCount || "0", 10);
        const totalPages = parseInt(block.dataset.totalPages || "1", 10);
        const start = (currentPage - 1) * pageSize;
        const end = start + pageSize;

        block.querySelectorAll("tr.o_group_row").forEach((row) => {
            const idx = parseInt(row.dataset.rowIndex || "0", 10);
            row.style.display = idx >= start && idx < end ? "" : "none";
        });

        const rangeEl = block.querySelector(".o_page_range");
        if (rangeEl) {
            const last = Math.min(end, rowCount);
            rangeEl.textContent = `${start + 1}–${last}`;
        }
        const cur = block.querySelector(".o_current_page");
        if (cur) cur.textContent = String(currentPage);

        const prev = block.querySelector(".o_page_prev");
        const next = block.querySelector(".o_page_next");
        if (prev) prev.classList.toggle("disabled", currentPage <= 1);
        if (next) next.classList.toggle("disabled", currentPage >= totalPages);
    }

    onClickReport(ev) {
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
    .add("generate_stock_no_stock_report", StockNoStockReport);
