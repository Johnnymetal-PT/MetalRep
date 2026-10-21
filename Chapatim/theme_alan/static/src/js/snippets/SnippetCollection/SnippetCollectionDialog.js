import { _t } from "@web/core/l10n/translation";
import { Component, useState } from "@odoo/owl";
import { Dialog } from "@web/core/dialog/dialog";

export class CollectionDialog extends Component {
    static template = "theme_alan.CollectionDialog";
    static components = { Dialog };
    static props = {
        close: Function,
        onSave: Function,
        onPageSave: { type: Function, optional: true },
        defaultName: { type: String, optional: true },
        existingNames: { type: Array, optional: true },
    };

    setup() {
        this.state = useState({
            name: this.props.defaultName || "",
        });
    }

    async _onSaveToPage() {
        if (this.props.onPageSave) {
            await this.props.onPageSave();
        }
        this.props.close();
    }

    get isDuplicate() {
        const names = this.props.existingNames || [];
        return names.map(n => n.toLowerCase()).includes(this.state.name.trim().toLowerCase());
    }

    async _onSave() {
        if (!this.state.name.trim() || this.isDuplicate) {
            return;
        }
        await this.props.onSave(this.state.name);
        this.props.close();
    }
}

export class DeleteConfirmDialog extends Component {
    static template = "theme_alan.DeleteConfirmDialog";
    static components = { Dialog };
    static props = {
        close: Function,
        onConfirm: Function,
        collectionName: { type: String, optional: true },
    };

    async _onConfirm() {
        await this.props.onConfirm();
        this.props.close();
    }

    _onCancel() {
        this.props.close();
    }
}