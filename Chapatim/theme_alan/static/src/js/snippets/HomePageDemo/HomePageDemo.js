/** @odoo-module **/
import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";
import { Dialog } from "@web/core/dialog/dialog";
import { withSequence } from "@html_editor/utils/resource";
import { CONTAINER_WIDTH } from "@website/builder/option_sequence";
import { BuilderAction } from "@html_builder/core/builder_action";
import { Component, useState, useRef, onMounted, onWillUnmount } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { rpc } from "@web/core/network/rpc";
import { AlanSelectSearch } from "../../alan_select_search/alan_select_search";


// ─────────────────────────────────────────────────────────────────────────────
// 12 STEP DEFINITIONS
// ─────────────────────────────────────────────────────────────────────────────
const STEPS = [
    {
        id: "hero_slider",
        num: 1,
        type: "wb_static",
        label: "Hero Slider",
        badge: "Website Builder",
        icon: "fa-play-circle",
        templateOWL: "theme_alan.slider_temp18",
        snippetName: "Alan Website Builder - Sider - Sider 18",
        info: "A full-width hero carousel added at top of page.",
        note: "Pre-selected. No extra config needed.",
        previewImage: "/theme_alan/static/src/img/snippets/snippets_icon/slider_temp18.png",
        features: [
            { title: "Full-width Banner", desc: "Captivate users instantly with a high-impact sliding hero section." },
            { title: "Interactive CTA Buttons", desc: "Pre-designed primary and secondary buttons ready for links." },
            { title: "Fluid Transitions", desc: "Supports smooth touch swipes and auto-play carousel features." }
        ]
    },
    {
        id: "title_category",
        num: 2,
        type: "composite",
        label: "Category Section",
        badge: "Title + Dynamic",
        icon: "fa-th-large",
        titleOWL: "theme_alan.title_8",
        dynamicKey: "categories",
        dynamicLabel: "Categories",
        defaultTitle: "Shop by Category",
        defaultSubtitle: "Find furniture that fits your lifestyle.",
        defaultView: "slider",
        info: "Section Title heading + dynamic category carousel/grid.",
        previewImage: "/theme_alan/static/src/img/snippets/category_slider_demo_page.png",
        features: [
            { title: "Shop by Category", desc: "Directly navigate customers to relevant shopping collections." },
            { title: "Interactive Grid/Slider", desc: "Toggle category card designs between scrolling slider or static grid." },
            { title: "Modern Image Cards", desc: "Beautiful layouts with hover transitions and clean typography." }
        ]
    },
    {
        id: "feature_23",
        num: 3,
        type: "wb_static",
        label: "Feature 23",
        badge: "Website Builder",
        icon: "fa-star",
        templateOWL: "theme_alan.feature_temp23",
        snippetName: "Alan Website Builder - Features - Feature 23",
        info: "Feature highlights block.",
        note: "Pre-selected. No extra config needed.",
        previewImage: "/theme_alan/static/src/img/snippets/snippets_icon/feature_temp23.png",
        features: [
            { title: "3-Column Value Block", desc: "Present value propositions, guarantees, or core services cleanly." },
            { title: "Custom Icon Headers", desc: "Includes FontAwesome icons that can be changed dynamically." },
            { title: "Minimalist Design", desc: "Optimized spacing and typography focusing on readability." }
        ]
    },
    {
        id: "title_bestseller",
        num: 4,
        type: "composite",
        label: "Best Seller Products",
        badge: "Title + Dynamic",
        icon: "fa-trophy",
        titleOWL: "theme_alan.title_8",
        dynamicKey: "products",
        dynamicLabel: "Products",
        defaultTitle: "Best Sellers",
        defaultSubtitle: "Our most popular products loved by customers.",
        defaultView: "slider",
        defaultFilter: "best_seller",
        info: "Section Title heading + best-seller product slider.",
        previewImage: "/theme_alan/static/src/img/snippets/as_sb_product.png",
        features: [
            { title: "Dynamic Best-Sellers", desc: "Automatically queries and populates your most popular products." },
            { title: "Complete Shop Actions", desc: "Includes quick Add-to-Cart, Wishlist, and variant preview triggers." },
            { title: "Discount Badges", desc: "Shows original vs sale price differences automatically." }
        ]
    },
    {
        id: "feature_25",
        num: 5,
        type: "wb_static",
        label: "Feature 25",
        badge: "Website Builder",
        icon: "fa-star",
        templateOWL: "theme_alan.feature_temp25",
        snippetName: "Alan Website Builder - Features - Feature 25",
        info: "Feature section 25 layout.",
        note: "Pre-selected. No extra config needed.",
        previewImage: "/theme_alan/static/src/img/snippets/snippets_icon/feature_temp25.png",
        features: [
            { title: "Promotional Banner Grid", desc: "Showcase seasonal discounts or collections in split layouts." },
            { title: "Clean Hover Effects", desc: "Includes image zoom and title slide-up animations." },
            { title: "Fully Responsive", desc: "Adapts layouts perfectly for tablet and mobile screens." }
        ]
    },
    {
        id: "title_highlighted",
        num: 6,
        type: "composite",
        label: "Trending Now",
        badge: "Title + Dynamic",
        icon: "fa-bolt",
        titleOWL: "theme_alan.title_8",
        dynamicKey: "highlighted_product_grid",
        dynamicLabel: "Trending Now",
        defaultTitle: "Trending Now",
        defaultSubtitle: "Products that customers are loving this week",
        defaultView: "grid",
        info: "Section Title heading + highlighted products grid.",
        previewImage: "/theme_alan/static/src/img/snippets/as_sb_highlighted.png",
        features: [
            { title: "Asymmetric Product Grid", desc: "Highlights specific products with a modern offset layout." },
            { title: "Product Variants", desc: "Allows users to inspect different product color variants." },
            { title: "Live Stock Labels", desc: "Integrates with live inventory to display custom stock badges." }
        ]
    },
    {
        id: "feature_26",
        num: 7,
        type: "wb_static",
        label: "Feature 26",
        badge: "Website Builder",
        icon: "fa-star",
        templateOWL: "theme_alan.feature_temp26",
        snippetName: "Alan Website Builder - Features - Feature 26",
        info: "Feature section 26 layout.",
        note: "Pre-selected. No extra config needed.",
        previewImage: "/theme_alan/static/src/img/snippets/feature_temp26_demo.png",
        features: [
            { title: "Campaign Showcase", desc: "Excellent section for brand storytelling or campaign launch." },
            { title: "Action Callouts", desc: "Clean buttons matching the global theme color scheme." },
            { title: "High Contrast Panels", desc: "Stunning background overlay support for clean reading." }
        ]
    },
    {
        id: "brand_collection",
        num: 8,
        type: "dynamic",
        label: "Brand Collection",
        badge: "Snippet Builder",
        icon: "fa-building",
        dynamicKey: "brand_collection_showcase",
        dynamicLabel: "Brand Collection Gallery",
        defaultView: "slider",
        info: "Brand gallery with products per brand.",
        previewImage: "/theme_alan/static/src/img/snippets/as_sb_brand_collection.png",
        features: [
            { title: "Brand Gallery", desc: "Exhibits brand categories alongside their related products." },
            { title: "Multi-Brand Filtering", desc: "Enables customers to filter catalog items based on manufacturers." },
            { title: "Grid & Carousel", desc: "Flexible presentation styles for brand card elements." }
        ]
    },
    {
        id: "feature_24",
        num: 9,
        type: "wb_static",
        label: "Feature 24",
        badge: "Website Builder",
        icon: "fa-star",
        templateOWL: "theme_alan.feature_temp24",
        snippetName: "Alan Website Builder - Features - Feature 24",
        info: "Feature section 24 layout.",
        note: "Pre-selected. No extra config needed.",
        previewImage: "/theme_alan/static/src/img/snippets/snippets_icon/feature_temp24.png",
        features: [
            { title: "Trust Badges Section", desc: "Display customer trust indicators (Free Shipping, Secure Payment)." },
            { title: "Scalable Vector Icons", desc: "Fully editable icon library placeholders ready to modify." },
            { title: "Clean Layout Grid", desc: "Four columns that snap beautifully on smaller viewport sizes." }
        ]
    },
    {
        id: "product_spotlight",
        num: 10,
        type: "dynamic",
        label: "Product Spotlight",
        badge: "Snippet Builder",
        icon: "fa-fire",
        dynamicKey: "product_spotlight",
        dynamicLabel: "Product Spotlight",
        defaultView: "grid",
        info: "Tabbed: Best Seller / New Arrival / On Sale.",
        previewImage: "/theme_alan/static/src/img/snippets/as_sb_spotlight.png",
        features: [
            { title: "Tabbed Spotlights", desc: "Switch between Best Sellers, New Arrivals, and Sale items." },
            { title: "Hero Highlight Panel", desc: "Large focus product card on the left with smaller items on the right." },
            { title: "Dynamic Database Fetch", desc: "Keeps product listings synchronized with live catalog changes." }
        ]
    },
    {
        id: "title_blog",
        num: 11,
        type: "composite",
        label: "Blog Section",
        badge: "Title + Dynamic",
        icon: "fa-rss",
        titleOWL: "theme_alan.title_8",
        dynamicKey: "blogs",
        dynamicLabel: "Blog Posts",
        defaultTitle: "Latest News",
        defaultSubtitle: "Home into a smart home, you're not alone.",
        defaultView: "slider",
        info: "Section Title heading + blog posts slider.",
        previewImage: "/theme_alan/static/src/img/snippets/as_sb_blog.png",
        features: [
            { title: "Latest News Slider", desc: "Displays your published blog posts inside a clean carousel." },
            { title: "Post Metadata Bar", desc: "Renders post publication date, author name, and comments count." },
            { title: "Content Previews", desc: "Automatically generates short summary snippets of article texts." }
        ]
    },
    {
        id: "brand_slider",
        num: 12,
        type: "dynamic",
        label: "Brand Slider",
        badge: "Snippet Builder",
        icon: "fa-certificate",
        dynamicKey: "brands",
        dynamicLabel: "Brands",
        defaultView: "slider",
        info: "Brand logo slider at bottom of page.",
        previewImage: "/theme_alan/static/src/img/snippets/as_sb_brand.png",
        features: [
            { title: "Partner Logo Loop", desc: "Displays all partner/manufacturer logos in a horizontal loop." },
            { title: "Automatic Scrolling", desc: "Smooth loop animation that scrolls logos automatically." },
            { title: "Logo Shop Links", desc: "Clicking a logo filters shop products for that brand." }
        ]
    },
];

