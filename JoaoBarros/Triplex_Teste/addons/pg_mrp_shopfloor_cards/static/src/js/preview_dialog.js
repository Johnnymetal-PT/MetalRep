/** @odoo-module **/

import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";

const ZOOM_STEP = 0.25;
const MIN_ZOOM = 0.25;
const MAX_ZOOM = 5;

export class PgMrpBinaryPreviewDialog extends Component {
    static template = "pg_mrp_shopfloor_cards.BinaryPreviewDialog";
    static components = { Dialog };
    static props = {
        close: Function,
        title: { type: String, optional: true },
        mode: String,
        src: String,
    };

    setup() {
        this.state = useState({ zoom: 1 });
    }

    get isImageMode() {
        return this.props.mode === "image";
    }

    get imageStyle() {
        return `transform: scale(${this.state.zoom}); transform-origin: top left;`;
    }

    get zoomLabel() {
        return _t("%s%%", Math.round(this.state.zoom * 100));
    }

    zoomIn() {
        this.state.zoom = Math.min(MAX_ZOOM, +(this.state.zoom + ZOOM_STEP).toFixed(2));
    }

    zoomOut() {
        this.state.zoom = Math.max(MIN_ZOOM, +(this.state.zoom - ZOOM_STEP).toFixed(2));
    }

    resetZoom() {
        this.state.zoom = 1;
    }

    onWheel(ev) {
        if (!this.isImageMode || !ev.ctrlKey) {
            return;
        }
        ev.preventDefault();
        if (ev.deltaY < 0) {
            this.zoomIn();
        } else {
            this.zoomOut();
        }
    }
}
