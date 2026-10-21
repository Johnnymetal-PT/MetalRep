/** @odoo-module **/

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { rpc } from "@web/core/network/rpc";

/**
 * Zebra ZPL Print Handler
 *
 * Intercepta reports ZPL (qweb-text), renderiza o ZPL no servidor,
 * e envia para o Zebra Print Server via URL publica (ngrok).
 * Fallback: cria zebra.print.job se o print server nao responder.
 */

const ZPL_REPORTS = [
    "mh_stone_reports.report_stickers_zpl",
    "mh_stone_reports.report_stone_stock_stickers_zpl",
];

async function getPrintServerUrl() {
    try {
        const result = await rpc("/mh_stone_reports/zpl/settings");
        return result.print_server_url || "";
    } catch {
        return "";
    }
}

const PRINT_API_TOKEN = "st-zebra-2026-mhc";

async function sendToPrintServer(url, zpl) {
    const response = await fetch(url + "/print", {
        method: "POST",
        headers: {
            "Content-Type": "application/json",
            "X-Print-Token": PRINT_API_TOKEN,
        },
        body: JSON.stringify({ zpl: zpl, method: "auto" }),
    });
    return await response.json();
}

async function createPrintJob(orm, reportName, zpl) {
    await orm.create("zebra.print.job", [{
        name: reportName.split(".").pop(),
        zpl: zpl,
        method: "auto",
    }]);
}

async function zebraPrintHandler(action, options, env) {
    const reportName = action.report_name;
    if (!reportName || !ZPL_REPORTS.includes(reportName)) {
        return false;
    }

    const orm = env.services.orm;
    const notification = env.services.notification;
    const activeIds = action.context?.active_ids || [];

    if (!activeIds.length) {
        notification.add(_t("Nenhum registo seleccionado."), { type: "warning" });
        return true;
    }

    notification.add(_t("A preparar impressao ZPL..."), { type: "info" });

    try {
        // 1. Renderizar ZPL no servidor Odoo
        const result = await rpc("/mh_stone_reports/zpl/render", {
            report_name: reportName,
            res_ids: activeIds,
        });

        if (result.error) {
            notification.add(_t("Erro ao gerar ZPL: ") + result.error, { type: "danger" });
            return true;
        }

        const zpl = result.zpl;
        if (!zpl) {
            notification.add(_t("ZPL vazio - nenhum dado para imprimir."), { type: "warning" });
            return true;
        }

        const labelCount = (zpl.match(/\^XZ/g) || []).length;

        // 2. Obter URL do print server
        const printServerUrl = await getPrintServerUrl();

        if (printServerUrl) {
            // Via 1: Enviar directamente ao print server (ngrok URL)
            try {
                notification.add(_t("A enviar para Zebra..."), { type: "info" });
                const printResult = await sendToPrintServer(printServerUrl, zpl);

                if (printResult.ok) {
                    const method = printResult.method === "ble" ? "Bluetooth" : "USB";
                    notification.add(
                        _t("Impresso com sucesso via ") + method + "! " + labelCount + _t(" etiqueta(s)"),
                        { type: "success" }
                    );
                    return true;
                } else {
                    notification.add(
                        _t("Erro: ") + (printResult.error || "Desconhecido"),
                        { type: "danger" }
                    );
                    return true;
                }
            } catch (fetchError) {
                console.warn("Print server indisponivel, a usar fila:", fetchError);
                // Fallback para Via 2
            }
        }

        // Via 2: Criar print job (fallback)
        await createPrintJob(orm, reportName, zpl);
        notification.add(
            _t("Enviado para fila de impressao! ") + labelCount + _t(" etiqueta(s)"),
            { type: "success" }
        );

    } catch (error) {
        console.error("Zebra Print Error:", error);
        notification.add(
            _t("Erro ao imprimir: ") + (error.message || "Desconhecido"),
            { type: "danger" }
        );
    }

    if (options.onClose) {
        env.services.action.doAction(
            { type: "ir.actions.act_window_close" },
            { onClose: options.onClose }
        );
        options.onClose();
    }

    return true;
}

registry
    .category("ir.actions.report handlers")
    .add("zebra_zpl_print_handler", zebraPrintHandler, { sequence: 5 });
