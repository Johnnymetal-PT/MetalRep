{
    'name': 'QR Code Contact Scanner',
    'version': '1.0',
    'category': 'Tools',
    'summary': 'Scan vCard QR code to create contact',
    'depends': ['base', 'web'],
    'data': [
        #'views/res_partner_view.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'pg_qrcode/static/src/js/qr_scanner.js',
            #'https://unpkg.com/html5-qrcode@2.3.7/html5-qrcode.min.js',
            'pg_qrcode/static/lib/html5-qrcode.min.js',
        ],
    },
    'installable': True,
    'application': False,
}

