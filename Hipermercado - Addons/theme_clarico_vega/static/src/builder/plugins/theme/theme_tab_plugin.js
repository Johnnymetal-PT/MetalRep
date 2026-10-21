import { Plugin } from "@html_editor/plugin";
import { withSequence } from "@html_editor/utils/resource";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { reactive } from "@odoo/owl";
import { BaseOptionComponent } from "@html_builder/core/utils";

export const GRAY_PARAMS = {
    EXTRA_SATURATION: "gray-extra-saturation",
    HUE: "gray-hue",
};

export const OPTION_POSITIONS = {
    GENERAL: 10,
    SHOP: 20,
    PRODUCT: 30,
    CART: 40,
};

export class ThemeTabExtPlugin extends Plugin {
    static id = "themeTabExt";

    grayParams = {};
    grays = reactive({});

    resources = {
        themeext_options: [
            withSequence(
                OPTION_POSITIONS.GENERAL,
                this.getThemeOptionBlock("general-custom", _t("General Settings"),
                /*{
                    template: "theme_clarico_vega.ThemeGeneralOptionExt",
                }*/
                class ThemeGeneralOptionExt extends BaseOptionComponent {
                        static template = "theme_clarico_vega.ThemeGeneralOptionExt";
                }
                )
            ),
            withSequence(
                OPTION_POSITIONS.SHOP,
                this.getThemeOptionBlock("theme-custom", _t("Shop Page"),
                /*{
                    template: "theme_clarico_vega.ThemeShopOptionExt",
                }*/
                class ThemeShopOptionExt extends BaseOptionComponent {
                        static template = "theme_clarico_vega.ThemeShopOptionExt";
                }
                )
            ),
            withSequence(
                OPTION_POSITIONS.PRODUCT,
                this.getThemeOptionBlock("product-custom", _t("Product Page"),
                /*{
                    template: "theme_clarico_vega.ThemeProductOptionExt",
                }*/
                class ThemeProductOptionExt extends BaseOptionComponent {
                        static template = "theme_clarico_vega.ThemeProductOptionExt";
                }
                )
            ),
            withSequence(
                OPTION_POSITIONS.CART,
                this.getThemeOptionBlock("cart-custom", _t("Cart Page"),
                /*{
                    template: "theme_clarico_vega.ThemeCartOptionExt",
                }*/
                class ThemeCartOptionExt extends BaseOptionComponent {
                        static template = "theme_clarico_vega.ThemeCartOptionExt";
                }
                )
            ),
        ],
    };
    getThemeOptionBlock(id, name, options) {
        const el = this.document.createElement("div");
        el.dataset.name = name;
        this.document.body.appendChild(el); // Currently editingElement needs to be isConnected

        options.selector = "*";

        return {
            id: id,
            element: el,
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

registry.category("website-plugins").add(ThemeTabExtPlugin.id, ThemeTabExtPlugin);
