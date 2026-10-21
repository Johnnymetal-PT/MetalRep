import { rpc } from "@web/core/network/rpc";
import { Plugin } from "@html_editor/plugin";
import { registry } from "@web/core/registry";
import { _t } from "@web/core/l10n/translation";
import { withSequence } from "@html_editor/utils/resource";
import { BuilderAction } from "@html_builder/core/builder_action";
import { BaseOptionComponent } from "@html_builder/core/utils";

export const OPTION_POSITIONS = {
    AlanGlobal: 90
};

// ─── Alan Configuration ─────────────────────────────────────────────────
export class SetAlanConfigAction extends BuilderAction {
    static id = "setAlanConfig";
    static dependencies = ["builderActions", "customizeWebsite"];

    setup() {
        this.fieldValues = {};
        this.reload = {};
        this.preview = false;
    }

    async prepare({ actionParam }) {
        // Load current configuration from server
        const result = await rpc("/get_alan_configuration", {});
        this.fieldValues = result;

        return this.dependencies.customizeWebsite.loadConfigKey(actionParam);
    }

    getPriority({ params }) {
        const records = [...(params.views || []), ...(params.assets || [])];
        return records.length + (params.fields?.length || 0);
    }

    isApplied({ params }) {
        // Check if field is applied
        const fieldName = params?.fields?.[0];
        let fieldApplied = true;
        if (fieldName) {
            const value = this.fieldValues[fieldName] ?? false;
            fieldApplied = value === true;
        }

        // Check if views/assets are applied
        const records = [...(params.views || []), ...(params.assets || [])];
        const configKeysIsApplied = records.length === 0 || records.every((v) =>
            this.dependencies.customizeWebsite.getConfigKey(v)
        );

        return fieldApplied && configKeysIsApplied;
    }

    async apply(action) {
        return this._toggleConfig(action, true);
    }

    async clean(action) {
        return this._toggleConfig(action, false);
    }

    async _toggleConfig(action, apply) {
        const promises = [];
        // Step 1: Toggle field configuration
        const fieldName = action?.params?.fields?.[0];
        if (fieldName) {
            promises.push(this._toggleField(fieldName, apply));
        }

        // Step 2: Toggle views and assets using default WebsiteConfigAction method
        const websiteConfigAction = this.dependencies.builderActions.getAction("websiteConfig");
        if (action.params?.views) {
            promises.push(websiteConfigAction._toggleTheme(action, "views", apply));
        }
        if (action.params?.assets) {
            promises.push(websiteConfigAction._toggleTheme(action, "assets", apply));
        }

        // Step 3: Handle variables if present
        const updateVars =
            !apply && action.params.varsOnClean
                ? this.dependencies.customizeWebsite.customizeWebsiteVariables(
                    action.params.varsOnClean,
                    "null",
                    apply
                )
                : action.params.vars
                    ? this.dependencies.customizeWebsite.customizeWebsiteVariables(
                        action.params.vars,
                        "null",
                        !apply
                    )
                    : Promise.resolve();

        promises.push(updateVars);
        await Promise.all(promises);
        if (this.dependencies.customizeWebsite.isPluginDestroyed()) {
            return true;
        }
        // Reload bundles to apply changes
        if (this.dependencies.customizeWebsite) {
            await this.dependencies.customizeWebsite.reloadBundles();
        }
    }

    async _toggleField(fieldName, apply) {
        try {
            const payload = {};
            payload[fieldName] = apply;
            const result = await rpc("/get_alan_configuration", payload);
            this.fieldValues[fieldName] = result[fieldName];
            return result;
        } catch (error) {
            console.error('Error toggling field config:', error);
            return false;
        }
    }
}

// ─── Alan Shop Page Filter Option─────────────────────────────────────────────────
class AlanShopPageFilterOptionPlugin extends Plugin {
    static id = "alanShopPageFilterOptionPlugin";

    resources = {
        builder_actions: {
            SetAlanConfigAction,
        },
    };
}

registry.category("website-plugins").add(AlanShopPageFilterOptionPlugin.id, AlanShopPageFilterOptionPlugin);

class AlanShopPageConfig extends BaseOptionComponent {
    static template = "theme_alan.AlanShopPageConfigOptionPlugin";
    static selector = "#products_grid:has(div.o_wsale_products_grid_table_wrapper)";
    static editableOnly = false;
    static reloadTarget = true;
    static title = _t("Alan Config");
}

// ─── Alan Shop Page Config Option─────────────────────────────────────────────────
class AlanShopPageConfigOptionPlugin extends Plugin {
    static id = "alanShopPageConfigOptionPlugin";

    resources = {
        builder_options: [AlanShopPageConfig],
    }
}

registry.category("website-plugins").add(AlanShopPageConfigOptionPlugin.id, AlanShopPageConfigOptionPlugin);

class AlanGlobalThemeTab extends BaseOptionComponent {
    static template = "theme_alan.ThemeAlanGlobalConfig";
    static title = _t("Alan Global Config");
}

// ─── Alan Global Config─────────────────────────────────────────────────
class AlanGlobalThemeTabPlugin extends Plugin {
    static id = "alanGlobalThemeTabPlugin";

    resources = {
        theme_options: [
            withSequence(
                OPTION_POSITIONS.AlanGlobal,
                this.getThemeOptionBlock("theme-alan-global", AlanGlobalThemeTab)
            ),
        ]
    };
    getThemeOptionBlock(id, options) {
        options.selector = "*";

        return {
            id: id,
            element: this.editable,
            hasOverlayOptions: false,
            headerMiddleButton: false,
            isClonable: false,
            isRemovable: false,
            options: [options],
            optionsContainerTopButtons: [],
            snippetModel: {},
        };
    }
}

registry.category("website-plugins").add(AlanGlobalThemeTabPlugin.id, AlanGlobalThemeTabPlugin);
