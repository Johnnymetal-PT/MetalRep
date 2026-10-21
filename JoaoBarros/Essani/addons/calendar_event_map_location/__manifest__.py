# -*- coding: utf-8 -*-
{
    "name": "Calendar Map Location",
    "summary": "Allow calendar map view to use the event location when geocoding",
    "version": "19.0.1.0.0",
    "category": "Hidden",
    "license": "LGPL-3",
    "depends": ["calendar", "web_map"],
    "assets": {
        "web.assets_backend": [
            "calendar_event_map_location/static/src/js/map_view_lazy_loader.js",
        ],
    },
    "installable": True,
    "application": False,
}
