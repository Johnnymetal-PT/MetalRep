import { Component, useState, useRef, useEffect, useInteractOutside, onWillStart } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { AlanSelectSearch } from "../../alan_select_search/alan_select_search";
import { useSortable } from "@web/core/utils/sortable_owl";
import { MegaMenuSubCategory } from "./MegaMenuSubCategory";

const MODEL_MAP = {
    Products: { model: "product.template", active_model: "Products" },
    Variants: { model: "product.product", active_model: "Variants" },
};

function getEventValue(ev) {
    return ev && ev.target ? ev.target.value : "";
}

// ─── Snippet Builder Configuration Component ─────────────────────────────────
export class SnippetBuilderConfig extends Component {
    static template = "theme_alan.snippet_builder_configuration";
    static props = {
        editor: Object,
        config: Object,
        snippet_type: String,
    };

    setup() {
        this.dialog = useService("dialog");
        this.inputRef = useRef("search_record");
        this.sortableContainer = useRef("sortableContainer");
        this.searchRecords = null;
        this.selectSearch = null;
        this._filterSelects = new Map();
        this.subCategory = useState({ 'second_level': [], 'second_level_ids': [] });
        this.state = useState({
            showWarning: false,
            warningMessage: "",
            bg_mode: "color",
            selectedColor: "#FFB8B8",
            blurAmount: 24,
            angle: 62,
            activeTab: null,
            mmActiveSection: null,
        });

        useEffect(() => {
            this.state.warningMessage = ""
            if (this.props.config?.technical_name === "product_spotlight") {
                this.state.activeTab = "design";
            } else if (!this.state.activeTab) {
                this.state.activeTab = "selection";
            }

            if (!this.props.config.selection_mode_default) {
                this.props.config.selection_mode_default = 'manual';
            }

            if (
                this.props.config?.default_mm_section &&
                (!this.state.mmActiveSection || !this.state.mmActiveSection.key)
            ) {
                let sectionKey = this.props.config.default_mm_section;
                let section = this.props.config.sections?.[sectionKey];

                if (section) {
                    this.state.mmActiveSection = {
                        key: sectionKey,
                        ...section,
                    };
                }
            }
            this.initializeSearch();
            setTimeout(() => this._initAllFilterSelects(), 100);

            return () => {
                if (this.selectSearch) {
                    this.selectSearch.destroy();
                    this.selectSearch = null;
                }
                if (this.inputRef.el) {
                    const wrapper = this.inputRef.el.parentNode;
                    if (wrapper) {
                        const dropdowns = wrapper.querySelectorAll('.alan-select-dropdown');
                        dropdowns.forEach(d => d.remove());
                    }
                }
                this._destroyAllFilterSelects();
            };
        }, () => [
            this.props.config?.technical_name,
            this.state.mmActiveSection?.key
        ]);

        this._sortable();
    }

    onTabClick(tabName) {
        this.state.activeTab = tabName;
    }

    // ───────────────── Get Options ────────────────────────────
    get currentActiveTab() {
        return this.state.activeTab;
    }

    get filterFieldOptions() {
        return [
            { value: "name", label: "Name" },
            { value: "public_categ_ids", label: "Category" },
            { value: "product_brand_id", label: "Brand" },
            { value: "list_price", label: "Price" },
            { value: "product_tag_ids", label: "Tags" },
            { value: "website_ribbon_id", label: "Label" },
            { value: "attribute_line_ids", label: "Attributes" },
        ];
    }

    filterOperatorOptions(filter) {
        if (filter.field === "list_price") {
            return [
                { value: "=", label: "equals" },
                { value: ">", label: "greater than" },
                { value: "<", label: "less than" },
            ];
        }
        if (filter.field === "name") {
            return [
                { value: "ilike", label: "contains" },
                { value: "not ilike", label: "not contain" },
                { value: "=ilike", label: "starts with" },
            ]
        }
        return [
            { value: "ilike", label: "contains" },
            { value: "not ilike", label: "not contain" },
            { value: "=ilike", label: "starts with" },
            { value: "set", label: "is set" },
            { value: "not_set", label: "is not set" },
            { value: "=", label: "is equal to" },
            { value: "!=", label: "is not equal to" },
        ];
    }

    getFilterLabel(filter) {
        const snippetName = this.props.config.name;
        const fieldOption = this.filterFieldOptions.find(opt => opt.value === filter.field);
        const operatorOption = this.filterOperatorOptions(filter).find(opt => opt.value === filter.operator);
        const fieldLabel = fieldOption ? fieldOption.label : filter.field || "Field";
        const operatorLabel = operatorOption ? operatorOption.label : filter.operator || "Operator";

        return `${snippetName} ${fieldLabel} "${operatorLabel}"`;
    }

