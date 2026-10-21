import { Builder } from "@html_builder/builder";
import { isVisible } from "@html_builder/utils/utils";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { WebsiteBuilder } from "@website/builder/website_builder";
import { ThemeTabExt } from "@theme_clarico_vega/builder/plugins/theme/theme_tab";

patch(WebsiteBuilder.prototype, {
    get builderProps() {
        const main = super.builderProps;
        main.getThemeTabExt = () => this.websiteService.isDesigner && ThemeTabExt;
        return main;
    },
});

patch(Builder, {
    props: {
        ...Builder.props,
        getThemeTabExt: { type: Function, optional: true },
        themeTabDisplayNameExt: { type: String, optional: true },
    },
    defaultProps: {
        ...Builder.defaultProps,
        themeTabDisplayNameExt: _t("Theme Clarico Vega"),
    },
});

patch(Builder.prototype, {
    setup() {
        super.setup();
        this.ThemeTabExt = this.props.getThemeTabExt?.();
        // Add state for themeext options containers
        if (!this.state.optionsContainersExt) {
            this.state.optionsContainersExt = [];
        }
    },
    onTabClickExt(tab, presetId = null) {
        if (this.state.activeTab === tab) {
            // If the tab is already active, do nothing.
            return;
        }
        this.setTab(tab);
        // Deactivate the options when clicking on the "BLOCKS", "THEME", or "THEMEEXT" tabs.
        if (tab === "theme" || tab === "blocks" || tab === "themeext") {
            this.colorPresetToShow = presetId;
            this.activeTargetEl = this.activeTargetEl || this.getActiveTarget();
            this.editor.shared.builderOptions.deactivateContainers();
            // If themeext, set optionsContainersExt from plugin if available
            if (tab === "themeext" && this.ThemeTabExt) {
                // Try to get optionsContainers from the plugin registry
                const plugin = this.editor.plugins?.themeTabExt;
                if (plugin && plugin.resources && plugin.resources.theme_options) {
                    this.state.optionsContainersExt = plugin.resources.theme_options;
                }
            }
        } else if (this.activeTargetEl) {
            if (isVisible(this.activeTargetEl)) {
                // Reactivate the previously active element.
                this.editor.shared.builderOptions.updateContainers(this.activeTargetEl);
            }
            this.activeTargetEl = null;
        }
    },
    setTab(tab) {
        this.state.activeTab = tab;
        // Set the fallback tab on the "THEME" or "THEMEEXT" tab if it was selected.
        if (tab === "theme") {
            this.noSelectionTab = "theme";
        } else if (tab === "themeext") {
            this.noSelectionTab = "themeext";
        } else {
            this.noSelectionTab = "blocks";
        }
    },
});
