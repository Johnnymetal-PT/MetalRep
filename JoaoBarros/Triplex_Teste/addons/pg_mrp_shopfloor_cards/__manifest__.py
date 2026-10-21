{
    "name": "PG MRP Shop Floor Cards",
    "summary": "Customize Shop Floor cards with origin and binary previews",
    "version": "17.0.1.0.0",
    "category": "Manufacturing",
    "depends": ["mrp_workorder", "web"],
    "data": [
        "views/mrp_production_search_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "pg_mrp_shopfloor_cards/static/src/js/preview_dialog.js",
            "pg_mrp_shopfloor_cards/static/src/js/mrp_display_action_patch.js",
            "pg_mrp_shopfloor_cards/static/src/js/mrp_display_patch.js",
            "pg_mrp_shopfloor_cards/static/src/js/mrp_display_record_patch.js",
            "pg_mrp_shopfloor_cards/static/src/xml/preview_dialog.xml",
            "pg_mrp_shopfloor_cards/static/src/xml/mrp_display_record.xml",
            "pg_mrp_shopfloor_cards/static/src/scss/mrp_display_record.scss"
        ]
    },
    "license": "LGPL-3",
    "installable": True,
    "application": False
}
