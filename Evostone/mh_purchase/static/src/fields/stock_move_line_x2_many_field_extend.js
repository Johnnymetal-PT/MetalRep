/** @odoo-module **/

import { SMLX2ManyField } from "@stock/fields/stock_move_line_x2_many_field";
import { Domain } from "@web/core/domain";
import { _t } from "@web/core/l10n/translation";
import { patch } from "@web/core/utils/patch";

patch(SMLX2ManyField.prototype, {
    /**
     * Override onAdd() to add lot_base_name filter to domain
     */
    async onAdd({ context, editable } = {}) {
        if (!this.props.record.data.show_quant) {
            return super.onAdd(...arguments);
        }

        // Compute the quant offset from move lines quantity changes that were not saved yet.
        await this.updateDirtyQuantsData();

        context = {
            ...context,
            single_product: true,
            list_view_ref: "stock.view_stock_quant_tree_simple",
            search_default_on_hand: true,
            search_default_in_stock: true,
        };

        const productName = this.props.record.data.product_id[1];
        const title = _t("Add line: %s", productName);

        let domain = [
            ["product_id", "=", this.props.record.data.product_id[0]],
            ["location_id", "child_of", this.props.context.default_location_id],
        ];

        // ===== MH CUSTOMIZATION: Add lot_base_name filter =====
        // If lot_name exists (sales with lot), filter quants by lot_base_name
        if (this.props.record.data.lot_name) {
            domain.push(["lot_base_name", "=", this.props.record.data.lot_name]);
        }
        // ======================================================

        if (this.dirtyQuantsData.size) {
            const notFullyUsed = [];
            const fullyUsed = [];
            for (const [quantId, quantData] of this.dirtyQuantsData.entries()) {
                if (quantData.available_quantity > 0) {
                    notFullyUsed.push(quantId);
                } else {
                    fullyUsed.push(quantId);
                }
            }
            if (fullyUsed.length) {
                domain = Domain.and([domain, [["id", "not in", fullyUsed]]]).toList();
            }
            if (notFullyUsed.length) {
                domain = Domain.or([domain, [["id", "in", notFullyUsed]]]).toList();
            }
        }

        return this.selectCreate({ domain, context, title });
    },

    /**
     * Override selectRecord() to auto-fill dimensions from quant
     */
    async selectRecord(res_ids) {
        const demand =
            this.props.record.data.product_uom_qty -
            this.props.record.data.move_line_ids.records
                .map((ml) => ml.data.quantity)
                .reduce((val, sum) => val + sum, 0);

        const params = {
            context: { default_quant_id: res_ids[0] },
        };

        if (demand <= 0) {
            params.context.default_quantity = 0;
        } else if (this.dirtyQuantsData.has(res_ids[0])) {
            params.context.default_quantity = Math.min(
                this.dirtyQuantsData.get(res_ids[0]).available_quantity,
                demand
            );
        }

        // ===== MH CUSTOMIZATION: Auto-fill dimensions from quant =====
        // If product has dimensions (product_form != 'none'), fetch quant data
        if (res_ids[0] && this.props.record.data.product_id) {
            try {
                // Fetch product and quant data
                const productId = this.props.record.data.product_id[0];
                const productData = await this.orm.read(
                    "product.product",
                    [productId],
                    ["product_form"]
                );

                const productForm = productData && productData.length > 0
                    ? productData[0].product_form
                    : 'none';

                console.log("[MH] Product form:", productForm);

                if (productForm && productForm !== 'none') {
                    // Fetch quant dimensions
                    const quantData = await this.orm.read(
                        "stock.quant",
                        [res_ids[0]],
                        ["length", "width", "thickness", "available_quantity"]
                    );

                    console.log("[MH] Quant data:", quantData);

                    if (quantData && quantData.length > 0) {
                        const quant = quantData[0];

                        // Set default dimensions from quant
                        if (quant.length) {
                            params.context.default_length = quant.length;
                        }
                        if (quant.width) {
                            params.context.default_width = quant.width;
                        }
                        if (quant.thickness) {
                            params.context.default_thickness = quant.thickness;
                        }

                        // Override quantity with quant's available quantity
                        if (quant.available_quantity !== undefined) {
                            params.context.default_quantity = quant.available_quantity;
                        }

                        console.log("[MH] Dimensions and quantity set:", {
                            length: quant.length,
                            width: quant.width,
                            thickness: quant.thickness,
                            quantity: params.context.default_quantity,
                            available_quantity: quant.available_quantity
                        });
                    }
                }
            } catch (error) {
                console.error("[MH] Error fetching quant dimensions:", error);
            }
        }
        // ============================================================

        this.list.addNewRecord(params).then((record) => {
            // Make it dirty to force the save of the record
            record.dirty = true;
        });
    }
});