    get orderByOptions() {
        return [
            { id: "latest_product", name: "New Arrival", description: "Show most recently published products" },
            { id: "best_seller", name: "Best Seller", description: "Show products with highest sales" },
            { id: "top_related", name: "Top Related", description: "Show related products based on current context" },
            { id: "random", name: "Random Products", description: "Show a random selection of products" },
            { id: "a_to_z", name: "Name: A → Z", description: "Show a Product with Name A to Z" },
            { id: "z_to_a", name: "Name: Z → A", description: "Show a Product with Name Z to A" },
            { id: "low_to_high", name: "Price: Low → High", description: "Show a Product with Price A to Z" },
            { id: "high_to_low", name: "Price: High → Low", description: "Show a Product with Price A to Z" },
        ]
    }

    get sliderPagination() {
        return [
            ['none', 'None'],
            ['simple', 'Simple'],
            ['dynamic', 'Dynamic'],
            ['progress_bar', 'Progress Bar'],
            ['fraction', 'Fraction'],
            ['scroll_bar', 'Scrollbar'],
            ['coverflow', 'Coverflow'],
            ['cards', 'Cards'],
        ]
    }

    get desktopItem() {
        const technicalName = this.props.config.technical_name;
        let colList = [];

        if (technicalName === 'ProductBanner' || technicalName === 'product_banner') {
            colList = [1, 2];
        } else {
            colList = [1, 2, 3, 4, 5, 6];
        }

        return colList.map((col, index) => ({
            value: col,
            label: `Screen ${col}`,
        }));
    }

    get mobileItem() {
        const technicalName = this.props.config.technical_name;
        let colList = [];

        if (technicalName === 'categories' || technicalName === 'brands') {
            colList = [1, 2, 3, 4];
        }
        else {
            colList = [1, 2];
        }
        return colList.map((col, index) => ({
            value: col,
            label: `Screen ${col}`,
        }));
    }

    get sliderLayouts() {
        const bannerSliders = ["product_banner", "ProductBanner"];
        const technicalNames = ["categories_products", "brand_products", "CategoryProduct", "BrandProduct"];
        const { technical_name, slider_layout_style } = this.props.config;
        let sliderPrefix = technicalNames.includes(technical_name)
            ? "as-tab-slider-"
            : "as-slider-";
        let sliderCount = bannerSliders.includes(technical_name) ? 3 : 5;
        if (technical_name === "categories") {
            sliderCount = 7;
        }
        const styles = [];
        for (let i = 1; i <= sliderCount; i++) {
            styles.push([
                `Style ${i}`,
                `theme_alan.${slider_layout_style}`,
                `${sliderPrefix}${i}`,
            ]);
        }
        return styles;
    }

    get megaMenuLayouts() {
        const styles = [];
        const templateId = this.props.config.template_id;
        for (let i = 1; i <= 2; i++) {
            styles.push([
                `Style ${i}`,
                `${templateId}`,
                `as-slider-${i}`,
            ]);
        }
        return styles;
    }

    get gridLayouts() {
        const bannerSliders = ["product_banner", "ProductBanner"];
        const technicalNames = ["categories_products", "brand_products", "CategoryProduct", "BrandProduct"];
        const { technical_name } = this.props.config;
        const grid_layout_style = this.props.config.grid_layout_style;

        let gridPrefix = technicalNames.includes(technical_name)
            ? "as-tab-grid-"
            : "as-grid-";

        let gridCount = bannerSliders.includes(technical_name) ? 3 : 5;

        if (technical_name === "categories") {
            gridCount = 7;
        }

        if (technical_name === "highlighted_product_grid" || technical_name === "product_spotlight") {
            gridCount = 2;
        }
        const styles = [];
        for (let i = 1; i <= gridCount; i++) {
            styles.push([
                `Style ${i}`,
                `theme_alan.${grid_layout_style}`,
                `${gridPrefix}${i}`,
            ]);
        }
        return styles;
    }

