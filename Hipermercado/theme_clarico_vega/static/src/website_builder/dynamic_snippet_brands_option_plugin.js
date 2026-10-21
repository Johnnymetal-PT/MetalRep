import { DYNAMIC_SNIPPET_CAROUSEL } from "@website/builder/plugins/options/dynamic_snippet_carousel_option_plugin";
import { setDatasetIfUndefined } from "@website/builder/plugins/options/dynamic_snippet_option_plugin";
import { Plugin } from "@html_editor/plugin";
import { withSequence } from "@html_editor/utils/resource";
import { registry } from "@web/core/registry";
import {
    DynamicSnippetBrandsOption,
    getContextualFilterDomain,
} from "./dynamic_snippet_brands_option";

class DynamicSnippetBrandsOptionPlugin extends Plugin {
    static id = "dynamicSnippetBrandsOption";
    static dependencies = ["dynamicSnippetCarouselOption"];
    static shared = ["fetchCategories", "getModelNameFilter"];
    modelNameFilter = "product.brand";
    resources = {
        builder_options: withSequence(DYNAMIC_SNIPPET_CAROUSEL, DynamicSnippetBrandsOption),
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
        if (snippetEl.matches(DynamicSnippetBrandsOption.selector)) {
            for (const [optionName, value] of [
                ["productCategoryId", "all"],
                ["showVariants", true],
                ["brandId", "all"],
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
        if (el.matches(DynamicSnippetBrandsOption.selector)) {
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
    .add(DynamicSnippetBrandsOptionPlugin.id, DynamicSnippetBrandsOptionPlugin);
