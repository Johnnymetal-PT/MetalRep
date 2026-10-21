import { registry } from "@web/core/registry";
import { Interaction } from "@web/public/interaction";
import { DynamicSnippets, AlanMegaMenu } from "./website_snippets";

// ─── Dynamic Snippet Edit ─────────────────────────────────────────────────
export class DynamicSnippetsEdit extends Interaction {
    static selector = DynamicSnippets.selector;

    async willStart() {
        const snippetDropContainer = this.el.querySelector('.as-snippet-drop-container');
        if (snippetDropContainer && snippetDropContainer.dataset) {
            if (snippetDropContainer.dataset.snippetName === "static_snippets") {
                return;
            }
            else {
                const snippetPlaceholder = JSON.parse(snippetDropContainer.dataset.designEdit).name;
                snippetDropContainer.innerHTML = `
                    <div class="alan-snippet-placeholder">
                        <img src="/theme_alan/static/src/img/sb-empty-image.svg"
                            alt="placeholder"
                            class="alan-placeholder-image"/>
                        <h3 class="alan-snippet-title">${snippetPlaceholder}</h3>
                    </div>
                `;
                snippetDropContainer.style.display = '';
            }
        }
    }
}

registry.category("public.interactions.edit").add("theme_alan.DynamicSnippets", {
    Interaction: DynamicSnippetsEdit,
});