import { markup } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { patch } from '@web/core/utils/patch';
import { _t } from "@web/core/l10n/translation";
import { uniqueId } from "@web/core/utils/functions";
import { Interaction } from "@web/public/interaction";
import { MegaMenuDropdown } from "@website/interactions/dropdown/mega_menu_dropdown";
import comparisonUtils from '@website_sale_comparison/js/website_sale_comparison_utils';
import { ProductComparison } from '@website_sale_comparison/interactions/product_comparison';

// ─── Dynamic Snippets Selector ──────────────────────────────────────────────────
const ALAN_DYNAMIC_SNIPPETS_SELECTOR = `
.as-snippet-builder,
[data-snippet-name='ProductSlider'],
[data-snippet-name='products'],
[data-snippet-name='BestSellingProduct'],
[data-snippet-name='LatestProduct'],
[data-snippet-name='CategoryProduct'],
[data-snippet-name='categories_products'],
[data-snippet-name='BrandProduct'],
[data-snippet-name='brand_products'],
[data-snippet-name='ProductBanner'],
[data-snippet-name='product_banner'],
[data-snippet-name='CategorySlider'],
[data-snippet-name='categories'],
[data-snippet-name='BrandSlider'],
[data-snippet-name='brands'],
[data-snippet-name='BlogSlider'],
[data-snippet-name='blogs'],
[data-snippet-name='highlighted_product_grid'],
[data-snippet-name='brand_collection_showcase']
`;

// ─── Alan MegaMenu Snippets Selector ────────────────────────────────────────────
const ALAN_MEGAMENU_SNIPPETS_SELECTOR = `
.as-mega-menu-preview-section,
[data-snippet-name='megamenu_products'],
[data-snippet-name='MegaMenuProduct'],
[data-snippet-name='megamenu_category'],
[data-snippet-name='MegaMenuCategory'],
[data-snippet-name='megamenu_brand'],
[data-snippet-name='MegaMenuBrand'],
[data-snippet-name='megamenu_shop_navigator'],
[data-snippet-name='megamenu_multi_category']
`;

// ─── Swiper Initialization ──────────────────────────────────────────────────────
const initializeSwipers = (el, sliderConfig, uniqueId) => {
    if (!el || !window.Swiper || !sliderConfig) return;

    const sliderEls = el.querySelectorAll(".as_page_swiper");
    if (!sliderEls.length) return;

    sliderEls.forEach((slider, idx) => {
        try {
            const id = `as_swiper_slider_${uniqueId}_${idx}`;
            slider.id = id;
            new window.Swiper(`#${id}`, sliderConfig);
            slider.removeAttribute("id");
        } catch (err) {
            console.warn("Swiper init failed:", err);
        }
    });
};

// ─── Snippet Loader ──────────────────────────────────────────────────────────────
const snippetLoader = async (container) => {
    if (!container) return;
    try {
        const designEditAttr = container.getAttribute('data-design-edit') || container.getAttribute('data-designEdit') || '{}';
        const snippetEditor = JSON.parse(designEditAttr);

        let defCol = Number(snippetEditor.default_col_desk) || 4;
        if (isNaN(defCol) || defCol < 1 || defCol > 6) {
            defCol = 4;
        }

        const res = await rpc('/get/snippets_loader_gif');
        const colSize = Math.floor(12 / defCol) || 1;
        const colClass = `col-lg-${colSize} col-md-${Math.min(6, colSize * 2)}`;
        const loaderCount = defCol;
        let rowHtml = '<div class="row">Missing Loader GIF</div>';
        if (res) {
            let singleLoaderGif = `
            <div class="${colClass} mb-4 text-center">
                <img
                    src="${res}"
                    alt="Loading…"
                    style="margin:auto;"
                />
            </div>`;
            rowHtml = '<div class="row">';

            for (let i = 0; i < loaderCount; i++) {
                rowHtml += singleLoaderGif;
            }
            rowHtml += '</div>';
        }
        else {

            let singleLoaderGif = `
            <div class="${colClass} mob-col-${defCol} mb-4">
            <div class="as_tab_products_loader-inner">
                    <div class="card placeholder-glow" aria-hidden="true">
                        <div class="card-img-top placeholder"></div>
                        <div class="card-body">
                            <h5 class="card-title placeholder-glow">
                                <span class="placeholder col-6"></span>
                            </h5>
                            <p class="card-text placeholder-glow">
                                <span class="placeholder col-7"></span>
                                <span class="placeholder col-4"></span>
                                <span class="placeholder col-4"></span>
                                <span class="placeholder col-6"></span>
                                <span class="placeholder col-8"></span>
                            </p>
                            <a class="btn btn-primary disabled placeholder col-6" aria-disabled="true"></a>
                        </div>
                    </div>
                </div>
            </div>
            `;

            rowHtml = `<div class="row g-2 g-md-3 as-snippets-row as_tab_products_loader">`;

            for (let i = 0; i < loaderCount; i++) {
                rowHtml += singleLoaderGif;
            }
            rowHtml += '</div>';
        }
        container.innerHTML = rowHtml;
    } catch (err) {
        console.error("Error showing loader:", err);
    }
};

