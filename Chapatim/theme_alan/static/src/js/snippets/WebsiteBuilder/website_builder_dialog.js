import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";
import { Component, onMounted, useRef, useState } from "@odoo/owl";

// ─── WebsiteBuilder dialog component for snippet selection ─────────────────────────────────
export class WebsiteBuilder extends Component {
    static template = "theme_alan.website_builder";
    static components = { Dialog };

    static props = {
        snippet: { type: Object, optional: true },
        snippetEl: { type: Object, optional: true },
    };

    setup() {
        this.snippetBuilderTab = useRef("snippetBuilderTab");
        this.state = useState({
            activeTab: "e_slider",
        });

        // Pre-select snippet if reopening with existing snippet
        onMounted(() => {
            this._preselectActiveSnippet();
        });
    }

    // Pre-select the active snippet based on data attributes
    _preselectActiveSnippet() {
        const snippetEl = this.props.snippetEl;
        if (!snippetEl) return;

        // Check for snippet type and ID in data attributes
        const snippetType = snippetEl.dataset.snippetType;
        const snippetId = snippetEl.dataset.snippetId;

        if (snippetType && snippetId) {
            // Switch to the appropriate tab
            this.state.activeTab = snippetType;

            // Wait for DOM to render the tab content, then select the radio
            setTimeout(() => {
                const radioInput = document.getElementById(snippetId);
                if (radioInput) {
                    radioInput.checked = true;
                }
            }, 100);
        }
    }

    // Switch active tab
    activeTab(target) {
        this.state.activeTab = target;
    }

    // Confirm selection and inject snippet
    _confirm() {
        const uniqId = `myCarousel_${Date.now()}_${Math.floor(Math.random() * 1000)}`;

        const checked = document.querySelector("input[name='radio-snippet']:checked");
        if (!checked) return console.warn("No snippet selected");

        const snippetBox = checked.closest(".snippet-as");
        const snippetSection = snippetBox?.querySelector("section");
        if (!snippetSection) return console.warn("No snippet section found");

        const snippetClone = snippetSection.cloneNode(true);

        // Add data attributes for snippet identification (for pre-selection on reopen)
        const snippetId = checked.id;  // Use id instead of value
        snippetClone.dataset.snippetType = this.state.activeTab;
        snippetClone.dataset.snippetId = snippetId;

        snippetClone.querySelectorAll("[id], [href], [data-bs-target]").forEach((el) => {
            if (el.hasAttribute("id")) {
                el.setAttribute("id", uniqId);
            }
            if (el.hasAttribute("href") && el.hasAttribute("data-bs-slide")) {
                el.setAttribute("href", `#${uniqId}`);
            }
            if (el.hasAttribute("data-bs-target")) {
                el.setAttribute("data-bs-target", `#${uniqId}`);
            }
        });

        const target = this.props.snippetEl;
        target.replaceWith(snippetClone);

        if (typeof this.props.close === "function") {
            this.props.close();
        }
    }
}
