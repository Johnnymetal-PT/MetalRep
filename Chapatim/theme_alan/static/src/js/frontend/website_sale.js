import { markup } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { MiniCart } from "theme_alan.MiniCart";
import { registry } from '@web/core/registry';
import { patch } from '@web/core/utils/patch';
import { _t } from '@web/core/l10n/translation';
import { redirect } from '@web/core/utils/urls';
import { Interaction } from '@web/public/interaction';
import wSaleUtils from '@website_sale/js/website_sale_utils';
import { QuickViewDialog } from "theme_alan.QuickViewDialog";
import { WebsiteSale } from '@website_sale/interactions/website_sale';

// ─── Website Sale ──────────────────────────────────────────────────────────
patch(WebsiteSale.prototype, {
    setup() {
        super.setup();
        Object.assign(this.dynamicContent, {
            '.product_detail_img': {
                "t-on-mouseenter": this.onProductImageMouseEnter,
                "t-on-mouseleave": this.onProductImageMouseLeave,
                't-on-mousemove': this.onProductImageMouseMove,
            }
        });
    },

    _isEditorEnabled() {
        return document.body.classList.contains("editor_enable");
    },

    onProductImageMouseEnter(ev) {
        if (this._isEditorEnabled()) return;
        ev.currentTarget.style.transition = 'transform 0.3s ease';
    },

    onProductImageMouseMove(ev) {
        if (this._isEditorEnabled()) return;
        const image = ev.currentTarget;
        image.style.cursor = 'zoom-in';
        const rect = image.getBoundingClientRect();
        const x = ((ev.clientX - rect.left) / rect.width) * 100;
        const y = ((ev.clientY - rect.top) / rect.height) * 100;
        image.style.transformOrigin = `${x}% ${y}%`;
        image.style.transform = 'scale(1.5)';
    },

    onProductImageMouseLeave(ev) {
        if (this._isEditorEnabled()) return;
        const image = ev.currentTarget;
        image.style.transform = '';
        image.style.cursor = '';
        image.style.transition = '';
        image.style.transformOrigin = '';
    },

    onChangeAttribute(ev) {
        const productGrid = this.el.querySelector('.o_wsale_products_grid_table_wrapper');
        if (productGrid) {
            productGrid.classList.add('opacity-50');
        }
        const form = wSaleUtils.getClosestProductForm(ev.currentTarget);
        const filters = form.querySelectorAll('input:checked, select');
        const attributeValues = new Map();
        const tags = new Set();
        const brands = new Set();
        const ratings = new Set();
        for (const filter of filters) {
            if (filter.value) {
                if (filter.name === 'attribute_value') {
                    const [attributeId, attributeValueId] = filter.value.split('-');
                    const valueIds = attributeValues.get(attributeId) ?? new Set();
                    valueIds.add(attributeValueId);
                    attributeValues.set(attributeId, valueIds);
                } else if (filter.name === 'tags') {
                    tags.add(filter.value);
                }
                else if (filter.name === 'brands') {
                    brands.add(filter.value);
                }
                else if (filter.name === 'ratings') {
                    ratings.add(filter.value);
                }
            }
        }
        const url = new URL(form.action);
        const searchParams = url.searchParams;
        for (const entry of attributeValues.entries()) {
            searchParams.append('attribute_values', `${entry[0]}-${[...entry[1]].join(',')}`);
        }
        if (tags.size) {
            searchParams.set('tags', [...tags].join(','));
        }
        if (brands.size) {
            searchParams.set('brands', [...brands].join(','));
        }
        if (ratings.size) {
            searchParams.set('ratings', [...ratings].join(','));
        }
        redirect(`${url.pathname}?${searchParams.toString()}`);
    },

    _setUrlHash() {
        var alan_quick_view = $('.as_quick_view_content');
        if (alan_quick_view.length > 0) {
            return
        } else {
            super._setUrlHash();
        }
    },
});

// ─── Similar Products ──────────────────────────────────────────────────────────
export class AlanSimilarProduct extends Interaction {
    static selector = '.as_similar_product';
    dynamicContent = {
        _root: {
            "t-on-click": this.onClickSimilarDialog,
        },
    };
    async onClickSimilarDialog(ev) {
        const productId = ev.currentTarget.dataset.product_tmpl_id;
        var template = rpc('/get_similar_product', { product_id: productId });
        Promise.all([template]).then((response) => {
            $(".offcanvas_similar_product").empty().append(markup(response[0]))
        });
    }
}
registry.category('public.interactions').add('theme_alan.alan_similar_product', AlanSimilarProduct);

