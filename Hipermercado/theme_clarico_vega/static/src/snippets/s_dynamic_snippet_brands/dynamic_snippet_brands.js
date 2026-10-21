import { DynamicSnippetCarousel } from "@website/snippets/s_dynamic_snippet_carousel/dynamic_snippet_carousel";
import { registry } from "@web/core/registry";

export class DynamicSnippetBrands extends DynamicSnippetCarousel {
    static selector = ".s_dynamic_snippet_brands";

    /**
     * Gets the category search domain for brands (if applicable)
     */
    getCategorySearchDomain() {
        const searchDomain = [];
        let brandCategoryId = this.el.dataset.brandCategoryId;
        if (brandCategoryId && brandCategoryId !== "all") {
            searchDomain.push(["category_id", "=", Number.parseInt(brandCategoryId)]);
        }
        return searchDomain;
    }

    /**
     * Gets the tag search domain for brands (if applicable)
     */
    getTagSearchDomain() {
        const searchDomain = [];
        let brandTagIds = this.el.dataset.brandTagIds;
        brandTagIds = brandTagIds ? JSON.parse(brandTagIds) : [];
        if (brandTagIds.length) {
            searchDomain.push(["tag_ids", "in", brandTagIds.map(tag => tag.id)]);
        }
        return searchDomain;
    }

    /**
     * @override
     */
    getSearchDomain() {
        const searchDomain = super.getSearchDomain(...arguments);
        searchDomain.push(...this.getCategorySearchDomain());
        searchDomain.push(...this.getTagSearchDomain());
        // Brand name filter logic
        const brandNames = this.el.dataset.brandNames;
        if (brandNames) {
            for (const brandName of brandNames.split(",")) {
                if (brandName.trim()) {
                    searchDomain.push(["name", "ilike", brandName.trim()]);
                }
            }
        }
        return searchDomain;
    }

    /**
     * Listen for changes to the brand name filter and re-render
     */
    setup() {
        super.setup();
        // Listen for changes to the brand name filter from the editor
        this.el.addEventListener("change", (ev) => {
            if (ev.target && ev.target.name === "brandNames") {
                this.el.dataset.brandNames = ev.target.value;
                this.render();
            }
        });
        this.render();
    }
}

registry
    .category("public.interactions")
    .add("theme_clarico_vega.dynamic_snippet_brands", DynamicSnippetBrands);