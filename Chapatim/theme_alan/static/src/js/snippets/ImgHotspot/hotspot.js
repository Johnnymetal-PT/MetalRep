import { markup } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { registry } from '@web/core/registry';
import { _t } from '@web/core/l10n/translation';
import { Interaction } from '@web/public/interaction';
import { QuickViewDialog } from "theme_alan.QuickViewDialog";
import { HotspotStaticPopover, HotspotStaticDialog, HotspotDynamicPopover } from "theme_alan.hotspot_dialog";

// ─── ImgHotSpot ─────────────────────────────────────────────────
export class ImgHotSpot extends Interaction {
    static selector = '.hotspot';

    setup() {
        const hsIcon = this.el.querySelector(".hs_icon");
        if (!hsIcon) return;

        if (hsIcon.classList.contains("dynamic_type")) {
            this._handleDynamicType(hsIcon);
        } else if (hsIcon.classList.contains("static_type")) {
            this._handleStaticType(hsIcon);
        }
    }

    _handleDynamicType(hsIcon) {
        const productTmplId = hsIcon.dataset.product_tmpl_id;
        const dyType = hsIcon.dataset.dy_type || hsIcon.dataset.st_type;
        const popStyle = hsIcon.dataset.po_style || "hs-default-style";

        if (dyType === "popover" && productTmplId) {
            let isPopoverVisible = false;
            let popoverCloseFn = null;

            const mouseEnterHandler = async (ev) => {
                const target = ev.currentTarget;
                if (isPopoverVisible) return;

                const res = await rpc("/get_hotspot_product", {
                    product_tmpl_id: productTmplId,
                    style: popStyle,
                });

                popoverCloseFn = this.services.popover.add(
                    target,
                    HotspotDynamicPopover,
                    { body: markup(res.template) },
                    {
                        closeOnClickAway: true,
                        position: "top",
                        popoverClass: "as-popover",
                    }
                );
                isPopoverVisible = true;
            };

            const mouseLeaveHandler = (ev) => {
                if (popoverCloseFn) {
                    popoverCloseFn();
                    popoverCloseFn = null;
                }
                isPopoverVisible = false;
            };

            hsIcon.addEventListener("mouseenter", mouseEnterHandler);
            hsIcon.addEventListener("mouseleave", mouseLeaveHandler);

        } else if (dyType === "modal" && productTmplId) {
            hsIcon.addEventListener("click", async (ev) => {
                const target = ev.currentTarget;
                const productTmplId = target.getAttribute("data-product_tmpl_id");
                const res = await rpc("/get_quick_view_template", { product_id: parseInt(productTmplId) });

                this.services.dialog.add(QuickViewDialog, {
                    productTemplateId: productTmplId,
                    body: markup(res),
                });

                setTimeout(() => {
                    const dialogContainer = document.querySelector(".o_dialog");
                    if (dialogContainer && this.services["public.interactions"]) {
                        this.services["public.interactions"].startInteractions(dialogContainer);
                    }
                }, 100);
            });
        }
    }

    _handleStaticType(hsIcon) {
        const getAttr = (key, def = "") => hsIcon.getAttribute(key) || def;
        const lang = document.documentElement.lang?.replace(/-/g, "_");
        const title = getAttr(`data-lang-${lang}`) || getAttr("data-po_title", "");
        const description = getAttr(`data-description-lang-${lang}`) || getAttr("data-po_desc", "");
        const btnTxt = getAttr(`data-btn-lang-${lang}`) || getAttr("data-po_btxt", "");
        const btnUrl = getAttr("data-po_bturl", "");
        const imgUrl = getAttr("data-po_imgurl", "");
        const popThm = getAttr("data-po_theme", "");
        const popStyle = getAttr("data-po_style", "hs-default-style");
        const context = {
            title,
            description,
            btn_txt: btnTxt,
            btn_url: btnUrl,
            img_url: imgUrl,
            pop_thm: popThm,
            pop_style: popStyle,
        };

        if (hsIcon.dataset.st_type === "popover") {
            let hoverTimeout = null;
            let isPopoverVisible = false;

            hsIcon.addEventListener("mouseenter", () => {
                clearTimeout(hoverTimeout);
                if (isPopoverVisible) return;

                this._showPopover(hsIcon, context);
                isPopoverVisible = true;
            });

            hsIcon.addEventListener("mouseleave", () => {
                hoverTimeout = setTimeout(() => {
                    if (this.popoverCloseFn) {
                        this.popoverCloseFn();
                        this.popoverCloseFn = null;
                    }
                    isPopoverVisible = false;
                }, 150);
            });
        } else if (hsIcon.dataset.st_type === "modal") {
            hsIcon.addEventListener("click", () => {
                this.services.dialog.add(HotspotStaticDialog, { data: context });
            });
        }
    }

    _showPopover(targetElement, context) {
        const popoverService = this.services.popover;
        let isPopoverVisible = false;
        let hideTimeout = null;

        const showPopover = () => {
            if (isPopoverVisible) return;
            if (this.popoverCloseFn) {
                this.popoverCloseFn();
                this.popoverCloseFn = null;
            }

            this.popoverCloseFn = popoverService.add(
                targetElement,
                HotspotStaticPopover,
                { data: context },
                {
                    position: "top",
                    popoverClass: "as-popover",
                    closeOnClickAway: false,
                }
            );
            isPopoverVisible = true;

            setTimeout(() => {
                const popoverEl = document.querySelector(".as-popover");
                if (popoverEl) {
                    popoverEl.addEventListener("mouseenter", () => {
                        clearTimeout(hideTimeout);
                    });
                    popoverEl.addEventListener("mouseleave", hidePopover);
                }
            }, 50);
        };

        const hidePopover = () => {
            hideTimeout = setTimeout(() => {
                if (this.popoverCloseFn) {
                    this.popoverCloseFn();
                    this.popoverCloseFn = null;
                }
                isPopoverVisible = false;
            }, 100);
        };
        targetElement.addEventListener("mouseenter", showPopover);
        targetElement.addEventListener("mouseleave", hidePopover);
    }
}
registry.category('public.interactions').add('theme_alan.alan_img_hotSpot', ImgHotSpot);
