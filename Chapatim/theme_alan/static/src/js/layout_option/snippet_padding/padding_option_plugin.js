import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";
import { withSequence } from "@html_editor/utils/resource";
import { CONTAINER_WIDTH } from "@website/builder/option_sequence";
import { after } from "@html_builder/utils/option_sequence";
import { BaseOptionComponent } from "@html_builder/core/utils";

export class AsPaddingOption extends BaseOptionComponent {
    static template = "as_snippet_padding.AsPaddingOption";
    static selector = "section";
}

class AsPaddingOptionPlugin extends Plugin {
    static id = "asPaddingOption";
    resources = {
        builder_options: [withSequence(after(CONTAINER_WIDTH), AsPaddingOption)],
    };
}

registry.category("website-plugins").add(AsPaddingOptionPlugin.id, AsPaddingOptionPlugin);