const DYNAMIC_DEFAULTS = {
    products: { name: "Products", technical_name: "products", model: "product.template", template_id: "theme_alan.s_product_slider", default_stemplate_id: "theme_alan.s_product_slider", default_gtemplate_id: "theme_alan.s_product_grid", grid_style: "as-grid-1", slider_style: "as-slider-1", active_view: "slider", record_limit: 5, loop: true, auto_slider: true, slider_time: 6, pagination: "none", default_col_mob: 2, default_col_desk: "5", allow_add_to_cart: true, allow_quick_view: true, allow_wishlist: true, allow_label: true, allow_color_variant: true, allow_product_discount: true, user_visibility: "all" },
    highlighted_product_grid: { name: "Highlighted Products", technical_name: "highlighted_product_grid", model: "product.template", template_id: "theme_alan.s_product_highlighted_grid", default_gtemplate_id: "theme_alan.s_product_highlighted_grid", grid_layout_style: "s_product_highlighted_grid", grid_style: "as-grid-1", active_view: "grid", record_limit: 7, allow_add_to_cart: true, allow_quick_view: true, allow_wishlist: true, allow_label: true, allow_color_variant: true, allow_product_discount: true, user_visibility: "all" },
    categories: { name: "Categories", technical_name: "categories", model: "product.public.category", template_id: "theme_alan.s_category_slider", default_stemplate_id: "theme_alan.s_category_slider", default_gtemplate_id: "theme_alan.s_category_grid", grid_style: "as-grid-1", slider_style: "as-slider-6", active_view: "slider", record_limit: 5, loop: true, auto_slider: true, slider_time: 6, pagination: "none", default_col_mob: 2, default_col_desk: "5", allow_link: true, user_visibility: "all" },
    brand_collection_showcase: { name: "Brand Collection Gallery", technical_name: "brand_collection_showcase", model: "as.product.brand", template_id: "theme_alan.s_brand_collection_showcase_slider", default_stemplate_id: "theme_alan.s_brand_collection_showcase_slider", default_gtemplate_id: "theme_alan.s_brand_collection_showcase_grid", grid_style: "as-grid-1", slider_style: "as-slider-1", slider_layout_style: "s_brand_collection_showcase_slider", grid_layout_style: "s_brand_collection_showcase_grid", active_view: "slider", record_limit: 10, loop: true, auto_slider: true, slider_time: 6, pagination: "progress_bar", default_col_mob: 2, default_col_desk: "3", slide_one_item: true, display_all_items: false, allow_add_to_cart: true, allow_quick_view: true, allow_compare: true, allow_wishlist: true, allow_rating: true, allow_label: true, allow_hover_image: true, allow_stock_info: true, allow_offer_time: true, allow_brand_info: true, allow_color_variant: true, allow_product_discount: true, mob_allow_add_to_cart: true, mob_allow_compare: true, mob_allow_wishlist: true, mob_allow_rating: true, mob_allow_label: true, mob_allow_hover_image: true, mob_allow_stock_info: true, mob_allow_offer_time: true, mob_allow_brand_info: true, mob_allow_product_discount: true, user_visibility: "all" },
    product_spotlight: { name: "Product Spotlight", technical_name: "product_spotlight", model: "product.template", template_id: "theme_alan.s_product_spotlight", default_gtemplate_id: "theme_alan.s_product_spotlight", grid_style: "as-grid-1", active_view: "grid", record_limit: 5, tab_names: [{ key: "best_seller", label: "Best Seller", enabled: true }, { key: "new_arrival", label: "New Arrival", enabled: true }, { key: "on_sale", label: "On Sale", enabled: true }], allow_rating: true, allow_brand_info: true, allow_product_discount: true, user_visibility: "all" },
    blogs: { name: "Blogs", technical_name: "blogs", model: "blog.post", template_id: "theme_alan.s_blog_slider", default_stemplate_id: "theme_alan.s_blog_slider", default_gtemplate_id: "theme_alan.s_blog_grid", grid_style: "as-grid-3", slider_style: "as-slider-3", style: "as-blog-1", slider_layout_style: "s_blog_slider", grid_layout_style: "s_blog_grid", active_view: "slider", record_limit: 5, loop: true, auto_slider: true, slider_time: 6, pagination: "none", default_col_mob: 2, default_col_desk: "3", slide_one_item: true, display_all_items: false, user_visibility: "all" },
    brands: { name: "Brands", technical_name: "brands", model: "as.product.brand", template_id: "theme_alan.s_brand_slider", default_stemplate_id: "theme_alan.s_brand_slider", default_gtemplate_id: "theme_alan.s_brand_grid", grid_style: "as-grid-1", slider_style: "as-slider-3", slider_layout_style: "s_brand_slider", grid_layout_style: "s_brand_grid", active_view: "slider", record_limit: 5, loop: true, auto_slider: true, slider_time: 6, pagination: "none", default_col_mob: 2, default_col_desk: "6", slide_one_item: true, display_all_items: false, allow_link: true, user_visibility: "all" },
};

