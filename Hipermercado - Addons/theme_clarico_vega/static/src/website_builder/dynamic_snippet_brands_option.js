import { BaseOptionComponent, useDomState } from "@html_builder/core/utils";
import { useDynamicSnippetOption } from "@website/builder/plugins/options/dynamic_snippet_hook";
import { onWillStart, useState } from "@odoo/owl";

export class DynamicSnippetBrandsOption extends BaseOptionComponent {
    static template = "theme_clarico_vega.DynamicSnippetBrandsOption";
    static dependencies = ["dynamicSnippetBrandsOption"];
    static selector = ".s_dynamic_snippet_brands";
    setup() {
        super.setup();
        const { fetchCategories, getModelNameFilter } = this.dependencies.dynamicSnippetBrandsOption;
        const contextualFilterDomain = getContextualFilterDomain(this.env.editor.editable);
        this.dynamicOptionParams = useDynamicSnippetOption(
            getModelNameFilter(),
            contextualFilterDomain
        );
        this.state = useState({
            categories: [],
            brands: [], // Add brands state for selector
        });
        this.domState = useDomState((el) => ({
            isAlternative: el.classList.contains("o_wsale_alternative_products"),
        }));
        this.dynamicOptionParams.showFilterOption = () =>
            Object.values(this.dynamicOptionParams.dynamicFilters).length > 1 &&
            !this.domState.isAlternative;
        onWillStart(async () => {
            this.state.categories.push(...(await fetchCategories()));
            // Fetch brands for the options selector
            this.state.brands = await this.env.services.orm.searchRead(
                "product.brand",
                [],
                ["id", "name"],
                { limit: 50 }
            );
        });
    }
}

export function getContextualFilterDomain(editable) {
    const productTemplateId = editable.querySelector("input.product_template_id");
    const hasProductTemplateId = productTemplateId?.value;
    return hasProductTemplateId ? [] : [["product_cross_selling", "=", false]];
}
