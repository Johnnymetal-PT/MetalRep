/** @odoo-module **/
import { patch } from "@web/core/utils/patch";
import { SearchBar } from "@website/snippets/s_searchbar/search_bar";
import { getTemplate } from "@web/core/templates";

patch(SearchBar.prototype, {
    /**
     * Inherit Odoo base search for pass a customer values like a category and brand and others...
     * @override
     */
    render(res) {
        if (this.menuEl) {
            this.services["public.interactions"].stopInteractions(this.menuEl);
        }
        const prevMenuEl = this.menuEl;

        if (res && this.limit) {
            const results = res["results"];
            const categories = res["categories"];
            const search_brands = res["search_brands"];
            const selected_categories = res["selected_categories"];
            const quickLink = res['is_quick_link'];
            const parts = res["parts"];
            let template = "website.s_searchbar.autocomplete";

            const candidate = template + "." + this.searchType;
            if (getTemplate(candidate)) {
                template = candidate;
            }

            // Pass categories to template
            this.menuEl = this.renderAt(template, {
                results: results,
                categories: categories,       // ✅ pass categories
                quickLink: quickLink, // ✅ pass is_quick_link
                search_brands: search_brands, // ✅ pass brands
                selected_categories: selected_categories,
                parts: parts,
                hasMoreResults: results.length < res["results_count"],
                search: this.inputEl.value,
                fuzzySearch: res["fuzzy_search"],
                widget: this.options,
            }, this.el)[0];
        }

        this.hasDropdown = !!res;
        prevMenuEl?.remove();
    },
});