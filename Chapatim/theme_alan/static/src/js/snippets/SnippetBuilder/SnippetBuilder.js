import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { Dialog } from "@web/core/dialog/dialog";
import { Component, useState, onMounted, onWillUnmount } from "@odoo/owl";
import { CollectionDialog } from "../SnippetCollection/SnippetCollectionDialog";
import { DeleteConfirmDialog } from "../SnippetCollection/SnippetCollectionDialog";
import { SnippetBuilderCanvas } from "../SnippetBuilderCanvas/SnippetBuilderCanvas";
import { SnippetBuilderConfig } from "../SnippetBuilderConfig/SnippetBuilderConfig";

// ─── Allowed editor keys (used for filtering config safely) ─────────────────────────────────
const EDITOR_KEYS = [
    "name", "technical_name", "preview_image", "selection_mode_default", "model", "active_model",
    "template_id", "filters", "filter_match", "active_quick_selction", "selected_records",
    "view", "active_view", "auto_slider", "slider_time", "loop", "pagination",
    "default_col_mob", "default_col_desk", "col_item", "grid_style", "slider_style", "style", "slide_one_item", "display_all_items",
    "default_stemplate_id", "default_gtemplate_id", "grid_layout_style", "slider_layout_style",
    "allow_add_to_cart", "allow_quick_view", "allow_compare", "allow_wishlist",
    "allow_rating", "allow_label", "allow_hover_image", "allow_stock_info", "allow_offer_time",
    "allow_brand_info", "allow_color_variant", "mob_allow_add_to_cart", "mob_allow_quick_view", "mob_allow_compare", "mob_allow_wishlist",
    "mob_allow_rating", "mob_allow_label", "mob_allow_hover_image", "mob_allow_stock_info", "mob_allow_offer_time",
    "mob_allow_brand_info", "mob_allow_product_discount", "mob_allow_color_variant", "record_limit", "allow_link", "active_selection", "start_date", "end_date",
    "quick_selection", "extra_info", "record_info", "tab_names", "sections", "default_mm_section", "mm_style", "allow_product_discount", "user_visibility"
];

// ─── Pick only valid editor props from snippet/config ─────────────────────────────────
export function pickEditorProps(snippet = {}) {
    const result = {};
    for (const key of EDITOR_KEYS) {
        if (snippet[key] !== undefined) {
            result[key] = snippet[key];
        }
    }
    return result;
}

export class SnippetBuilder extends Component {
    static template = "theme_alan.snippet_builder";
    static components = { Dialog, SnippetBuilderCanvas, SnippetBuilderConfig };

    static props = {
        close: Function,
        snippets: Array,
        target: { type: true, optional: true },
        config_data: { type: String, optional: true },
        record_ids: { type: Array, optional: true },
        snippet_type: { type: String, optional: true },
    };

    setup() {
        this.editor = useState({});
        this.config = useState({});
        this.configLoaded = false;
        this.lastLoadedSnapshot = null;
        this.snippetTabs = this.props.snippets || [];
        this.state = useState({
            activeCategory: this.snippetTabs[0] || null,
            showSnippets: false,
            showCollections: false,
            deviceView: "desktop",
            history: [],
            redoStack: [],
            searchQuery: "",
            collections: [],
        });

        onMounted(() => {
            if (this.props.config_data && !this.configLoaded) {
                document
                    .querySelector(".as-sb-canvas-empty")
                    ?.classList.add("d-none");

                this.loadSnippetConfig();
                this.configLoaded = true;
            }
            this.fetchCollections();
            // Close Event For Canvas
            this.env.bus.addEventListener("close_template_menu", () => {
                this.state.showSnippets = false;
                this.state.showCollections = false
            });

            this.outsideClick = (e) => {
                const menus = document.querySelectorAll('.as-sb-top-template');
                const mainHeader = document.querySelector('.as-sb-main-header');
                const canvasPreview = document.querySelector('.as-sb-canvas-preview');

                if (canvasPreview?.contains(e.target)) return;
                const isInsideAnyMenu = [...menus].some(menu => menu.contains(e.target));
                if (!isInsideAnyMenu && !mainHeader?.contains(e.target)) {
                    this.state.showSnippets = false;
                }
            };

            this.outsideClickCollections = (e) => {
                const menus = document.querySelectorAll('.as-sb-top-template');
                const mainHeader = document.querySelector('.as-sb-main-header');
                const canvasPreview = document.querySelector('.as-sb-canvas-preview');

                if (canvasPreview?.contains(e.target)) return;
                const isInsideAnyMenu = [...menus].some(menu => menu.contains(e.target));
                if (!isInsideAnyMenu && !mainHeader?.contains(e.target)) {
                    this.state.showCollections = false;
                }
            };

            document.addEventListener('click', this.outsideClick, true);
            document.addEventListener('click', this.outsideClickCollections, true);
        });

        onWillUnmount(() => {
            document.removeEventListener('click', this.outsideClick, true);
            document.removeEventListener('click', this.outsideClickCollections, true);
            this.env.bus.removeEventListener("close_template_menu", () => { });
        });
    }

