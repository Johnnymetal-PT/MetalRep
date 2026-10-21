/** @odoo-module **/

import publicWidget from "@web/legacy/js/public/public_widget";

publicWidget.registry.ProductModelViewer = publicWidget.Widget.extend({
    selector: ".oe_website_sale",
    events: {
        "click .o_product_model_viewer_open": "_onOpenViewer",
        "click .o_product_model_viewer_fullscreen": "_onFullscreenClick",
    },

    start() {
        const result = this._super.apply(this, arguments);
        this._moveAllViewerModalsToBody();
        return result;
    },

    _moveAllViewerModalsToBody() {
        const modals = this.el ? this.el.querySelectorAll(".o_pg_3d_viewer_modal") : [];
        for (const modal of modals) {
            this._moveViewerModalToBody(modal);
        }
    },

    _moveViewerModalToBody(modalEl) {
        if (!modalEl || !document.body || modalEl.dataset.pgMovedToBody === "1") {
            return;
        }
        document.body.appendChild(modalEl);
        modalEl.dataset.pgMovedToBody = "1";
    },

    _onOpenViewer(ev) {
        const trigger = ev.currentTarget;
        const selector = trigger?.getAttribute("data-bs-target") || "";
        if (!selector || !selector.startsWith("#")) {
            return;
        }
        const modalEl = document.querySelector(selector);
        this._moveViewerModalToBody(modalEl);
    },

    _onFullscreenClick(ev) {
        const container = ev.currentTarget?.closest(".o_product_model_viewer_container");
        const modelViewerElem = container ? container.querySelector("model-viewer") : null;
        if (!modelViewerElem) {
            return;
        }
        const isFullscreenAvailable =
            document.fullscreenEnabled ||
            document.mozFullScreenEnabled ||
            document.webkitFullscreenEnabled ||
            document.msFullscreenEnabled ||
            false;
        if (!isFullscreenAvailable) {
            console.error("ERROR: full screen not supported by web browser");
            return;
        }
        const fullscreenElement =
            document.fullscreenElement ||
            document.mozFullScreenElement ||
            document.webkitFullscreenElement ||
            document.msFullscreenElement;
        if (fullscreenElement) {
            if (document.exitFullscreen) {
                document.exitFullscreen();
            } else if (document.mozCancelFullScreen) {
                document.mozCancelFullScreen();
            } else if (document.webkitExitFullscreen) {
                document.webkitExitFullscreen();
            } else if (document.msExitFullscreen) {
                document.msExitFullscreen();
            }
            return;
        }
        if (modelViewerElem.requestFullscreen) {
            modelViewerElem.requestFullscreen();
        } else if (modelViewerElem.mozRequestFullScreen) {
            modelViewerElem.mozRequestFullScreen();
        } else if (modelViewerElem.webkitRequestFullscreen) {
            modelViewerElem.webkitRequestFullscreen();
        } else if (modelViewerElem.msRequestFullscreen) {
            modelViewerElem.msRequestFullscreen();
        }
    },
});

export default publicWidget.registry.ProductModelViewer;
