import { DYNAMIC_SNIPPET_CAROUSEL } from "@website/builder/plugins/options/dynamic_snippet_carousel_option_plugin";
import { setDatasetIfUndefined } from "@website/builder/plugins/options/dynamic_snippet_option_plugin";
import { Plugin } from "@html_editor/plugin";
import { withSequence } from "@html_editor/utils/resource";
import { registry } from "@web/core/registry";
import {
    DynamicSnippetCategoryOption,
    getContextualFilterDomain,
} from "./dynamic_snippet_category_option";

class DynamicSnippetCategoryOptionPlugin extends Plugin {
    static id = "dynamicSnippetCategoryOption";
    static dependencies = ["dynamicSnippetCarouselOption"];
    static shared = ["fetchCategories", "getModelNameFilter"];
    modelNameFilter = "product.public.category";
    resources = {
        builder_options: withSequence(DYNAMIC_SNIPPET_CAROUSEL, DynamicSnippetCategoryOption),
        dynamic_snippet_template_updated: this.onTemplateUpdated.bind(this),
        on_snippet_dropped_handlers: this.onSnippetDropped.bind(this),
    };
    setup() {
        this.categories = undefined;
    }
    destroy() {
        super.destroy();
        this.categories = undefined;
    }
    async onSnippetDropped({ snippetEl }) {
        if (snippetEl.matches(DynamicSnippetCategoryOption.selector)) {
            for (const [optionName, value] of [
                ["productCategoryId", "all"],
                ["showVariants", true],
            ]) {
                setDatasetIfUndefined(snippetEl, optionName, value);
            }
            await this.dependencies.dynamicSnippetCarouselOption.setOptionsDefaultValues(
                snippetEl,
                this.modelNameFilter,
                getContextualFilterDomain(this.editable)
            );
        }
    }
    getModelNameFilter() {
        return this.modelNameFilter;
    }
    onTemplateUpdated({ el, template }) {
        if (el.matches(DynamicSnippetCategoryOption.selector)) {
            this.dependencies.dynamicSnippetCarouselOption.updateTemplateSnippetCarousel(
                el,
                template
            );
        }
    }
    async fetchCategories() {
        return Array.isArray(this.categories) ? this.categories : [];
    }
}

registry
    .category("website-plugins")
    .add(DynamicSnippetCategoryOptionPlugin.id, DynamicSnippetCategoryOptionPlugin);