    get preDefineTemplates() {
        return [
            {
                id: "latest_products",
                name: "Latest Products",
                description: "Displays the most recently published products.",
                order_by: "latest_product",
                filters: [],
            },
            {
                id: "latest_by_category",
                name: "Latest Collection by Category",
                description: "Displays the newest products filtered by selected categories.",
                order_by: "latest_product",
                filters: [{ field: "categ_id", operator: "set", value: false }],
            },
            {
                id: "latest_by_brand",
                name: "Latest Collection by Brand",
                description: "Displays the newest products filtered by selected brands.",
                order_by: "latest_product",
                filters: [{ field: "product_brand_id", operator: "set", value: false }],
            },
            {
                id: "latest_by_tag",
                name: "Latest Collection by Tag",
                description: "Displays the newest products filtered by selected tags.",
                order_by: "latest_product",
                filters: [{ field: "product_tag_ids", operator: "set", value: false }],
            },
            {
                id: "product_attributes",
                name: "Product Attribute Sets",
                description: "Displays products filtered by selected attribute values.",
                order_by: "a_to_z",
                filters: [{ field: "attribute_line_ids", operator: "set", value: false }],
            },
            {
                id: "best_selling",
                name: "Top Selling Products",
                description: "Displays products with the highest sales volume.",
                order_by: "best_seller",
                filters: [],
            },
            {
                id: "best_selling_by_category",
                name: "Top Selling by Category",
                description: "Displays top-selling products filtered by selected categories.",
                order_by: "best_seller",
                filters: [{ field: "categ_id", operator: "set", value: false }],
            },
            {
                id: "best_selling_by_brand",
                name: "Top Selling by Brand",
                description: "Displays top-selling products filtered by selected brands.",
                order_by: "best_seller",
                filters: [{ field: "product_brand_id", operator: "set", value: false }],
            },
            {
                id: "best_selling_by_tag",
                name: "Top Selling by Tag",
                description: "Displays top-selling products filtered by selected tags.",
                order_by: "best_seller",
                filters: [{ field: "product_tag_ids", operator: "set", value: false }],
            },
            {
                id: "recommended_products",
                name: "Recommended Products",
                description: "Displays products recommended based on user or product context.",
                order_by: "top_related",
                filters: [],
            },
        ];
    }

    // ───────────────── Update Editors ────────────────────────────
    _updateConfig(patch = {}) {
        if (!this.props?.config) return;

        if ('record_limit' in patch) {
            let limit = parseInt(patch.record_limit);
            if (isNaN(limit) || limit < 1) limit = 1;
            if (limit > 100) limit = 100;
            patch.record_limit = limit;
        }

        if ('slider_time' in patch) {
            let time = parseInt(patch.slider_time);
            if (isNaN(time) || time < 1) time = 1;
            if (time > 10) time = 10;
            patch.slider_time = time;
        }

        Object.assign(this.props.config, patch);
        this._emitConfigUpdated();
    }

    _emitConfigUpdated() {
        this.env.bus.trigger("config_updated", this.props.config);
    }

    // ───────────────── Selection Tab ────────────────────────────
    initializeSearch() {
        if (!this.inputRef.el) return;

        if (this.selectSearch) {
            this.selectSearch.destroy();
        }
        const wrapper = this.inputRef.el.parentNode;
        if (wrapper) {
            const existingDropdowns = wrapper.querySelectorAll('.alan-select-dropdown');
            existingDropdowns.forEach(dropdown => dropdown.remove());
        }

        const model = this.props.config?.model;
        setTimeout(() => {
            this.selectSearch = new AlanSelectSearch(
                this.inputRef.el,
                model,
                this.onProductSelect.bind(this),
                {
                    debounceTime: 300,
                    multiple: true,
                }
            )
        }, 0);
    }

    _filterFieldToModel(field) {
        switch (field) {
            case 'public_categ_ids':
                return 'product.public.category';
            case 'product_brand_id':
                return 'as.product.brand';
            case 'product_tag_ids':
                return 'product.tag';
            case 'attribute_line_ids':
                return 'product.attribute';
            case 'website_ribbon_id':
                return 'product.ribbon';
            default:
                return null;
        }
    }

    _getFilterRowEl(filter) {
        return document.querySelector(`[data-filter-id="${filter.id}"]`);
    }

    _initAllFilterSelects() {
        const filters = this.props.config.filters || [];
        filters.forEach(f => this._initFilterSelect(f));
    }

    _destroyAllFilterSelects() {
        this._filterSelects.forEach((inst, id) => {
            try { inst.destroy && inst.destroy(); } catch (e) { }
        });
        this._filterSelects.clear();
    }

    _destroyFilterSelect(filter) {
        const inst = this._filterSelects.get(filter.id);
        const row = this._getFilterRowEl(filter);
        if (inst) {
            try { inst.destroy && inst.destroy(); } catch (e) { }
            this._filterSelects.delete(filter.id);
        }
        if (row) {
            const dropdowns = row.querySelectorAll('.alan-select-dropdown');
            dropdowns.forEach(d => d.remove());
        }
    }

