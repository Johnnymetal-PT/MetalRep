/** @odoo-module */

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { usePopover } from "@web/core/popover/popover_hook";
import { standardWidgetProps } from "@web/views/widgets/standard_widget_props";

export class ConsumptionAvailabilityWidget extends Component {
    static template = "mh_internal_consumption.ConsumptionAvailabilityWidget";
    static props = standardWidgetProps;

    setup() {
        this.popover = usePopover(ConsumptionAvailabilityPopover);
    }

    get shouldDisplay() {
        const data = this.props.record.data;
        if (!data.product_id || !data.quantity || data.quantity <= 0) {
            return false;
        }
        if (!('free_qty' in data)) {
            return false;
        }
        // Verificar estado do parent (consumo) - só mostrar em draft e confirmed
        const parentRecord = this.props.record.model.root;
        if (parentRecord && parentRecord.data && parentRecord.data.state) {
            const state = parentRecord.data.state;
            if (state !== 'draft') {
                return false;
            }
        }
        return true;
    }

    get availability() {
        const data = this.props.record.data;
        return data.free_qty || 0;
    }

    get colorClass() {
        const data = this.props.record.data;
        const available = this.availability;
        const needed = data.quantity || 0;

        if (available < needed) {
            return "text-danger";
        }
        return "text-success";
    }

    showPopover(ev) {
        const data = this.props.record.data;

        this.popover.open(ev.currentTarget, {
            availability: this.availability,
            needed: data.quantity || 0,
            productName: data.product_id ? data.product_id[1] : "",
            uom: data.uom_id ? data.uom_id[1] : "",
            locationName: data.location_id ? data.location_id[1] : "",
        });
    }
}

export class ConsumptionAvailabilityPopover extends Component {
    static template = "mh_internal_consumption.ConsumptionAvailabilityPopover";
    static props = {
        availability: { type: Number },
        needed: { type: Number },
        productName: { type: String },
        uom: { type: String },
        locationName: { type: String },
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

registry.category("view_widgets").add("consumption_availability_widget", {
    component: ConsumptionAvailabilityWidget,
});
