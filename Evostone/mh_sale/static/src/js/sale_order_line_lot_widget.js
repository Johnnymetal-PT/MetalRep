/** @odoo-module */

import { patch } from "@web/core/utils/patch";

// Use dynamic import with promise to avoid top-level await
const patchPromise = import("@sale_stock/widgets/qty_at_date_widget")
    .then(module => {
        if (module) {
            const { QtyAtDateWidget, QtyAtDatePopover } = module;

            // Patch the popover to show lot information
            if (QtyAtDatePopover) {
                patch(QtyAtDatePopover.prototype, {
                    setup() {
                        this._super(...arguments);
                        // Add lot name if exists
                        const data = this.props.record && this.props.record.data;
                        if (data && data.lot_id) {
                            this.lotName = data.lot_id[1];  // lot_id is [id, name] format
                        }
                    }
                });
            }

            // Patch the widget to consider lot in calculations
            if (QtyAtDateWidget) {
                patch(QtyAtDateWidget.prototype, {
                    initCalcData() {
                        this._super(...arguments);
                        const data = this.props.record && this.props.record.data;

                        // If lot is selected, add lot info to calculation data
                        if (data && data.lot_id) {
                            this.calcData.has_lot = true;
                            this.calcData.lot_name = data.lot_id[1];

                            // Recalculate will_be_fulfilled based on lot availability
                            if (data.state === 'sale') {
                                this.calcData.will_be_fulfilled = data.free_qty_today >= data.qty_to_deliver;
                            } else {
                                this.calcData.will_be_fulfilled = data.virtual_available_at_date >= data.product_uom_qty;
                            }

                            // Update forecasted_issue flag
                            this.calcData.forecasted_issue = !this.calcData.will_be_fulfilled && !data.is_mto;
                        }
                    }
                });
            }

            console.log("Successfully patched qty_at_date widgets for lot support");
        }
    })
    .catch(error => {
        // Module not available - sale_stock might not be installed
        console.log("sale_stock widgets not available, skipping lot widget patch");
    });

// Export the promise in case other modules need to wait for it
export { patchPromise };