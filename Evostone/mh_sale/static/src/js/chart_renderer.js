/** @odoo-module */
import { Component, onWillStart, useRef, onMounted, onWillUnmount } from "@odoo/owl";
import { loadJS } from "@web/core/assets";

export class ChartRenderer extends Component {
    setup() {
        this.chartRef = useRef("chart");
        this.chart = null;

        onWillStart(async () => {
            await loadJS("/web/static/lib/Chart/Chart.js");
        });

        onMounted(() => {
            this.renderChart();
        });

        onWillUnmount(() => {
            if (this.chart) {
                this.chart.destroy();
            }
        });
    }

    renderChart() {
        const ctx = this.chartRef.el;

        if (!ctx || !this.props.data.labels.length) {
            return;
        }

        this.chart = new Chart(ctx, {
            type: this.props.type,
            data: this.getChartData(),
            options: this.getChartOptions()
        });
    }

    getChartData() {
        const colors = [
            'rgba(52, 152, 219, 0.8)',   // Blue
            'rgba(46, 204, 113, 0.8)',   // Green
            'rgba(155, 89, 182, 0.8)',   // Purple
            'rgba(241, 196, 15, 0.8)',   // Yellow
            'rgba(231, 76, 60, 0.8)',    // Red
            'rgba(26, 188, 156, 0.8)',   // Teal
            'rgba(230, 126, 34, 0.8)',   // Orange
            'rgba(149, 165, 166, 0.8)',  // Gray
        ];

        return {
            labels: this.props.data.labels,
            datasets: [{
                label: this.props.title,
                data: this.props.data.values,
                backgroundColor: colors,
                borderColor: colors.map(c => c.replace('0.8', '1')),
                borderWidth: 2,
                hoverOffset: 4,
                tension: 0.4,
                fill: this.props.type === 'line'
            }]
        };
    }

    getChartOptions() {
        const baseOptions = {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        font: { size: 11 }
                    }
                },
                title: {
                    display: false
                }
            }
        };

        // Adicionar onClick se callback foi fornecido
        if (this.props.onClick) {
            baseOptions.onClick = (event, elements, chart) => {
                if (elements.length > 0) {
                    const index = elements[0].index;
                    const label = chart.data.labels[index];
                    const value = chart.data.datasets[0].data[index];
                    this.props.onClick(label, value, index);
                }
            };

            // Adicionar cursor pointer no hover para feedback visual
            baseOptions.onHover = (event, chartElement) => {
                event.native.target.style.cursor = chartElement.length ? 'pointer' : 'default';
            };
        }

        if (this.props.type === 'line' || this.props.type === 'bar') {
            baseOptions.scales = {
                y: {
                    beginAtZero: true,
                    ticks: {
                        callback: function(value) {
                            return value.toLocaleString('pt-MZ');
                        }
                    }
                }
            };
        }

        return baseOptions;
    }
}

ChartRenderer.template = "mh_sale.ChartRenderer";
ChartRenderer.props = {
    type: String,
    title: String,
    data: Object,
    onClick: { type: Function, optional: true }
};
