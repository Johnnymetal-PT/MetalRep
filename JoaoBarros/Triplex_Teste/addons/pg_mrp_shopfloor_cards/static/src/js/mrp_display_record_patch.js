/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { useService } from "@web/core/utils/hooks";
import { onWillStart, onWillUpdateProps, useState } from "@odoo/owl";
import { MrpDisplayRecord } from "@mrp_workorder/mrp_display/mrp_display_record";
import { PgMrpBinaryPreviewDialog } from "@pg_mrp_shopfloor_cards/js/preview_dialog";

const PG_BINARY_FLAG_CACHE = new Map();
const PG_BINARY_FLAG_PENDING = new Map();

patch(MrpDisplayRecord.prototype, {
    setup() {
        super.setup(...arguments);
        this.notification = useService("notification");
        this.pgState = useState({
            hasPdf: false,
            hasImage: false,
        });

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

    get hasPgPdfFile() {
        return this.pgState.hasPdf;
    },

    get hasPgImageFile() {
        return this.pgState.hasImage;
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
        if (!this.pgProductionId) {
            return "";
        }
        return `/web/image/mrp.production/${this.pgProductionId}/x_studio_imagem_estofo`;
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
        if (!flags.hasImage) {
            this.notification.add(_t("No image file found for this order."), { type: "warning" });
            return;
        }
        this.dialog.add(PgMrpBinaryPreviewDialog, {
            title: _t("Image Preview"),
            mode: "image",
            src: this.getImagePreviewUrl(),
        });
    },

    _applyPgFlagsFromData(productionData) {
        if (!productionData) {
            return;
        }
        if (Object.prototype.hasOwnProperty.call(productionData, "x_studio_ficheiro_pdf")) {
            this.pgState.hasPdf = Boolean(productionData.x_studio_ficheiro_pdf);
        }
        if (Object.prototype.hasOwnProperty.call(productionData, "x_studio_imagem_estofo")) {
            this.pgState.hasImage = Boolean(productionData.x_studio_imagem_estofo);
        }
    },

    _applyPgFlags(flags) {
        this.pgState.hasPdf = flags.hasPdf;
        this.pgState.hasImage = flags.hasImage;
    },

    async _loadPgBinaryFlags(production, forceRefresh = false) {
        const productionId = production?.resId;
        if (!productionId) {
            this._applyPgFlags({ hasPdf: false, hasImage: false });
            return { hasPdf: false, hasImage: false };
        }

        if (!forceRefresh && PG_BINARY_FLAG_CACHE.has(productionId)) {
            const cached = PG_BINARY_FLAG_CACHE.get(productionId);
            this._applyPgFlags(cached);
            return cached;
        }

        if (!forceRefresh && PG_BINARY_FLAG_PENDING.has(productionId)) {
            await PG_BINARY_FLAG_PENDING.get(productionId);
            const cached = PG_BINARY_FLAG_CACHE.get(productionId) || { hasPdf: false, hasImage: false };
            this._applyPgFlags(cached);
            return cached;
        }

        const fetchPromise = this.model.orm
            .read("mrp.production", [productionId], ["x_studio_ficheiro_pdf", "x_studio_imagem_estofo"])
            .then(([record]) => {
                const flags = {
                    hasPdf: Boolean(record?.x_studio_ficheiro_pdf),
                    hasImage: Boolean(record?.x_studio_imagem_estofo),
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
