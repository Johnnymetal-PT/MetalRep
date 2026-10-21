import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";
import { withSequence } from "@html_editor/utils/resource";
import { CONTAINER_WIDTH } from "@website/builder/option_sequence";
import { BuilderAction } from "@html_builder/core/builder_action";
import { SnippetBuilder } from "../../snippets/SnippetBuilder/SnippetBuilder";

// ─── Plugin: adds a custom builder option for Alan MegaMenu Builder ───────────────
class AlanSnippetBuilderOption extends Plugin {
    static id = "alanSnippetBuilderOption";
    static dependencies = ["builderActions"];
    resources = {
        builder_options: [
            withSequence(CONTAINER_WIDTH, {
                template: "theme_alan.AlanSnippetBuilderOption",
                selector: ".as-snippet-builder ",
            }),
        ],
        builder_actions: {
            SetOpenSnippetBuilder,
        },
    };
}

// ─── Action: opens Alan Snippet Builder dialog ─────────────────────────────────
export class SetOpenSnippetBuilder extends BuilderAction {
    static id = "setOpenSnippetBuilder";
    async apply({ editingElement, params }) {
        const snippet_type = editingElement.getAttribute("data-as-snippet") || "";
        editingElement = editingElement.querySelector('.as-snippet-drop-container') || editingElement;
        const DynamicSnippetLists = registry.category("snippet_builder").get("as_snippet_tabs");
        const config_data = editingElement.dataset.designEdit || undefined;
        this.services.dialog.add(SnippetBuilder, {
            snippets: DynamicSnippetLists,
            target: editingElement,
            config_data,
            record_ids: JSON.parse(editingElement.dataset.recordIds || editingElement.dataset.recordsIds || "[]"),
            snippet_type,
        });
    }
};

registry.category("website-plugins").add(AlanSnippetBuilderOption.id, AlanSnippetBuilderOption);
