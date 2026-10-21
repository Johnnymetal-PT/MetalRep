import { DYNAMIC_SNIPPET } from "@website/builder/plugins/options/dynamic_snippet_option_plugin";
import { Plugin } from "@html_editor/plugin";
import { withSequence } from "@html_editor/utils/resource";
import { registry } from "@web/core/registry";
import { DynamicSnippetProductOption, NumberOfElementsAction, NumberOfElementsSmallDevicesAction, SliderVisibilityByDateAction } from "./dynamic_snippet_option";

class DynamicSnippetProductOptionPlugin extends Plugin {
    static id = "dynamicSnippetProductOption";
    modelNameFilter = "product.product";
    static shared = ["getModelNameFilter"];
    resources = {
        builder_options: [withSequence(DYNAMIC_SNIPPET, DynamicSnippetProductOption)],
        builder_actions: {
            NumberOfElementsAction,
            NumberOfElementsSmallDevicesAction,
            SliderVisibilityByDateAction,
        },
    };
    setup() {
        super.setup();
    }
    getModelNameFilter() {
        return this.modelNameFilter;
    }
}

registry.category("website-plugins").add(DynamicSnippetProductOptionPlugin.id, DynamicSnippetProductOptionPlugin);