// ─── Snippet Lazy Loader ──────────────────────────────────────────────────────────────
const SnippetLazyLoader = {
    AlanLoader(el, callback, options = { threshold: 0, rootMargin: '400px 0px' }) {
        const observer = new IntersectionObserver(async (entries, obs) => {
            if (!entries.some(e => e.isIntersecting)) return;
            await callback();
            obs.unobserve(el);
        }, options);
        observer.observe(el);
    }
};

// ─── Dynamic Snippets ────────────────────────────────────────────────────────────────
export class DynamicSnippets extends Interaction {
    static selector = ALAN_DYNAMIC_SNIPPETS_SELECTOR;
    dynamicContent = {
        ".as-tab-name": { "t-on-click": this.onClickTabs.bind(this) },
    };

    setup() {

        this.data = {};
        this.uniqueId = uniqueId("alan_slider_");
        this.containers = [...this.el.querySelectorAll(".as-snippet-drop-container")];

        this.onResize = () => {
            this.containers.forEach(container => this._updateHoverClasses(container));
        };
        window.addEventListener("resize", this.onResize);
    }

    async willStart() {
        const isEditMode = document.body.classList.contains('editor_enable');
        if (isEditMode) {
            return;
        }
        await Promise.all(
            this.containers.map(container =>
                this._loadContainer(container)
            )
        );
    }

    async _loadContainer(container) {
        if (container && container.dataset.snippetName != "static_snippets") {
            if (!this._shouldDisplaySnippet(container)) {
                container.style.display = 'none';
                return;
            }

            SnippetLazyLoader.AlanLoader(this.el, async () => {
                await snippetLoader(container);
                await this.fetchData(container);
                if (!this.data || !this.data.template) {
                    container.style.display = 'none';
                    return;
                }
                this.render(container);
                $(".css_attribute_preview_thumbnail").trigger("widgets_start_request")
                this.services["public.interactions"].startInteractions(container);
            });
        }
    }

    _shouldDisplaySnippet(container) {
        if (!container) return false;

        try {
            const snippetEditor = JSON.parse(container.dataset.designEdit || "{}");
            const startDate = snippetEditor.start_date;
            const endDate = snippetEditor.end_date;
            const now = new Date();
            if (!startDate && !endDate) {
                return true;
            }
            // Check start date
            if (startDate) {
                const start = new Date(startDate);
                if (now < start) {
                    return false;
                }
            }
            // Check end date
            if (endDate) {
                const end = new Date(endDate);
                if (now > end) {
                    return false;
                }
            }
            return true;

        } catch (err) {
            console.error("Error checking snippet date range:", err);
            return true;
        }
    }

    async fetchData(container) {
        if (!container) return;
        const snippetEditor = JSON.parse(container.dataset.designEdit || "{}");
        const context = {
            snippet: container.dataset.snippetName,
            record_ids: JSON.parse(container.dataset.recordIds || container.dataset.recordsIds || "[]"),
            model: container.dataset.modal,
            design_editor: snippetEditor,
        };
        try {
            const res = await this.waitFor(rpc("/get_snippet_template", context));
            this.data = res || {};
        } catch (err) {
            console.error("DynamicSnippets fetchData error:", err);
            this.data = {};
        }
    }

