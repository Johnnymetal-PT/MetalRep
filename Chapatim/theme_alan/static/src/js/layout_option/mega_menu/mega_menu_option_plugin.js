import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";
import { withSequence } from "@html_editor/utils/resource";
import { CONTAINER_WIDTH } from "@website/builder/option_sequence";
import { BuilderAction } from "@html_builder/core/builder_action";
import { patch } from "@web/core/utils/patch";
import { ToggleFetchEcomCategoriesAction } from "@website_sale/website_builder/mega_menu_option_plugin";
import { SnippetBuilder } from "../../snippets/SnippetBuilder/SnippetBuilder";

function isAlanMegaMenu(el) {
    const isAlanMegaMenu = el.querySelector('.as_mega_menu')
    return isAlanMegaMenu
}

patch(ToggleFetchEcomCategoriesAction.prototype, {
    async load({ editingElement }) {
        if (!isAlanMegaMenu(editingElement)) {
            return super.load({ editingElement });
        }
        const hasCategoryClass = editingElement.classList.contains("fetchEcomCategories");
        const templateKey = hasCategoryClass
            ? "atharva_theme_base.as_megamenus"
            : "atharva_theme_base.as_mega_menu_category";

        await this.dependencies.customizeWebsite.loadTemplateKey(templateKey);
        return templateKey;
    },
});

// ─── Plugin: adds a custom builder option for Alan MegaMenu Builder ───────────────
class AlanMegaMenuOptionPlugin extends Plugin {
    static id = "alanMegaMenuOptionPlugin";
    static dependencies = ["builderActions"];
    resources = {
        builder_options: [
            withSequence(CONTAINER_WIDTH, {
                template: "theme_alan.AlanMegaMenuOptionPlugin",
                selector: ".as_mega_menu",
            }),
        ],
        builder_actions: {
            SetOpenMegaMenuBuilder,
        },
    };
}

// ─── Action: opens Alan MegaMenu Builder dialog ─────────────────────────────────
export class SetOpenMegaMenuBuilder extends BuilderAction {
    static id = "setOpenMegaMenuBuilder";

    async apply({ editingElement, params }) {
        const snippet_type = editingElement.getAttribute("data-as-snippet") || "";
        editingElement = editingElement.querySelector('.as-snippet-drop-container') || editingElement;
        const MegamenuSnippetLists = registry.category("snippet_builder").get("as_megamenu_snippet_tabs");
        const config_data = editingElement.dataset.designEdit || undefined;
        this.services.dialog.add(SnippetBuilder, {
            snippets: MegamenuSnippetLists,
            target: editingElement,
            config_data,
            record_ids: JSON.parse(editingElement.dataset.recordIds || editingElement.dataset.recordsIds || "[]"),
            snippet_type,
        });
    }
}

registry.category("website-plugins").add(AlanMegaMenuOptionPlugin.id, AlanMegaMenuOptionPlugin);
