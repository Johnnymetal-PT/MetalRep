/** @odoo-module **/
// Adiciona a cada cartão do Shop Floor os botões de pré-visualização de PDF e imagem.
//
// A escolha da imagem é feita no SERVIDOR, no campo calculado `pg_card_image_url`
// (`models/mrp_production.py`), que já vem resolvido por precedência: imagem manual da
// ordem, foto da linha de venda, imagem de catálogo do produto. Aqui só se usa o endereço.
//
// Foi assim de propósito: a foto da linha de venda exige percorrer
// `move_finished_ids.move_dest_ids.sale_line_id`, e fazê-lo no browser custaria várias
// chamadas por cartão. Ver o __manifest__.py para o historial.
//
// O estado é cacheado por ordem (mapas abaixo) para evitar leituras repetidas.

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { onWillStart, onWillUpdateProps, useState } from "@odoo/owl";
import { MrpDisplayRecord } from "@mrp_workorder/mrp_display/mrp_display_record";
import { PgMrpBinaryPreviewDialog } from "@pg_mrp_shopfloor_cards/js/preview_dialog";

const PG_BINARY_FLAG_CACHE = new Map();
const PG_BINARY_FLAG_PENDING = new Map();

const FLAGS_VAZIAS = { hasPdf: false, imageUrl: "" };

patch(MrpDisplayRecord.prototype, {
    setup() {
        super.setup(...arguments);
        this.notification = useService("notification");
        this.pgState = useState({ ...FLAGS_VAZIAS });

        this._applyPgFlagsFromData(this.props.production?.data);
        onWillStart(async () => {
            await this._loadPgBinaryFlags(this.props.production);
        });
        onWillUpdateProps(async (nextProps) => {
            const oldId = this.props.production?.resId;
            const nextId = nextProps.production?.resId;
            if (oldId !== nextId) {
                this._applyPgFlagsFromData(nextProps.production?.data);
                await this._loadPgBinaryFlags(nextProps.production);
            } else if (PG_BINARY_FLAG_CACHE.has(nextId)) {
                this._applyPgFlags(PG_BINARY_FLAG_CACHE.get(nextId));
            }
        });
    },

    get pgProductionData() {
        return this.props.production?.data || {};
    },

    get pgProductionId() {
        return this.props.production?.resId || false;
    },

    get pgOrigin() {
        return this.pgProductionData.origin || "";
    },

    // Tecido da peça. Vem resolvido do servidor (componentes da ordem, ou materiais da
    // descrição da venda) e fica vazio quando nenhum dos dois o identifica — nesse caso a
    // linha não aparece no cartão, em vez de mostrar um rótulo sem valor.
    get pgFabric() {
        return this.pgProductionData.pg_fabric_label || "";
    },

    get hasPgPdfFile() {
        return this.pgState.hasPdf;
    },

    // O servidor devolve endereço vazio quando não existe imagem em nenhuma das três
    // origens, por isso o endereço é ao mesmo tempo o sinal e o valor.
    get hasPgImageFile() {
        return Boolean(this.pgState.imageUrl);
    },

    get hasPgPreviewButtons() {
        return this.hasPgPdfFile || this.hasPgImageFile;
    },

    getPdfPreviewUrl() {
        if (!this.pgProductionId) {
            return "";
        }
        return `/web/content/mrp.production/${this.pgProductionId}/x_studio_ficheiro_pdf?download=false`;
    },

    getImagePreviewUrl() {
        return this.pgState.imageUrl || "";
    },

    async openPdfPreview() {
        if (!this.pgProductionId) {
            return;
        }
        const flags = await this._loadPgBinaryFlags(this.props.production, true);
        if (!flags.hasPdf) {
            this.notification.add(_t("No PDF file found for this order."), { type: "warning" });
            return;
        }
        this.dialog.add(PgMrpBinaryPreviewDialog, {
            title: _t("PDF Preview"),
            mode: "pdf",
            src: this.getPdfPreviewUrl(),
        });
    },

    async openImagePreview() {
        if (!this.pgProductionId) {
            return;
        }
        const flags = await this._loadPgBinaryFlags(this.props.production, true);
        if (!flags.imageUrl) {
            this.notification.add(_t("No image found for this order."), { type: "warning" });
            return;
        }
        this.dialog.add(PgMrpBinaryPreviewDialog, {
            title: _t("Image Preview"),
            mode: "image",
            src: flags.imageUrl,
        });
    },

    _applyPgFlagsFromData(productionData) {
        if (!productionData) {
            return;
        }
        if (Object.prototype.hasOwnProperty.call(productionData, "x_studio_ficheiro_pdf")) {
            this.pgState.hasPdf = Boolean(productionData.x_studio_ficheiro_pdf);
        }
        if (Object.prototype.hasOwnProperty.call(productionData, "pg_card_image_url")) {
            this.pgState.imageUrl = productionData.pg_card_image_url || "";
        }
    },

    _applyPgFlags(flags) {
        this.pgState.hasPdf = flags.hasPdf;
        this.pgState.imageUrl = flags.imageUrl;
    },

    async _loadPgBinaryFlags(production, forceRefresh = false) {
        const productionId = production?.resId;
        if (!productionId) {
            this._applyPgFlags(FLAGS_VAZIAS);
            return FLAGS_VAZIAS;
        }

        if (!forceRefresh && PG_BINARY_FLAG_CACHE.has(productionId)) {
            const cached = PG_BINARY_FLAG_CACHE.get(productionId);
            this._applyPgFlags(cached);
            return cached;
        }

        if (!forceRefresh && PG_BINARY_FLAG_PENDING.has(productionId)) {
            await PG_BINARY_FLAG_PENDING.get(productionId);
            const cached = PG_BINARY_FLAG_CACHE.get(productionId) || FLAGS_VAZIAS;
            this._applyPgFlags(cached);
            return cached;
        }

        const fetchPromise = this.model.orm
            .read("mrp.production", [productionId], [
                "x_studio_ficheiro_pdf",
                "pg_card_image_url",
            ])
            .then(([record]) => {
                const flags = {
                    hasPdf: Boolean(record?.x_studio_ficheiro_pdf),
                    imageUrl: record?.pg_card_image_url || "",
                };
                PG_BINARY_FLAG_CACHE.set(productionId, flags);
                return flags;
            })
            .finally(() => {
                PG_BINARY_FLAG_PENDING.delete(productionId);
            });

        PG_BINARY_FLAG_PENDING.set(productionId, fetchPromise);
        const flags = await fetchPromise;
        this._applyPgFlags(flags);
        return flags;
    },
});
