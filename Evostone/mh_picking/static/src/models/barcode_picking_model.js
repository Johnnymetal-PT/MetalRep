/** @odoo-module **/
import BarcodePickingModel from '@stock_barcode/models/barcode_picking_model';
import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";

const FORM_LABELS = {
    slab: 'Placa',
    block: 'Bloco',
    strip: 'Banda',
    tiles: 'Ladrilhos',
};

patch(BarcodePickingModel.prototype, {
    /**
     * Block creation of new lines when the scanned lot is not reserved in this picking.
     * Only applies when the product already has reserved lines (i.e. is expected in this picking).
     */
    createNewLine(params) {
        const lot = params.fieldsParams?.lot_id;
        const lotName = params.fieldsParams?.lot_name || (lot && lot.name);
        const product = params.fieldsParams?.product_id;

        if (lotName && product && product.tracking !== 'none') {
            // Find reserved lines for this product
            const productLines = this.currentState.lines.filter(
                line => line.product_id.id === product.id && line.reserved_uom_qty > 0
            );

            if (productLines.length > 0) {
                // Product is expected — check if the scanned lot is among the reserved ones
                const isLotReserved = productLines.some(line => {
                    const lineLotName = line.lot_name || (line.lot_id && line.lot_id.name);
                    return lineLotName === lotName;
                });

                if (!isLotReserved) {
                    const reservedLots = productLines
                        .map(l => l.lot_name || (l.lot_id && l.lot_id.name))
                        .filter(Boolean)
                        .join('\n  ');
                    const message = _t(
                        "SN \"%(lotName)s\" não está reservado neste picking.\nSN esperados:\n  %(reservedLots)s",
                        { lotName, reservedLots }
                    );
                    this.notification(message, { type: "danger" });
                    return false;
                }
            }
        }

        return super.createNewLine(...arguments);
    },

    /**
     * For products with physical form (slab, block, strip, tiles),
     * set qty_done = reserved_uom_qty instead of incrementing +1.
     */
    _updateLineQty(line, args) {
        const productForm = line.product_id?.product_form;
        if (args.qty_done && productForm && productForm !== 'none') {
            if (line.reserved_uom_qty) {
                if (line.qty_done < line.reserved_uom_qty) {
                    // First scan: set full reserved qty
                    line.qty_done = line.reserved_uom_qty;
                    this._setUser();
                } else {
                    // Already scanned: block and notify
                    const formLabel = FORM_LABELS[productForm] || 'Artigo';
                    const sn = line.lot_name || (line.lot_id && line.lot_id.name) || '';
                    this.notification(
                        _t("%(formLabel)s SN \"%(sn)s\" já foi escaneada (%(qty)s)", { formLabel, sn, qty: line.qty_done }),
                        { type: "warning" }
                    );
                }
                return;
            }
        }
        return super._updateLineQty(...arguments);
    },

    /**
     * Disable edit (pencil) button for products with physical form.
     */
    lineCanBeEdited(line) {
        const productForm = line.product_id?.product_form;
        if (productForm && productForm !== 'none') {
            return false;
        }
        return super.lineCanBeEdited(...arguments);
    },

    get canScrap() {
        return false;
    },

    get displayCancelButton() {
        return false;
    },

    get displayAddProductButton() {
        return false;
    },
});