    onSearchSnippet(ev) {
        this.state.searchQuery = ev.target.value.toLowerCase();
    }

    get filteredSnippets() {
        const category = this.state.activeCategory;
        if (!category || !category.snippets) return [];

        const query = this.state.searchQuery;
        if (!query) return category.snippets;

        return category.snippets.filter(snippet =>
            snippet.name?.toLowerCase().includes(query)
        );
    }

    get parsedCollections() {
        return this.state.collections.map(collection => {
            let previewImage = "";
            try {
                const config = JSON.parse(collection.config_data || '{}');
                previewImage = config.preview_image || "";
            } catch (e) { }
            return { ...collection, preview_image: previewImage };
        });
    }

    _getCleanedConfigSnapshot(obj) {
        const cleaned = { ...obj };
        delete cleaned.selected_records;
        delete cleaned.record_info;
        delete cleaned.deviceView;
        return JSON.stringify(cleaned, Object.keys(cleaned).sort());
    }

    loadSnippetConfig() {
        const { config_data, record_ids } = this.props;
        let configObj = {};

        if (typeof config_data === "string") {
            try {
                configObj = JSON.parse(config_data);
            } catch (err) {
                console.error("Failed to parse snippet config data:", err);
                configObj = {};
            }
        }

        // Normalize selected records
        configObj.selected_records = Array.isArray(record_ids)
            ? record_ids
            : configObj.selected_records || [];

        const newProps = pickEditorProps(configObj);

        // Prevent unnecessary re-renders
        if (!this._isSameConfig(newProps, this.editor)) {
            this.updateEditor(newProps);
            this.lastLoadedSnapshot = this._getCleanedConfigSnapshot(this.config);
        }
    }

    async updateEditor(patch = {}) {
        Object.assign(this.editor, patch);
        Object.assign(this.config, patch);
        this.env.bus.trigger("config_updated", this.config);
        // Store snapshot for undo (de-duplicated)
        const snapshot = JSON.stringify(this.config);
        if (this.state.history[this.state.history.length - 1] !== snapshot) {
            this.state.history.push(snapshot);
            if (this.state.history.length > 50) this.state.history.shift(); // Limit history
        }
        this.state.redoStack.length = 0;

        if (patch.technical_name) {
            await this.fetchCollections();
        }
    }

    async fetchCollections() {
        const collections = await rpc('/get_collections', {});
        this.state.collections = collections;
    }

   async loadCollection(collection) {
        try {
            const config = JSON.parse(collection.config_data);
            await this.updateEditor(config);
            this.lastLoadedSnapshot = this._getCleanedConfigSnapshot(this.config);
            document.querySelector(".as-sb-canvas-empty")?.classList.add("d-none");
        } catch (err) {
            console.error("Failed to load collection:", err);
        }
    }

    onClickCollectionsMenu() {
        this.state.showCollections = !this.state.showCollections;
        this.state.showSnippets = false;
    }

    onCloseCollectionsMenu() {
        this.state.showCollections = false;
    }

    onCollectionSelect(collection) {
        this.loadCollection(collection);
        this.state.showCollections = false;
        document.querySelector(".as-sb-canvas-empty")?.classList.add("d-none");
    }

    async onDeleteCollection(ev, snippet) {
        ev.stopPropagation();
        this.env.services.dialog.add(DeleteConfirmDialog, {
            collectionName: snippet.name,
            onConfirm: async () => {
                await rpc('/delete_collection', { collection_id: snippet.id });
                await this.fetchCollections();
            },
        });
    }

    _isSameConfig(a, b) {
        if (!a || !b) return a === b;
        return JSON.stringify(a) === JSON.stringify(b);
    }

    // ---------------- UI Actions ----------------
    onClickTemplateMenu() {
        this.state.showCollections = false;
        this.state.showSnippets = !this.state.showSnippets;
        if (this.state.showSnippets && !this.state.activeCategory) {
            this.state.activeCategory = this.snippetTabs[0] || null;
        }
    }

    onCloseTemplateMenu() {
        this.state.showSnippets = false;
    }

    async onSnippetTabSelect(tab) {
        this.state.activeCategory = tab;
    }

    async onSnippetSelect(snippet) {
        this.config.selected_records = [];
        await this.updateEditor(pickEditorProps(snippet));
        this.lastLoadedSnapshot = null;
        this.state.showSnippets = false;
        document.querySelector(".as-sb-canvas-empty")?.classList.add("d-none");
    }