    render(container) {
        if (!container) return;
        if (this.data?.template) {
            const range = document.createRange();
            const fragment = range.createContextualFragment(this.data.template);
            container.replaceChildren(...fragment.childNodes);
        }

        const sliderEls = this.el.querySelectorAll(".as_page_swiper");
        if (sliderEls.length) {
            this.waitForTimeout(() => this.initSliders(), 0);
        }
        this.waitForTimeout(() => this._updateHoverClasses(container), 0);
    }

    initSliders() {
        initializeSwipers(this.el, this.data.slider_config, this.uniqueId);
    }

    async onClickTabs(ev) {
        const target = ev.target.closest(".as-tab-name");
        if (!target || !target.dataset?.id) return;
        const container = target.closest(".as-snippet-drop-container");
        const tabId = target.dataset.id;
        const snippetName = this._getSnippetName(container);
        if (!snippetName) return;

        // ================= BRAND NAME =================
        const brandName =
            target.dataset.name ||
            target.querySelector("span")?.innerText;

        const titleEl = this.el.querySelector(".as-active-brand-name");
        if (titleEl && brandName) {
            titleEl.textContent = brandName;
        }

        // ================= PRODUCT COUNT =================
        const countEl = this.el.querySelector(".as-brand-product-count");
        if (countEl) {
            countEl.textContent = `${target.dataset.count || 0} Products in this brand.`;
        }

        // ================= VIEW ALL LINK =================
        const viewAllBtn = this.el.querySelector(".as-view-all-link");
        if (viewAllBtn) {
            const separator = viewAllBtn.href.includes('?') ? '&' : '?';
            viewAllBtn.href = `/shop?${snippetName === 'brand' ? 'brands' : 'category'}=${tabId}`;
        }

        // ================= ACTIVE TAB =================
        this.el.querySelectorAll(".as-tab-name").forEach(b => {
            b.classList.toggle("active", b === target);
        });

        // ================= TAB CONTENT =================
        const pane = this.el.querySelector(`[data-tab-id="${snippetName}_${tabId}"]`);
        if (!pane) return;

        this.el.querySelectorAll(".as-tab-pane").forEach(e => e.classList.remove("active"));
        pane.classList.add("active");

        if (pane.dataset.loaded === "1") {
            window.dispatchEvent(new Event("resize"));
            return;
        }

        const snippetEditor = JSON.parse(container.dataset.designEdit || "{}");
        const res = await this.waitFor(rpc("/tab/products", {
            snippet_name: snippetName,
            tab_id: tabId,
            design_editor: snippetEditor
        }));

        if (res && res.template) {
            const range = document.createRange();
            const fragment = range.createContextualFragment(res.template);
            pane.innerHTML = "";
            pane.appendChild(fragment);
            pane.dataset.loaded = "1";
            if (snippetEditor.active_view === 'slider') {
                initializeSwipers(pane, this.data.slider_config, this.uniqueId);
            }
            this.services["public.interactions"].startInteractions(pane);
        }
    }

    _getSnippetName(container) {
        const CATEGORY_SNIPPETS = ['CategoryProduct', 'categories_products'];
        const BRAND_SNIPPETS = ['BrandProduct', 'brand_products', 'brand_collection_showcase'];
        const name = container?.dataset.snippetName;
        if (CATEGORY_SNIPPETS.includes(name)) return "category";
        if (BRAND_SNIPPETS.includes(name)) return "brand";
        return null;
    }