    _initFilterSelect(filter) {
        if (!filter || !filter.id) {
            console.warn('_initFilterSelect: No filter or filter.id');
            return;
        }

        const row = this._getFilterRowEl(filter);
        if (!row) {
            console.warn('_initFilterSelect: Filter row not found for filter', filter.id);
            return;
        }

        const inputEl = row.querySelector('.filter-value');
        if (!inputEl) {
            console.warn('_initFilterSelect: Input element not found for filter', filter.id);
            return;
        }

        if (filter.field === 'list_price') {
            this._destroyFilterSelect(filter);
            if (['>', '<', '='].includes(filter.operator) && !filter.locked) {
                inputEl.removeAttribute('readonly');
                inputEl.removeAttribute('readonly');
                inputEl.type = "number";
                inputEl.step = "0.01";
            }
            return;
        }

        if (filter.field === 'name') {
            this._destroyFilterSelect(filter);
            if (['ilike', 'not ilike', '=ilike'].includes(filter.operator) && !filter.locked) {
                inputEl.removeAttribute('readonly');
                inputEl.type = "text";
            }
            return;
        }

        if (['set', 'not_set'].includes(filter.operator)) {
            this._destroyFilterSelect(filter);
            inputEl.setAttribute('readonly', 'readonly');
            return;
        }

        if (['ilike', 'not ilike', '=ilike'].includes(filter.operator)) {
            this._destroyFilterSelect(filter);
            if (!filter.locked) {
                inputEl.removeAttribute('readonly');
            }
            return;
        }

        if (!['=', '!='].includes(filter.operator)) {
            this._destroyFilterSelect(filter);
            inputEl.removeAttribute('readonly');
            return;
        }

        const model = this._filterFieldToModel(filter.field);
        if (this._filterSelects.has(filter.id)) {
            return;
        }

        try {
            const instance = new AlanSelectSearch(
                inputEl,
                model,
                (record) => this._onFilterSelected(filter, record),
                {
                    debounceTime: 300,
                    multiple: true
                }
            );
            this._filterSelects.set(filter.id, instance);
        } catch (e) {
            console.error('Failed to init AlanSelectSearch for filter', filter.field, e);
        }
    }


    _onFilterSelected(filter, record) {
        if (!['=', '!='].includes(filter.operator)) {
            return;
        }

        if (record && record.id) {
            if (!filter.selected_items) {
                filter.selected_items = [];
            }

            const exists = filter.selected_items.some(item => item.id === record.id);
            if (!exists) {
                filter.selected_items.push({
                    id: record.id,
                    name: record.name || record.display_name || ''
                });

                filter.value = filter.selected_items.map(item => item.id);

                const row = this._getFilterRowEl(filter);
                const inputEl = row ? row.querySelector('.filter-value') : null;
                if (inputEl) {
                    inputEl.value = '';
                }
                this.render();
            }
        }
    }

    async onProductSelect(record) {
        if (!record || !record.id || record.id === 0) {
            return;
        }
        let selectedRecords = this.props.config.selected_records || [];
        let limit = Number(20);

        if (this.props.config.technical_name == 'highlighted_product_grid') {
            limit = Number(this.props.config.record_limit || 0);
        }
        if (this.props.config.technical_name == 'brand_collection_showcase') {
            limit = Number(6);
        }

        if (selectedRecords.length >= limit) {
            this.state.showWarning = true;
            this.state.warningMessage = `Your Record Limit Will be ${limit}.`
            return;
        }
        else if (selectedRecords.length <= limit) {
            this.state.showWarning = false;
            this.state.warningMessage = "";
            selectedRecords = selectedRecords.filter(id => id !== record.id);
            selectedRecords.unshift(record.id);
            const patch = { selected_records: selectedRecords };
            if (this.state.mmActiveSection && this.props.config.sections) {
                const key = this.state.mmActiveSection.key;
                if (key && this.props.config.sections[key]) {
                    const sections = { ...this.props.config.sections };
                    sections[key] = { ...sections[key], record_ids: selectedRecords };
                    patch.sections = sections;
                }
            }
            this._updateConfig(patch);
        }

        if (this.inputRef.el) {
            setTimeout(() => {
                this.inputRef.el.value = "";
                this.inputRef.el.dispatchEvent(new Event("input", { bubbles: true }));
            }, 0);
        }
    }

    _sortable() {
        useSortable({
            ref: this.sortableContainer,
            elements: ".sortable-record-item",
            handle: ".drag-handle",
            cursor: "grabbing",
            tolerance: 10,
            onDrop: ({ element, previous }) => {
                const oldIndex = parseInt(element.dataset.index);
                let newIndex = 0;
                if (previous) {
                    newIndex = parseInt(previous.dataset.index) + 1;
                }
                this.updateProductOrder(oldIndex, newIndex);
            }
        });
    }

    updateProductOrder(oldIndex, newIndex) {
        const records = [...this.props.config.selected_records];
        const movedItem = records.splice(oldIndex, 1)[0];
        const adjustedIndex = oldIndex < newIndex ? newIndex - 1 : newIndex;
        records.splice(adjustedIndex, 0, movedItem);
        const patch = { selected_records: records };
        if (this.state.mmActiveSection && this.props.config.sections) {
            const key = this.state.mmActiveSection.key;
            if (key && this.props.config.sections[key]) {
                const sections = { ...this.props.config.sections };
                sections[key] = { ...sections[key], record_ids: records };
                patch.sections = sections;
            }
        }
        this._updateConfig(patch);
    }

    onChangeSelection(ev) {
        const val = getEventValue(ev);
        Object.assign(this.props.config, this.props.editor);
        this.props.config.selected_records = []
        const patch = { selection_mode_default: val };
        if (this.state.mmActiveSection && this.props.config.sections) {
            const key = this.state.mmActiveSection.key;
            if (this.props.config.sections[key]) {
                this.props.config.sections[key].record_ids = [];
                patch.sections = this.props.config.sections;
            }
        }
        this._updateConfig(patch);
    }

