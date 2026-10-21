"""Ecra de definicoes do Hiper Sync (Definicoes > Hiper Sync).

Expoe as chaves de API e flags globais armazenadas como ``ir.config_parameter``
(prefixo ``hiper_sync.``) para os utilizadores nao terem de mexer em parametros
tecnicos.
"""

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Ponte UI <-> ``ir.config_parameter`` para opcoes do Hiper Sync."""

    _inherit = "res.config.settings"

    hiper_sync_stock_location_id = fields.Many2one(
        "stock.location",
        string="Legacy Sync Stock Location",
        domain=[("usage", "=", "internal")],
        config_parameter="hiper_sync.stock_location_id",
        help="Legacy setting kept for backwards compatibility. The PG supplier stock flow now synchronizes supplier availability on the product instead of creating internal quants.",
    )
    hiper_sync_disable_out_of_stock = fields.Boolean(
        string="Disable Products When Total Sellable Qty Is Zero",
        config_parameter="hiper_sync.disable_out_of_stock",
        default=True,
        help="If enabled, products are unpublished/disabled only when internal stock plus supplier availability is zero.",
    )
    hiper_sync_publish_zero_price = fields.Boolean(
        string="Publish Zero Price Products",
        config_parameter="hiper_sync.publish_zero_price",
        default=False,
        help="Allow products with zero price to remain active/published after sync.",
    )
    hiper_sync_translate_openai_api_key = fields.Char(
        string="OpenAI API Key",
        config_parameter="hiper_sync.translate_openai_api_key",
        help="Global OpenAI API key used for AI translation when vendors do not override the key.",
    )
    hiper_sync_translate_google_api_key = fields.Char(
        string="Google Translate API Key",
        config_parameter="hiper_sync.translate_google_api_key",
        help="Global Google Cloud Translation API key used when vendors select Google Translate.",
    )
    hiper_sync_translate_openai_model = fields.Char(
        string="OpenAI Model",
        config_parameter="hiper_sync.translate_openai_model",
        default="gpt-4.1-mini",
        help="Default OpenAI model used for AI translation, for example gpt-4.1-mini.",
    )
    hiper_sync_remote_crawler_upload_token = fields.Char(
        string="Remote Crawler Upload Token",
        config_parameter="hiper_sync.remote_crawler_upload_token",
        help="Shared secret used by the external crawler bot when uploading generated CSV files back into Odoo.",
    )
