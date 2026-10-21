import { markup } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { patch } from "@web/core/utils/patch";
import { getTemplate } from "@web/core/templates";
import { SearchBar } from "@website/snippets/s_searchbar/search_bar";

// ─── Alan Advanced Header SearchBar ─────────────────────────────────────────────────
patch(SearchBar.prototype, {
    async fetch() {
        if (this.searchType === "as_advance_search") {
            const res = await rpc("/website/snippet/autocomplete", {
                search_type: this.searchType,
                term: this.inputEl.value,
                order: this.order,
                limit: this.limit,
                max_nb_chars: Math.round(
                    Math.max(this.autocompleteMinWidth, parseInt(this.el.clientWidth)) * 0.22
                ),
                options: this.options,
            });
            res.products = res.products || [];
            res.brands = res.brands || [];
            res.tags = res.tags || [];
            res.parent_categories = res.parent_categories || [];
            res.sub_categories = res.sub_categories || [];
            res.exact_match = res.exact_match || null;
            const fieldNames = [
                'name',
                'description',
                'extra_link',
                'detail',
                'detail_strike',
                'detail_extra',
            ];
            const as_srch_lst = [res.products, res.brands, res.tags, res.parent_categories, res.sub_categories, res.exact_match ? [res.exact_match] : []];
            as_srch_lst.forEach(ele => {
                ele.forEach(record => {
                    for (const fieldName of fieldNames) {
                        if (record[fieldName]) {
                            if (typeof record[fieldName] === "object") {
                                for (const fieldKey of Object.keys(record[fieldName])) {
                                    record[fieldName][fieldKey] = markup(record[fieldName][fieldKey]);
                                }
                            } else {
                                record[fieldName] = markup(record[fieldName]);
                            }
                        }
                    }
                });
            });
            const regularFieldNames = this.getFieldsNames();
            if (res.results) {
                res.results.forEach((record) => {
                    for (const fieldName of regularFieldNames) {
                        if (record[fieldName]) {
                            record[fieldName] = markup(record[fieldName]);
                        }
                    }
                });
            }
            return res;
        } else {
            return super.fetch(...arguments);
        }
    },

    render(res) {
        if (this.menuEl) {
            this.services["public.interactions"].stopInteractions(this.menuEl);
        }
        const prevMenuEl = this.menuEl;
        if (res && this.limit) {
            const results = res["results"];
            let template = "website.s_searchbar.autocomplete";
            if (this.searchType === 'as_advance_search') {
                template = 'theme_alan.s_alan_searchbar';
            }
            const candidate = template + "." + this.searchType;
            if (getTemplate(candidate)) {
                template = candidate;
            }
            this.menuEl = this.renderAt(
                template,
                {
                    results: results,
                    brands: res['brands'] || [],
                    tags: res['tags'] || [],
                    parent_categories: res['parent_categories'] || [],
                    sub_categories: res['sub_categories'] || [],
                    exact_match: res['exact_match'] || null,
                    products: res['products'] || [],
                    parts: res["parts"],
                    hasMoreResults: results.length < res["results_count"],
                    search: this.inputEl.value,
                    fuzzySearch: res["fuzzy_search"],
                    widget: this.options,
                },
                this.el
            )[0];
            const extraLinks = this.menuEl.querySelectorAll('button.extra_link');
            extraLinks.forEach(btn => {
                btn.addEventListener('click', (event) => {
                    event.preventDefault();
                    window.location.href = event.currentTarget.dataset['target'];
                });
            });
            const fuzzySubmit = this.menuEl.querySelector('.s_searchbar_fuzzy_submit');
            if (fuzzySubmit) {
                fuzzySubmit.addEventListener('click', (event) => {
                    event.preventDefault();
                    this.inputEl.value = res['fuzzy_search'];
                    const form = this.el.closest('form');
                    if (form) {
                        form.submit();
                    }
                });
            }
        }
        this.hasDropdown = !!res;
        if (prevMenuEl) {
            prevMenuEl.remove();
        }
    },
});