    removeRecord(record) {
        if (!record || !record.id) return;
        const selected = this.props.config.selected_records || [];

        let updated = selected.filter(id => id !== record.id);

        const actualCount = updated.length === 1 && updated[0] === 0 ? 0 : updated.length;
        let limit = Number(20);

        if (this.props.config.technical_name == 'highlighted_product_grid') {
            limit = Number(this.props.config.record_limit || 0);
        }
        if (this.props.config.technical_name == 'brand_collection_showcase') {
            limit = Number(6);
        }

        if (limit > 0 && actualCount >= limit) {
            this.state.showWarning = true;
            this.state.warningMessage = `Your Record Limit Will be ${limit}.`;
        } else {
            this.state.showWarning = false;
            this.state.warningMessage = "";
        }

        if (this.inputRef && this.inputRef.el) {
            setTimeout(() => {
                this.inputRef.el.value = "";
                this.inputRef.el.dispatchEvent(new Event("input", { bubbles: true }));
            }, 0);
        }

        if (this.props.config.selected_records.length == 1) {
            updated = [0]
        }

        const patch = { selected_records: updated };
        if (this.state.mmActiveSection && this.props.config.sections) {
            const key = this.state.mmActiveSection.key;
            if (key && this.props.config.sections[key]) {
                const sections = { ...this.props.config.sections };
                sections[key] = { ...sections[key], record_ids: updated };
                patch.sections = sections;
            }
        }

        this._updateConfig(patch);
    }

    onChangeModel(ev) {
        const val = getEventValue(ev);
        const mapped = MODEL_MAP[val];
        this.props.config.selected_records = []
        if (mapped) {
            const patch = { model: mapped.model, active_model: mapped.active_model };
            if (this.state.mmActiveSection && this.props.config.sections) {
                const key = this.state.mmActiveSection.key;
                if (this.props.config.sections[key]) {
                    this.props.config.sections[key].record_ids = [];
                    patch.sections = this.props.config.sections;
                }
            }
            this._updateConfig(patch);
            this.initializeSearch();
        }
    }

    onChangeMode(ev) {
        const val = getEventValue(ev);
        let template_id = this.props.config.template_id
        if (val == "grid") {
            template_id = this.props.config.default_gtemplate_id
        }
        else {
            template_id = this.props.config.default_stemplate_id
        }
        this._updateConfig({ active_view: val, template_id: template_id });
    }

    onChangeOrderBy(ev) {
        const selected = getEventValue(ev);
        this._updateConfig({ active_quick_selction: selected });
    }

    addNewFilter() {
        const filters = this.props.config.filters || [];
        const newFilter = { id: Date.now(), field: "name", operator: "ilike", value: "", locked: false };
        this._updateConfig({ filters: [...filters, newFilter] });
        setTimeout(() => this._initFilterSelect(newFilter), 100);
    }

    removeFilter(filter) {
        try { this._destroyFilterSelect(filter); } catch (e) { }
        const filters = this.props.config.filters || [];
        this._updateConfig({ filters: filters.filter((f) => f.id !== filter.id) });
    }

    removeFilterItem(filter, item) {
        if (!filter.selected_items) return;
        filter.selected_items = filter.selected_items.filter(i => i.id !== item.id);
        filter.value = filter.selected_items.map(i => i.id);
        this._emitConfigUpdated();
        this.render();
    }

    setFilter(ev, filter) {
        const row = ev.target.closest("[data-filter-id]");
        if (!row) return;

        const field = row.querySelector(".filter-field")?.value ?? "";
        const operator = row.querySelector(".filter-operator")?.value ?? "";

        filter.field = field;
        filter.operator = operator;
        if (['ilike', 'not ilike', '=ilike'].includes(operator)) {
            const inputEl = row.querySelector('.filter-value');
            const textValue = inputEl?.value?.trim() ?? "";
            filter.value = textValue;
            filter.selected_items = [];
        }
        else if (field === 'list_price' && ['>', '<', '='].includes(operator)) {
            const inputEl = row.querySelector('.filter-value');
            const priceValue = inputEl?.value?.trim() ?? "";
            filter.value = priceValue ? parseFloat(priceValue) : "";
            filter.selected_items = [];
        }
        else if (['set', 'not_set'].includes(operator)) {
            filter.value = "";
            filter.selected_items = [];
        }

        filter.locked = true;
        this._emitConfigUpdated();
    }

    editFilter(ev, filter) {
        filter.locked = false;
        const row = this._getFilterRowEl(filter);
        const inputEl = row ? row.querySelector('.filter-value') : null;
        if (inputEl && !['=', '!='].includes(filter.operator)) {
            inputEl.removeAttribute('readonly');
        }

        this.render();
    }

