/** @odoo-module alias=theme_alan.ProductAdvanceInfoDialog **/

import { markup } from "@odoo/owl";
import { rpc } from "@web/core/network/rpc";
import { _t } from "@web/core/l10n/translation";
import { Dialog } from "@web/core/dialog/dialog";
import { Component, onWillStart} from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

// ─── Product Advance Info Dialog ─────────────────────────────────────────────────
export class ProductAdvanceInfoDialog extends Component {
    static template = "theme_alan.ProductAdvanceInfo";
    static components = { Dialog };
    static props = {
        close: Function,
        infoId: Number,
        body: String,
    };
    setup() {
        this.rpc = rpc
        this.orm = useService("orm");
        onWillStart(async () => {
            await this.rpc('/get_advance_info', { advance_info_id: this.props.infoId }).then((result) => {
                if (result){
                    this.props.body = markup(result)
                }
            })
        })
        super.setup();
    }
}
export default {
    ProductAdvanceInfoDialog: ProductAdvanceInfoDialog,
}
