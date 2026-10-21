/** @odoo-module **/

import options from "@web_editor/js/editor/snippets.options";
import { MediaDialog } from "@web_editor/components/media_dialog/media_dialog";
import { _t } from "@web/core/l10n/translation";
import "@website_sale/js/website_sale.editor";

// Classe que marca o distintivo como "selo com imagem". Fica guardada no campo
// `html_class` do product.ribbon pelo mecanismo standard do Odoo (_saveRibbon).
const STAMP_CLASS = "pg_ribbon_stamp";
// Classes de tamanho. Vazio (ausencia de classe) = tamanho medio.
const SIZE_CLASSES = ["pg_stamp_sm", "pg_stamp_lg"];
// Opcoes standard que nao fazem sentido quando o distintivo e uma imagem.
const TEXT_ONLY_OPTS = [
    "pg_ribbon_text_opt",
    "pg_ribbon_bg_opt",
    "pg_ribbon_color_opt",
    "pg_ribbon_shape_opt",
];
// Opcoes que so fazem sentido quando o distintivo ja e uma imagem.
const STAMP_ONLY_OPTS = ["pg_ribbon_image_remove_opt", "pg_ribbon_stamp_size_opt"];

options.registry.WebsiteSaleProductsItem.include({

    //--------------------------------------------------------------------------
    // Options
    //--------------------------------------------------------------------------

    /**
     * Abre o seletor de media e transforma o distintivo num selo com a imagem escolhida.
     *
     * O conteudo do distintivo e gravado pelo mecanismo standard (`_saveRibbon` le o
     * innerHTML do `.o_ribbon`), pelo que basta colocar o `<img>` no sitio certo.
     *
     * @see this.selectClass for params
     */
    async setRibbonImage(previewMode, widgetValue, params) {
        const mediaEl = await new Promise(resolve => {
            let selected = null;
            this.dialog.add(MediaDialog, {
                onlyImages: true,
                save: el => {
                    selected = el;
                },
            }, {
                onClose: () => resolve(selected),
            });
        });
        if (!mediaEl || mediaEl.tagName !== "IMG") {
            return;
        }
        const ribbonEl = this.$ribbon[0];
        // Reconstroi-se a imagem no documento do site (o editor corre num iframe) e sem os
        // atributos do seletor de media, que aqui nao servem para nada.
        const imgEl = ribbonEl.ownerDocument.createElement("img");
        imgEl.setAttribute("src", mediaEl.getAttribute("src"));
        imgEl.setAttribute("alt", mediaEl.getAttribute("alt") || "");
        imgEl.classList.add("pg_ribbon_img");

        ribbonEl.replaceChildren(imgEl);
        ribbonEl.classList.add(STAMP_CLASS);
        // Um selo nao usa a forma inclinada: passa-se para "tag", mantendo o lado escolhido.
        ribbonEl.className = ribbonEl.className.replace(/o_ribbon_(left|right)/, "o_tag_$1");
        // As cores do distintivo de texto nao se aplicam a uma imagem.
        ribbonEl.style.backgroundColor = "";
        ribbonEl.style.color = "";

        await this._saveRibbon();
    },
    /**
     * Remove a imagem e devolve o distintivo ao formato de texto standard.
     *
     * @see this.selectClass for params
     */
    async removeRibbonImage(previewMode, widgetValue, params) {
        const ribbonEl = this.$ribbon[0];
        ribbonEl.classList.remove(STAMP_CLASS, ...SIZE_CLASSES);
        ribbonEl.textContent = _t("Badge Text");
        await this._saveRibbon();
    },
    /**
     * Define o tamanho do selo. O valor vazio corresponde ao tamanho medio (sem classe).
     *
     * @see this.selectClass for params
     */
    async setRibbonStampSize(previewMode, widgetValue, params) {
        const ribbonEl = this.$ribbon[0];
        ribbonEl.classList.remove(...SIZE_CLASSES);
        if (widgetValue) {
            ribbonEl.classList.add(widgetValue);
        }
        await this._saveRibbon();
    },

    //--------------------------------------------------------------------------
    // Private
    //--------------------------------------------------------------------------

    /**
     * O template standard da lista de distintivos escreve o conteudo com `t-out`, que em
     * Owl escapa o HTML. Um selo apareceria ali como texto (`<img src=...>`), pelo que se
     * substitui esse texto por uma miniatura da imagem.
     *
     * @override
     */
    async _renderCustomXML(uiFragment) {
        await this._super(...arguments);
        for (const [ribbonId, ribbon] of Object.entries(this.ribbons || {})) {
            const imgSrc = this._getRibbonImageSrc(ribbon.html);
            if (!imgSrc) {
                continue;
            }
            const buttonEl = uiFragment.querySelector(`we-button[data-set-ribbon="${ribbonId}"]`);
            if (!buttonEl) {
                continue;
            }
            for (const node of [...buttonEl.childNodes]) {
                if (node.nodeType === Node.TEXT_NODE) {
                    node.remove();
                }
            }
            const previewEl = document.createElement("img");
            previewEl.setAttribute("src", imgSrc);
            previewEl.classList.add("pg_ribbon_option_preview");
            buttonEl.prepend(previewEl);
        }
    },
    /**
     * @override
     */
    async _computeWidgetState(methodName, params) {
        if (methodName === "setRibbonStampSize") {
            const classList = this.$ribbon[0].classList;
            return SIZE_CLASSES.find(className => classList.contains(className)) || "";
        }
        return this._super(...arguments);
    },
    /**
     * @override
     */
    async _computeWidgetVisibility(widgetName, params) {
        if (STAMP_ONLY_OPTS.includes(widgetName)) {
            return this._isRibbonStamp();
        }
        if (TEXT_ONLY_OPTS.includes(widgetName)) {
            return !this._isRibbonStamp();
        }
        return this._super(...arguments);
    },
    /**
     * Extrai o src da imagem de um conteudo de distintivo, se existir.
     *
     * @private
     * @param {String} [ribbonHtml]
     * @returns {String} vazio quando o distintivo nao tem imagem
     */
    _getRibbonImageSrc(ribbonHtml) {
        if (!ribbonHtml || !ribbonHtml.includes("<img")) {
            return "";
        }
        const holderEl = document.createElement("div");
        holderEl.innerHTML = ribbonHtml;
        const imgEl = holderEl.querySelector("img");
        return imgEl ? imgEl.getAttribute("src") || "" : "";
    },
    /**
     * @private
     * @returns {Boolean} o distintivo selecionado e um selo com imagem
     */
    _isRibbonStamp() {
        return !!this.$ribbon && !!this.$ribbon.length
            && this.$ribbon[0].classList.contains(STAMP_CLASS);
    },
});