    onMatchChange(ev) {
        const val = getEventValue(ev);
        this._updateConfig({ filter_match: val });
    }

    getFieldPlaceholder(field, operator) {
        if (['set', 'not_set'].includes(operator)) {
            return "";
        }

        const placeholders = {
            name: "Search Name...",
            public_categ_ids: "Search Category...",
            product_brand_id: "Search Brand...",
            list_price: "Enter Price...",
            product_tag_ids: "Search Tags...",
            website_ribbon_id: "Search Label...",
            attribute_line_ids: "Search Attributes..."
        };

        return placeholders[field];
    }

    onFieldChange(ev, filter) {
        const newField = ev.target.value;

        filter.field = newField;
        filter.value = "";
        filter.selected_items = [];

        if (newField === 'list_price') {
            filter.operator = '=';
        } else if (newField === 'name') {
            filter.operator = 'ilike';
        } else {
            if (!filter.operator || !['ilike', 'not ilike', '=ilike', '=', '!=', 'set', 'not_set'].includes(filter.operator)) {
                filter.operator = 'ilike';
            }
        }

        const row = this._getFilterRowEl(filter);
        const inputEl = row ? row.querySelector('.filter-value') : null;
        if (inputEl) {
            inputEl.value = "";
            const placeholder = this.getFieldPlaceholder(newField, filter.operator);
            if (newField === 'list_price' && ['>', '<', '='].includes(filter.operator)) {
                inputEl.removeAttribute('readonly');
                inputEl.type = "number";
                inputEl.step = "1";
                inputEl.placeholder = placeholder
            } else if (newField === 'name' && ['ilike', 'not ilike', '=ilike'].includes(filter.operator)) {
                inputEl.removeAttribute('readonly');
                inputEl.type = "text";
                inputEl.placeholder = placeholder
            } else if (['=', '!='].includes(filter.operator)) {
                inputEl.setAttribute('readonly', 'readonly');
                inputEl.type = "text";
                inputEl.placeholder = placeholder

            } else if (['ilike', 'not ilike', '=ilike'].includes(filter.operator)) {
                inputEl.removeAttribute('readonly');
                inputEl.type = "text";
                inputEl.placeholder = placeholder
            } else {
                inputEl.removeAttribute('readonly');
                inputEl.type = "text";
                inputEl.placeholder = placeholder
            }
        }

        try {
            this._destroyFilterSelect(filter);
        } catch (e) {
            console.error('onFieldChange: Error destroying select', e);
        }

        this._emitConfigUpdated();
        if (['=', '!='].includes(filter.operator) && newField !== 'list_price' && newField !== 'name') {
            setTimeout(() => {
                this._initFilterSelect(filter);
            }, 150);
        }
    }

    onOperatorChange(ev, filter) {
        const oldOperator = filter.operator;
        const newOperator = ev.target.value;
        filter.operator = newOperator;

        const oldIsTextOperator = ['ilike', 'not ilike', '=ilike'].includes(oldOperator);
        const newIsTextOperator = ['ilike', 'not ilike', '=ilike'].includes(newOperator);

        if (oldIsTextOperator !== newIsTextOperator) {
            filter.value = "";
            filter.selected_items = [];
            const row = this._getFilterRowEl(filter);
            const inputEl = row ? row.querySelector('.filter-value') : null;

            if (inputEl) {
                inputEl.value = "";
            }
        }

        const placeholder = this.getFieldPlaceholder(filter.field, newOperator);
        // Handle text operators (ilike, not ilike, =ilike)
        if (newIsTextOperator) {
            try {
                this._destroyFilterSelect(filter);
                const row = this._getFilterRowEl(filter);
                const inputEl = row ? row.querySelector('.filter-value') : null;
                if (inputEl) {
                    if (!filter.locked) {
                        inputEl.removeAttribute('readonly');
                        inputEl.placeholder = placeholder;
                    }
                }
            } catch (e) { }
            this._emitConfigUpdated();
            return;
        }

        if (['=', '!='].includes(newOperator)) {
            const row = this._getFilterRowEl(filter);
            const inputEl = row ? row.querySelector('.filter-value') : null;
            if (inputEl) {
                inputEl.setAttribute('readonly', 'readonly');
                inputEl.placeholder = placeholder;
            }

            setTimeout(() => {
                this._initFilterSelect(filter);
            }, 150);

            this._emitConfigUpdated();
            return;
        }

        if (['set', 'not_set'].includes(newOperator)) {
            const row = this._getFilterRowEl(filter);
            const inputEl = row ? row.querySelector('.filter-value') : null;
            if (inputEl) {

                inputEl.setAttribute('readonly', 'readonly');
                inputEl.value = "";
                inputEl.placeholder = placeholder;
            }
            filter.value = "";
            filter.selected_items = [];
        }

        if (filter.field === 'list_price' && ['>', '<', '='].includes(newOperator)) {
            const row = this._getFilterRowEl(filter);
            const inputEl = row ? row.querySelector('.filter-value') : null;
            if (inputEl && !filter.locked) {
                inputEl.removeAttribute('readonly');
                inputEl.type = "number";
                inputEl.step = "0.01";
                inputEl.placeholder = placeholder;
            }
        }
        this._emitConfigUpdated();
    }

