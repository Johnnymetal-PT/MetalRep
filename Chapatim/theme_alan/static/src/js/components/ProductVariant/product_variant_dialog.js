/** @odoo-module alias=theme_alan.ProductVariantDialog **/

import { Component, onWillStart } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { Dialog } from "@web/core/dialog/dialog";

export class ProductVariantDialog extends Component {
    static template = "theme_alan.ProductVariantDialog";
    static components = { Dialog };
    static props = {
        close: Function,
        productTemplateId: Number,
    };

    setup() {
        this.state = {
            variants: [],
            loading: true,
        };

        onWillStart(async () => {
            const data = await rpc('/shop/get_product_variants', {
                product_template_id: this.props.productTemplateId,
            });
            this.state.variants = data.variants || [];
            this.state.loading = false;
        });
    }

    onVariantClick(url) {
        window.location.href = url;
    }
}
export default {
    ProductVariantDialog: ProductVariantDialog
}
