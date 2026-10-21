/** @odoo-module **/

// Abre anexos de produto em nova aba apos validar permissao de leitura no website.

import publicWidget from "@web/legacy/js/public/public_widget";
import { _t } from "@web/core/l10n/translation";

function buildPreviewURL(anchor) {
    const url = new URL(anchor.href, window.location.origin);
    url.searchParams.set("download", "false");
    return url.toString();
}

async function checkAttachmentAccessible(url) {
    try {
        const response = await fetch(url, {
            method: "HEAD",
            credentials: "same-origin",
        });
        if (response.ok) {
            return true;
        }
        // Some controllers may not support HEAD requests. Try a lightweight GET
        if (response.status === 405 || response.status === 501) {
            const getResponse = await fetch(url, {
                method: "GET",
                credentials: "same-origin",
                headers: {
                    "X-Requested-With": "XMLHttpRequest",
                },
            });
            return getResponse.ok;
        }
        return false;
    } catch (error) {
        return false;
    }
}

publicWidget.registry.AttachmentPreview = publicWidget.Widget.extend({
    selector: ".oe_website_sale",
    events: {
        "click a.attachment-link": "_onAttachmentClick",
    },

    async _onAttachmentClick(ev) {
        ev.preventDefault();
        const url = buildPreviewURL(ev.currentTarget);
        const accessible = await checkAttachmentAccessible(url);
        if (accessible) {
            window.open(url, "_blank", "noopener,noreferrer");
        } else {
            window.alert(_t("You do not have permission to view this attachment."));
        }
    },
});

export default publicWidget.registry.AttachmentPreview;
