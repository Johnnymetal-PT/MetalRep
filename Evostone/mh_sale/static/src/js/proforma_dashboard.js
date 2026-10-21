/** @odoo-module */
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { Component, useState, onWillStart, onWillUnmount } from "@odoo/owl";
import { KpiCard } from "./kpi_card";
import { ChartRenderer } from "./chart_renderer";

const actionRegistry = registry.category("actions");

class ProformaDashboard extends Component {
    setup() {
        super.setup();

        // Serviços
        this.orm = useService('orm');
        this.actionService = useService("action");

        // Datas default: primeiro dia do mês até hoje
        const today = new Date();
        const firstDayOfMonth = new Date(today.getFullYear(), today.getMonth(), 1);

        // Verificar se é primeira abertura (do menu) ou restauração (voltando de navegação)
        const isRestored = sessionStorage.getItem('proforma_dashboard_active') === 'true';

        // Se é primeira abertura, limpar filtros salvos
        if (!isRestored) {
            sessionStorage.removeItem('proforma_dashboard_filters');
        }

        // Marcar dashboard como ativo
        sessionStorage.setItem('proforma_dashboard_active', 'true');

        // Tentar restaurar filtros salvos (só terá valor se for restauração)
        let savedFilters = null;
        try {
            const stored = sessionStorage.getItem('proforma_dashboard_filters');
            if (stored) {
                savedFilters = JSON.parse(stored);
            }
        } catch (e) {
            console.error('Erro ao restaurar filtros do dashboard:', e);
        }

        // Estado reativo
        this.state = useState({
            // Filtros (restaurar salvos ou usar padrão)
            date_from: savedFilters?.date_from || firstDayOfMonth.toISOString().split('T')[0],
            date_to: savedFilters?.date_to || today.toISOString().split('T')[0],
            partner_id: savedFilters?.partner_id || '',
            partners: [],

            loading: true,

            // KPIs
            count_draft: 0,
            count_posted: 0,
            count_paid: 0,
            count_cancelled: 0,
            count_ready: 0,

            amount_draft: 0,
            amount_posted: 0,
            amount_paid: 0,
            amount_cancelled: 0,
            amount_ready: 0,

            currency: 'MT',

            // Totalizador geral
            total_count: 0,
            total_amount: 0,
            average_ticket: 0,

            // Recibos prontos
            ready_payments: [],

            // Gráficos
            methodChart: { labels: [], values: [] },
            timelineChart: { labels: [], values: [] },
            allocationChart: { labels: [], values: [] }
        });

        // Carregar dados ao inicializar
        onWillStart(async () => {
            await this.loadPartners();
            await this.loadData();
        });

        // Limpar flag ao sair do dashboard
        onWillUnmount(() => {
            sessionStorage.removeItem('proforma_dashboard_active');
        });
    }

    async loadPartners() {
        // Carregar lista de clientes
        const partners = await this.orm.searchRead(
            'res.partner',
            [['customer_rank', '>', 0]],
            ['name'],
            { limit: 100, order: 'name' }
        );
        this.state.partners = partners;
    }

    async loadData() {
        this.state.loading = true;

        try {
            const partnerId = this.state.partner_id ? parseInt(this.state.partner_id) : false;

            const data = await this.orm.call(
                "proforma.payment",
                "get_dashboard_data",
                [],
                {
                    date_from: this.state.date_from,
                    date_to: this.state.date_to,
                    partner_id: partnerId
                }
            );

            // Atualizar estado com dados recebidos (preservar reatividade do OWL)
            // NÃO usar Object.assign com spread operator - quebra o proxy reativo!
            // Atualizar apenas os dados do servidor, mantendo filtros intactos
            this.state.count_draft = data.count_draft;
            this.state.count_posted = data.count_posted;
            this.state.count_paid = data.count_paid;
            this.state.count_cancelled = data.count_cancelled;
            this.state.count_ready = data.count_ready;
            this.state.amount_draft = data.amount_draft;
            this.state.amount_posted = data.amount_posted;
            this.state.amount_paid = data.amount_paid;
            this.state.amount_cancelled = data.amount_cancelled;
            this.state.amount_ready = data.amount_ready;
            this.state.ready_payments = data.ready_payments;
            this.state.total_count = data.total_count;
            this.state.total_amount = data.total_amount;
            this.state.average_ticket = data.average_ticket;
            this.state.currency = data.currency;
            this.state.methodChart = data.methodChart;
            this.state.timelineChart = data.timelineChart;
            this.state.allocationChart = data.allocationChart;
            this.state.loading = false;
        } catch (error) {
            console.error("Erro ao carregar dados do dashboard:", error);
            this.state.loading = false;
        }
    }

    async onApplyFilters() {
        this.saveFilters();
        await this.loadData();
    }

    saveFilters() {
        try {
            sessionStorage.setItem('proforma_dashboard_filters', JSON.stringify({
                date_from: this.state.date_from,
                date_to: this.state.date_to,
                partner_id: this.state.partner_id
            }));
        } catch (e) {
            console.error('Erro ao salvar filtros do dashboard:', e);
        }
    }

    onPartnerChange(ev) {
        this.state.partner_id = ev.target.value;
    }

