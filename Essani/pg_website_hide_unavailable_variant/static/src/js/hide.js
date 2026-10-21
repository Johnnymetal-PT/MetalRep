/** @odoo-module **/

// Patch do configurador de variantes para esconder opcoes que geram variantes marcadas hide_on_website.

import { rpc } from "@web/core/network/rpc";
import { patch } from "@web/core/utils/patch";
import { WebsiteSale } from "@website_sale/interactions/website_sale";

function toInt(value) {
    const parsed = parseInt(value, 10);
    return Number.isNaN(parsed) ? null : parsed;
}

const PG_HISTORY_LIMIT = 50;

function statesEqual(a, b) {
    if (!a || !b || a.length !== b.length) return false;
    for (let i = 0; i < a.length; i++) {
        if (a[i] !== b[i]) return false;
    }
    return true;
}

patch(WebsiteSale.prototype, {
    async start() {
        const result = await super.start(...arguments);
        await this._pgLoadHiddenVariantData();
        this._pgApplyHiddenVariants();
        this._pgInitializeHistory();
        this._pgBindHistoryButtons();
        this._pgUpdateHistoryButtons();
        return result;
    },

    onChangeVariant(ev) {
        const product = ev.currentTarget.closest(".js_product");
        if (product && !this._pgIsProgrammaticChange && this._pgLastSettledState) {
            this._pgPushHistory(this._pgLastSettledState);
        }
        const result = super.onChangeVariant(...arguments);
        this._pgScheduleHiddenVariants(product);
        this._pgScheduleHistoryButtonsUpdate();
        return result;
    },

    _disableInput(parent, attributeValueId, excludedBy, attributeNames, productName) {
        super._disableInput(...arguments);
        const input = parent.querySelector(
            `option[value="${attributeValueId}"], input[value="${attributeValueId}"]`
        );
        if (!input) {
            return;
        }
        if (input.tagName === "OPTION") {
            input.hidden = true;
            return;
        }

        const container = input.closest(".o_variant_pills, .js_attribute_value, li");
        if (container) {
            container.style.display = "none";
            return;
        }

        input.closest("label")?.style?.setProperty("display", "none");
    },

    async _pgLoadHiddenVariantData(parent = null) {
        const product = this._pgGetProductContainer(parent);
        const productTemplateId = toInt(
            product?.querySelector('input[name="product_template_id"]')?.value
        );
        if (!productTemplateId) {
            this._pgHiddenVariantData = null;
            this._pgHiddenVariantTemplateId = null;
            return null;
        }
        if (
            this._pgHiddenVariantData
            && this._pgHiddenVariantTemplateId === productTemplateId
        ) {
            return this._pgHiddenVariantData;
        }
        this._pgHiddenVariantData = await this.waitFor(rpc("/get_product_variant_data_website", {
            product_tmpl_id: productTemplateId,
        }));
        this._pgHiddenVariantTemplateId = productTemplateId;
        return this._pgHiddenVariantData;
    },

    _pgScheduleHiddenVariants(parent = null) {
        clearTimeout(this._pgHiddenVariantsTimeout);
        this._pgHiddenVariantsTimeout = setTimeout(async () => {
            await this._pgLoadHiddenVariantData(parent);
            this._pgApplyHiddenVariants(parent);
        }, 0);
    },

    _pgApplyHiddenVariants(parent = null) {
        const product = this._pgGetProductContainer(parent);
        const variantData = this._pgHiddenVariantData;
        if (!product || !variantData || !variantData.value_to_show_tuple?.length) {
            return;
        }

        const groups = this._pgGetVariantGroups(product);
        const allVisibleValueIds = new Set(
            Object.keys(variantData.value_to_show || {}).map((valueId) => toInt(valueId))
        );

        // Hide values that never belong to any valid combination.
        for (const group of groups) {
            const attrIndex = this._pgGetAttributeIndex(group, variantData);
            if (attrIndex < 0) {
                continue;
            }
            for (const item of this._pgGetVariantItems(group)) {
                const valueId = this._pgGetItemValueId(item);
                if (valueId === null) {
                    continue;
                }
                this._pgSetItemVisible(item, allVisibleValueIds.has(valueId));
            }
        }

        // Progressively hide invalid values for following attributes based on current selection.
        const selectedPrefix = [];
        let changedControl = null;
        for (const group of groups) {
            const attrIndex = this._pgGetAttributeIndex(group, variantData);
            const allowedValueIds = new Set(
                selectedPrefix.length
                    ? variantData.value_to_show_tuple
                        .filter((combination) => selectedPrefix.every((valueId) => combination.includes(valueId)))
                        .flat()
                    : allVisibleValueIds
            );

            if (attrIndex >= 0) {
                for (const item of this._pgGetVariantItems(group)) {
                    const valueId = this._pgGetItemValueId(item);
                    if (valueId === null) {
                        continue;
                    }
                    this._pgSetItemVisible(item, allowedValueIds.has(valueId));
                }
            }

            changedControl = changedControl || this._pgEnsureValidSelection(group);
            const selectedValueId = this._pgGetSelectedValueId(group);
            if (selectedValueId !== null) {
                selectedPrefix.push(selectedValueId);
            }
        }

        this._pgSyncPills(product);

        if (changedControl) {
            this._pgIsProgrammaticChange = true;
            try {
                changedControl.dispatchEvent(new Event("change", { bubbles: true }));
            } finally {
                this._pgIsProgrammaticChange = false;
            }
        } else {
            this._pgLastSettledState = this._pgCaptureState(product);
            this._pgScheduleHistoryButtonsUpdate();
        }
    },

    _pgGetProductContainer(parent = null) {
        return parent || this.el.querySelector(".js_main_product") || this.el.querySelector(".js_product");
    },

    _pgGetVariantGroups(product) {
        return Array.from(product.querySelectorAll('.js_add_cart_variants > [name="variant_attribute"]'));
    },

    _pgGetAttributeIndex(group, variantData) {
        const attributeId = toInt(group.dataset.attributeId || group.getAttribute("data-attribute_id"));
        return variantData.attribute_ids.indexOf(attributeId);
    },

    _pgGetVariantItems(group) {
        const select = group.querySelector("select.js_variant_change");
        if (select) {
            return Array.from(select.options).filter((option) => option.value !== "0");
        }
        const list = group.querySelector("ul");
        return list ? Array.from(list.children) : [];
    },

    _pgGetItemValueId(item) {
        if (item.tagName === "OPTION") {
            return toInt(item.value || item.dataset.valueId || item.getAttribute("data-value_id"));
        }
        const input = item.querySelector("input.js_variant_change");
        return toInt(
            input?.value
            || input?.dataset.valueId
            || input?.getAttribute("data-value_id")
            || item.dataset.valueId
            || item.getAttribute("data-value_id")
        );
    },

    _pgSetItemVisible(item, visible) {
        if (item.tagName === "OPTION") {
            item.hidden = !visible;
            return;
        }
        item.style.display = visible ? "" : "none";
    },

    _pgGetSelectedValueId(group) {
        const checkedInput = group.querySelector("input.js_variant_change:checked");
        if (checkedInput) {
            return toInt(checkedInput.value);
        }
        const select = group.querySelector("select.js_variant_change");
        if (select && select.value !== "0") {
            return toInt(select.value);
        }
        return null;
    },

    _pgEnsureValidSelection(group) {
        const visibleItems = this._pgGetVariantItems(group).filter((item) => {
            if (item.tagName === "OPTION") {
                return !item.hidden;
            }
            return item.style.display !== "none";
        });
        if (!visibleItems.length) {
            return null;
        }

        const select = group.querySelector("select.js_variant_change");
        if (select) {
            const currentOption = select.options[select.selectedIndex];
            if (currentOption && !currentOption.hidden && currentOption.value !== "0") {
                return null;
            }
            const firstVisibleOption = visibleItems[0];
            if (firstVisibleOption && select.value !== firstVisibleOption.value) {
                firstVisibleOption.selected = true;
                return select;
            }
            return null;
        }

        const checkedInput = group.querySelector("input.js_variant_change:checked");
        if (checkedInput) {
            const item = checkedInput.closest("li");
            if (item && item.style.display !== "none") {
                return null;
            }
        }
        const firstVisibleInput = visibleItems[0]?.querySelector("input.js_variant_change");
        if (firstVisibleInput && !firstVisibleInput.checked) {
            firstVisibleInput.checked = true;
            return firstVisibleInput;
        }
        return null;
    },

    _pgSyncPills(product) {
        product.querySelectorAll(".o_variant_pills").forEach((pill) => {
            const input = pill.querySelector("input.js_variant_change");
            const activeClasses = [
                "active",
                "border-primary",
                "text-primary-emphasis",
                "bg-primary-subtle",
            ];
            pill.classList.toggle("active", !!input?.checked);
            pill.classList.toggle("border-primary", !!input?.checked);
            pill.classList.toggle("text-primary-emphasis", !!input?.checked);
            pill.classList.toggle("bg-primary-subtle", !!input?.checked);
            if (!input?.checked) {
                for (const className of activeClasses) {
                    pill.classList.remove(className);
                }
            }
        });
    },

    _pgInitializeHistory() {
        this._pgHistoryStack = [];
        const product = this._pgGetProductContainer();
        this._pgInitialState = product ? this._pgCaptureState(product) : null;
        this._pgLastSettledState = this._pgInitialState;
    },

    _pgBindHistoryButtons() {
        const product = this._pgGetProductContainer();
        if (!product) return;
        const undoBtn = product.querySelector(".pg_variant_undo");
        const resetBtn = product.querySelector(".pg_variant_reset");
        if (undoBtn) {
            undoBtn.addEventListener("click", (ev) => {
                ev.preventDefault();
                this._pgUndo();
            });
        }
        if (resetBtn) {
            resetBtn.addEventListener("click", (ev) => {
                ev.preventDefault();
                this._pgReset();
            });
        }
    },

    _pgPushHistory(state) {
        if (!state) return;
        if (!this._pgHistoryStack) this._pgHistoryStack = [];
        const last = this._pgHistoryStack[this._pgHistoryStack.length - 1];
        if (statesEqual(last, state)) return;
        this._pgHistoryStack.push(state.slice());
        if (this._pgHistoryStack.length > PG_HISTORY_LIMIT) {
            this._pgHistoryStack.shift();
        }
    },

    _pgUndo() {
        if (!this._pgHistoryStack || !this._pgHistoryStack.length) return;
        const product = this._pgGetProductContainer();
        if (!product) return;
        const target = this._pgHistoryStack.pop();
        this._pgRestoreState(product, target);
    },

    _pgReset() {
        const product = this._pgGetProductContainer();
        if (!product || !this._pgInitialState) return;
        this._pgHistoryStack = [];
        this._pgRestoreState(product, this._pgInitialState);
    },

    _pgCaptureState(product) {
        if (!product) return [];
        return this._pgGetVariantGroups(product).map(
            (group) => this._pgGetSelectedValueId(group)
        );
    },

    _pgRestoreState(product, state) {
        if (!product || !state) return;
        const groups = this._pgGetVariantGroups(product);
        let changedControl = null;
        this._pgIsProgrammaticChange = true;
        try {
            groups.forEach((group, index) => {
                const valueId = state[index];
                if (valueId === null || valueId === undefined) return;
                const select = group.querySelector("select.js_variant_change");
                if (select) {
                    const option = Array.from(select.options).find(
                        (opt) => toInt(opt.value) === valueId
                    );
                    if (option) {
                        option.hidden = false;
                        if (toInt(select.value) !== valueId) {
                            select.value = String(valueId);
                            changedControl = changedControl || select;
                        }
                    }
                    return;
                }
                const input = group.querySelector(
                    `input.js_variant_change[value="${valueId}"]`
                );
                if (input) {
                    const container = input.closest(".o_variant_pills, .js_attribute_value, li, label");
                    if (container && container.style) container.style.display = "";
                    if (!input.checked) {
                        input.checked = true;
                        changedControl = changedControl || input;
                    }
                }
            });
            if (!changedControl) {
                changedControl = groups[0]?.querySelector("select.js_variant_change, input.js_variant_change:checked, input.js_variant_change");
            }
            if (changedControl) {
                changedControl.dispatchEvent(new Event("change", { bubbles: true }));
            }
        } finally {
            this._pgIsProgrammaticChange = false;
        }
        this._pgLastSettledState = state.slice();
        this._pgScheduleHistoryButtonsUpdate();
    },

    _pgScheduleHistoryButtonsUpdate() {
        clearTimeout(this._pgHistoryButtonsTimeout);
        this._pgHistoryButtonsTimeout = setTimeout(
            () => this._pgUpdateHistoryButtons(),
            0,
        );
    },

    _pgUpdateHistoryButtons() {
        const product = this._pgGetProductContainer();
        if (!product) return;
        const undoBtn = product.querySelector(".pg_variant_undo");
        const resetBtn = product.querySelector(".pg_variant_reset");
        if (!undoBtn && !resetBtn) return;
        const currentState = this._pgCaptureState(product);
        const hasHistory = !!(this._pgHistoryStack && this._pgHistoryStack.length);
        const isInitial = statesEqual(currentState, this._pgInitialState);
        if (undoBtn) {
            undoBtn.classList.toggle("d-none", !hasHistory);
        }
        if (resetBtn) {
            resetBtn.classList.toggle("d-none", isInitial);
        }
    },
});
