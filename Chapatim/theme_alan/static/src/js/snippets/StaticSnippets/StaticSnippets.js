import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { renderToElement } from "@web/core/utils/render";

/**
 * StaticSnippets Component
 *
 * This component displays a dialog with a list of static templates (snippets)
 * that the user can select and apply to the snippet container.
 *
 * Features:
 *  - Highlights the currently selected template when the dialog opens.
 *  - Allows selecting a template from the list.
 *  - Saves the selected template into the snippet container with all necessary metadata.
 */

// ─── StaticSnippets Component ─────────────────────────────────
export class StaticSnippets extends Component {
    static components = { Dialog };
    static template = 'theme_alan.static_snippets';
    setup() {
        this.state = useState({
            selected_templ_id: false,
        });
        const selected_template_id = this.props.snippet_builder.template_id;
        if (selected_template_id) {
            this.state.selected_templ_id = selected_template_id;
        }
    }

    select_template(ev) {
        const templ_id = ev.currentTarget.dataset.temp;
        this.state.selected_templ_id = templ_id;
    }

    save() {
        if (!this.state.selected_templ_id) {
            console.warn("StaticSnippets: No template selected");
            return;
        }

        const selected_snippet = 'theme_alan.' + this.state.selected_templ_id;
        this.props.snippet_builder.template_id = this.state.selected_templ_id;
        const selected_template = renderToElement(selected_snippet);
        const firstDiv = this.props.target.querySelector("div");
        if (firstDiv) {
            firstDiv.innerHTML = '';
            firstDiv.appendChild(selected_template);
        }

        const target = this.props.target;
        target.dataset.snippetName = this.props.snippet_builder.technical_name;
        target.dataset.size = 0;
        target.dataset.posId = 0;
        target.dataset.rowId = 0;
        target.dataset.activeId = 'as_slider';
        target.dataset.selectedTemplId = this.props.snippet_builder.template_id;
        target.dataset.defaultContent = true;
        target.dataset.designEdit = JSON.stringify(this.props.snippet_builder);
        this.props.close();
    }
}