    onCardClick(type) {
        this.saveFilters();
        const domain = this.getDomainForType(type);

        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: this.getTitleForType(type),
            res_model: 'proforma.payment',
            views: [[false, 'list'], [false, 'form']],
            domain: domain,
            context: { create: false },
        });
    }

    getDomainForType(type) {
        const baseDomain = [];

        // Adicionar filtro de data apenas se preenchida
        if (this.state.date_from && this.state.date_from !== '') {
            baseDomain.push(['date', '>=', this.state.date_from]);
        }

        if (this.state.date_to && this.state.date_to !== '') {
            baseDomain.push(['date', '<=', this.state.date_to]);
        }

        if (this.state.partner_id && this.state.partner_id !== '') {
            baseDomain.push(['partner_id', '=', parseInt(this.state.partner_id)]);
        }

        const domains = {
            'draft': [...baseDomain, ['state', '=', 'draft']],
            'posted': [...baseDomain, ['state', '=', 'posted']],
            'paid': [...baseDomain, ['state', '=', 'paid']],
            'cancelled': [...baseDomain, ['state', '=', 'cancelled']],
            'ready': [...baseDomain, ['state', '=', 'posted'], ['allocation_type', '=', 'normal']]
        };

        return domains[type] || baseDomain;
    }

    getTitleForType(type) {
        const titles = {
            'draft': 'Recibos em Rascunho',
            'posted': 'Recibos Confirmados',
            'paid': 'Recibos Pagos',
            'cancelled': 'Recibos Cancelados',
            'ready': 'Prontos para Pagamento'
        };

        return titles[type] || 'Recibos Pró-forma';
    }

    onPaymentClick(paymentId) {
        this.saveFilters();
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Recibo Pró-forma',
            res_model: 'proforma.payment',
            res_id: paymentId,
            views: [[false, 'form']],
        });
    }

    onViewAllReady() {
        this.saveFilters();
        const domain = this.getDomainForType('ready');
        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: 'Prontos para Pagamento Definitivo',
            res_model: 'proforma.payment',
            views: [[false, 'list'], [false, 'form']],
            domain: domain,
            context: { create: false },
        });
    }

    onMethodChartClick(label, value, index) {
        this.saveFilters();

        // Mapear label traduzido para valor técnico
        const METHOD_MAPPING = {
            'Dinheiro': 'cash',
            'Transferência Bancária': 'bank_transfer',
            'Cheque': 'check',
            'M-Pesa': 'mpesa',
            'Mkesh': 'mkesh',
            'E-Mola': 'emola',
            'Talão de Depósito': 'deposit_slip',
            'POS/Cartão': 'pos',
            'Outro': 'other'
        };

        const method = METHOD_MAPPING[label];
        if (!method) {
            console.error('Método de pagamento não mapeado:', label);
            return;
        }

        const domain = this.getDomainForChart('method', method);

        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: `Recibos Pró-forma - ${label}`,
            res_model: 'proforma.payment',
            views: [[false, 'list'], [false, 'form']],
            domain: domain,
            context: { create: false },
        });
    }

    onAllocationChartClick(label, value, index) {
        this.saveFilters();

        // Mapear label traduzido para valor técnico
        const ALLOCATION_MAPPING = {
            'Sem Alocações': 'none',
            'Fatura Pró-Forma': 'proforma',
            'Encomenda Normal': 'normal'
        };

        const allocationType = ALLOCATION_MAPPING[label];
        if (!allocationType) {
            console.error('Tipo de alocação não mapeado:', label);
            return;
        }

        const domain = this.getDomainForChart('allocation', allocationType);

        this.actionService.doAction({
            type: 'ir.actions.act_window',
            name: `Recibos Pró-forma - ${label}`,
            res_model: 'proforma.payment',
            views: [[false, 'list'], [false, 'form']],
            domain: domain,
            context: { create: false },
        });
    }

    getDomainForChart(chartType, filterValue) {
        const baseDomain = [];

        // Adicionar filtros de data (se preenchidos)
        if (this.state.date_from && this.state.date_from !== '') {
            baseDomain.push(['date', '>=', this.state.date_from]);
        }

        if (this.state.date_to && this.state.date_to !== '') {
            baseDomain.push(['date', '<=', this.state.date_to]);
        }

        // Adicionar filtro de cliente (se selecionado)
        if (this.state.partner_id && this.state.partner_id !== '') {
            baseDomain.push(['partner_id', '=', parseInt(this.state.partner_id)]);
        }

        // Adicionar filtro específico do tipo de gráfico
        if (chartType === 'method') {
            baseDomain.push(['payment_method', '=', filterValue]);
            // Apenas recibos confirmados ou pagos (mesma lógica do gráfico)
            baseDomain.push(['state', 'in', ['posted', 'paid']]);
        } else if (chartType === 'allocation') {
            baseDomain.push(['allocation_type', '=', filterValue]);
        }

        return baseDomain;
    }
}

ProformaDashboard.template = "mh_sale.ProformaDashboard";
ProformaDashboard.components = { KpiCard, ChartRenderer };

actionRegistry.add("proforma_dashboard_action", ProformaDashboard);
