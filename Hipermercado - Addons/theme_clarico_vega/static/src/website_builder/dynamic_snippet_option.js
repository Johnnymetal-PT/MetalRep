import { BaseOptionComponent } from "@html_builder/core/utils";
import { useDynamicSnippetOption } from "@website/builder/plugins/options/dynamic_snippet_hook";
import { BuilderAction } from "@html_builder/core/builder_action";

export class DynamicSnippetProductOption extends BaseOptionComponent {
    static template = "theme_clarico_vega.DynamicSnippetProductOption";
    static dependencies = ["dynamicSnippetProductOption"];
    static selector = ".s_dynamic_snippet_products";
    setup() {
        super.setup();
        const { getModelNameFilter } = this.dependencies.dynamicSnippetProductOption;
        this.dynamicOptionParams = useDynamicSnippetOption(getModelNameFilter());
    }
}

export class NumberOfElementsAction extends BuilderAction {
    static id = "numberOfElements";
    isApplied({ editingElement, params }) {
        return editingElement.dataset.numberOfElements === params.mainParam;
    }
    apply({ editingElement, params }) {
        editingElement.dataset.numberOfElements = params.mainParam;
    }
}

export class NumberOfElementsSmallDevicesAction extends BuilderAction {
    static id = "numberOfElementsSmallDevices";
    isApplied({ editingElement, params }) {
        return editingElement.dataset.numberOfElementsSmallDevices === params.mainParam;
    }
    apply({ editingElement, params }) {
        editingElement.dataset.numberOfElementsSmallDevices = params.mainParam;
    }
}

// Helper to normalize Odoo datetime or UNIX timestamp to ISO 8601 or ms
function normalizeDateString(str) {
    if (!str) return str;
    // If it's a 10-digit number, treat as UNIX timestamp (seconds)
    if (/^\d{10}$/.test(str)) {
        return parseInt(str, 10) * 1000;
    }
    // Replace first space with T if present
    return str.replace(' ', 'T');
}

export class SliderVisibilityByDateAction extends BuilderAction {
    static id = "sliderVisibilityByDate";
    isApplied({ editingElement, params }) {
        return false;
    }
    apply({ editingElement, params }) {
        let rawStart = editingElement.getAttribute('data-start-time') || editingElement.dataset.startTime;
        let rawEnd = editingElement.getAttribute('data-end-time') || editingElement.dataset.endTime;
        // Get current time once for both attributes
        let nowIso = new Date().toISOString();
        // If both are missing, set both to current time
        if (!rawStart && !rawEnd) {
            rawStart = nowIso;
            rawEnd = nowIso;
            editingElement.setAttribute('data-start-time', nowIso);
            editingElement.setAttribute('data-end-time', nowIso);
        } else if (!rawStart) {
            rawStart = rawEnd || nowIso;
            editingElement.setAttribute('data-start-time', rawStart);
        } else if (!rawEnd) {
            rawEnd = rawStart || nowIso;
            editingElement.setAttribute('data-end-time', rawEnd);
        }
        const startNorm = normalizeDateString(rawStart);
        const endNorm = normalizeDateString(rawEnd);
        let startDate = startNorm ? new Date(startNorm) : null;
        let endDate = endNorm ? new Date(endNorm) : null;
        const now = new Date();
        let visible = true;
        if (startDate && now < startDate) visible = false;
        if (endDate && now > endDate) visible = false;
        editingElement.classList.add('d-none');
        if (visible) {
            editingElement.classList.remove('d-none');
        }
    }
}
