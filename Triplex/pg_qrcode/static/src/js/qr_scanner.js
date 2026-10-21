/** @odoo-module **/
// Ação cliente "open_qr_scanner": abre a câmara em sobreposição, lê um QR vCard com a
// biblioteca html5-qrcode e envia o texto para o backend criar o contacto.
// Registada no fim do ficheiro em registry.category("actions"). Ver o __manifest__.py.

import { registry } from "@web/core/registry";
import { Component, onMounted } from "@odoo/owl";
import { xml } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";

const TEMPLATE = xml`<div id="qr-root"></div>`;

class QRScanner extends Component {
    static template = TEMPLATE;

    setup() {
        this.rpc = useService("rpc");
        this.notification = useService("notification");
        onMounted(() => this.startScanner());
    }

    async startScanner() {
        console.log("🟢 Starting QR Scanner...");

        const container = document.createElement("div");
        container.id = "qr-reader";
        container.style = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100vw;
            height: 100vh;
            background: rgba(0, 0, 0, 0.85);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        `;

        const innerBox = document.createElement("div");
        innerBox.style = `
            background: white;
            padding: 20px;
            border-radius: 8px;
            display: flex;
            flex-direction: column;
            align-items: center;
        `;

        const closeBtn = document.createElement("button");
        closeBtn.textContent = "Fechar";
        closeBtn.style = "margin-bottom: 10px; padding: 8px 16px; font-size: 16px; cursor: pointer;";
        closeBtn.onclick = () => {
            console.log("🔴 Scanner manually closed.");
            if (qrScanner && qrScanner.getState() === "scanning") {
                qrScanner.stop();
            }
            document.body.removeChild(container);
        };
        innerBox.appendChild(closeBtn);

        const readerDiv = document.createElement("div");
        readerDiv.id = "qr-camera";
        readerDiv.style = "width: 400px; height: 600px;";
        innerBox.appendChild(readerDiv);

        container.appendChild(innerBox);
        document.body.appendChild(container);

        // html5-qrcode é carregado via static/lib (window.Html5Qrcode).
        const Html5Qrcode = window.Html5Qrcode;
        const qrScanner = new Html5Qrcode("qr-camera");

        // facingMode "environment" = câmara traseira (telemóvel). Ao ler com sucesso,
        // para o scanner, envia o vCard ao backend e redireciona para o contacto criado.
        qrScanner.start(
            { facingMode: "environment" },
            { fps: 10, qrbox: 300 },
            async (decodedText) => {
                try {
                    console.log("✅ QR decoded text:\n", decodedText);
                    qrScanner.stop();
                    document.body.removeChild(container);

                    const response = await this.rpc("/create_partner_from_vcard", {
                        vcard: decodedText,
                    });

                    console.log("✅ RPC response:", response);

                    if (response.status === "success") {
                        // 🚀 Go directly to the created contact
                        window.location.href = `/web#id=${response.partner_id}&model=res.partner&view_type=form`;
                    } else {
                        this.notification.add("❌ Erro: " + response.message, {
                            type: "danger",
                        });
                    }

                } catch (err) {
                    console.error("❌ Fatal error in QR logic:", err);
                    this.notification.add("Erro ao processar o QR Code.", {
                        type: "danger",
                    });
                }
            },
            (errorMsg) => {
                console.warn("⚠️ QR Scanner warning:", errorMsg);
            }
        );
    }

    render() {}
}

registry.category("actions").add("open_qr_scanner", QRScanner);