// ─── Offer Timer ────────────────────────────────────────────────────────────────
export class AlanOfferTimer extends Interaction {
    static selector = '.as_offer_timer';
    setup() {
        if (this.el.getAttribute("data-offer-end") != 'false') {
            const runOfferTimer = () => {
                this.services.offer_timer.create({
                    target: this.el,
                    offerDate: this.el.getAttribute("data-offer-end")
                });
                const offerEnd = new Date(this.el.getAttribute("data-offer-end")).getTime();
                const now = new Date().getTime();
                if (now < offerEnd) {
                    setTimeout(runOfferTimer, 1000);
                }
            };
            runOfferTimer();
        }
    }
}
registry.category('public.interactions').add('theme_alan.alan_offer_timer', AlanOfferTimer);

// ─── MiniCart ─────────────────────────────────────────────────────────────────
export class AlanMiniCart extends Interaction {
    static selector = '.as_mini_cart';
    dynamicContent = {
        _root: {
            "t-on-click": this.onClickOpenMiniCart,
        },
    };

    async onClickOpenMiniCart() {
        this.services.dialog.add(MiniCart);
    }
}
registry.category('public.interactions').add('theme_alan.alan_mini_cart', AlanMiniCart);

// ─── Clear Filters ───────────────────────────────────────────────────────────
export class AlanClearFilter extends Interaction {
    static selector = '.as-shop-top-filter, .as-shop-sidebar-header';
    dynamicContent = {
        ".as-clear-filter": { "t-on-click": this.onClickClearFilter },
        ".as_hide_sidebar": { "t-on-click": this.onClickHideSidebar },
        ".as_show_sidebar": { "t-on-click": this.onClickShowSidebar },
    };
    setup() {
        super.setup();
        const asideContainer = document.querySelector('#products_grid_before');
        const showSidebarBtn = document.querySelector('.as_show_sidebar');
        const state = localStorage.getItem("as_filter_sidebar_state");
        if (asideContainer && showSidebarBtn) {
            if (state === "hidden") {
                showSidebarBtn.classList.remove('d-none');
                asideContainer.classList.add('as-filter-sidebar-hidden');
            } else {
                showSidebarBtn.classList.add('d-none');
                asideContainer.classList.remove('as-filter-sidebar-hidden');
            }
        }
    }
    async onClickClearFilter(ev) {
        const target = ev.currentTarget;
        const fieldName = target.dataset.name;
        const fieldValue = target.dataset.value;
        const inputs = document.querySelectorAll(
            `input[name="${fieldName}"][value="${fieldValue}`
        );
        if (inputs.length == 0) {
            const options = document.querySelectorAll(`option[value="${fieldValue}"]`);
            if (options) {
                options.forEach(option => {
                    const select = option.closest('select');
                    if (select) {
                        select.value = "";
                        select.dispatchEvent(new Event("change", { bubbles: true }));
                    }
                });
            }
        } else {
            inputs.forEach(input => {
                input.checked = false;
                input.dispatchEvent(new Event("change", { bubbles: true, cancelable: true }));
            });
        }
    }
    async onClickHideSidebar(ev) {
        const asideContainer = document.querySelector('#products_grid_before')
        const showSidebarBtn = document.querySelector('.as_show_sidebar');
        showSidebarBtn.classList.remove('d-none');
        asideContainer.classList.add('as-filter-sidebar-hidden')
        localStorage.setItem("as_filter_sidebar_state", "hidden");
    }
    async onClickShowSidebar(ev) {
        const asideContainer = document.querySelector('#products_grid_before')
        const showSidebarBtn = document.querySelector('.as_show_sidebar');
        showSidebarBtn.classList.add('d-none');
        asideContainer.classList.remove('as-filter-sidebar-hidden')
        localStorage.setItem("as_filter_sidebar_state", "visible");
    }
}
registry.category('public.interactions').add('theme_alan.alan_clear_filter', AlanClearFilter);

