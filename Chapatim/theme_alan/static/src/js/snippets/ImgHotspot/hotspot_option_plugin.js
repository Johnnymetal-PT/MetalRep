import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";
import { AlanImageHotspotOption } from "./hotspot_option";
import { withSequence } from "@html_editor/utils/resource";
import { loadLanguages } from "@web/core/l10n/translation";
import { BuilderAction } from "@html_builder/core/builder_action";
import { REPLACE_MEDIA } from "@html_builder/utils/option_sequence";
import { HotspotTranslationDialog, HotspotProductSelector, HotspotStaticDialog, HotspotStaticPopover } from "theme_alan.hotspot_dialog";
import { patch } from "@web/core/utils/patch";
import { ImageToolOption } from "@html_builder/plugins/image/image_tool_option";

// ─── Patch Base Image Tool Option ───────────────────────────────────────────
patch(ImageToolOption.prototype, {
    get isHotspotSupported() {
        const template = this.constructor.template || "";
        if (this.massMailingState || template.includes("mass_mailing")) {
            return false;
        }
        const editingElement = this.props.editingElement;
        const selector = ".s_category, .s_brand, .as_category_product";
        if (editingElement && editingElement.closest(selector)) {
            return false;
        }
        return true;
    }
});

// ─── Plugin Registration ─────────────────────────────────────────────────────
class ImageToolOptionPlugin extends Plugin {
    static id = "imageToolOptionPlugin";
    resources = {
        builder_actions: {
            AddHotspotAction,
            SetHotspotStyleAction,
            SetOnClickTypeAction,
            SetOnClickThemeAction,
            SetBtnUrlAction,
            SetHotspotImageAction,
            SetHotspotPositionAction,
            SetHotspotFieldAction,
            setHotspotTranslationAction,
            SetDynamicProductAction,
            ShowPreviewAction,
        },
        builder_options: [
            withSequence(REPLACE_MEDIA, AlanImageHotspotOption)
        ],
    };
}

registry.category("website-plugins").add(ImageToolOptionPlugin.id, ImageToolOptionPlugin);
registry.category("mass_mailing-plugins").add(ImageToolOptionPlugin.id, ImageToolOptionPlugin);

// ─── Add Hotspot Action ─────────────────────────────────────────────────────
export class AddHotspotAction extends BuilderAction {
    static id = "addHotspot";
    apply({ editingElement }) {
        const $block = `<div class="hotspot" style="position: absolute;top:50%;left: 50%;transform: translate(-50%, -50%);">
                <p class="hs_icon as_img_icon" data-name="Hotspot">
                    <a href="#" class="icon">
                        <i class="fa fa-circle"></i>
                    </a>
                </p>
            </div>`;
        editingElement.parentElement.style.position = "relative";
        editingElement.parentElement.insertAdjacentHTML('beforeend', $block);
    }
}

// ─── Hotspot Style & Theme Actions ──────────────────────────────────────────
export class SetHotspotStyleAction extends BuilderAction {
    static id = "setHotspotStyle";
    apply({ editingElement, params }) {
        if (params) {
            editingElement.setAttribute('data-po_style', params.mainParam);
        }
    }
}

export class SetOnClickTypeAction extends BuilderAction {
    static id = "setOnClickType";
    apply({ editingElement, params }) {
        if (params) {
            editingElement.setAttribute('data-st_type', params.mainParam);
        }
    }
}

export class SetOnClickThemeAction extends BuilderAction {
    static id = "setOnClickTheme";
    apply({ editingElement, params }) {
        if (params) {
            editingElement.setAttribute('data-po_theme', params.mainParam);
        }
    }
}

// ─── Button URL Action ──────────────────────────────────────────────────────
export class SetBtnUrlAction extends BuilderAction {
    static id = "setBtnUrl";
    apply({ editingElement, params }) {
        if (params) {
            editingElement.setAttribute('po_bturl', params.mainParam);
        }
    }
}

// ─── Hotspot Image Action ───────────────────────────────────────────────────
export class SetHotspotImageAction extends BuilderAction {
    static id = "setHotspotImage";
    static dependencies = ["media"];
    async apply({ editingElement }) {
        let imageUrl;
        await new Promise((resolve) => {
            const onClose = this.dependencies.media.openMediaDialog({
                onlyImages: true,
                noDocuments: true,
                save: (selectedImageEl) => {
                    imageUrl = selectedImageEl?.src;
                },
            });
            onClose.then(resolve);
        });
        if (!imageUrl) {
            return;
        }
        editingElement.setAttribute('data-po_imgurl', imageUrl);
    }
}

// ─── Hotspot Position Action ────────────────────────────────────────────────
export class SetHotspotPositionAction extends BuilderAction {
    static id = "setHotspotPosition";
    apply({ editingElement, value, params }) {
        if (value == null || !params || !params.direction) return;

        const hotspot = editingElement.closest(".hotspot");
        if (!hotspot) return;

        const posVal = value + "%";

        if (params.direction === "left") {
            hotspot.style.left = posVal;
            editingElement.setAttribute("data-hs_left", value);
        } else if (params.direction === "top") {
            hotspot.style.top = posVal;
            editingElement.setAttribute("data-hs_top", value);
        }
    }

    getValue({ editingElement, params }) {
        if (!params || !params.direction) return "";

        if (params.direction === "left") {
            return editingElement.getAttribute("data-hs_left") || "50";
        } else if (params.direction === "top") {
            return editingElement.getAttribute("data-hs_top") || "50";
        }
        return "";
    }
}