    _updateHoverClasses(container) {
        if (!container) return;
        try {
            const snippetEditor = JSON.parse(container.dataset.designEdit || "{}");
            const hasHoverDesktop = snippetEditor.allow_hover_image;
            const hasHoverMobile = snippetEditor.mob_allow_hover_image;

            container.classList.remove(
                "o_wsale_products_opt_img_secondary_show",
                "o_wsale_products_opt_img_hover_zoom_out_light"
            );

            let shouldShowHover = false;
            if (window.innerWidth < 992) {
                shouldShowHover = hasHoverMobile;
            } else {
                shouldShowHover = hasHoverDesktop;
            }

            if (shouldShowHover) {
                container.classList.add("o_wsale_products_opt_img_secondary_show");
                container.classList.add("o_wsale_products_opt_img_hover_zoom_out_light");
            }
        } catch (e) {
            console.warn("Failed to update hover classes:", e);
        }
    }

    destroy() {
        if (this.onResize) {
            window.removeEventListener("resize", this.onResize);
        }
        super.destroy();
    }
}

registry.category("public.interactions").add("DynamicSnippets", DynamicSnippets);

// ─── Alan MegaMenu ──────────────────────────────────────────────────────────────
export class AlanMegaMenu extends Interaction {
    static selector = ALAN_MEGAMENU_SNIPPETS_SELECTOR;

    setup() {
        this.data = {};
        this.uniqueId = uniqueId("alan_slider_");
        this.containers = [...this.el.querySelectorAll(".as-snippet-drop-container")];
    }

    async willStart() {
        await Promise.all(
            this.containers.map(container =>
                this._loadContainer(container)
            )
        );
    }

    async _loadContainer(container) {
        if (container && container.dataset.snippetName != "static_snippets") {
            SnippetLazyLoader.AlanLoader(this.el, async () => {
                await this.fetchData(container);
                this.render(container);
                this.services["public.interactions"].startInteractions(container);
            });
        }
    }

    async fetchData(container) {
        if (!container) return;
        const snippetEditor = JSON.parse(container.dataset.designEdit || "{}");
        let recordIdsRaw = container.dataset.recordIds || container.dataset.recordsIds || "[]";

        const context = {
            snippet: container.dataset.snippetName,
            record_ids: JSON.parse(recordIdsRaw),
            model: container.dataset.modal,
            design_editor: snippetEditor,
        };

        try {
            const res = await this.waitFor(rpc("/get_megamenu_snippet_template", context));
            this.data = res || {};
        } catch (err) {
            console.error("AlanMegaMenu fetchData error:", err);
            this.data = {};
        }
    }

    render(container) {
        if (!container) return;

        if (this.data?.template) {
            const range = document.createRange();
            const fragment = range.createContextualFragment(this.data.template);
            container.replaceChildren(...fragment.childNodes);
        }

        const sliderEls = this.el.querySelectorAll(".as_page_swiper");
        if (sliderEls.length) {
            this.waitForTimeout(() => this.initSliders(), 0);
        }
    }

    initSliders() {
        initializeSwipers(this.el, this.data.slider_config, this.uniqueId);
    }
}

registry.category("public.interactions").add("AlanMegaMenu", AlanMegaMenu);

// ─── MegaMenu Tabs Snippets ──────────────────────────────────────────────────────────
export class MegaMenuTabsSnippets extends Interaction {
    static selector = ".as-mm-tabs-level-1";

    dynamicContent = {
        _root: {
            "t-on-mouseenter": this._showMegaMenuTabs.bind(this),
        },
        ".as-mob-tab-menu": { "t-on-click": this._showMegaMenuTabsMob.bind(this) },
        ".as-mm-tabs-level-2": { "t-on-click": this._stopClickProp.bind(this) },
    };

    _stopClickProp(ev) {
        ev.stopPropagation();
    }

    _showMegaMenuTabs(ev) {
        const current = ev.currentTarget;
        if (!current.classList.contains("active")) {
            const parentLevels = current.closest(".as-mm-tabs-levels");
            parentLevels.querySelectorAll(".as-mm-tabs-level-1.active").forEach((el) => {
                el.classList.remove("active");
            });
            current.classList.add("active");
        }
    }
    _showMegaMenuTabsMob(ev) {
        if (!ev || !ev.currentTarget) {
            return;
        }
        ev.preventDefault();
        ev.stopPropagation();
        const parentTab = ev.currentTarget.closest('.as-mm-tabs-level-1');
        if (!parentTab || !parentTab.classList) {
            return;
        }

        parentTab.classList.toggle('active');
        parentTab.classList.toggle('as-mob-menu');
    }
}

