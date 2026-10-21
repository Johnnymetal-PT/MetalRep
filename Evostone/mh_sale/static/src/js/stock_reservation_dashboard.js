/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

class StockReservationDashboard extends Component {
    static template = "mh_sale.StockReservationDashboard";

    setup() {
        this.orm = useService("orm");
        this.actionService = useService("action");
        this.state = useState({
            date_from: '',
            date_to: '',
            product_form: '',
            location_id: '',
            reservations: [],
            locations: [],
            loading: true,
        });

        onWillStart(async () => {
            await this.loadData();
        });
    }

    async loadData() {
        this.state.loading = true;

        try {
            const data = await this.orm.call(
                'stock.reservation.report',
                'get_reservation_data',
                [],
                {
                    date_from: this.state.date_from || null,
                    date_to: this.state.date_to || null,
                    product_form: this.state.product_form || null,
                    location_id: this.state.location_id || null,
                }
            );

            this.state.date_from = data.date_from;
            this.state.date_to = data.date_to;
            this.state.reservations = data.reservations;
            this.state.locations = data.locations;

            // Debug: verificar estrutura dos dados
            if (data.reservations.length > 0) {
                console.log("Primeira reserva:", data.reservations[0]);
                console.log("Product name:", data.reservations[0].product_name);
            }
        } catch (error) {
            console.error("Erro ao carregar dados de reservas:", error);
        } finally {
            this.state.loading = false;
        }
    }

    async onApplyFilters() {
        await this.loadData();
    }

    onRowClick(saleOrderId) {
        if (!saleOrderId) return;

        this.actionService.doAction({
            type: 'ir.actions.act_window',
            res_model: 'sale.order',
            res_id: saleOrderId,
            views: [[false, 'form']],
            view_mode: 'form',
        });
    }
}

registry.category("actions").add("stock_reservation_dashboard_action", StockReservationDashboard);