// Staging template order (must match t-call order in XML)
const STAGING_ORDER = [
    "theme_alan.slider_temp18",
    "theme_alan.title_8",
    "theme_alan.feature_temp23",
    "theme_alan.feature_temp25",
    "theme_alan.feature_temp26",
    "theme_alan.feature_temp24",
];

// ─────────────────────────────────────────────────────────────────────────────
// WIZARD COMPONENT
// ─────────────────────────────────────────────────────────────────────────────
export class HomePageDemoWizard extends Component {
    static template = "theme_alan.home_page_demo_wizard";
    static components = { Dialog };
    static props = {
        close: Function,
        snippetEl: { type: Object, optional: true },
    };

    get currentHost() {
        return window.location.host;
    }

    setup() {
        this.steps = STEPS;
        this.stagingRef = useRef("hpdStaging");
        this._selectSearch = null;

        // Per-step saved data
        this._data = {};
        for (const s of STEPS) {
            this._data[s.id] = {
                titleText: s.defaultTitle || "Section Title",
                subtitleText: s.defaultSubtitle || "",
                view: s.defaultView || "slider",
                filter: s.defaultFilter || "a_to_z",
                recordLimit: 5,
                selectedRecords: [],
                skipped: false,
            };
        }

        this.state = useState({
            currentStep: 0,
            saving: false,
            error: "",
            titleText: STEPS[0].defaultTitle || "",
            subtitleText: STEPS[0].defaultSubtitle || "",
            view: STEPS[0].defaultView || "slider",
            filter: STEPS[0].defaultFilter || "a_to_z",
            recordLimit: 5,
            selectedRecords: [],
            missingRecords: [],
            skipped: false,
        });

        onMounted(async () => {
            this._initSearch();
            this._scrollActiveStepIntoView();
            try {
                const stats = await rpc('/theme_alan/get_homepage_demo_stats', {});
                const missing = [];
                if (stats.product === 0) missing.push("Products");
                if (stats.category === 0) missing.push("Categories");
                if (stats.blog === 0) missing.push("Blog Posts");
                if (stats.brand === 0) missing.push("Brands");
                this.state.missingRecords = missing;
            } catch (err) {
                console.error("Failed to load homepage demo stats:", err);
            }
        });
        onWillUnmount(() => this._destroySearch());
    }

