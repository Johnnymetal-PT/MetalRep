/** @odoo-module **/

import { browser } from "@web/core/browser/browser";
import { patch } from "@web/core/utils/patch";
import { FormController } from "@web/views/form/form_controller";
import { onMounted, onPatched, onWillUnmount } from "@odoo/owl";

const ACTIVE_STATES = new Set(["queued", "running"]);
const REFRESH_DELAY_MS = 3000;

patch(FormController.prototype, {
    setup() {
        super.setup();
        this._hiperSyncRefreshTimer = null;

        const syncRefreshTimer = () => {
            this._scheduleHiperSyncRefresh();
        };

        onMounted(syncRefreshTimer);
        onPatched(syncRefreshTimer);
        onWillUnmount(() => this._clearHiperSyncRefresh());
    },

    _isHiperSyncRunForm() {
        return this.props?.resModel === "hiper.sync.run";
    },

    _getHiperSyncRunState() {
        return this.model?.root?.data?.state || null;
    },

    _clearHiperSyncRefresh() {
        if (this._hiperSyncRefreshTimer) {
            browser.clearTimeout(this._hiperSyncRefreshTimer);
            this._hiperSyncRefreshTimer = null;
        }
    },

    _scheduleHiperSyncRefresh() {
        this._clearHiperSyncRefresh();
        if (!this._isHiperSyncRunForm()) {
            return;
        }
        if (!ACTIVE_STATES.has(this._getHiperSyncRunState())) {
            return;
        }
        this._hiperSyncRefreshTimer = browser.setTimeout(() => {
            if (!this._isHiperSyncRunForm()) {
                return;
            }
            if (!ACTIVE_STATES.has(this._getHiperSyncRunState())) {
                return;
            }
            browser.location.reload();
        }, REFRESH_DELAY_MS);
    },
});
