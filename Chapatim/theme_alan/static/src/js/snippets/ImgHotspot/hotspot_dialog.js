/** @odoo-module alias=theme_alan.hotspot_dialog **/

import { _t } from "@web/core/l10n/translation";
import { Component, onMounted, onWillUnmount, useRef } from "@odoo/owl";
import { AlanSelectSearch } from "../../alan_select_search/alan_select_search";

// ─── Hotspot Product Selector: Input with live product search and selection. ────────────────
export class HotspotProductSelector extends Component {
    static template = "theme_alan.HotspotProductSelector";
    static props = {
        select_tmpl_id: { type: Number, optional: true },
        select_tmpl_name: { type: String, optional: true },
        close: { type: Function },
        onSave: { type: Function},
        editingElement: Object,
    }

    setup() {
        this.inputRef = useRef("as_search_input");
        this.selectSearch = null;

        onMounted(() => {
            if (this.props.select_tmpl_id !== 0 && this.props.select_tmpl_name) {
                 this.inputRef.el.value = this.props.select_tmpl_name;
            }
            this.selectSearch = new AlanSelectSearch(
                this.inputRef.el,
                "product.template",
                this.onProductSelect.bind(this),
                {
                    debounceTime: 300,
                }
            );
            const startEl = this.inputRef.el.parentNode;
            this.modalBody = startEl ? startEl.closest('.modal-body') : null;
            if (this.modalBody){
                this.modalBody.style.overflow = "inherit";
            }
        });

        onWillUnmount(() => {
            if (this.selectSearch) {
                this.selectSearch.destroy();
            }

        });
    }

    //Callback when a product is selected
    onProductSelect(selected) {
        this.props.select_tmpl_id =  selected.id
        this.props.select_tmpl_name =  selected.name
    }

    onSave() {
        if (this.props.select_tmpl_id && this.props.select_tmpl_name && this.props.editingElement) {
            this.props.editingElement.setAttribute("data-product_tmpl_id", this.props.select_tmpl_id);
            this.props.editingElement.setAttribute("data-product-name", this.props.select_tmpl_name);
        }
        this.props.close();
    }

    close() {
        this.props.close();
    }
}

// ─── Translation dialog for hotspot ───────────────────────────────────────────
export class HotspotTranslationDialog extends Component {
    static template = "theme_alan.HotspotTranslationDialog";
    static props = {
        close: Function,
        add_transalte: Function,
        data :{
            lang_code_name: String,
            defaultTitle: String,
            defaultAtt: Array,
            key_data: String,
        }
    };
}

// ─── Static content dialog for hotspot configuration ───────────────────────────
export class HotspotStaticDialog extends Component {
    static template = "theme_alan.HotspotStaticDialog";
    static props = {
        close: Function,
        data :{
            title: String,
            description: String,
            btn_txt: String,
            btn_url: String,
            img_url: String,
            pop_thm: String,
            pop_style: String
        }
    };
}

// ─── Static popover for hotspot display ─────────────────────────────────────────
export class HotspotStaticPopover extends Component {
    static template = "theme_alan.HotspotStaticPopover";
    static props = {
        close: Function,
        data :{
            title: String,
            description: String,
            btn_txt: String,
            btn_url: String,
            img_url: String,
            pop_thm: String,
            pop_style: String
        }
    };
}

// ─── Dynamic popover for hotspot display ──────────────────────────────────────────
export class HotspotDynamicPopover extends Component {
    static template = "theme_alan.HotspotDynamicPopover";
    static props = {
        close: Function,
        body: String,
    };
}

export default {
    HotspotProductSelector: HotspotProductSelector,
    HotspotTranslationDialog: HotspotTranslationDialog,
    HotspotStaticDialog: HotspotStaticDialog,
    HotspotStaticPopover: HotspotStaticPopover,
    HotspotDynamicPopover: HotspotDynamicPopover,
}
