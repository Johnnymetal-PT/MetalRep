import { rpc } from "@web/core/network/rpc";
import { registry } from "@web/core/registry";
import { _t } from '@web/core/l10n/translation';
import { Interaction } from "@web/public/interaction";

// ─── AI Product Recommanded ─────────────────────────────────────────────────
export class AIProductRecommandation extends Interaction {
    static selector = '.product_recommanded_ai, .as_recommanded_model';

    setup() {
        this._loaded = false;
        this._observer = null;
        this._observer = new IntersectionObserver(
            (entries) => {
                for (const entry of entries) {
                    if (entry.isIntersecting && !this._loaded) {
                        this._loaded = true;
                        this._observer.disconnect();
                        this._observer = null;
                        this.get_recommanded_product();
                    }
                }
            },
            { threshold: 0.1 }
        );
        this._observer.observe(this.el);
    }

    destroy() {
        if (this._observer) {
            this._observer.disconnect();
            this._observer = null;
        }
    }

    async get_recommanded_product() {
        const productEl = this.el.classList.contains("product_recommanded_ai")
            ? this.el
            : document.querySelector(".product_recommanded_ai");
        const product = productEl?.getAttribute("data-product-tmpl-id") || 0;
        const url = `/fetch_ai_recommanded_product/${product}`;
        try {
            const data = await rpc(url, {});
            const offcanvas = document.querySelector(".offcanvas_recommanded_product");
            const container = document.querySelector(".product_recommanded_container");
            if (offcanvas) offcanvas.innerHTML = data.shop_template || "";
            if (container) {
                container.innerHTML = data.product_template || "";
            }
            new Swiper(".as-ai-recommanded-swiper", {
                slidesPerView: 1.75,
                spaceBetween: 10,
                navigation: {
                    nextEl: ".swiper-button-alt-next",
                    prevEl: ".swiper-button-alt-prev",
                },
                breakpoints: {
                    640: { slidesPerView: 2, spaceBetween: 24 },
                    768: { slidesPerView: 3, spaceBetween: 24 },
                    1024: { slidesPerView: 4, spaceBetween: 24 },
                },
            });
        } catch (error) {
            console.error("Error fetching AI recommended products:", error);
        }
    }
}
registry.category('public.interactions').add('theme_alan.ai_product_recommandation', AIProductRecommandation);