// ─── Attribute Search ───────────────────────────────────────────────────────
export class AlanAttributeSearch extends Interaction {
    static selector = '.as_filter_search';
    dynamicContent = {
        _root: {
            "t-on-keyup": this.onTriggerAttribute,

        },
    };
    async onTriggerAttribute(ev) {
        const curr_val = ev.target.value.toLowerCase();
        const item = ev.target.closest(".accordion-item");
        if (!item) return;
        const attrs = item.querySelectorAll("label.form-check-label");
        const colors = item.querySelectorAll("label.css_attribute_color");
        const brands = item.querySelectorAll("label.as_brand_attr_image");
        const imgs = item.querySelectorAll("label.css_attribute_image");
        const pills = item.querySelectorAll("label.pills-attr");

        // Attribute labels
        if (attrs.length > 0) {
            attrs.forEach(label => {
                const attr = label.textContent.toLowerCase();
                const formCheck = label.closest(".form-check");
                if (formCheck) {
                    formCheck.classList.toggle("d-none", !attr.includes(curr_val));
                }
            });
        }

        // Color attributes
        if (colors.length > 0) {
            colors.forEach(label => {
                const input = label.querySelector("input");
                const attr = input ? input.getAttribute("title").toLowerCase() : "";
                label.classList.toggle("d-none", !attr.includes(curr_val));

            });
        }

        // pills attributes
        pills.forEach(label => {
            const attr = label.textContent.toLowerCase();
            const isMatch = attr.includes(curr_val);
            label.classList.toggle("d-none", !isMatch);
            const count = label.nextElementSibling;
            if (count && count.classList.contains("as-attr-count")) {
                count.classList.toggle("d-none", !isMatch);
            }
        });

        // img attributes
        imgs.forEach(label => {
            const input = label.querySelector("input[type='checkbox']");
            const attr = input ? input.getAttribute("title").toLowerCase() : "";
            label.classList.toggle("d-none", !attr.includes(curr_val));
        });

        // Brand attributes
        if (brands.length > 0) {
            brands.forEach(label => {
                const attr = label.getAttribute("data-name")?.toLowerCase() || "";
                label.classList.toggle("d-none", !attr.includes(curr_val));
            });
        }
    }
}
registry.category('public.interactions').add('theme_alan.as_filter_search', AlanAttributeSearch);

// ─── Quick View ─────────────────────────────────────────────────────────────
export class AlanQuickView extends Interaction {
    static selector = '#wrapwrap';

    start() {
        super.start();
        this.addListener(this.el, 'click', (ev) => {
            const button = ev.target.closest('.as_quick_view');
            if (button) {
                this.onClickQuickView(ev, button);
            }
        });
    }

    async onClickQuickView(ev, button) {
        ev.preventDefault();
        ev.stopPropagation();
        let productTemplateId = parseInt(button.dataset.product_tmpl_id);
        if (!productTemplateId) {
            const form = button.closest('form');
            if (form) {
                const input = form.querySelector('input[type="hidden"][name="product_template_id"]');
                if (input) {
                    productTemplateId = parseInt(input.value);
                }
            }
        }
        if (!productTemplateId) {
            console.error("Product Template ID not found");
            return;
        }
        var template = await rpc('/get_quick_view_template', { product_id: productTemplateId });

        this.services.dialog.add(QuickViewDialog, {
            productTemplateId: productTemplateId,
            body: markup(template),
        });
        setTimeout(() => {
            const dialogContainer = document.querySelector('.o_dialog');
            if (dialogContainer && this.services["public.interactions"]) {
                this.services["public.interactions"].startInteractions(dialogContainer);
            }
        }, 100);
    }
}
registry.category('public.interactions').add('theme_alan.as_quick_view', AlanQuickView);

// ─── Load More ──────────────────────────────────────────────────────────────
export class ProductLoad extends Interaction {
    static selector = ".as-shop-page";

    dynamicContent = {
        "#loadMoreproducts": {
            "t-on-click": this._loadProduct,
        },
    };

    setup() {
        super.setup();
        this.rpc = rpc;
        this.next_products = false;
        this.pager = false;
        this.rmn_ids = [];
    }

    async start() {
        this.InitLoadProducts();
    }

