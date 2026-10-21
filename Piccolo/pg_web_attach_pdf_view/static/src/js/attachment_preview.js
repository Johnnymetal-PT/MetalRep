odoo.define('pg_attach_pdf_view.attachment_preview', function (require) {
    "use strict";

    var publicWidget = require('web.public.widget');

    publicWidget.registry.AttachmentPreview = publicWidget.Widget.extend({
        selector: '.oe_website_sale',
        events: {
            'click a.attachment-link': '_onAttachmentClick',
        },

        _onAttachmentClick: function (ev) {
            ev.preventDefault();
            var $link = $(ev.currentTarget);
            var url = $link.attr('href') + '?download=false';
            window.open(url, '_blank');
        },
    });

    return publicWidget.registry.AttachmentPreview;
});