registry.category("public.interactions").add(
    "theme_alan.megamenu_tabs_snippets",
    MegaMenuTabsSnippets
);

registry.category("public.interactions.edit").add("theme_alan.MegaMenuTabsSnippets", {
    Interaction: MegaMenuTabsSnippets,
});

// ─── Snippet Builder Preview ─────────────────────────────────────────────────────
export class SnippetBuilderPreview extends Interaction {
    static selector = "#as_sb_wrap";

    dynamicContent = {
        _root: {
            "t-on-click": this.onClick,
            "t-on-as-sb-reload": this.onReload,
        },
    }

    onClick(ev) {
        ev.stopImmediatePropagation();
        ev.stopPropagation();
        ev.preventDefault();
        return false;
    }

    onReload() {
        const container = document.querySelector('.as-snippet-drop-container');
        if (container && this.services["public.interactions"]) {
            this.services["public.interactions"].startInteractions(container);
        }

    }
}
registry.category("public.interactions").add(
    "theme_alan.snippet_builder_preview",
    SnippetBuilderPreview
);



// ─── Patch MegaMenuDropdown to keep active state on menu links ─────────────────────────────────────────
patch(MegaMenuDropdown.prototype, {
    updateActiveMenuLinks() {
        if (this.el.querySelector(".navbar #top_menu a.nav-link.active")) {
            return;
        }
        const currentHrefWithoutHash = `${window.location.origin}${window.location.pathname}`;
        const megaMenuEls = this.el.querySelectorAll(".o_mega_menu");
        let matchingLink = null;
        megaMenuEls.forEach((megaMenuEl, position) => {
            const linkEls = Array.from(megaMenuEl.querySelectorAll(`a[href]:not([href="#"])`));
            matchingLink = linkEls.find((linkEl) => {
                try {
                    const url = new URL(linkEl.href);
                    return `${url.origin}${url.pathname}` === currentHrefWithoutHash;
                } catch {
                    return false;
                }
            });
            if (matchingLink) {
                const megaMenuToggleEl = megaMenuEl
                    .closest(".nav-item")
                    .querySelector(".o_mega_menu_toggle");
                const mobileMegaMenuToggleEl = this.el.querySelectorAll(
                    "#top_menu_collapse_mobile .top_menu .o_mega_menu_toggle"
                )[position];
                if (megaMenuToggleEl && mobileMegaMenuToggleEl) {
                    megaMenuToggleEl.classList.add("active");
                    mobileMegaMenuToggleEl.classList.add("active");
                }
            }
        });
    }
})

patch(ProductComparison.prototype, {
    setup() {
        if (document.querySelector(".as-quick-view-modal")) {
            return;
        }
        const isSnippetContext = document.querySelector(".as-snippet-builder, #as_sb_wrap");
        const isWebsiteSale = document.querySelector(".oe_website_sale");
        if (isSnippetContext && !isWebsiteSale) {
            return;
        }
        super.setup();
    },

    async addProduct(ev) {
        const initialProducts = comparisonUtils.getComparisonProductIds();
        await super.addProduct(ev);
        const currentProducts = comparisonUtils.getComparisonProductIds();
        if (currentProducts.length > initialProducts.length) {
            this.services.notification.add(markup('<i class="fa fa-check-circle text-success me-2 as-compare-log"></i> Product Added to Comparison.'),
                {
                    type: 'success',
                    sticky: false,
                    messageIsHtml: true,
                    buttons: [
                        {
                            name: _t("View"),
                            icon: 'fa-eye',
                            primary: true,
                            onClick: () => {
                                const productIds = comparisonUtils.getComparisonProductIds();
                                const comparisonUrl = `/shop/compare?products=${encodeURIComponent(productIds.join(','))}`;
                                window.location.href = comparisonUrl;
                            }
                        },

                    ],
                }
            );
        }
    },

});