    async InitLoadProducts() {
        this.next_products = false;
        this.pager = false;
        this.rmn_ids = [];
        const $next_page = document.querySelector(".alan_pager li.active + li");
        const prd_ids = $next_page?.dataset?.prd_ids ? JSON.parse($next_page.dataset.prd_ids) : [];
        const next_url = $next_page?.querySelector("a")?.getAttribute("href");
        const ppr = parseInt($next_page?.dataset?.ppr || 4);
        const displayedProductCount = this.el.querySelectorAll(".o_wsale_products_grid_table_wrapper input.product_ref_id").length;
        const totalProduct = parseInt(this.el.querySelector(".total-product-count")?.textContent || 0);
        const progressBar = this.el.querySelector(".as-progress-bar");
        const percentage = (displayedProductCount / totalProduct) * 100;
        if (progressBar) progressBar.style.width = `${percentage}%`;
        const countValue = this.el.querySelector(".product-count-value");
        if (countValue) countValue.textContent = displayedProductCount;
        const loadMoreBtn = this.el.querySelector("#loadMoreproducts");
        const allLoadedDiv = this.el.querySelector(".all_loaded");

        if (!next_url || !prd_ids.length) {
            if (loadMoreBtn) loadMoreBtn.style.display = "none";
            if (allLoadedDiv) {
                allLoadedDiv.classList.remove("d-none");
                allLoadedDiv.textContent = _t("All products are loaded.");
            }
            return;
        } else {
            if (allLoadedDiv) {
                allLoadedDiv.classList.add("d-none");
                allLoadedDiv.textContent = "";
            }
        }

        // Remaining IDs
        const $lasttr = this.el.querySelectorAll(".o_wsale_products_grid_table_wrapper tbody tr:last-child td");
        if ($lasttr.length < ppr) {
            $lasttr.forEach(td => {
                const id = parseInt(td.querySelector('.product_ref_id')?.value || 0);
                if (id) this.rmn_ids.push(id);
            });
        }
        const products = Array.from(this.el.querySelectorAll(".o_wsale_products_grid_table_wrapper input.product_ref_id"))
            .map(input => parseInt(input.value));
        const all_prds = [...this.rmn_ids, ...prd_ids];

        try {
            const result = await this.rpc("/nextpage/products", {
                'product_ids': all_prds,
                'products': products,
                'ppr': ppr,
            });

            if (result) {
                this.next_products = result;
            }

        } catch (error) {
            console.error("RPC Load Error:", error);
        }
    }

    async _loadProduct() {
        if (this.next_products) {
            const $active_page = document.querySelector(".alan_pager li.active");
            const $next_page = document.querySelector(".alan_pager li.active + li");
            const wrapper = this.el.querySelector(".o_wsale_products_grid_table_wrapper section");
            if (wrapper) {
                wrapper.insertAdjacentHTML("beforeend", this.next_products);
            }
            if ($active_page) $active_page.classList.remove("active");
            if ($next_page) $next_page.classList.add("active");
        }
        await this.InitLoadProducts();
        window.dispatchEvent(new Event('resize'));
        $(".css_attribute_preview_thumbnail").trigger("widgets_start_request");
        $(".as_similar_product").trigger("widgets_start_request");
        $(".o_wsale_product_grid_wrapper").trigger("widgets_start_request");
        $(".as_offer_timer").trigger("widgets_start_request");
        const websiteSaleInteractions = this.services["public.interactions"].interactions.filter(
            (interaction) => interaction.interaction instanceof WebsiteSale || interaction.interaction.constructor.name === 'ProductComparison'
        );
        for (const interaction of websiteSaleInteractions) {
            interaction.updateContent();
        }
        this.services["public.interactions"].startInteractions(this.el);
    }
}

registry.category("public.interactions").add("theme_alan.product_load", ProductLoad);

// ─── Category Offcanvas ─────────────────────────────────────────────────
export class AlanCategoryOffcanvas extends Interaction {
    static selector = '.as-category-action';
    dynamicContent = {
        _root: {
            "t-on-click": this.onClickCategoryLoad,
        },
    };

    async onClickCategoryLoad() {
        var template = await rpc('/get_offcanvas_category');
        $(".as_offcanvas_categories").empty().append(markup(template));
        // Start interactions for dynamically loaded content
        this.startCategoryInteractions();
    }