    _scrollActiveStepIntoView() {
        setTimeout(() => {
            const container = document.querySelector(".as-hpd-mockup-scrollable-content");
            if (!container) return;
            const activeItem = container.querySelector(`#preview_step_${this.state.currentStep}`);
            if (activeItem) {
                activeItem.scrollIntoView({ behavior: 'smooth', block: 'center' });
            }
        }, 100);
    }

    get step() { return this.steps[this.state.currentStep]; }
    get isLast() { return this.state.currentStep === this.steps.length - 1; }
    get progress() { return Math.round(((this.state.currentStep + 1) / this.steps.length) * 100); }

    // ── Record Search ────────────────────────────────────────────────────────
    _initSearch() {
        this._destroySearch();
        const step = this.step;
        const key = step.dynamicKey;
        if (!key || (step.type === "wb_static")) return;
        const model = DYNAMIC_DEFAULTS[key]?.model;
        if (!model) return;
        setTimeout(() => {
            const el = document.getElementById("as_hpd_search");
            if (!el) return;
            this._selectSearch = new AlanSelectSearch(el, model, (rec) => {
                if (!rec || !rec.id) return;
                if (!this.state.selectedRecords.find(r => r.id === rec.id)) {
                    this.state.selectedRecords = [...this.state.selectedRecords,
                    { id: rec.id, name: rec.name || rec.display_name || `#${rec.id}`, image: rec.image || "" }];
                }
            }, { debounceTime: 300, multiple: true });
        }, 200);
    }

