/** @odoo-module alias=theme_alan.ProductShareDialog **/

import { Component, useRef } from "@odoo/owl";
import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";
import { useService } from "@web/core/utils/hooks";

// ─── Product Share Dialog ─────────────────────────────────────────────────
export class ProductShareDialog extends Component {
    static template = "theme_alan.ProductShare";
    static components = { Dialog };
    static props = {
        close: Function,
        product_link: String,
        body: String,
        title: { type: String, optional: true },
        media: { type: String, optional: true },
    }
    setup() {
        this.notification = useService("notification");
        this.copyBtn = useRef("copy_btn");
    }
    get facebookUrl() {
        const url = encodeURIComponent(this.props.product_link);
        return `https://www.facebook.com/sharer/sharer.php?u=${url}`;
    }
    get twitterUrl() {
        const url = encodeURIComponent(this.props.product_link);
        const title = encodeURIComponent(this.props.title || this.props.body || 'Check out this product!');
        return `https://twitter.com/intent/tweet?text=${title}&url=${url}`;
    }
    get linkedinUrl() {
        const url = encodeURIComponent(this.props.product_link);
        return `https://www.linkedin.com/sharing/share-offsite/?url=${url}`;
    }
    get whatsappUrl() {
        const title = encodeURIComponent(this.props.title || this.props.body || 'Check out this product!');
        const url = encodeURIComponent(this.props.product_link);
        return `https://wa.me/?text=${title} ${url}`;
    }
    get pinterestUrl() {
        const url = encodeURIComponent(this.props.product_link);
        const title = encodeURIComponent(this.props.title || this.props.body || 'Check out this product!');
        const media = encodeURIComponent(this.props.media || '');
        return `https://pinterest.com/pin/create/button/?url=${url}&media=${media}&description=${title}`;
    }
    get emailUrl() {
        const url = encodeURIComponent(this.props.product_link);
        const title = encodeURIComponent(this.props.title || this.props.body || 'Check out this product!');
        return `mailto:?body=${url}&subject=${title}`;
    }
    async copyToProductLink() {
        const button = this.copyBtn.el;
        try {
            if (navigator.clipboard) {
                await navigator.clipboard.writeText(this.props.product_link);
            } else {
                // Fallback for older browsers
                const input = document.createElement("input");
                input.value = this.props.product_link;
                document.body.appendChild(input);
                input.select();
                input.setSelectionRange(0, 99999);
                document.execCommand("copy");
                document.body.removeChild(input);
            }
            button.disabled = true;
            button.innerHTML = `<i class="fa fa-check" aria-hidden="true"></i>`;
            setTimeout(() => {
                button.disabled = false;
                button.innerHTML = `<i class="fa fa-clone"></i>`;
            }, 2000);
        } catch (err) {
            this.notification.add(_t("Failed to copy link!"));
        }
    }
}
export default {
    ProductShareDialog: ProductShareDialog
}