    // ---------------- History ----------------
    onUndo() {
        if (this.state.history.length <= 1) return;

        this.state.redoStack.push(this.state.history.pop());
        const previous = JSON.parse(this.state.history[this.state.history.length - 1]);

        Object.assign(this.config, previous);
        this.env.bus.trigger("config_updated", this.config);
    }

    onRedo() {
        if (!this.state.redoStack.length) return;

        const nextStr = this.state.redoStack.pop();
        this.state.history.push(nextStr);
        const next = JSON.parse(nextStr);

        Object.assign(this.config, next);
        this.env.bus.trigger("config_updated", this.config);
    }

    // ---------------- Device View ----------------
    setDeviceView(view) {
        this.state.deviceView = view;
        // this.updateEditor({ deviceView: view });
    }

    // ---------------- Save ----------------
    async onSave() {
        const snippetName = this.config.technical_name;
        if (!snippetName) return;

        const configToSave = { ...this.config };
        delete configToSave.selected_records;
        delete configToSave.record_info;
        delete configToSave.deviceView;

        const currentSnapshot = this._getCleanedConfigSnapshot(this.config);
        const lastLoadedCleaned = (() => {
            try {
                return this._getCleanedConfigSnapshot(JSON.parse(this.lastLoadedSnapshot || '{}'));
            } catch { return null; }
        })();
        const applySnippet = async () => {
            const container = this.props.target;
            if (!container || !this.config.technical_name) return;
            if (this.config.technical_name === "static_snippets") {
                return;
            }
            let dropContainer = null;
            const selectedRecords = this.config.selected_records || [];
            const title = this.config.name || "Unnamed Snippet";
            const canvasIframe = document.querySelector(".as-sb-canvas-iframe");
            const canvasDoc = canvasIframe?.contentDocument;
            const canvasDropContainer = canvasDoc?.querySelector(".as-snippet-drop-container");
            let previewContainer = canvasDoc?.querySelector(".as-snippet-preview");

            if (container.classList.contains("as-snippet-drop-container")) {
                dropContainer = container;
            } else {
                dropContainer = container.querySelector(".as-snippet-drop-container");
            }

            const placeholderHtml = `
                <div class="alan-snippet-placeholder">
                    <img src="/theme_alan/static/src/img/sb-empty-image.svg"
                        alt="placeholder"
                        class="alan-placeholder-image"/>
                    <h3 class="alan-snippet-title">${title}</h3>
                </div>
            `;

            if (canvasDropContainer) {
                canvasDropContainer.innerHTML = placeholderHtml;
                Object.assign(canvasDropContainer.dataset, {
                    snippetName: this.config.technical_name,
                    recordIds: JSON.stringify(selectedRecords),
                    modal: this.config.model || "",
                    designEdit: JSON.stringify(configToSave),
                });

                if (dropContainer) {
                    dropContainer.outerHTML = canvasDropContainer.outerHTML;
                }
                else {
                    container.innerHTML = previewContainer.outerHTML;
                }
            }

            const finalTarget = dropContainer || container;
            finalTarget.dispatchEvent(new Event("change", { bubbles: true }));
            finalTarget.dispatchEvent(new CustomEvent("as-sb-reload", { bubbles: true }));

            this._cleanup();
            this.props.close();
        }

        if (currentSnapshot === lastLoadedCleaned || this.props.snippet_type === 'as_mega_menu') {
            await applySnippet();
            return;
        }
        this.env.services.dialog.add(CollectionDialog, {
            defaultName: configToSave.name || "My Collection",
            existingNames: this.state.collections.map(c => c.name),
            onSave: async (name) => {
                await rpc('/save_collection', {
                    name: name,
                    snippet_key: snippetName,
                    config_data: JSON.stringify(configToSave)
                });
                await this.fetchCollections();
                await applySnippet();
                this._cleanup();
                this.props.close();
            },
            onPageSave: async () => {
                await applySnippet();
                this._cleanup();
                this.props.close();
            }
        });

    }

    // ---------------- Cleanup ----------------
    _cleanup() {
        this.state.history.length = 0;
        this.state.redoStack.length = 0;

        Object.keys(this.editor).forEach(k => delete this.editor[k]);
        Object.keys(this.config).forEach(k => delete this.config[k]);
    }

    onClose() {
        const container = this.props.target;
        const canvasIframe = document.querySelector(".as-sb-canvas-iframe");
        const canvasDoc = canvasIframe?.contentDocument;
        const canvasDropContainer = canvasDoc?.querySelector(".as-snippet-drop-container");
        const isBlank = !canvasDropContainer || canvasDropContainer.innerHTML.trim() === "";
        if (isBlank && container) {
            container.remove();
        }
        this._cleanup();
        this.props.close();
    }

}

registry.category("snippet_builder").add("snippet_builder_main", SnippetBuilder);