    startCategoryInteractions() {
        const container = document.querySelector('.as_offcanvas_categories');
        if (!container) return;

        // Handle category expand clicks
        const categoryLinks = container.querySelectorAll('.as-category-link');
        categoryLinks.forEach((link) => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const categoryId = link.getAttribute('data-category-id');
                this.loadCategoryContent(categoryId);
            });
        });

        // Handle back button
        const backBtn = container.querySelector('.as-back-btn');
        if (backBtn) {
            backBtn.addEventListener('click', (e) => {
                e.preventDefault();
                const parentId = backBtn.getAttribute('data-parent-id');
                if (parentId !== 'false') {
                    this.loadCategoryContent(parentId);
                } else {
                    this.loadCategoryContent(null);
                }
            });
        }

        // Handle leaf category clicks
        const leafCategories = container.querySelectorAll('.as-leaf-category');
        leafCategories.forEach((link) => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const categoryId = link.getAttribute('data-category-id');
                window.location.href = '/shop/category/' + categoryId;
            });
        });
    }

    async loadCategoryContent(categoryId) {
        try {
            const template = await rpc('/get_offcanvas_category', {
                parent_id: categoryId || null
            });

            const container = document.querySelector('.as_offcanvas_categories');
            if (container) {
                container.innerHTML = markup(template);
                // Re-attach event listeners for dynamically loaded content
                this.startCategoryInteractions();
            }
        } catch (error) {
            console.error('Error loading categories:', error);
        }
    }
}
registry.category('public.interactions').add('theme_alan.alan_category_offcanvas', AlanCategoryOffcanvas);

export class BrandAlphabetFilter extends Interaction {
    static selector = '.as-all-brand-page';

    dynamicContent = {
        '.as-letter-filter a[data-letter]': {
            "t-on-click": this.onAlphabetClick,
        },
    };

    setup() {
        super.setup();
        const params = new URLSearchParams(window.location.search);
        const letter = params.get('letter') || 'all';
        if (letter !== 'all') {
            this._filterBrands(letter);
            this._updateActiveState(letter);
        }
    }

    onAlphabetClick(ev) {
        ev.preventDefault();
        const letter = ev.currentTarget.dataset.letter || 'all';
        this._filterBrands(letter);
        this._updateActiveState(letter);

        const newUrl = new URL(window.location.href);
        if (letter === 'all') {
            newUrl.searchParams.delete('letter');
        } else {
            newUrl.searchParams.set('letter', letter);
        }
        window.history.pushState({}, '', newUrl.toString());
    }

    _filterBrands(letter) {
        const brandBoxes = this.el.querySelectorAll('.as-lp-brand-box');
        let visibleCount = 0;

        if (letter === 'all') {
            brandBoxes.forEach(box => {
                box.closest('[class*="col-"]').style.display = '';
            });
            visibleCount = brandBoxes.length;
        } else {
            brandBoxes.forEach(box => {
                const name = box.querySelector('h6 a')?.textContent?.trim() || '';
                const firstChar = name[0]?.toUpperCase() || '';
                const col = box.closest('[class*="col-"]');
                if (firstChar === letter) {
                    col.style.display = '';
                    visibleCount++;
                } else {
                    col.style.display = 'none';
                }
            });
        }

        this._toggleNoBrandsMessage(visibleCount === 0);
    }

    _toggleNoBrandsMessage(show) {
        const container = this.el.querySelector('.as-letter-container-box');
        if (!container) return;

        let msg = this.el.querySelector('.as-no-brands-msg');
        if (show && !msg) {
            msg = document.createElement('div');
            msg.className = 'as-no-brands-msg alert alert-info text-center';
            msg.innerHTML = '<p class="mb-0">No brands found.</p>';
            container.after(msg);
        } else if (!show && msg) {
            msg.remove();
        }
    }

    _updateActiveState(activeLetter) {
        this.el.querySelectorAll('.as-letter-filter a[data-letter]').forEach(a => {
            const isActive = a.dataset.letter === activeLetter;
            a.classList.toggle('btn-primary', isActive);
            a.classList.toggle('btn-outline-primary', !isActive);
        });
    }
}

registry.category('public.interactions').add('BrandAlphabetFilter', BrandAlphabetFilter);