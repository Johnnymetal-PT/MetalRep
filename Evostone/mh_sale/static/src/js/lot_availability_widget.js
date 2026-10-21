/** @odoo-module */

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { usePopover } from "@web/core/popover/popover_hook";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

export class LotAvailabilityWidget extends Component {
    static template = "mh_sale.LotAvailabilityWidget";
    static props = standardWidgetProps;

    setup() {
        this.popover = usePopover(LotAvailabilityPopover);
    }

    get shouldDisplay() {
        const data = this.props.record.data;
        // Show only if product is selected and quantity > 0
        // Also check if we have the availability fields (from sale_stock module)
        return data.product_id && data.product_uom_qty > 0 &&
               ('virtual_available_at_date' in data || 'free_qty_today' in data);
    }

    get availability() {
        const data = this.props.record.data;
        // Use virtual_available_at_date which is calculated considering lot if selected
        // The Python method _compute_qty_at_date already handles lot-specific availability
        return data.virtual_available_at_date || data.free_qty_today || 0;
    }

    get colorClass() {
        const data = this.props.record.data;
        const available = this.availability;
        const needed = data.product_uom_qty || 0;

        // Add text-danger only when there's insufficient stock
        if (available < needed) {
            return "text-danger";
        }
        return "";
    }

    showPopover(ev) {
        const data = this.props.record.data;

        this.popover.open(ev.currentTarget, {
            availability: this.availability,
            needed: data.product_uom_qty || 0,
            lotName: data.lot_id ? data.lot_id[1] : "",
            productName: data.product_id ? data.product_id[1] : "",
            uom: data.product_uom ? data.product_uom[1] : "",
        });
    }
}

export class LotAvailabilityPopover extends Component {
    static template = "mh_sale.LotAvailabilityPopover";
    static props = {
        availability: { type: Number },
        needed: { type: Number },
        lotName: { type: String },
        productName: { type: String },
        uom: { type: String },
        close: { type: Function, optional: true },
    };

    get statusText() {
        if (this.props.availability >= this.props.needed) {
            return "Disponível";
        } else if (this.props.availability > 0) {
            return "Parcialmente Disponível";
        } else {
            return "Indisponível";
        }
    }

    get statusClass() {
        if (this.props.availability >= this.props.needed) {
            return "text-success";
        } else if (this.props.availability > 0) {
            return "text-warning";
        } else {
            return "text-danger";
        }
    }
}

// Register the widget
registry.category("view_widgets").add("lot_availability_widget", {
    component: LotAvailabilityWidget,
});