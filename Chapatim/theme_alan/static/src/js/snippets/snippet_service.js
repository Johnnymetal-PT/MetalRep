
import { patch } from "@web/core/utils/patch";
import { SnippetModel } from "@html_builder/snippets/snippet_service";

// ─── Add Category for Alan snippets block ────────────────────────────
patch(SnippetModel.prototype, {
    get alanSnippetContents() {
        return this.snippetsByCategory.alan_snippets_block;
    }
})
