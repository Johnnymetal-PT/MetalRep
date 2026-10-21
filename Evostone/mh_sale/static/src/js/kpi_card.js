/** @odoo-module */
import { Component } from "@odoo/owl";

export class KpiCard extends Component {
    onClick() {
        if (this.props.onClick) {
            this.props.onClick();
        }
    }

    get formattedValue() {
        if (this.props.currency) {
            return `${this.props.value.toLocaleString('pt-MZ', {minimumFractionDigits: 2, maximumFractionDigits: 2})} ${this.props.currency}`;
        }
        return this.props.value;
    }
}

KpiCard.template = "mh_sale.KpiCard";
KpiCard.props = {
    title: String,
    value: Number,
    icon: String,
    color: String,
    onClick: { type: Function, optional: true },
    currency: { type: String, optional: true }
};