    onChangeRecordLimit(ev) {
        const newLimit = parseInt(ev.target.value);
        this.props.config.record_limit = newLimit;
        this._emitConfigUpdated();
    }

    onChangeMenuRecordLimit(ev) {
        const newLimit = parseInt(ev.target.value);
        const activeKey = this.state.mmActiveSection?.key;
        const config = this.props.config;
        if (activeKey && config.sections?.[activeKey]) {
            config.sections[activeKey].record_limit = newLimit;
        }
        this._emitConfigUpdated();
    }

    onSelectPreDefineTemplates(ev) {
        const selectedId = getEventValue(ev);
        const template = this.preDefineTemplates.find(t => t.id === selectedId);
        if (!template) return;
        this._updateConfig({
            filters: template.filters.map(f => ({ ...f, id: Date.now() + Math.random(), locked: true })),
            active_quick_selction: template.order_by,
        });
    }

    removeAllRecords(ev) {
        this._updateConfig({ selected_records: [0] });
    }

    getSubCategory(parent_id) {
        let extraInfo;
        if (this.props.config.technical_name === 'megamenu_shop_navigator' &&
            this.state.mmActiveSection?.key === 'category') {
            extraInfo = this.props.config.sections?.category?.extra_info;
        }
        else if (this.props.config.technical_name === 'megamenu_multi_category' &&
            this.state.mmActiveSection?.key === 'category_2') {
            extraInfo = this.props.config.sections?.category_2?.extra_info;
        }

        if (extraInfo && Array.isArray(extraInfo)) {
            for (const cat of extraInfo) {
                if (cat.parent == parent_id) {
                    return [cat.childs.toString(), cat.childs.length];
                }
            }
        }

        else if (this.props.config.extra_info) {
            for (const cat of this.props.config.extra_info) {
                if (cat.parent == parent_id) {
                    return [cat.childs.toString(), cat.childs.length];
                }
            }
        }
        return ["", 0];
    }

    selectSubCategory(ev) {
        const target = ev.target;
        const parentId = parseInt(target.getAttribute("data-id"));

        let extraInfo;
        if (this.props.config.technical_name === 'megamenu_shop_navigator' &&
            this.state.mmActiveSection?.key === 'category') {
            extraInfo = this.props.config.sections?.category?.extra_info;
        }
        else if (this.props.config.technical_name === 'megamenu_multi_category' &&
            this.state.mmActiveSection?.key === 'category_2') {
            extraInfo = this.props.config.sections?.category_2?.extra_info;
        }
        else {
            extraInfo = this.props.config.extra_info;
        }

        const existing = extraInfo?.find(e => e.parent === parentId);

        this.dialog.add(MegaMenuSubCategory, {
            parent_id: parentId,

            pre_selected_ids: existing ? existing.childs : [],

            onConfirm: (records) => {
                const childIds = records.map(r => r.id);

                let extraInfoArray = Array.isArray(extraInfo)
                    ? [...extraInfo]
                    : [];

                const existingIndex = extraInfoArray.findIndex(
                    item => item.parent === parentId
                );

                if (childIds.length) {
                    if (existingIndex !== -1) {
                        extraInfoArray[existingIndex].childs = childIds;
                    } else {
                        extraInfoArray.push({
                            parent: parentId,
                            childs: childIds,
                        });
                    }
                } else if (existingIndex !== -1) {
                    extraInfoArray.splice(existingIndex, 1);
                }

                if (this.props.config.technical_name === 'megamenu_shop_navigator' &&
                    this.state.mmActiveSection?.key === 'category') {
                    const sections = { ...this.props.config.sections };
                    sections.category = {
                        ...sections.category,
                        extra_info: extraInfoArray,
                    };
                    this._updateConfig({ sections });
                }
                else if (this.props.config.technical_name === 'megamenu_multi_category' &&
                    this.state.mmActiveSection?.key === 'category_2') {
                    const sections = { ...this.props.config.sections };
                    sections.category_2 = {
                        ...sections.category_2,
                        extra_info: extraInfoArray,
                    };
                    this._updateConfig({ sections });
                }
                else {
                    this._updateConfig({ extra_info: extraInfoArray });
                }
            }
        });
    }

    onChangeRecordConfig(ev, type) {
        const checked = ev.target.checked;
        const sections = { ...this.props.config.sections };
        const prodSection = { ...sections.product };

        if (checked) {
            prodSection.record_config = type;
        } else {
            prodSection.record_config = "";
        }

        sections.product = prodSection;
        this._updateConfig({ sections: sections });
    }

