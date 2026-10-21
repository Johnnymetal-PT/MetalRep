import { patch } from "@web/core/utils/patch";
import { HoverableDropdown } from "@website/interactions/dropdown/hoverable_dropdown";

// ─── User DashBoard Dropdown ─────────────────────────────────────────────────
patch(HoverableDropdown.prototype, {
    updateDropdownVisibility(dropdownEl, show) {
        const dropdownToggleEl = dropdownEl.querySelector(".dropdown-toggle");
        if (
            this.isSmall()
            || !dropdownToggleEl
            || dropdownEl.closest(".o_extra_menu_items")
        ) {
            return;
        }
        const dropdown = Dropdown.getOrCreateInstance(dropdownToggleEl);
        const isInsideDashboard = dropdown._parent.closest('.as_user_dashboard') !== null;
        if (!isInsideDashboard) {
            if (show) {
                dropdown.show();
            } else {
                dropdown.hide();
            }
        }
    }
});