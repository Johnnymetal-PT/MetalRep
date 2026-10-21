import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, useRef, onMounted } from "@odoo/owl";
import { AlanSelectSearch } from "../../alan_select_search/alan_select_search";

// ─── Snippet Builder MegaMenu Category ─────────────────────────────────
export class MegaMenuSubCategory extends Component {
    static template = "theme_alan.m_sub_category";
    static components = { Dialog };
    static props = {
        parent_id: Number,
        pre_selected_ids: { type: Array, optional: true },
        onConfirm: Function,
    };

    setup() {
        this.orm = useService("orm");
        this.categ_val = useRef("search_record");
        this.title = _t("Select Sub-Categories");
        this.footer = true;
        this.header = true;

        this.search = "product.public.category";
        this.selected = useState([]);
        this.selectSearch = null;
        this.removeSelected = this.removeSelected.bind(this);

        onMounted(() => {
            this._loadPreSelected();
            this._initSearchSubCategory();
        });
    }

    async _loadPreSelected() {
        const ids = this.props.pre_selected_ids || [];
        if (ids && ids.length > 0) {
            try {
                const records = await this.orm.read(
                    this.search,
                    ids,
                    ["id", "display_name"]
                );
                const selectedCategories = records.map(rec => ({
                    id: rec.id,
                    name: rec.display_name,
                }));

                this.selected.push(...selectedCategories);
            } catch (e) {
                console.error("Error loading pre-selected categories:", e);
            }
        }
    }

    _initSearchSubCategory() {
        if (!this.categ_val.el) return;
        this.selectSearch = new AlanSelectSearch(
            this.categ_val.el,
            this.search,
            this._onCategorySelect.bind(this),
            {
                debounceTime: 300,
                multiple: true,
                extraParams: {
                    parent_category: this.props.parent_id || 0,
                },
            }
        );
    }

    _onCategorySelect(record) {
        if (!record || !record.id) return;
        const exists = this.selected.some(r => r.id === record.id);
        if (!exists) {
            this.selected.push({
                id: record.id,
                name: record.name,
            });
        }
        if (this.categ_val.el) {
            this.categ_val.el.value = "";
        }
    }

    removeSelected(id) {
        const index = this.selected.findIndex(r => r.id === id);
        if (index > -1) {
            this.selected.splice(index, 1);
        }
    }

    _selectionDone() {
        if (this.props.onConfirm) {
            this.props.onConfirm([...this.selected]);
        }
        this.props.close();
    }
}