import { registry } from "@web/core/registry";
import { Interaction } from "@web/public/interaction";
import { AIProductRecommandation } from "./ai_recommanded_product";

// ─── AI Product Recommanded Edit ──────────────────────────────────────────
export class AIProductRecommandationEdit extends Interaction {
    static selector = AIProductRecommandation.selector;

    setup() {
        this._showPlaceholder();
    }

    _showPlaceholder() {
        const container = this.el.querySelector(".product_recommanded_container");
        if (container) {
            container.innerHTML = `
                <div class="alan-snippet-placeholder">
                    <img src="/theme_alan/static/src/img/sb-empty-image.svg"
                        alt="placeholder"
                        class="alan-placeholder-image"/>
                    <h3 class="alan-snippet-title">AI Recommended Products</h3>
                </div>
            `;
        }
    }
}

registry.category("public.interactions.edit").add("theme_alan.AIProductRecommandation", {
    Interaction: AIProductRecommandationEdit,
});