    _destroySearch() {
        if (this._selectSearch) { try { this._selectSearch.destroy(); } catch (_) { } this._selectSearch = null; }
    }

    removeRecord(rec) {
        this.state.selectedRecords = this.state.selectedRecords.filter(r => r.id !== rec.id);
    }

    // ── Navigation ────────────────────────────────────────────────────────────
    _save() {
        const d = this._data[this.step.id];
        Object.assign(d, {
            titleText: this.state.titleText,
            subtitleText: this.state.subtitleText,
            view: this.state.view,
            filter: this.state.filter,
            recordLimit: this.state.recordLimit,
            selectedRecords: [...this.state.selectedRecords],
            skipped: this.state.skipped,
        });
    }

    _load() {
        const step = this.step;
        const d = this._data[step.id];
        Object.assign(this.state, {
            titleText: d.titleText || step.defaultTitle || "",
            subtitleText: d.subtitleText !== undefined ? d.subtitleText : (step.defaultSubtitle || ""),
            view: d.view || step.defaultView || "slider",
            filter: d.filter || step.defaultFilter || "a_to_z",
            recordLimit: d.recordLimit || 5,
            selectedRecords: [...(d.selectedRecords || [])],
            skipped: !!d.skipped,
            error: "",
        });
        this._initSearch();
        this._scrollActiveStepIntoView();
    }

