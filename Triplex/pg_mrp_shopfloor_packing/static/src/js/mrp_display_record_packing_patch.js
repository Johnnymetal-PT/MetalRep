/** @odoo-module **/
// Intercepta o fecho da produção no Shop Floor para obrigar o preenchimento do packing
// list do produto final. Cobre as duas vias de fecho:
//   - validate()              -> botão "Close Production" no cartão da produção
//   - onClickCloseProduction() -> botão verde "Fechar produção" no cartão da operação
// Se o operador cancelar o diálogo, a produção não fecha. Ver o __manifest__.py.

import { patch } from "@web/core/utils/patch";
import { MrpDisplayRecord } from "@mrp_workorder/mrp_display/mrp_display_record";
import { PgPackingListDialog } from "@pg_mrp_shopfloor_packing/js/packing_dialog";

patch(MrpDisplayRecord.prototype, {
    _pgFinishedProductId() {
        const product = this.props.production?.data?.product_id;
        if (Array.isArray(product)) {
            return product[0];
        }
        return product || false;
    },

    _pgEnsurePackingFilled() {
        const productId = this._pgFinishedProductId();
        if (!productId) {
            // Sem produto final identificável: não bloquear o fecho.
            return Promise.resolve(true);
        }
        return new Promise((resolve) => {
            let confirmed = false;
            this.dialog.add(
                PgPackingListDialog,
                {
                    productId,
                    // As fotografias da embalagem ficam na ordem de fabrico, não no produto.
                    // Ver `models/mrp_production.py` para a razão.
                    productionId: this.props.production?.resId || undefined,
                    onConfirm: () => {
                        confirmed = true;
                        resolve(true);
                    },
                },
                {
                    onClose: () => {
                        if (!confirmed) {
                            resolve(false);
                        }
                    },
                }
            );
        });
    },

    async validate() {
        if (this.resModel === "mrp.production") {
            const ok = await this._pgEnsurePackingFilled();
            if (!ok) {
                return;
            }
        }
        return super.validate(...arguments);
    },

    async onClickCloseProduction() {
        const ok = await this._pgEnsurePackingFilled();
        if (!ok) {
            return;
        }
        return super.onClickCloseProduction(...arguments);
    },
});
