import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";
import { WebsiteBuilder } from "./website_builder_dialog"
import { withSequence } from "@html_editor/utils/resource";
import { CONTAINER_WIDTH } from "@website/builder/option_sequence";
import { BuilderAction } from "@html_builder/core/builder_action";

// ─── Plugin: adds a custom builder option for Alan Website Builder ───────────────
class WebsiteBuilderOptionPlugin extends Plugin {
    static id = "websiteBuilderOptionPlugin";
    static dependencies = ["builderActions"];
    resources = {
        builder_options: [
            withSequence(CONTAINER_WIDTH, {
                template: "theme_alan.WebsiteBuilderOption",
                selector: ".as_website_builder",
            }),
        ],
        builder_actions: {
            SetOpenWebsiteBuilder,
        },
    };
}

// ─── Action: opens Alan Website Builder dialog ─────────────────────────────────
export class SetOpenWebsiteBuilder extends BuilderAction {
    static id = "setOpenWebsiteBuilder";
    async apply({ editingElement, params }) {
        const SnippetTabs = registry.category("website_builder").get("as_snippet_categories");
        const snippet = { name: editingElement.dataset.name, el: editingElement };
        this.services.dialog.add(WebsiteBuilder,{
            tabs: SnippetTabs,
            snippet: snippet,
            snippetEl: editingElement,
            confirm: () => resolve(true),
            cancel: () => resolve(false),
        })
    }
};

registry.category("website-plugins").add(WebsiteBuilderOptionPlugin.id, WebsiteBuilderOptionPlugin);
