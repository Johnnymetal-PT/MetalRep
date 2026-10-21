/** @odoo-module **/

import { AutoComplete } from "@web/core/autocomplete/autocomplete";
import { ConfirmationDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { Dialog } from "@web/core/dialog/dialog";
import { rpc } from "@web/core/network/rpc";
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { OdooEditor } from "@web_editor/js/editor/odoo-editor/src/OdooEditor";
import { editorCommands } from "@web_editor/js/editor/odoo-editor/src/commands/commands";
import {
    FONT_SIZE_CLASSES,
    closestElement,
    closestPath,
    findNode,
    formatSelection,
    formatsSpecs,
    getFontSizeDisplayValue,
    isBlock,
} from "@web_editor/js/editor/odoo-editor/src/utils/utils";
import { Component, useEffect, useRef, useState } from "@odoo/owl";

const DYNAMIC_FIELD_SELECTOR = [
    "[data-oe-model]",
    ":not([data-oe-field='arch'])",
    ":not([data-oe-type='html'])",
    ":not([data-oe-translation-source-sha])",
].join("");

const BLOCKED_DYNAMIC_INPUT_PREFIXES = ["insert", "delete"];
const FONT_CUSTOMIZATION_SCSS_PATH = "/website/static/src/scss/options/user_values.scss";
const LOCAL_TYPOGRAPHY_MENU_GAP = 8;
const LOCAL_TYPOGRAPHY_VIEWPORT_MARGIN = 8;

const TYPOGRAPHY_STYLE_CONFIG = {
    fontFamily: {
        cssProperty: "font-family",
        propName: "family",
    },
    letterSpacing: {
        cssProperty: "letter-spacing",
        propName: "spacing",
    },
    lineHeight: {
        cssProperty: "line-height",
        propName: "height",
    },
};

class HmdGoogleFontAutoComplete extends AutoComplete {
    setup() {
        super.setup();
        this.inputRef = useRef("input");
        this.sourcesListRef = useRef("sourcesList");
        useEffect((el) => {
            el?.setAttribute("id", "google_font");
        }, () => [this.inputRef.el]);
    }

    get dropdownOptions() {
        return {
            ...super.dropdownOptions,
            position: "bottom-fit",
        };
    }

    onInput(ev) {
        super.onInput(ev);
        if (this.sourcesListRef.el) {
            this.sourcesListRef.el.scrollTop = 0;
        }
    }
}

function removeStyle(node, styleName, item) {
    const currentValue = node.style.getPropertyValue(styleName);
    if (item) {
        const newStyle = currentValue
            .split(" ")
            .filter((value) => value !== item)
            .join(" ");
        if (newStyle) {
            node.style.setProperty(styleName, newStyle);
        } else {
            node.style.removeProperty(styleName);
        }
    } else {
        node.style.removeProperty(styleName);
    }
    if (node.getAttribute("style") === "") {
        node.removeAttribute("style");
    }
}

function unquote(value) {
    if (!value) {
        return "";
    }
    return value.replace(/^['"]|['"]$/g, "");
}

function normalizeFontToken(value) {
    return unquote((value || "").split(",")[0].trim()).toLowerCase();
}

function trimNumericValue(value, digits = 2) {
    if (!Number.isFinite(value)) {
        return "";
    }
    return Number.parseFloat(value.toFixed(digits)).toString();
}

function getSelectionNode(editor, fallbackNode) {
    const selection = editor.document.getSelection();
    return fallbackNode || selection?.anchorNode || selection?.focusNode || null;
}

function getWebsiteWysiwyg(editor) {
    const iframeWindow = editor.document.defaultView;
    const iframe$ = iframeWindow?.$ || window.$;
    if (!iframe$) {
        return null;
    }
    const wrap = editor.document.getElementById("wrapwrap");
    if (!wrap) {
        return null;
    }
    return iframe$(wrap).data("wysiwyg") || null;
}

function parseFontListProperty(value, { unquoteEntries = false } = {}) {
    if (!value || value === "null") {
        return [];
    }
    const entries = value
        .slice(1, -1)
        .split(/\s*,\s*/g)
        .filter(Boolean);
    return unquoteEntries ? entries.map((entry) => entry.slice(1, -1)) : entries;
}

function getFontCustomizationState(editor) {
    const style = editor.document.defaultView.getComputedStyle(editor.document.documentElement);
    const numberOfFonts = Number.parseInt(
        editor.options.getCSSVariableValue("number-of-fonts", style),
        10
    );
    const googleFonts = parseFontListProperty(
        editor.options.getCSSVariableValue("google-fonts", style),
        { unquoteEntries: true }
    );
    const googleLocalFonts = parseFontListProperty(
        editor.options.getCSSVariableValue("google-local-fonts", style)
    );
    const uploadedLocalFonts = parseFontListProperty(
        editor.options.getCSSVariableValue("uploaded-local-fonts", style)
    );
    const dedupedGoogleFonts = googleFonts.filter((font) => {
        const localFonts = googleLocalFonts.map((localFont) => localFont.split(":")[0]);
        return !localFonts.includes(`'${font}'`);
    });
    const allFonts = [];
    for (let fontIndex = 1; fontIndex <= numberOfFonts; fontIndex++) {
        const fontKey = editor.options.getCSSVariableValue(`font-number-${fontIndex}`, style);
        if (fontKey) {
            allFonts.push(fontKey);
        }
    }
    return {
        allFonts,
        googleFonts: dedupedGoogleFonts,
        googleLocalFonts,
        uploadedLocalFonts,
    };
}

function buildFontCustomizationValues({
    googleFonts,
    googleLocalFonts,
    uploadedLocalFonts,
}) {
    const values = {};
    values["google-fonts"] = googleFonts.length
        ? `('${googleFonts.join("', '")}')`
        : "null";
    values["google-local-fonts"] = googleLocalFonts.length
        ? `(${googleLocalFonts.join(", ")})`
        : "null";
    values["uploaded-local-fonts"] = uploadedLocalFonts.length
        ? `(${uploadedLocalFonts.join(", ")})`
        : "null";
    return values;
}

async function openAddCustomFontDialog(editor) {
    const wysiwyg = getWebsiteWysiwyg(editor);
    if (!wysiwyg) {
        return;
    }
    const dialogService = wysiwyg.env.services.dialog;
    const orm = wysiwyg.orm;
    const initialState = getFontCustomizationState(editor);

    const AddFontDialog = class extends Component {
        static template = "website.dialog.addFont";
        static components = { GoogleFontAutoComplete: HmdGoogleFontAutoComplete, Dialog };
        static props = { close: Function, title: String, onClickSave: Function };

        setup() {
            this.state = useState({
                loading: false,
                googleFontFamily: undefined,
                googleServe: true,
                uploadedFontName: undefined,
                uploadedFonts: [],
                uploadedFontFaces: undefined,
                previewText: _t("The quick brown fox jumps over the lazy dog."),
            });
            this.fileInput = useRef("fileInput");
        }

        async onClickSave() {
            if (this.state.loading) {
                return;
            }
            this.state.loading = true;
            const shouldClose = await this.props.onClickSave(this.state);
            if (shouldClose) {
                this.props.close();
                return;
            }
            this.state.loading = false;
        }

        onClickCancel() {
            this.props.close();
        }

        get getGoogleFontList() {
            return [
                {
                    options: async (term) => {
                        if (!this.googleFontList) {
                            const data = await rpc("/website/google_font_metadata");
                            this.googleFontList = data.familyMetadataList.map((font) => font.family);
                        }
                        const lowerCaseTerm = term.toLowerCase();
                        return this.googleFontList
                            .filter((value) => value.toLowerCase().includes(lowerCaseTerm))
                            .map((fontFamilyName) => ({
                                label: fontFamilyName,
                                value: fontFamilyName,
                            }));
                    },
                },
            ];
        }

        async onGoogleFontSelect(selected) {
            this.fileInput.el.value = "";
            this.state.uploadedFonts = [];
            this.state.uploadedFontName = undefined;
            this.state.uploadedFontFaces = undefined;
            try {
                const fontFamily = selected.value;
                const result = await fetch(
                    `https://fonts.googleapis.com/css?family=${encodeURIComponent(fontFamily)}:300,300i,400,400i,700,700i`,
                    { method: "HEAD" }
                );
                if (result.ok) {
                    const linkId = `hmdPreviewFont${fontFamily}`;
                    if (!document.querySelector(`link[id='${linkId}']`)) {
                        const linkEl = document.createElement("link");
                        linkEl.id = linkId;
                        linkEl.setAttribute("href", result.url);
                        linkEl.setAttribute("rel", "stylesheet");
                        linkEl.dataset.fontPreview = true;
                        document.head.appendChild(linkEl);
                    }
                    this.state.googleFontFamily = fontFamily;
                } else {
                    this.state.googleFontFamily = undefined;
                }
            } catch (error) {
                console.error(error);
                this.state.googleFontFamily = undefined;
            }
        }

        onUploadChange() {
            this.state.googleFontFamily = undefined;
            const file = this.fileInput.el.files[0];
            if (!file) {
                this.state.uploadedFonts = [];
                this.state.uploadedFontName = undefined;
                this.state.uploadedFontFaces = undefined;
                return;
            }
            const reader = new FileReader();
            reader.onload = (ev) => {
                const base64 = ev.target.result.split(",")[1];
                rpc("/website/theme_upload_font", {
                    name: file.name,
                    data: base64,
                }).then((result) => {
                    this.state.uploadedFonts = result;
                    this.updateFontStyle(file.name.slice(0, file.name.lastIndexOf(".")));
                });
            };
            reader.readAsDataURL(file);
        }

        updateFontStyle(baseFontName) {
            const targetFonts = {};
            let shortestNamedFont;
            for (const font of this.state.uploadedFonts) {
                if (!shortestNamedFont || font.name.length < shortestNamedFont.name.length) {
                    shortestNamedFont = font;
                }
                font.isItalic = /italic/i.test(font.name);
                font.isLight = /light|300/i.test(font.name);
                font.isBold = /bold|700/i.test(font.name);
                font.isRegular = /regular|400/i.test(font.name);
                font.weight = font.isRegular ? 400 : font.isLight ? 300 : font.isBold ? 700 : undefined;
                if (font.isItalic && !font.weight) {
                    if (!/00|thin|medium|black|condense|extrude/i.test(font.name)) {
                        font.isRegular = true;
                        font.weight = 400;
                    }
                }
                font.style = font.isItalic ? "italic" : "normal";
                if (font.weight) {
                    targetFonts[`${font.weight}${font.style}`] = font;
                }
            }
            if (!Object.values(targetFonts).some((font) => font.isRegular)) {
                shortestNamedFont.weight = 400;
                shortestNamedFont.style = "normal";
                targetFonts["400"] = shortestNamedFont;
            }
            const fontFaces = Object.values(targetFonts).map(
                (font) => `@font-face{
                    font-family: ${baseFontName};
                    font-style: ${font.style};
                    font-weight: ${font.weight};
                    src:url("${font.url}");
                }`
            );
            let styleEl = document.head.querySelector(
                `style[id='WebsiteThemeFontPreview-${baseFontName}']`
            );
            if (!styleEl) {
                styleEl = document.createElement("style");
                styleEl.id = `WebsiteThemeFontPreview-${baseFontName}`;
                styleEl.dataset.fontPreview = true;
                document.head.appendChild(styleEl);
            }
            this.state.uploadedFontName = baseFontName;
            this.state.uploadedFontFaces = fontFaces.join("");
            styleEl.textContent = this.state.uploadedFontFaces;
        }
    };

    dialogService.add(
        AddFontDialog,
        {
            title: _t("Add a Google font or upload a custom font"),
            onClickSave: async (state) => {
                try {
                    const googleFonts = [...initialState.googleFonts];
                    const googleLocalFonts = [...initialState.googleLocalFonts];
                    const uploadedLocalFonts = [...initialState.uploadedLocalFonts];
                    const allFonts = [...initialState.allFonts];
                    const uploadedFontName = state.uploadedFontName;
                    const uploadedFontFaces = state.uploadedFontFaces;

                    if (uploadedFontName && uploadedFontFaces) {
                        const fontExistsLocally = uploadedLocalFonts.some(
                            (localFont) => localFont.split(":")[0] === `'${uploadedFontName}'`
                        );
                        if (fontExistsLocally) {
                            dialogService.add(ConfirmationDialog, {
                                title: _t("Font exists"),
                                body: _t(
                                    "This uploaded font already exists.\nTo replace an existing font, remove it first."
                                ),
                            });
                            return false;
                        }
                        const homonymGoogleFontExists =
                            googleFonts.some((font) => font === uploadedFontName) ||
                            googleLocalFonts.some(
                                (font) => font.split(":")[0] === `'${uploadedFontName}'`
                            );
                        if (homonymGoogleFontExists) {
                            dialogService.add(ConfirmationDialog, {
                                title: _t("Font name already used"),
                                body: _t(
                                    "A font with the same name already exists.\nTry renaming the uploaded file."
                                ),
                            });
                            return false;
                        }
                        const [fontCssId] = await orm.call("ir.attachment", "create_unique", [[{
                            name: uploadedFontName,
                            description: `CSS font face for ${uploadedFontName}`,
                            datas: btoa(uploadedFontFaces),
                            res_model: "ir.attachment",
                            mimetype: "text/css",
                            public: true,
                        }]]);
                        uploadedLocalFonts.push(`'${uploadedFontName}': ${fontCssId}`);
                    } else {
                        const font = state.googleFontFamily;
                        let isValidFamily = false;
                        if (!font) {
                            return false;
                        }
                        try {
                            const result = await fetch(
                                `https://fonts.googleapis.com/css?family=${encodeURIComponent(font)}:300,300i,400,400i,700,700i`,
                                { method: "HEAD" }
                            );
                            if (result.ok) {
                                isValidFamily = true;
                            }
                        } catch (error) {
                            console.error(error);
                        }
                        if (!isValidFamily) {
                            dialogService.add(ConfirmationDialog, {
                                title: _t("Font access"),
                                body: _t("The selected font cannot be accessed."),
                            });
                            return false;
                        }
                        const fontName = `'${font}'`;
                        const fontExistsLocally = googleLocalFonts.some(
                            (localFont) => localFont.split(":")[0] === fontName
                        );
                        const fontExistsOnServer = allFonts.includes(fontName);
                        const preventFontAddition =
                            fontExistsLocally || (fontExistsOnServer && state.googleServe);
                        if (preventFontAddition) {
                            dialogService.add(ConfirmationDialog, {
                                title: _t("Font exists"),
                                body: _t(
                                    "This font already exists, you can only add it as a local font to replace the server version."
                                ),
                            });
                            return false;
                        }
                        if (state.googleServe) {
                            googleFonts.push(font);
                        } else {
                            googleLocalFonts.push(`'${font}': ''`);
                        }
                    }

                    await wysiwyg.save();
                    await orm.call("web_editor.assets", "make_scss_customization", [
                        FONT_CUSTOMIZATION_SCSS_PATH,
                        buildFontCustomizationValues({
                            googleFonts,
                            googleLocalFonts,
                            uploadedLocalFonts,
                        }),
                    ]);
                    window.location.reload();
                    return true;
                } catch (error) {
                    console.error(error);
                    dialogService.add(ConfirmationDialog, {
                        title: _t("Operation failed"),
                        body: _t("The font could not be added."),
                    });
                    return false;
                }
            },
        },
        {
            onClose: () => {
                for (const el of document.head.querySelectorAll("[data-font-preview]")) {
                    el.remove();
                }
            },
        }
    );
}

function getDynamicFieldTarget(editor, node) {
    const selectionNode = getSelectionNode(editor, node);
    if (!selectionNode) {
        return null;
    }
    const element = closestElement(selectionNode);
    return element?.closest(DYNAMIC_FIELD_SELECTOR) || null;
}

function applyDynamicStyle(editor, propertyName, value, node) {
    const dynamicField = getDynamicFieldTarget(editor, node);
    if (!dynamicField) {
        return false;
    }
    if (value === undefined || value === null || value === "") {
        dynamicField.style.removeProperty(propertyName);
    } else {
        dynamicField.style.setProperty(propertyName, value);
    }
    return true;
}

function getDynamicFontSizeValue(editor, className) {
    if (!className) {
        return null;
    }
    const htmlStyle = editor.document.defaultView.getComputedStyle(editor.document.documentElement);
    const variableName = className.endsWith("-fs") ? className.slice(0, -3) : className;
    const remValue = Number.parseFloat(
        editor.options.getCSSVariableValue(`${variableName}-font-size`, htmlStyle)
    );
    if (!Number.isFinite(remValue)) {
        return null;
    }
    return `${remValue}rem`;
}

function ensureTypographyFormatSpec(key, cssProperty, propName) {
    if (formatsSpecs[key]) {
        return;
    }
    formatsSpecs[key] = {
        isFormatted: (node) =>
            !!findNode(
                closestPath(node),
                (el) => el.style?.getPropertyValue(cssProperty),
                isBlock
            ),
        hasStyle: (node) => node.style && node.style.getPropertyValue(cssProperty),
        addStyle: (node, props) => {
            node.style.setProperty(cssProperty, props[propName]);
        },
        removeStyle: (node) => removeStyle(node, cssProperty),
    };
}

for (const [key, config] of Object.entries(TYPOGRAPHY_STYLE_CONFIG)) {
    ensureTypographyFormatSpec(key, config.cssProperty, config.propName);
}

editorCommands.setFontSize = (editor, size) => {
    if (applyDynamicStyle(editor, "font-size", size)) {
        return true;
    }
    return size
        ? formatSelection(editor, "fontSize", { applyStyle: true, formatProps: { size } })
        : formatSelection(editor, "fontSize", { applyStyle: false });
};

editorCommands.setFontSizeClassName = (editor, className) => {
    const dynamicFontSize = getDynamicFontSizeValue(editor, className);
    const dynamicField = getDynamicFieldTarget(editor);
    if (dynamicField) {
        dynamicField.classList.remove(...FONT_SIZE_CLASSES);
        applyDynamicStyle(editor, "font-size", dynamicFontSize);
        return true;
    }
    return className
        ? formatSelection(editor, "setFontSizeClassName", {
              applyStyle: true,
              formatProps: { className },
          })
        : formatSelection(editor, "setFontSizeClassName", { applyStyle: false });
};

for (const [commandName, config] of Object.entries(TYPOGRAPHY_STYLE_CONFIG)) {
    const methodName = `set${commandName.charAt(0).toUpperCase()}${commandName.slice(1)}`;
    editorCommands[methodName] = (editor, value) => {
        if (applyDynamicStyle(editor, config.cssProperty, value)) {
            return true;
        }
        return value
            ? formatSelection(editor, commandName, {
                  applyStyle: true,
                  formatProps: { [config.propName]: value },
              })
            : formatSelection(editor, commandName, { applyStyle: false });
    };
}

patch(OdooEditor.prototype, {
    setupToolbar(toolbar) {
        super.setupToolbar(toolbar);

        const localTypographyToggleButton = this.toolbar.querySelector(
            "#hmd-local-typography > button"
        );
        const fontFamilySelect = this.toolbar.querySelector("#hmdFontFamilyCurrentValue");
        const addCustomFontButton = this.toolbar.querySelector("#hmdAddCustomFontButton");
        const fontSizeInput = this.toolbar.querySelector("#hmdLocalFontSizeCurrentValue");
        const letterSpacingInput = this.toolbar.querySelector("#hmdLetterSpacingCurrentValue");
        const lineHeightInput = this.toolbar.querySelector("#hmdLineHeightCurrentValue");

        if (
            !localTypographyToggleButton ||
            !fontFamilySelect ||
            !addCustomFontButton ||
            !fontSizeInput ||
            !letterSpacingInput ||
            !lineHeightInput
        ) {
            return;
        }

        this._hmdPopulateFontFamilySelect(fontFamilySelect);

        this.addDomListener(fontFamilySelect, "change", (ev) => {
            this._hmdApplyTypographySelection("setFontFamily", ev.target.value);
        });
        this.addDomListener(addCustomFontButton, "click", () => {
            openAddCustomFontDialog(this);
        });
        this.addDomListener(localTypographyToggleButton, "shown.bs.dropdown", () => {
            this._hmdPositionLocalTypographyMenu();
        });
        this.addDomListener(localTypographyToggleButton, "hidden.bs.dropdown", () => {
            this._hmdResetLocalTypographyMenuPosition();
        });
        this.addDomListener(window, "resize", () => {
            this._hmdPositionLocalTypographyMenu();
        });
        this.addDomListener(fontSizeInput, "change", (ev) => {
            const pxValue = Number.parseFloat(ev.target.value);
            if (!Number.isFinite(pxValue) || pxValue <= 0) {
                this._hmdApplyTypographySelection("setFontSize", "");
                return;
            }
            const remValue = this.options.convertNumericToUnit(pxValue, "px", "rem");
            this._hmdApplyTypographySelection("setFontSize", `${remValue}rem`);
        });
        this.addDomListener(letterSpacingInput, "change", (ev) => {
            const rawValue = ev.target.value.trim();
            const pxValue = Number.parseFloat(rawValue);
            this._hmdApplyTypographySelection(
                "setLetterSpacing",
                rawValue === "" || !Number.isFinite(pxValue) ? "" : `${pxValue}px`
            );
        });
        this.addDomListener(lineHeightInput, "change", (ev) => {
            const rawValue = ev.target.value.trim();
            const lineHeight = Number.parseFloat(rawValue);
            this._hmdApplyTypographySelection(
                "setLineHeight",
                rawValue === "" || !Number.isFinite(lineHeight) || lineHeight <= 0
                    ? ""
                    : `${lineHeight}`
            );
        });
    },

    _onBeforeInput(ev) {
        if (this._hmdShouldPreventDynamicTextEdition(ev)) {
            ev.preventDefault();
            ev.stopPropagation();
            return;
        }
        super._onBeforeInput(ev);
    },

    _updateToolbar(...args) {
        super._updateToolbar(...args);
        this._hmdUpdateLocalTypographyToolbar();
    },

    _hmdApplyTypographySelection(commandName, value) {
        if (!this.isSelectionInEditable()) {
            this.historyResetLatestComputedSelection(true);
        }
        this.execCommand(commandName, value);
        this.historyResetLatestComputedSelection(true);
        this._updateToolbar();
    },

    _hmdGetAvailableFonts() {
        if (this._hmdAvailableFonts) {
            return this._hmdAvailableFonts;
        }
        const style = this.document.defaultView.getComputedStyle(this.document.documentElement);
        const fonts = [];
        const numberOfFonts = Number.parseInt(
            this.options.getCSSVariableValue("number-of-fonts", style),
            10
        );
        for (let fontIndex = 1; fontIndex <= numberOfFonts; fontIndex++) {
            const fontKey = unquote(
                this.options.getCSSVariableValue(`font-number-${fontIndex}`, style)
            );
            if (!fontKey) {
                continue;
            }
            const label = fontKey === "SYSTEM_FONTS" ? "System Fonts" : fontKey;
            const value = fontKey === "SYSTEM_FONTS" ? "var(--o-system-fonts)" : `'${fontKey}'`;
            fonts.push({ label, value, token: normalizeFontToken(label) });
        }
        this._hmdAvailableFonts = fonts;
        return fonts;
    },

    _hmdPopulateFontFamilySelect(selectEl) {
        if (selectEl.dataset.hmdLoaded === "1") {
            return;
        }
        const options = this._hmdGetAvailableFonts();
        for (const option of options) {
            const optionEl = selectEl.ownerDocument.createElement("option");
            optionEl.value = option.value;
            optionEl.textContent = option.label;
            selectEl.append(optionEl);
        }
        selectEl.dataset.hmdLoaded = "1";
    },

    _hmdShouldPreventDynamicTextEdition(ev) {
        const inputType = ev.inputType || "";
        if (!BLOCKED_DYNAMIC_INPUT_PREFIXES.some((prefix) => inputType.startsWith(prefix))) {
            return false;
        }
        return Boolean(getDynamicFieldTarget(this, ev.target));
    },

    _hmdPositionLocalTypographyMenu() {
        const toggleButton = this.toolbar.querySelector("#hmd-local-typography > button");
        const menu = this.toolbar.querySelector("#hmd-local-typography .o_hmd_local_typography_menu");
        if (!toggleButton || !menu || !menu.classList.contains("show")) {
            return;
        }

        this._hmdPortalLocalTypographyMenu();
        menu.classList.add("o_hmd_local_typography_menu_floating");
        menu.style.visibility = "hidden";
        menu.style.maxHeight = "";

        const toggleRect = toggleButton.getBoundingClientRect();
        const menuRect = menu.getBoundingClientRect();
        const viewportWidth = window.innerWidth;
        const viewportHeight = window.innerHeight;

        let left = toggleRect.right - menuRect.width;
        left = Math.max(
            LOCAL_TYPOGRAPHY_VIEWPORT_MARGIN,
            Math.min(left, viewportWidth - menuRect.width - LOCAL_TYPOGRAPHY_VIEWPORT_MARGIN)
        );

        const availableBelow =
            viewportHeight - toggleRect.bottom - LOCAL_TYPOGRAPHY_MENU_GAP - LOCAL_TYPOGRAPHY_VIEWPORT_MARGIN;
        const availableAbove =
            toggleRect.top - LOCAL_TYPOGRAPHY_MENU_GAP - LOCAL_TYPOGRAPHY_VIEWPORT_MARGIN;

        let top;
        if (menuRect.height <= availableBelow || availableBelow >= availableAbove) {
            top = Math.max(
                LOCAL_TYPOGRAPHY_VIEWPORT_MARGIN,
                toggleRect.bottom + LOCAL_TYPOGRAPHY_MENU_GAP
            );
            menu.style.maxHeight = `${Math.max(140, availableBelow)}px`;
        } else {
            const clampedHeight = Math.max(140, availableAbove);
            top = Math.max(
                LOCAL_TYPOGRAPHY_VIEWPORT_MARGIN,
                toggleRect.top - LOCAL_TYPOGRAPHY_MENU_GAP - Math.min(menuRect.height, clampedHeight)
            );
            menu.style.maxHeight = `${clampedHeight}px`;
        }

        menu.style.left = `${left}px`;
        menu.style.top = `${top}px`;
        menu.style.visibility = "";
    },

    _hmdPortalLocalTypographyMenu() {
        const menu = this.toolbar.querySelector("#hmd-local-typography .o_hmd_local_typography_menu");
        if (!menu || menu.dataset.hmdPortaled === "1") {
            return;
        }
        this._hmdLocalTypographyMenuAnchor = {
            parent: menu.parentNode,
            nextSibling: menu.nextSibling,
        };
        menu.ownerDocument.body.appendChild(menu);
        menu.dataset.hmdPortaled = "1";
    },

    _hmdRestoreLocalTypographyMenu() {
        const menu = this.toolbar.querySelector("#hmd-local-typography .o_hmd_local_typography_menu");
        if (!menu || menu.dataset.hmdPortaled !== "1" || !this._hmdLocalTypographyMenuAnchor) {
            return;
        }
        const { parent, nextSibling } = this._hmdLocalTypographyMenuAnchor;
        if (nextSibling && nextSibling.parentNode === parent) {
            parent.insertBefore(menu, nextSibling);
        } else {
            parent.appendChild(menu);
        }
        delete menu.dataset.hmdPortaled;
        this._hmdLocalTypographyMenuAnchor = null;
    },

    _hmdResetLocalTypographyMenuPosition() {
        const menu = this.toolbar.querySelector("#hmd-local-typography .o_hmd_local_typography_menu");
        if (!menu) {
            return;
        }
        menu.classList.remove("o_hmd_local_typography_menu_floating");
        menu.style.left = "";
        menu.style.top = "";
        menu.style.maxHeight = "";
        menu.style.visibility = "";
        this._hmdRestoreLocalTypographyMenu();
    },

    _hmdUpdateLocalTypographyToolbar() {
        if (!this.toolbar) {
            return;
        }
        const fontFamilySelect = this.toolbar.querySelector("#hmdFontFamilyCurrentValue");
        const fontSizeInput = this.toolbar.querySelector("#hmdLocalFontSizeCurrentValue");
        const letterSpacingInput = this.toolbar.querySelector("#hmdLetterSpacingCurrentValue");
        const lineHeightInput = this.toolbar.querySelector("#hmdLineHeightCurrentValue");
        if (!fontFamilySelect || !fontSizeInput || !letterSpacingInput || !lineHeightInput) {
            return;
        }

        const selection = this.document.getSelection();
        if (!selection?.rangeCount) {
            fontFamilySelect.value = "";
            fontSizeInput.value = "";
            letterSpacingInput.value = "";
            lineHeightInput.value = "";
            return;
        }
        const node = selection?.anchorNode || selection?.focusNode;
        if (!node || !this.isSelectionInEditable()) {
            fontFamilySelect.value = "";
            fontSizeInput.value = "";
            letterSpacingInput.value = "";
            lineHeightInput.value = "";
            return;
        }

        const sourceElement = getDynamicFieldTarget(this, node) || closestElement(node);
        const computedStyle = this.document.defaultView.getComputedStyle(sourceElement);
        const currentFontToken = normalizeFontToken(computedStyle.fontFamily);

        fontFamilySelect.value = "";
        for (const option of this._hmdGetAvailableFonts()) {
            if (option.token && option.token === currentFontToken) {
                fontFamilySelect.value = option.value;
                break;
            }
        }

        const fontSize = Number.parseFloat(
            getFontSizeDisplayValue(
                selection,
                this.options.getCSSVariableValue,
                this.options.convertNumericToUnit
            )
        );
        fontSizeInput.value = Number.isFinite(fontSize) ? Math.round(fontSize) : "";

        const letterSpacing = computedStyle.letterSpacing;
        letterSpacingInput.value =
            letterSpacing && letterSpacing !== "normal"
                ? trimNumericValue(Number.parseFloat(letterSpacing))
                : "";

        const lineHeight = computedStyle.lineHeight;
        if (!lineHeight || lineHeight === "normal") {
            lineHeightInput.value = "";
            return;
        }

        const lineHeightValue = Number.parseFloat(lineHeight);
        const fontSizeValue = Number.parseFloat(computedStyle.fontSize);
        const normalizedLineHeight =
            lineHeight.endsWith("px") && Number.isFinite(fontSizeValue) && fontSizeValue > 0
                ? lineHeightValue / fontSizeValue
                : lineHeightValue;
        lineHeightInput.value = trimNumericValue(normalizedLineHeight);
    },
});