    onStepClick(idx) { this._save(); this.state.currentStep = idx; this._load(); }
    onPrev() { if (this.state.currentStep > 0) { this._save(); this.state.currentStep--; this._load(); } }
    onNext() { this._save(); if (this.isLast) { this._generate(); } else { this.state.currentStep++; this._load(); } }
    onSkip() {
        this.state.skipped = !this.state.skipped;
        this._save();
        if (this.state.skipped && !this.isLast) {
            this.state.currentStep++;
            this._load();
        }
    }

    onTitleInput(ev) { this.state.titleText = ev.target.value; }
    onSubtitleInput(ev) { this.state.subtitleText = ev.target.value; }
    setView(view) { this.state.view = view; }
    setFilter(filterId) { this.state.filter = filterId; }
    onRecordLimitInput(ev) { this.state.recordLimit = parseInt(ev.target.value) || 5; }



    // ── Extract staging HTML ──────────────────────────────────────────────────
    _getHtmlByOWL(owlTemplateId) {
        const stagingEl = this.stagingRef.el || document.querySelector(".as-hpd-staging-area");
        if (!stagingEl) return "";
        const container = stagingEl.querySelector(`[data-owl-template="${owlTemplateId}"]`);
        if (!container) return "";
        const ta = container.querySelector("textarea.snippet-textarea");
        if (!ta) return "";

        // 1. If there are actual child elements, serialize them
        if (ta.children && ta.children.length > 0) {
            return Array.from(ta.children).map(child => child.outerHTML).join("").trim();
        }

        // 2. Try value or textContent
        let content = (ta.value || ta.textContent || "").trim();
        if (content.includes("<section") || content.includes("<div")) {
            return content;
        }

        // 3. Try innerHTML and unescape if it contains escaped HTML entities
        let inner = (ta.innerHTML || "").trim();
        if (inner.includes("&lt;")) {
            const txt = document.createElement("textarea");
            txt.innerHTML = inner;
            return txt.value.trim();
        }
        return inner;
    }