    setActiveSection(sectionKey) {
        const section = this.props.config.sections?.[sectionKey];
        if (!section) return;

        this.state.mmActiveSection = {
            key: sectionKey,
            ...section,
        };
        const recordIds = section.record_ids || [];
        this._updateConfig({
            default_mm_section: this.state.mmActiveSection.key,
            model: this.state.mmActiveSection.model,
            selected_records: recordIds
        });
    }

    // ───────────────── Design Tab ────────────────────────────
    changeSliderStyle(ev) {
        const value = ev.target.value;
        this._updateConfig({ slider_style: value });
    }

    changeMegaMenuStyle(ev) {
        const value = ev.target.value;
        this._updateConfig({ mm_style: value });
    }

    changeGridStyle(ev) {
        const value = ev.target.value;
        const optionEl = ev.target.selectedOptions[0];
        const template = optionEl.getAttribute("data-template");
        this._updateConfig({ grid_style: value, template_id: template });
    }

    changeAutoSlider() {
        const value = !this.props.config.auto_slider;
        this._updateConfig({ auto_slider: value });
    }

    onChangeSliderSpeed(ev) {
        const newLimit = parseInt(ev.target.value);
        this._updateConfig({ slider_time: newLimit });
    }

    changeInfinityLoop() {
        const value = !this.props.config.loop;
        this._updateConfig({ loop: value });
    }

    changePagination(ev) {
        const value = ev.target.value;
        this._updateConfig({ pagination: value });
    }

    onChangeDisplayAllItems(ev) {
        const checked = ev.target.checked;
        this._updateConfig({
            display_all_items: checked,
            slide_one_item: !checked
        });
    }

    onChangeSlideOneItem(ev) {
        const checked = ev.target.checked;
        this._updateConfig({
            slide_one_item: checked,
            display_all_items: !checked
        });
    }

    changeColItem(ev) {
        const value = ev.target.value;
        const optionEl = ev.target.selectedOptions[0];
        const viewType = optionEl.getAttribute("data-view-type");
        if (viewType === "desk") {
            this._updateConfig({ default_col_desk: value });
        }
        else if (viewType === "mob") {
            this._updateConfig({ default_col_mob: value });
        }
        else if (this.props.snippet_type === 'as_mega_menu') {
            this._updateConfig({ col_item: value });
        }
    }

    onBlurChange(ev) {
        this.state.blurAmount = ev.target.value;
    }

    onAngleChange(ev) {
        this.state.angle = ev.target.value;
    }

    onColorSelect(ev) {
        const color = ev.target.dataset.color;
        if (!color) return;
        this.state.selectedColor = color;
    }

    onBgModeChange(ev) {
        const mode = ev.target.value;
        this.state.bg_mode = mode;
    }

    get colorPalette() {
        return [
            "#ffffff",
            "#D97706",
            "#FFB8B8",
            "#FB923C",
            "#FDBA74",
            "#FDE68A",
            "#BEF264",
            "#86EFAC",
            "#7DD3FC",
            "#BAE6FD",
            "#3B82F6",
            "#818CF8",
            "#E879F9",
            "#f093fb",
        ];
    }

    // ───────────────── Extra Tab ────────────────────────────
    changeQuickOption(ev) {
        const targetKey = ev.target.dataset.target;
        const checked = ev.target.checked;
        if (targetKey) {
            this._updateConfig({ [targetKey]: checked });
        }
    }

    onStartDateChange(ev) {
        const startValue = ev.target.value;
        const container = ev.target.closest(".as-sp-scheduling");
        const endInput = container.querySelector(".as-end-datetime");
        if (endInput) {
            endInput.min = startValue;
            if (endInput.value && endInput.value < startValue) {
                endInput.value = startValue;
            }
        }
        this._updateConfig({
            start_date: startValue,
        });
    }

    onEndDateChange(ev) {
        const endValue = ev.target.value;
        const container = ev.target.closest(".as-sp-scheduling");
        const startInput = container.querySelector(".as-start-datetime");
        if (startInput && endValue < startInput.value) {
            ev.target.value = startInput.value;
        }
        this._updateConfig({
            end_date: ev.target.value,
        });
    }

    toggleTab(tabKey) {
        const config = this.props.config;
        if (config.tab_names) {
            const tab = config.tab_names.find(t => t.key === tabKey);
            if (tab) {
                tab.enabled = !tab.enabled;
                this._updateConfig(config);
            }
        }
    }

    get visibleTabs() {
        const config = this.props.config;
        if (!config.tab_names) return [];
        return config.tab_names.filter(tab => tab.enabled !== false);
    }

    get hasVisibleTabs() {
        return this.visibleTabs.length > 0;
    }

    onVisibilityChange(ev) {
        const visibilityUser = ev.target.value;
        this._updateConfig({ user_visibility: visibilityUser });
    }

}