// ─── Hotspot Field Data Action ─────────────────────────────────────────────
export class SetHotspotFieldAction extends BuilderAction {
    static id = "setHotspotField";

    apply({ editingElement, value, params }) {
        if (!value || !params || !params.field) return;

        const fieldMap = {
            main_title: "data-po_title",
            description: "data-po_desc",
            btn_text: "data-po_btxt",
        };

        const attrName = fieldMap[params.field];
        if (attrName) {
            editingElement.setAttribute(attrName, value);
        }
    }

    getValue({ editingElement, params }) {
        if (!params || !params.field) return "";

        const fieldMap = {
            main_title: "data-po_title",
            description: "data-po_desc",
            btn_text: "data-po_btxt",
        };

        const attrName = fieldMap[params.field];
        return attrName ? editingElement.getAttribute(attrName) || "" : "";
    }
}

// ─── Translation Dialog for Hotspot ────────────────────────────────────────
export class setHotspotTranslationAction extends BuilderAction {
    static id = "setHotspotTranslation";
    async apply({ editingElement, params, ev }) {
        const key_data = params.mainParam;
        let attributePrefix = "";
        let defaultDataAttr = "";

        switch (key_data) {
            case "title_translation":
                attributePrefix = "data-lang-";
                defaultDataAttr = "data-po_title";
                break;
            case "desc_translation":
                attributePrefix = "data-description-lang-";
                defaultDataAttr = "data-po_desc";
                break;
            case "btn_translation":
                attributePrefix = "data-btn-lang-";
                defaultDataAttr = "data-po_btxt";
                break;
            default:
                return;
        }

        const attributesDictionary = {};
        Array.from(editingElement.attributes).forEach(attr => {
            if (attr.name.startsWith(attributePrefix)) {
                attributesDictionary[attr.name] = attr.value;
            }
        });

        const outputArray = Object.entries(attributesDictionary);
        const DefaultData = editingElement.getAttribute(defaultDataAttr) || "";
        const languages = await loadLanguages(this.services.orm);
        const lowerCaseLanguages = languages.map(innerArray =>
            innerArray.map(item => item.toLowerCase())
        );
        const context = {
            lang_code_name: lowerCaseLanguages,
            defaultTitle: DefaultData,
            defaultAtt: outputArray,
            key_data: key_data,
        };

        this.services.dialog.add(HotspotTranslationDialog, {
            data: context,
            add_transalte: async () => {
                const languageData = {};
                document.querySelectorAll(".o_field_translation_code").forEach((el, index) => {
                    const codeValue = el.getAttribute("value");
                    const inputValue = document.querySelectorAll(".o_field_translation_field")[index].value;
                    if (inputValue) languageData[codeValue] = inputValue;
                });

                for (const [code, value] of Object.entries(languageData)) {
                    if (!value) continue;
                    let attrName;
                    if (key_data === "title_translation") attrName = `data-lang-${code}`;
                    else if (key_data === "desc_translation") attrName = `data-description-lang-${code}`;
                    else if (key_data === "btn_translation") attrName = `data-btn-lang-${code}`;
                    if (attrName) editingElement.setAttribute(attrName, value);
                }

                this.services.dialog.closeAll();
            },
            close: () => this.services.dialog.closeAll()
        });
    }
};

// ─── Dynamic Product Selection for Hotspot ──────────────────────────────────
export class SetDynamicProductAction extends BuilderAction {
    static id = "setDynamicProduct";
    async apply({ editingElement }) {
        await this.services.dialog.add(HotspotProductSelector, {
            select_tmpl_id: parseInt(editingElement.getAttribute("data-product_tmpl_id") || 0),
            select_tmpl_name: editingElement.getAttribute("data-product-name") || "",
            editingElement: editingElement,
        });
    }
}

// ─── Preview Hotspot (Popover/Modal) ───────────────────────────────────────
export class ShowPreviewAction extends BuilderAction {
    static id = "showPreview";

    async apply({ editingElement }) {
        const title = editingElement.getAttribute("data-po_title") || "";
        const description = editingElement.getAttribute("data-po_desc") || "";
        const btn_txt = editingElement.getAttribute("data-po_btxt") || "";
        const btn_url = editingElement.getAttribute("data-po_bturl") || "";
        const img_url = editingElement.getAttribute("data-po_imgurl") || "";
        const pop_thm = editingElement.getAttribute("data-po_theme") || "";
        const pop_style = editingElement.getAttribute("data-po_style") || "hs-default-style";

        const context = {
            title,
            description,
            btn_txt,
            btn_url,
            img_url,
            pop_thm,
            pop_style,
        };

        const st_type = editingElement.getAttribute("data-st_type") || "";
        if (st_type === "popover") {
            this._showPopover(editingElement, context);
        } else if (st_type === "modal") {
            this.services.dialog.add(HotspotStaticDialog, { data: context });
        }
    }

    _showPopover(targetElement, context) {
        const close = () => {
            if (this.popoverCloseFn) {
                this.popoverCloseFn();
                this.popoverCloseFn = null;
            }
        };

        if (this.popoverCloseFn) {
            close();
            return;
        }

        this.popoverCloseFn = this.services.popover.add(
            targetElement,
            HotspotStaticPopover,
            {
                data: context,
                onClose: close,
            },
            {
                closeOnClickAway: true,
                position: "top",
            }
        );
    }
}
