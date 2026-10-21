/** @odoo-module **/

import { PosDB } from "@point_of_sale/app/store/db";
import { patch } from "@web/core/utils/patch";

const _superProductSearchString = PosDB.prototype._product_search_string;

patch(PosDB.prototype, {
    /**
     * Include x_studio_referncia_interna in the product search string
     * so that it is matched when searching products in the POS interface.
     */
    _product_search_string(product) {
        let str = _superProductSearchString.call(this, product);
        if (product.x_studio_referncia_interna) {
            str = str.trim();
            if (str.endsWith("\n")) {
                str = str.slice(0, -1);
            }
            str += "|" + product.x_studio_referncia_interna + "\n";
        }
        return str;
    },
});