    // ── Build dynamic placeholder ─────────────────────────────────────────────
    _dynHtml(step, d) {
        const key = step.dynamicKey;
        const cfg = { ...DYNAMIC_DEFAULTS[key] };
        cfg.active_view = d.view || cfg.active_view;
        cfg.record_limit = d.recordLimit || cfg.record_limit;
        if (d.filter) cfg.active_quick_selction = d.filter;
        cfg.template_id = d.view === "grid"
            ? (cfg.default_gtemplate_id || cfg.template_id)
            : (cfg.default_stemplate_id || cfg.template_id);
        const ids = JSON.stringify(d.selectedRecords.map(r => r.id));
        const de = JSON.stringify(cfg).replace(/"/g, "&quot;");
        return `<section class="as-snippet-builder" data-as-snippet="as_dynamic_snippets">
  <div class="container">
    <div class="as-snippet-drop-container"
         data-snippet-name="${key}"
         data-record-ids="${ids.replace(/"/g, "&quot;")}"
         data-modal="${cfg.model}"
         data-design-edit="${de}">
      <div class="alan-snippet-placeholder d-flex flex-column align-items-center justify-content-center py-5 text-center">
        <img src="/theme_alan/static/src/img/sb-empty-image.svg" alt="" style="max-width:80px;opacity:.5;"/>
        <h3 class="text-muted mt-3">${cfg.name}</h3>
      </div>
    </div>
  </div>
</section>`;
    }

    // ── Generate page ─────────────────────────────────────────────────────────
    async _generate() {
        this.state.saving = true;
        this.state.error = "";
        try {
            const target = this.props.snippetEl;
            if (!target) throw new Error("Target element not found.");
            const parent = target.parentNode;
            const uniqBase = Date.now();

            for (let i = 0; i < this.steps.length; i++) {
                const step = this.steps[i];
                const d = this._data[step.id];

                if (d.skipped) {
                    continue;
                }

                if (step.type === "wb_static") {
                    const raw = this._getHtmlByOWL(step.templateOWL);
                    if (raw) {
                        const uid = `${uniqBase}_${i}`;
                        let processed = raw
                            .replace(/\{\{uniq\}\}/g, uid)
                            .replace(/t-attf-id="[^"]*"/g, `id="${uid}"`)
                            .replace(/t-attf-href="[^"]*"/g, `href="#${uid}"`)
                            .replace(/t-attf-data-bs-target="[^"]*"/g, `data-bs-target="#${uid}"`);
                        const tmp = document.createElement("div");
                        tmp.innerHTML = processed;
                        const sec = tmp.querySelector("section");
                        if (sec) parent.insertBefore(sec, target);
                    }
                } else if (step.type === "composite") {
                    // Insert Title
                    const titleRaw = this._getHtmlByOWL(step.titleOWL);
                    if (titleRaw) {
                        const tmp = document.createElement("div");
                        tmp.innerHTML = titleRaw;
                        const sec = tmp.querySelector("section");
                        if (sec) {
                            const h = sec.querySelector("h1,h2,h3,h4,h5,h6");
                            if (h && d.titleText) h.textContent = d.titleText;
                            const sub = sec.querySelector("p, .subtitle, [data-subtitle]");
                            if (sub && d.subtitleText !== undefined) sub.textContent = d.subtitleText;
                            parent.insertBefore(sec, target);
                        }
                    }
                    // Insert dynamic
                    const tmp2 = document.createElement("div");
                    tmp2.innerHTML = this._dynHtml(step, d);
                    const sec2 = tmp2.querySelector("section");
                    if (sec2) parent.insertBefore(sec2, target);
                } else {
                    const tmp = document.createElement("div");
                    tmp.innerHTML = this._dynHtml(step, d);
                    const sec = tmp.querySelector("section");
                    if (sec) parent.insertBefore(sec, target);
                }
            }

            target.remove();
            this.props.close();
        } catch (err) {
            console.error("[HomePageDemo]", err);
            this.state.error = err.message || "Page generation failed.";
        } finally {
            this.state.saving = false;
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// BUILDER OPTION PLUGIN  (same pattern as website_builder_option.js)
// ─────────────────────────────────────────────────────────────────────────────
class HomePageDemoOptionPlugin extends Plugin {
    static id = "homePageDemoOptionPlugin";
    static dependencies = ["builderActions"];
    resources = {
        builder_options: [
            withSequence(CONTAINER_WIDTH, {
                template: "theme_alan.HomePageDemoOption",
                selector: ".as-home-page-demo",
            }),
        ],
        builder_actions: {
            SetOpenHomePageDemo,
        },
    };
}

export class SetOpenHomePageDemo extends BuilderAction {
    static id = "setOpenHomePageDemo";
    async apply({ editingElement }) {
        this.services.dialog.add(HomePageDemoWizard, {
            snippetEl: editingElement,
        });
    }
}

registry.category("website-plugins").add(HomePageDemoOptionPlugin.id, HomePageDemoOptionPlugin);
