odoo.define('pg_attach_pdf_view.attachment_preview', function (require) {
    "use strict";

    var publicWidget = require('web.public.widget');

    publicWidget.registry.AttachmentPreview = publicWidget.Widget.extend({
        selector: '.oe_website_sale',
        events: {
            'click a.attachment-link': '_onAttachmentClick',
        },

        _onAttachmentClick: function (ev) {
            ev.preventDefault();s
            var $link = $(ev.currentTarget);
            var url = $link.attr('href') + '?download=false';

            $.ajax({
                url: url,
                type: 'GET',
                success: function() {
                    window.open(url, '_blank');
                },
                error: function() {
                    alert('You do not have permission to view this attachment.');
                }
            });
        },
    });

    return publicWidget.registry.AttachmentPreview;
});
