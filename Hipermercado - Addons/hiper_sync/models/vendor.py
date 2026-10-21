"""Modelo central de fornecedor para o Hiper Sync.

Cada registo de ``hiper.sync.vendor`` representa um fornecedor real
(Eldisser, Sorefoz, etc.) e concentra:

* credenciais e configuracao da fonte de dados (``source_kind``),
* mapeamento de categorias e regras de margem (``category_map_ids``),
* parametros de traducao (provider, chave, idiomas, termos protegidos),
* configuracao do crawler remoto (URLs, token, horario, freshness),
* estado da ultima execucao (``last_sync_at``, ``last_sync_status``).

Pontos de atencao:
    * ``code`` e o identificador estavel usado por ``services.vendor_adapters``
      para descobrir o adapter Python certo -- nao renomear sem migracao.
    * O modulo executa ``self.env.cr.commit()`` em pontos criticos (apos
      disparar o cron, apos cada checkpoint do crawler remoto) para nao
      perder estado em caso de timeout do worker.
"""

import logging
import time
import uuid
from datetime import timedelta
from urllib.parse import urljoin

import requests

from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..services.publisher import HiperPublisher
from ..services.pg_term_discovery import PgTermDiscoveryService
from ..services.translate import build_translation_service
from ..services.utils import clean_html_text, parse_json
from ..services.vendor_adapters import get_adapter

_logger = logging.getLogger(__name__)


class HiperSyncVendor(models.Model):
    """Ficha de fornecedor sincronizavel.

    Combina configuracao da fonte (FTP/HTTP/JSON/crawler), regras comerciais
    (margens por categoria) e estado de execucao (heartbeats do crawler,
    diagnostico do ultimo preview). E uma chat-record (``mail.thread``) para
    deixar registo das execucoes manuais no chatter.
    """

    _name = "hiper.sync.vendor"
    _description = "Hiper Supplier"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "name, id"
    # Job sem heartbeat > 90 min e considerado parado (override por field).
    _pg_remote_crawler_stale_timeout_minutes = 90
    # Janela usada para considerar que ainda existe job remoto "recente"
    # antes de pedir status forcado.
    _pg_remote_crawler_recent_job_window_minutes = 180

    name = fields.Char(
        required=True,
        tracking=True,
        help="Internal supplier name shown in Odoo. Use the commercial supplier name, for example Eldisser or Sorefoz.",
    )
    code = fields.Char(
        required=True,
        index=True,
        help="Stable technical code used by the sync logic. Keep the original Prestashop-style code unless there is a reason to change it.",
    )
    active = fields.Boolean(help="Archive this supplier record without deleting its configuration.")
    sync_active = fields.Boolean(
        default=True,
        tracking=True,
        help="If disabled, this supplier is ignored by manual and scheduled sync runs.",
    )
    source_kind = fields.Selection(
        [
            ("ftp_csv", "FTP CSV"),
            ("csv_url", "CSV URL"),
            ("json_url", "JSON URL"),
            ("crawler_csv", "Crawler CSV"),
            ("local_csv", "Local CSV"),
        ],
        required=True,
        help=(
            "How this supplier feed is obtained.\n"
            "FTP CSV: supplier gives an FTP login and a CSV filename.\n"
            "CSV URL: supplier or external crawler gives a direct CSV download URL.\n"
            "JSON URL: supplier exposes a JSON API endpoint.\n"
            "Crawler CSV: legacy local crawler mode.\n"
            "Local CSV: read a CSV file from a local path."
        ),
    )
    supplier_partner_id = fields.Many2one(
        "res.partner",
        domain=[("supplier_rank", ">", 0)],
        help="Vendor partner in Odoo used for supplierinfo records. If left empty, sync will create or reuse one.",
    )
    product_default_active = fields.Boolean(
        default=True,
        help="Default active state applied to newly created products from this supplier before stock/price publish rules run.",
    )
    ignore_out_of_stock_products = fields.Boolean(
        help="If enabled, products with supplier quantity 0 are unpublished/disabled during sync."
    )
    publish_to_website = fields.Boolean(
        default=True,
        help="If enabled, synced products can be published on the website when stock and price rules allow it.",
    )
    translate_enabled = fields.Boolean(
        help="Translate imported supplier text into Portuguese during sync."
    )
    translate_provider = fields.Selection(
        [
            ("google", "Google Translate"),
            ("openai", "OpenAI"),
        ],
        default="openai",
        help="Translation backend used for this supplier. OpenAI is safer for preserving protected terms and product context.",
    )
    translate_api_key = fields.Char(
        help="Optional vendor-specific override key. Usually leave empty and use the global key in Settings."
    )
    translate_ai_model = fields.Char(
        help="Optional vendor-specific AI model override. Example: gpt-4.1-mini."
    )
    translate_source_lang = fields.Char(
        default="es",
        help="Source language code from the supplier feed, for example es or en.",
    )
    translate_target_lang = fields.Char(
        default="pt",
        help="Target language code written into Odoo products. Usually pt.",
    )
    translate_protected_terms = fields.Text(
        help="One protected term per line. Use this for brand names, model codes, or terms that must never be translated."
    )
    pg_translate_discovery_query = fields.Char(
        help="Seed query for auto-discovery of protected terms. Example: Smartphones or Star Wars."
    )
    pg_translate_discovery_mode = fields.Selection(
        [
            ("heuristic", "Heuristic (Wikipedia/Wikidata)"),
            ("gtin", "GTIN only (requires setup)"),
            ("both", "Heuristic + GTIN"),
        ],
        default="heuristic",
        help="How protected terms should be discovered for this supplier.",
    )
    pg_translate_discovery_preset = fields.Selection(
        [
            ("", "None"),
            ("tv", "TV / Televisores"),
            ("smartphones", "Smartphones"),
            ("kitchen", "Kitchen Appliances"),
            ("tech", "Tech Appliances"),
            ("pg_informatica", "INFORMÁTICA"),
            ("pg_informatica_portateis", "INFORMÁTICA > Portáteis"),
            ("pg_informatica_monitores", "INFORMÁTICA > Monitores"),
            ("pg_informatica_perifericos", "INFORMÁTICA > Periféricos"),
            ("pg_informatica_impressoras", "INFORMÁTICA > Impressoras"),
            ("pg_informatica_consumiveis_impressao", "INFORMÁTICA > Consumíveis Impressão Originais"),
            ("pg_informatica_cadeiras_gaming", "INFORMÁTICA > Cadeiras Gaming"),
            ("pg_informatica_teclados_gaming", "INFORMÁTICA > Teclados Gaming"),
            ("pg_informatica_ratos_gaming", "INFORMÁTICA > Ratos Gaming"),
            ("pg_informatica_auscultadores_gaming", "INFORMÁTICA > Auscultadores Gaming"),
            ("pg_informatica_tapetes_gaming", "INFORMÁTICA > Tapetes Gaming"),
            ("pg_informatica_consolas", "INFORMÁTICA > Consolas"),
            ("pg_eletrodomesticos", "ELETRODOMÉSTICOS"),
            ("pg_eletro_maquinas_lavar_roupa", "ELETRODOMÉSTICOS > Máquinas de Lavar Roupa"),
            ("pg_eletro_combinados", "ELETRODOMÉSTICOS > Combinados"),
            ("pg_eletro_placas", "ELETRODOMÉSTICOS > Placas"),
            ("pg_eletro_micro_ondas", "ELETRODOMÉSTICOS > Micro-Ondas"),
            ("pg_eletro_lavar_secar_roupa", "ELETRODOMÉSTICOS > Máquinas de Lavar e Secar Roupa"),
            ("pg_eletro_frigorificos", "ELETRODOMÉSTICOS > Frigoríficos"),
            ("pg_eletro_fogoes", "ELETRODOMÉSTICOS > Fogões"),
            ("pg_eletro_tratamento_aguas", "ELETRODOMÉSTICOS > Tratamento de Águas"),
            ("pg_eletro_secar_roupa", "ELETRODOMÉSTICOS > Máquinas de Secar Roupa"),
            ("pg_eletro_side_by_side", "ELETRODOMÉSTICOS > Frigoríficos Side By Side"),
            ("pg_eletro_maquinas_cafe", "ELETRODOMÉSTICOS > Máquinas de Café"),
            ("pg_eletro_climatizacao", "ELETRODOMÉSTICOS > Climatização / Tratamento do Ar"),
            ("pg_eletro_tratamento_roupa", "ELETRODOMÉSTICOS > Tratamento de Roupa"),
            ("pg_eletro_arcas", "ELETRODOMÉSTICOS > Arcas Frigoríficas"),
            ("pg_eletro_preparacao_alimentar", "ELETRODOMÉSTICOS > Preparação Alimentar"),
            ("pg_eletro_lava_loicas_misturadoras", "ELETRODOMÉSTICOS > Lava Loiças / Misturadoras"),
            ("pg_eletro_cuidados_lar", "ELETRODOMÉSTICOS > Cuidados do Lar"),
            ("pg_eletro_lavar_louca", "ELETRODOMÉSTICOS > Máquinas de Lavar Louça"),
            ("pg_eletro_exaustores", "ELETRODOMÉSTICOS > Exaustores"),
            ("pg_eletro_cuidados_pessoais", "ELETRODOMÉSTICOS > Cuidados Pessoais"),
            ("pg_eletro_fornos", "ELETRODOMÉSTICOS > Fornos"),
            ("pg_eletro_hotelaria", "ELETRODOMÉSTICOS > Hotelaria / Industria"),
            ("pg_imagem_som", "IMAGEM E SOM"),
            ("pg_imagem_som_televisores", "IMAGEM E SOM > Televisores"),
            ("pg_imagem_som_videoprojetores", "IMAGEM E SOM > Videoprojetores"),
            ("pg_imagem_som_home_cinema", "IMAGEM E SOM > Home Cinema"),
            ("pg_imagem_som_home_audio", "IMAGEM E SOM > Home Audio"),
            ("pg_imagem_som_acessorios_tv", "IMAGEM E SOM > Acessórios TV"),
            ("pg_imagem_som_car_audio", "IMAGEM E SOM > Car Áudio/Multimédia"),
            ("pg_espaco_crianca", "ESPAÇO CRIANÇA"),
            ("pg_espaco_crianca_carros_eletricos", "ESPAÇO CRIANÇA > Carros Elétricos"),
            ("pg_espaco_crianca_motas_eletricas", "ESPAÇO CRIANÇA > Motas Elétricas"),
            ("pg_espaco_crianca_piscinas", "ESPAÇO CRIANÇA > Piscinas"),
            ("pg_espaco_crianca_brinquedos_exterior", "ESPAÇO CRIANÇA > Brinquedos de Exterior"),
            ("pg_geek_zone", "GEEK ZONE"),
            ("pg_geek_funko", "GEEK ZONE > Funko"),
            ("pg_geek_disney", "GEEK ZONE > Disney"),
            ("pg_geek_anime_manga", "GEEK ZONE > Anime / Manga"),
            ("pg_geek_series_tv", "GEEK ZONE > Series de TV"),
            ("pg_geek_filmes", "GEEK ZONE > Filmes"),
            ("pg_geek_super_herois", "GEEK ZONE > Super Heróis"),
            ("pg_geek_jogos_brinquedos", "GEEK ZONE > Jogos / Brinquedos"),
            ("pg_geek_videojogos", "GEEK ZONE > Videojogos"),
            ("pg_geek_pre_reservas", "GEEK ZONE > Pré-Reservas"),
            ("pg_mobilidade", "MOBILIDADE"),
            ("pg_mobilidade_smartphones", "MOBILIDADE > Smartphones"),
            ("pg_mobilidade_smartwatch", "MOBILIDADE > Smartwatch / Wearables"),
            ("pg_mobilidade_trotinetes", "MOBILIDADE > Trotinetes"),
            ("pg_mobilidade_acessorios_telemovel", "MOBILIDADE > Acessórios Telemóvel"),
            ("pg_outlet_hot", "OUTLET HOT"),
            ("pg_ofertas_flash_hot", "OFERTAS FLASH HOT"),
        ],
        default="",
        help="Optional product category preset that seeds relevant technical terms and search queries.",
    )
    pg_translate_discovery_last_run_at = fields.Datetime(readonly=True)
    pg_translate_discovery_status = fields.Selection(
        [
            ("idle", "Idle"),
            ("done", "Done"),
            ("failed", "Failed"),
        ],
        default="idle",
        readonly=True,
    )
    pg_translate_discovery_log = fields.Text(readonly=True)
    default_categ_id = fields.Many2one(
        "product.category",
        string="Default Internal Category",
        help="Fallback Odoo internal category when no category map matches the supplier category.",
    )
    default_public_categ_id = fields.Many2one(
        "product.public.category",
        string="Default Website Category",
        help="Fallback website category when no category map matches the supplier category.",
    )

    ftp_host = fields.Char(help="FTP server hostname supplied by the vendor, for example ftp.vendor.com.")
    ftp_port = fields.Integer(default=21, help="FTP port. Usually 21 unless the vendor says otherwise.")
    ftp_user = fields.Char(help="FTP username given by the supplier.")
    ftp_password = fields.Char(help="FTP password given by the supplier.")
    remote_filename = fields.Char(
        help="Remote CSV filename or path on the supplier FTP server, for example products.csv."
    )

    feed_url = fields.Char(
        help=(
            "Direct CSV/HTTP feed URL. Use this for CSV URL suppliers or for a CSV generated by an external crawler. "
            "Ask the old admin or supplier for the direct file URL, not the public storefront homepage."
        )
    )
    api_url_template = fields.Char(
        help=(
            "API URL template for suppliers that use placeholders such as {_user_}, {_pass_}, {_apikey_}, "
            "{_userid_}, {_call_type_}, or {_type_}."
        )
    )
    username = fields.Char(help="Supplier API username or login.")
    password = fields.Char(help="Supplier API password.")
    api_key = fields.Char(help="Supplier API key when required.")
    username_id = fields.Char(
        string="Username ID",
        help="Extra supplier user id when the API requires both an id and a username.",
    )
    request_call_type = fields.Char(
        default="products",
        help="API call type inserted into the URL template when the supplier supports different endpoints.",
    )
    delimiter = fields.Char(
        default=";",
        help="CSV delimiter used by the supplier file. Common values are ; or ,.",
    )
    pg_adapter_mode = fields.Selection(
        [
            ("code", "Code Adapter"),
            ("generic", "Generic Mapping"),
        ],
        default="code",
        help=(
            "Code Adapter uses a supplier-specific Python adapter registered by supplier code. "
            "Generic Mapping uses the JSON configuration below so a new supplier can be onboarded from the UI."
        ),
    )
    pg_mapping_json = fields.Text(
        help=(
            "Generic supplier mapping JSON used when Adapter Mode is Generic Mapping. "
            "Typical keys are row_path, row_item_path, and field_map. "
            "Example: "
            '{"row_path":"Produtos","field_map":{"name_pt":["Nome","name"],'
            '"reference":["Referencia","sku"],"ean13":["EAN","barcode"],'
            '"unit_price":["Preco","price"],"quantity":{"path":"Stock","map":{"0":0,"1":2,"2":5}},'
            '"brand":["Marca.Valor","Marca"],"category":["Familia.Valor","Familia"],'
            '"sub_category":["SubFamilia.Valor","SubFamilia"],"description_pt":["Descricao","description"],'
            '"description_short_pt":["Resumo","short_description"],"images":{"path":["Imagem","images"],"split":","}}}'
        ),
    )

    # ----------------------------------------------------------------------
    # Crawler local legado (``source_kind = 'crawler_csv'``).
    # Mantido para suportar fornecedores antigos que ainda corram crawlers
    # no proprio host do Odoo. Para integracoes novas, preferir o modo
    # *Remote Crawler* (``source_kind = 'csv_url'`` + ``remote_crawler_*``)
    # que executa numa maquina dedicada e entrega o CSV via webhook seguro.
    # ----------------------------------------------------------------------
    crawler_workdir = fields.Char(help="Working directory where the legacy local crawler command should run.")
    crawler_command = fields.Char(help="Legacy local shell command that runs the crawler and generates a CSV.")
    crawler_output_path = fields.Char(help="Local file path to the crawler-generated CSV output.")
    crawler_env_text = fields.Text(
        help="Optional JSON object of environment variables passed to the legacy local crawler command."
    )
    remote_crawler_source_url = fields.Char(help="Website URL that the external crawler should crawl.")
    pg_remote_crawler_adapter_key = fields.Char(
        help="Optional crawler adapter key sent to the external bot, for example pg_mielectro."
    )
    pg_remote_crawler_login_url = fields.Char(
        help="Optional login URL for authenticated remote crawlers such as Eldisser B2B."
    )
    pg_remote_crawler_login_username = fields.Char(
        help="Optional login username sent to the remote crawler for authenticated supplier websites."
    )
    pg_remote_crawler_login_password = fields.Char(
        help="Optional login password sent to the remote crawler for authenticated supplier websites."
    )
    pg_remote_crawler_force_tienda_view = fields.Boolean(
        default=True,
        help="If enabled, the remote crawler is instructed to force the supplier website into Tienda/store view when supported."
    )
    remote_crawler_trigger_url = fields.Char(
        help="Webhook URL that starts the external crawler job, for example https://crawler.example.com/crawl/start."
    )
    remote_crawler_status_url = fields.Char(
        help="Status endpoint URL used to check the job result. You can use {job_id} as a placeholder."
    )
    remote_crawler_auth_token = fields.Char(
        help="Bearer token used to authenticate with the external crawler service."
    )
    remote_crawler_payload_json = fields.Text(
        help="Extra JSON payload sent to the remote crawler trigger endpoint."
    )
    remote_crawler_auto_refresh = fields.Boolean(
        default=True,
        help="Refresh remote crawler status before importing the CSV URL feed.",
    )
    pg_remote_crawler_trigger_time = fields.Char(
        help=(
            "Optional daily UTC time in HH:MM format used by the crawler prewarm cron. "
            "Example: 01:30 means Odoo should trigger the remote crawler after 01:30 UTC."
        )
    )
    pg_remote_crawler_max_age_minutes = fields.Integer(
        default=360,
        help=(
            "Maximum accepted age in minutes for the last ready remote crawler CSV. "
            "If the result is older, Odoo treats it as stale and triggers a fresh crawl."
        ),
    )
    pg_remote_crawler_stale_timeout_minutes = fields.Integer(
        default=0,
        help=(
            "Minutes without a status update before a running remote crawler job is marked stale. "
            "Set to 0 to disable stale marking and allow optional manual refresh."
        ),
    )
    remote_crawler_job_id = fields.Char(readonly=True, help="Last job id returned by the external crawler service.")
    remote_crawler_job_status = fields.Char(
        readonly=True,
        help="Last known status returned by the external crawler service, for example queued, running, or done.",
    )
    remote_crawler_result_url = fields.Char(
        readonly=True,
        help="Last CSV URL returned by the external crawler service. This is copied into Feed URL when available.",
    )
    remote_crawler_last_requested_at = fields.Datetime(
        readonly=True,
        help="When Odoo last triggered the external crawler job.",
    )
    remote_crawler_last_checked_at = fields.Datetime(
        readonly=True,
        help="When Odoo last checked the external crawler job status.",
    )
    remote_crawler_last_error = fields.Text(
        readonly=True,
        help="Last error returned while triggering or polling the external crawler service.",
    )
    pg_remote_crawler_result_ready_at = fields.Datetime(
        readonly=True,
        copy=False,
        help="When Odoo last received a ready CSV URL from the remote crawler for this supplier.",
    )
    pg_remote_crawler_last_scheduled_trigger_at = fields.Datetime(
        readonly=True,
        copy=False,
        help="When the scheduled crawler prewarm cron last triggered this supplier.",
    )
    pg_remote_crawler_visited_pages = fields.Integer(
        readonly=True,
        copy=False,
        help="Last known pages visited reported by the remote crawler job.",
    )
    pg_remote_crawler_discovered_products = fields.Integer(
        readonly=True,
        copy=False,
        help="Last known number of detected products reported by the remote crawler job.",
    )
    pg_remote_crawler_progress_note = fields.Char(
        readonly=True,
        copy=False,
        help="Last progress note returned by the remote crawler job while it is running.",
    )

    extra_config_json = fields.Text(
        help="Advanced JSON options for special supplier behaviors. Leave empty unless you know a supplier-specific option is needed."
    )
    last_sync_at = fields.Datetime(readonly=True, help="When this supplier was last synced or previewed.")
    last_sync_status = fields.Selection(
        [
            ("idle", "Idle"),
            ("running", "Running"),
            ("done", "Done"),
            ("failed", "Failed"),
        ],
        default="idle",
        readonly=True,
        help="Last recorded sync state for this supplier.",
    )
    last_sync_message = fields.Text(
        readonly=True,
        help="Short result message from the last sync, preview, or validation attempt.",
    )
    category_map_ids = fields.One2many("hiper.sync.category.map", "vendor_id")

    _sql_constraints = [
        ("hiper_sync_vendor_code_unique", "unique(code)", "Supplier code must be unique."),
    ]

    @api.constrains("pg_remote_crawler_trigger_time")
    def _check_pg_remote_crawler_trigger_time(self):
        for vendor in self:
            vendor._parse_pg_remote_crawler_trigger_time(raise_if_invalid=True)

    def _get_or_create_supplier_partner(self):
        self.ensure_one()
        if self.supplier_partner_id:
            return self.supplier_partner_id
        partner = self.env["res.partner"].search([("name", "=", self.name), ("supplier_rank", ">", 0)], limit=1)
        if not partner:
            partner = self.env["res.partner"].create(
                {
                    "name": self.name,
                    "supplier_rank": 1,
                    "company_type": "company",
                }
            )
        self.supplier_partner_id = partner
        return partner

    def _get_target_categories_for_row(self, row):
        self.ensure_one()
        internal = False
        public_categories = self.env["product.public.category"]
        explicit_mapping_found = False
        for kind in ("category", "sub_category"):
            mapping = self._find_category_mapping_for_row(row, kind)
            if mapping:
                explicit_mapping_found = True
                if mapping.target_categ_id:
                    internal = mapping.target_categ_id
                if mapping.target_public_categ_id:
                    public_categories |= mapping.target_public_categ_id
        if not explicit_mapping_found:
            internal, public_categories = self._auto_create_categories_for_row(row, public_categories)
        if not internal:
            internal = self.default_categ_id
        if not public_categories and self.default_public_categ_id:
            public_categories = self.default_public_categ_id
        return internal, public_categories

    def _auto_create_categories_for_row(self, row, public_categories):
        self.ensure_one()
        internal = False
        category_name = clean_html_text(row.get("category") or "")
        sub_category_name = clean_html_text(row.get("sub_category") or "")
        if category_name and sub_category_name and category_name.casefold() == sub_category_name.casefold():
            sub_category_name = ""

        internal_parent = self._get_auto_create_internal_category_parent()
        if internal_parent and category_name:
            category = self._get_or_create_internal_category(category_name, internal_parent)
            internal = category
            if sub_category_name:
                internal = self._get_or_create_internal_category(sub_category_name, category)

        if category_name:
            public_parent = self.default_public_categ_id
            public_category = self._get_or_create_public_category(category_name, public_parent)
            public_categories |= public_category
            if sub_category_name:
                public_sub_category = self._get_or_create_public_category(sub_category_name, public_category)
                public_categories |= public_sub_category

        return internal, public_categories

    def _get_auto_create_internal_category_parent(self):
        self.ensure_one()
        if self.default_categ_id:
            return self.default_categ_id
        category = self.env.ref("product.product_category_all", raise_if_not_found=False)
        if category:
            return category
        return self.env["product.category"].search([("parent_id", "=", False)], order="id asc", limit=1)

    def _get_or_create_internal_category(self, name, parent):
        name = clean_html_text(name)
        if not name:
            return parent
        ProductCategory = self.env["product.category"]
        category = ProductCategory.search(
            [("name", "=", name), ("parent_id", "=", parent.id)],
            limit=1,
        )
        if not category:
            category = ProductCategory.create(
                {
                    "name": name,
                    "parent_id": parent.id,
                }
            )
        return category

    def _get_or_create_public_category(self, name, parent):
        name = clean_html_text(name)
        if not name:
            return parent
        PublicCategory = self.env["product.public.category"]
        domain = [("name", "=", name)]
        if parent:
            domain.append(("parent_id", "=", parent.id))
        else:
            domain.append(("parent_id", "=", False))
        category = PublicCategory.search(domain, limit=1)
        if not category:
            values = {"name": name}
            if parent:
                values["parent_id"] = parent.id
            category = PublicCategory.create(values)
        return category

    def _compute_price_for_row(self, row):
        """Calcula o preco final de venda a partir do preco de custo do feed.

        Regra: ``preco_final = (custo - desconto_origem) + acrescimo``, onde
        ``acrescimo = shipping + (shipping + custo) * (margin + extra_margin) / 100``.
        Procura mapeamento na ``category`` e na ``sub_category`` e usa o que der
        maior acrescimo (favorece a regra mais especifica quando ambas existem).
        """
        self.ensure_one()
        final_price = float(row.get("unit_price") or 0.0)
        if not final_price:
            return 0.0

        def get_increment(kind):
            mapping = self._find_category_mapping_for_row(row, kind)
            if not mapping:
                return 0.0, 0.0
            shipping = float(mapping.shipping_cost or 0.0)
            margin = float(mapping.margin_percent or 0.0)
            extra_margin = float(mapping.extra_margin_percent or 0.0)
            origin_discount = float(mapping.origin_discount_percent or 0.0)
            discount_from_base = final_price - (final_price * ((100 - origin_discount) / 100))
            increment = shipping + ((shipping + final_price) * ((margin + extra_margin) / 100))
            return increment, discount_from_base

        category_increment, category_discount = get_increment("category")
        sub_increment, sub_discount = get_increment("sub_category")

        increment = category_increment
        discount = category_discount
        if sub_increment > increment:
            increment = sub_increment
            discount = sub_discount
        return (final_price - discount) + increment

    def _find_category_mapping_for_row(self, row, kind):
        self.ensure_one()
        candidates = []
        for value in (row.get(kind), row.get("_origin_%s" % kind)):
            cleaned = (value or "").strip() if isinstance(value, str) else value
            if not cleaned or cleaned in candidates:
                continue
            candidates.append(cleaned)
        for candidate in candidates:
            mapping = self.category_map_ids.filtered(
                lambda item: item.active and item.kind == kind and item.origin_name == candidate
            )[:1]
            if mapping:
                return mapping
        return False

    def _translate_row_text_fields(self, rows, translator):
        self.ensure_one()
        translated_fields = ("name_pt", "description_pt", "description_short_pt", "category", "sub_category")
        source_map = {
            "name_pt": "name",
            "description_pt": "description",
            "description_short_pt": "description_short",
        }
        for row in rows:
            if row.get("category") and "_origin_category" not in row:
                row["_origin_category"] = row.get("category")
            if row.get("sub_category") and "_origin_sub_category" not in row:
                row["_origin_sub_category"] = row.get("sub_category")
            for field_name in translated_fields:
                source_key = source_map.get(field_name, field_name)
                source_value = row.get(field_name) or row.get(source_key)
                if not source_value:
                    _logger.debug(
                        "Vendor %s translation skip field=%s reason=empty source_key=%s ref=%s ean=%s",
                        self.code,
                        field_name,
                        source_key,
                        row.get("reference"),
                        row.get("ean13"),
                    )
                    continue
                translated_value = translator.translate(
                    source_value,
                    field_name=field_name,
                    context=self._translation_context_for_row(row),
                )
                row[field_name] = translated_value
                if translated_value.strip() == str(source_value).strip():
                    _logger.info(
                        "Vendor %s translation unchanged field=%s ref=%s ean=%s",
                        self.code,
                        field_name,
                        row.get("reference"),
                        row.get("ean13"),
                    )
                else:
                    _logger.info(
                        "Vendor %s translation applied field=%s ref=%s ean=%s",
                        self.code,
                        field_name,
                        row.get("reference"),
                        row.get("ean13"),
                    )

    def _fetch_normalized_rows(self, allow_remote_crawler_defer=False):
        self.ensure_one()
        feed_ready = self._prepare_remote_csv_feed(
            allow_defer=allow_remote_crawler_defer,
            trigger_if_missing=not allow_remote_crawler_defer,
        )
        if not feed_ready:
            return []
        adapter = get_adapter(self)
        diagnostics = adapter.fetch_with_diagnostics()
        rows = diagnostics["rows"]
        translation_warning = self._get_translation_warning()
        if translation_warning:
            _logger.warning("Supplier %s translation warning: %s", self.code, translation_warning)
        for row in rows:
            computed_price = self._compute_price_for_row(row)
            if computed_price:
                row["unit_price"] = computed_price
        return rows

    def _fetch_normalized_rows_with_diagnostics(self, allow_remote_crawler_defer=False):
        self.ensure_one()
        feed_ready = self._prepare_remote_csv_feed(
            allow_defer=allow_remote_crawler_defer,
            trigger_if_missing=not allow_remote_crawler_defer,
        )
        if not feed_ready:
            waiting_message = _(
                "remote crawler result not ready yet; supplier deferred until the external CSV feed is available"
            )
            return {
                "rows": [],
                "raw_count": 0,
                "normalized_count": 0,
                "dropped_count": 0,
                "invalid_ean_count": 0,
                "missing_identity_count": 0,
                "sample_keys": [],
                "first_row_preview": False,
                "translation_warning": waiting_message,
                "deferred": True,
                "deferred_reason": waiting_message,
            }
        adapter = get_adapter(self)
        diagnostics = adapter.fetch_with_diagnostics()
        rows = diagnostics["rows"]
        translation_warning = self._get_translation_warning()
        for row in rows:
            computed_price = self._compute_price_for_row(row)
            if computed_price:
                row["unit_price"] = computed_price
        diagnostics["rows"] = rows
        if translation_warning:
            diagnostics["translation_warning"] = translation_warning
        elif self.translate_enabled:
            diagnostics["translation_warning"] = _("translation deferred until publish stage")
        else:
            diagnostics["translation_warning"] = False
        return diagnostics

    def _build_diagnostics_message(self, diagnostics):
        self.ensure_one()
        normalized_count = diagnostics.get("normalized_count", 0)
        message = _("%s rows normalized for %s.") % (normalized_count, self.name)
        details = []
        raw_count = diagnostics.get("raw_count", 0)
        dropped_count = diagnostics.get("dropped_count", 0)
        if raw_count:
            details.append(_("raw rows=%s") % raw_count)
        if dropped_count:
            details.append(_("dropped=%s") % dropped_count)
        invalid_ean_count = diagnostics.get("invalid_ean_count", 0)
        if invalid_ean_count:
            details.append(_("invalid/missing EAN=%s") % invalid_ean_count)
        missing_identity_count = diagnostics.get("missing_identity_count", 0)
        if missing_identity_count:
            details.append(_("missing name/reference=%s") % missing_identity_count)
        sample_keys = diagnostics.get("sample_keys") or []
        if sample_keys:
            details.append(_("sample keys=%s") % ", ".join(sample_keys))
        first_row_preview = diagnostics.get("first_row_preview")
        if first_row_preview:
            details.append(_("first row=%s") % first_row_preview)
        translation_warning = diagnostics.get("translation_warning")
        if translation_warning:
            details.append(translation_warning)
        if details:
            message = "%s\n%s" % (message, " | ".join(details))
        return message

    def _is_remote_crawler_supplier(self):
        self.ensure_one()
        return bool(self.source_kind == "csv_url" and self.remote_crawler_trigger_url)

    def _parse_pg_remote_crawler_trigger_time(self, raise_if_invalid=False):
        self.ensure_one()
        raw_value = (self.pg_remote_crawler_trigger_time or "").strip()
        if not raw_value:
            return False
        pieces = raw_value.split(":")
        is_valid = len(pieces) == 2 and all(piece.isdigit() for piece in pieces)
        if not is_valid:
            if raise_if_invalid:
                raise ValidationError(_("Remote crawler trigger time must use HH:MM format in UTC."))
            return False
        hours = int(pieces[0])
        minutes = int(pieces[1])
        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            if raise_if_invalid:
                raise ValidationError(_("Remote crawler trigger time must use valid UTC values between 00:00 and 23:59."))
            return False
        return hours, minutes

    def _remote_crawler_result_timestamp(self):
        self.ensure_one()
        if self.pg_remote_crawler_result_ready_at:
            return self.pg_remote_crawler_result_ready_at
        if self.remote_crawler_result_url and self.remote_crawler_last_checked_at:
            return self.remote_crawler_last_checked_at
        return False

    def _is_remote_crawler_result_fresh(self, now=None):
        self.ensure_one()
        if not (self.remote_crawler_result_url or self.feed_url):
            return False
        max_age_minutes = int(self.pg_remote_crawler_max_age_minutes or 0)
        if max_age_minutes <= 0:
            return True
        result_timestamp = self._remote_crawler_result_timestamp()
        if not result_timestamp:
            return False
        now = now or fields.Datetime.now()
        return result_timestamp >= (now - timedelta(minutes=max_age_minutes))

    def _remote_crawler_active_job_running(self):
        self.ensure_one()
        return (self.remote_crawler_job_status or "").strip().lower() in {"queued", "running", "processing", "cancelling"}

    def _remote_crawler_terminal_status(self, status):
        return str(status or "").strip().lower() in {"done", "failed", "cancelled"}

    def _wait_for_remote_crawler_job_stop(self, timeout_seconds=20.0, poll_interval=1.0):
        self.ensure_one()
        if not self.remote_crawler_status_url or not self.remote_crawler_job_id:
            return True
        status_url = self.remote_crawler_status_url.format(job_id=self.remote_crawler_job_id or "")
        deadline = time.monotonic() + max(float(timeout_seconds or 0.0), 0.0)
        last_error = None
        while time.monotonic() < deadline:
            try:
                response = requests.get(
                    status_url,
                    headers=self._remote_crawler_headers(),
                    timeout=self._remote_crawler_timeout(status_check=True),
                )
                if response.status_code == 404:
                    payload = {
                        "job_id": self.remote_crawler_job_id,
                        "status": "cancelled",
                        "meta": {"progress_note": "Remote crawler job not found after cancellation; treating as cancelled."},
                    }
                    self._apply_remote_crawler_response(payload, checked=True)
                    return True
                response.raise_for_status()
                payload = response.json() if response.content else {}
                self._apply_remote_crawler_response(payload, checked=True)
                if self._remote_crawler_terminal_status(payload.get("status") or self.remote_crawler_job_status):
                    return True
            except Exception as exc:
                last_error = exc
            time.sleep(max(float(poll_interval or 0.0), 0.1))
        if last_error:
            self.write({"remote_crawler_last_error": str(last_error)})
        return False

    def _remote_crawler_job_heartbeat(self):
        self.ensure_one()
        return self.remote_crawler_last_checked_at or self.remote_crawler_last_requested_at or False

    def _remote_crawler_has_recent_job_reference(self, now=None):
        self.ensure_one()
        if not self.remote_crawler_job_id:
            return False
        heartbeat = self._remote_crawler_job_heartbeat()
        if not heartbeat:
            return False
        now = now or fields.Datetime.now()
        recent_cutoff = now - timedelta(minutes=self._pg_remote_crawler_recent_job_window_minutes)
        return heartbeat >= recent_cutoff

    def _remote_crawler_job_is_stale(self, now=None):
        self.ensure_one()
        if not self._remote_crawler_active_job_running():
            return False
        timeout_minutes = int(
            self.pg_remote_crawler_stale_timeout_minutes
            if self.pg_remote_crawler_stale_timeout_minutes is not None
            else 0
        )
        if timeout_minutes <= 0:
            return False
        heartbeat = self._remote_crawler_job_heartbeat()
        if not heartbeat:
            return True
        now = now or fields.Datetime.now()
        stale_cutoff = now - timedelta(minutes=timeout_minutes)
        return heartbeat < stale_cutoff

    def _mark_remote_crawler_job_stale(self):
        self.ensure_one()
        message = _(
            "Remote crawler job marked stale after %(minutes)s minutes without a status update."
        ) % {"minutes": int(self.pg_remote_crawler_stale_timeout_minutes or 0)}
        payload = {
            "job_id": self.remote_crawler_job_id,
            "status": "failed",
            "error": message,
            "meta": {
                "visited_pages": int(self.pg_remote_crawler_visited_pages or 0),
                "discovered_products": int(self.pg_remote_crawler_discovered_products or 0),
                "progress_note": message,
            },
        }
        return self._apply_remote_crawler_response(payload, checked=True)

    def _scheduled_remote_crawler_due_datetime(self, now=None):
        self.ensure_one()
        parsed_time = self._parse_pg_remote_crawler_trigger_time()
        if not parsed_time:
            return False
        now = now or fields.Datetime.now()
        hour, minute = parsed_time
        return now.replace(hour=hour, minute=minute, second=0, microsecond=0)

    def _is_scheduled_remote_crawler_due(self, now=None):
        self.ensure_one()
        if not self._is_remote_crawler_supplier():
            return False
        scheduled_at = self._scheduled_remote_crawler_due_datetime(now=now)
        if not scheduled_at:
            return False
        now = now or fields.Datetime.now()
        if now < scheduled_at:
            return False
        if self._is_remote_crawler_result_fresh(now=now):
            return False
        if self.pg_remote_crawler_last_scheduled_trigger_at and self.pg_remote_crawler_last_scheduled_trigger_at >= scheduled_at:
            return False
        if (
            self._remote_crawler_active_job_running()
            and self.remote_crawler_last_requested_at
            and self.remote_crawler_last_requested_at >= scheduled_at
        ):
            return False
        return True

    def _prime_remote_crawler_job_for_sync(self):
        self.ensure_one()
        if not self._is_remote_crawler_supplier():
            return {}
        if self.remote_crawler_auto_refresh and self.remote_crawler_status_url and self.remote_crawler_job_id:
            self._refresh_remote_crawler_status()
        if self._is_remote_crawler_result_fresh():
            return {
                "job_id": self.remote_crawler_job_id,
                "status": self.remote_crawler_job_status or "done",
                "csv_url": self.feed_url or self.remote_crawler_result_url,
            }
        if self._remote_crawler_active_job_running():
            return {
                "job_id": self.remote_crawler_job_id,
                "status": self.remote_crawler_job_status or "running",
            }
        return self._trigger_remote_crawler_job(clear_previous_result=bool(self.feed_url or self.remote_crawler_result_url))

    def _prepare_remote_csv_feed(self, allow_defer=False, trigger_if_missing=True):
        """Garante que o CSV gerado pelo crawler remoto esta pronto antes do sync.

        * ``allow_defer=True`` -- usado pelo worker em background quando se
          aceita que o run fique em ``deferred`` ate o CSV chegar (evita
          encher a fila com tentativas que iriam falhar).
        * ``trigger_if_missing=True`` -- dispara um novo job se nao houver
          resultado fresco; usado pelas acoes manuais a partir da UI.

        Levanta ``UserError`` (interrompe o sync UI) apenas quando nao se pode
        adiar nem disparar e nao ha CSV recente; nesse caso, o utilizador tem
        de aguardar a finalizacao do crawler externo e voltar a tentar.
        """
        self.ensure_one()
        if self.source_kind != "csv_url":
            return True
        if self._is_remote_crawler_result_fresh():
            return True
        if self.remote_crawler_auto_refresh and self.remote_crawler_status_url and self.remote_crawler_job_id:
            self._refresh_remote_crawler_status()
        if self._is_remote_crawler_result_fresh():
            return True
        if self._remote_crawler_active_job_running():
            if allow_defer and self.remote_crawler_trigger_url:
                return False
        elif trigger_if_missing and self.remote_crawler_trigger_url:
            payload = self._trigger_remote_crawler_job(clear_previous_result=bool(self.feed_url or self.remote_crawler_result_url))
            if payload.get("csv_url") or self._is_remote_crawler_result_fresh():
                return True
        if allow_defer and self.remote_crawler_trigger_url:
            return False
        if self.remote_crawler_trigger_url:
            if self.remote_crawler_job_id or self.remote_crawler_job_status:
                self.env.cr.commit()
            raise UserError(
                _(
                    "Remote crawler job triggered for %s. Wait for completion, then refresh the remote result."
                )
                % self.name
            )
        return True

    def _get_translation_service(self):
        self.ensure_one()
        if not self.translate_enabled:
            return False
        params = self.env["ir.config_parameter"].sudo()
        provider = self.translate_provider or "openai"
        api_key = self.translate_api_key
        if not api_key:
            api_key = params.get_param("hiper_sync.translate_%s_api_key" % provider)
        model = self.translate_ai_model or params.get_param("hiper_sync.translate_openai_model") or "gpt-4.1-mini"
        return build_translation_service(
            provider,
            api_key,
            self.translate_source_lang or "es",
            self.translate_target_lang or "pt",
            model=model,
        )

    def _get_translation_warning(self):
        self.ensure_one()
        if not self.translate_enabled:
            return False
        params = self.env["ir.config_parameter"].sudo()
        provider = self.translate_provider or "openai"
        api_key = (self.translate_api_key or "").strip()
        if not api_key:
            api_key = (params.get_param("hiper_sync.translate_%s_api_key" % provider) or "").strip()
        if api_key:
            return False
        if provider == "google":
            return _("translation skipped: Google Translate API key is not configured")
        if provider == "openai":
            return _("translation skipped: OpenAI API key is not configured")
        return _("translation skipped: %s API key is not configured") % provider

    def _translation_context_for_row(self, row):
        self.ensure_one()
        protected_terms = []
        if self.translate_protected_terms:
            protected_terms.extend(
                [item.strip() for item in self.translate_protected_terms.splitlines() if item.strip()]
            )
        for field_name in ("brand", "reference", "ean13"):
            if row.get(field_name):
                protected_terms.append(str(row[field_name]).strip())
        return {
            "protected_terms": protected_terms,
        }

    def action_fetch_preview(self):
        self.ensure_one()
        diagnostics = self._fetch_normalized_rows_with_diagnostics()
        message = self._build_diagnostics_message(diagnostics)
        self.message_post(body=message)
        self.write({"last_sync_at": fields.Datetime.now(), "last_sync_status": "done", "last_sync_message": message})
        return True

    def action_use_external_feed_mode(self):
        self.ensure_one()
        for vendor in self:
            vendor.write(
                {
                    "source_kind": "csv_url",
                    "last_sync_message": _(
                        "Configured for old architecture mode: CSV must be generated externally and exposed by URL."
                    ),
                }
            )
            vendor.message_post(
                body=_(
                    "Supplier switched to external CSV mode. Configure Feed URL with the CSV generated outside Odoo."
                )
            )
        return {
            "type": "ir.actions.act_window",
            "name": _("Supplier"),
            "res_model": "hiper.sync.vendor",
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
        }

    def _remote_crawler_headers(self):
        self.ensure_one()
        headers = {"Accept": "application/json"}
        if self.remote_crawler_auth_token:
            headers["Authorization"] = "Bearer %s" % self.remote_crawler_auth_token
        for url_value in (self.remote_crawler_trigger_url, self.remote_crawler_status_url):
            if url_value and "ngrok" in url_value:
                headers.setdefault("ngrok-skip-browser-warning", "true")
                break
        return headers

    def _remote_crawler_timeout(self, *, status_check=False):
        self.ensure_one()
        if status_check:
            if any("ngrok" in (url_value or "") for url_value in (self.remote_crawler_trigger_url, self.remote_crawler_status_url)):
                return (10, 90)
            return (10, 60)
        return (10, 60)

    def _remote_crawler_cancel_url(self):
        self.ensure_one()
        if not self.remote_crawler_status_url or not self.remote_crawler_job_id:
            return None
        status_url = self.remote_crawler_status_url.format(job_id=self.remote_crawler_job_id or "")
        return status_url.rstrip("/") + "/cancel"

    def _remote_crawler_trigger_payload(self, clear_remote_resume_state=False):
        self.ensure_one()
        payload = parse_json(self.remote_crawler_payload_json, default={})
        payload.setdefault("vendor_code", self.code)
        payload.setdefault("vendor_name", self.name)
        if self.remote_crawler_source_url:
            payload.setdefault("source_url", self.remote_crawler_source_url)
        if self.pg_remote_crawler_adapter_key:
            payload.setdefault("adapter_key", self.pg_remote_crawler_adapter_key)
        if self.pg_remote_crawler_login_url:
            payload.setdefault("login_url", self.pg_remote_crawler_login_url)
        if self.pg_remote_crawler_login_username:
            payload.setdefault("login_username", self.pg_remote_crawler_login_username)
        if self.pg_remote_crawler_login_password:
            payload.setdefault("login_password", self.pg_remote_crawler_login_password)
        payload.setdefault("force_tienda_view", bool(self.pg_remote_crawler_force_tienda_view))
        params = self.env["ir.config_parameter"].sudo()
        upload_token = (params.get_param("hiper_sync.remote_crawler_upload_token") or "").strip()
        base_url = (params.get_param("web.base.url") or "").strip()
        if upload_token and base_url:
            payload.setdefault(
                "odoo_upload_url",
                urljoin(base_url.rstrip("/") + "/", "hiper_sync/crawler/upload"),
            )
            payload.setdefault("odoo_upload_token", upload_token)
        if clear_remote_resume_state:
            payload["pg_clear_resume_state"] = True
        return payload

    def _apply_remote_crawler_response(self, payload, requested=False, checked=False, clear_previous_result=False):
        self.ensure_one()
        payload = payload or {}
        meta = payload.get("meta") or {}
        if not isinstance(meta, dict):
            meta = {}
        values = {}
        if clear_previous_result:
            values.update(
                {
                    "feed_url": False,
                    "remote_crawler_result_url": False,
                    "remote_crawler_last_error": False,
                    "pg_remote_crawler_result_ready_at": False,
                    "pg_remote_crawler_visited_pages": 0,
                    "pg_remote_crawler_discovered_products": 0,
                    "pg_remote_crawler_progress_note": False,
                }
            )
        if payload.get("job_id"):
            incoming_job_id = str(payload["job_id"])
            values["remote_crawler_job_id"] = incoming_job_id
            has_progress_update = any(
                key in meta and meta.get(key) not in (None, "", False)
                for key in ("visited_pages", "discovered_products", "progress_note", "current_category", "current_sub_category")
            )
            if requested and (incoming_job_id != str(self.remote_crawler_job_id or "") or not has_progress_update):
                values.update(
                    {
                        "pg_remote_crawler_visited_pages": 0,
                        "pg_remote_crawler_discovered_products": 0,
                        "pg_remote_crawler_progress_note": False,
                    }
                )
        if payload.get("status"):
            values["remote_crawler_job_status"] = str(payload["status"])
        if payload.get("status_url"):
            values["remote_crawler_status_url"] = payload["status_url"]
        csv_url = payload.get("csv_url") or payload.get("result_url")
        if csv_url:
            values["remote_crawler_result_url"] = csv_url
            values["feed_url"] = csv_url
            values["pg_remote_crawler_result_ready_at"] = fields.Datetime.now()
        if payload.get("error"):
            values["remote_crawler_last_error"] = str(payload["error"])
        elif payload:
            values["remote_crawler_last_error"] = False
        if "visited_pages" in meta:
            try:
                values["pg_remote_crawler_visited_pages"] = int(meta.get("visited_pages") or 0)
            except (TypeError, ValueError):
                values["pg_remote_crawler_visited_pages"] = 0
        if "discovered_products" in meta:
            try:
                values["pg_remote_crawler_discovered_products"] = int(meta.get("discovered_products") or 0)
            except (TypeError, ValueError):
                values["pg_remote_crawler_discovered_products"] = 0
        progress_note = (meta.get("progress_note") or "").strip()
        if not progress_note:
            parts = [str(meta.get("current_category") or "").strip(), str(meta.get("current_sub_category") or "").strip()]
            progress_note = " / ".join([part for part in parts if part])
        if progress_note:
            values["pg_remote_crawler_progress_note"] = progress_note
        elif str(payload.get("status") or "").strip().lower() in {"done", "failed", "cancelled"}:
            values["pg_remote_crawler_progress_note"] = False
        if requested:
            values["remote_crawler_last_requested_at"] = fields.Datetime.now()
        if checked:
            values["remote_crawler_last_checked_at"] = fields.Datetime.now()
        if values:
            self.write(values)
        return payload

    def _trigger_remote_crawler_job(self, clear_previous_result=False, clear_remote_resume_state=False):
        self.ensure_one()
        if not self.remote_crawler_trigger_url:
            raise UserError(_("Remote crawler trigger URL is not configured for %s.") % self.name)
        if self._remote_crawler_active_job_running() and self.remote_crawler_job_id:
            cancel_url = self._remote_crawler_cancel_url()
            if not cancel_url:
                raise UserError(_("Remote crawler cancel URL is not available for %s.") % self.name)
            try:
                response = requests.post(
                    cancel_url,
                    headers=self._remote_crawler_headers(),
                    timeout=self._remote_crawler_timeout(status_check=True),
                )
                response.raise_for_status()
                cancel_payload = response.json() if response.content else {}
                if cancel_payload:
                    self._apply_remote_crawler_response(cancel_payload, checked=True)
                if not self._remote_crawler_terminal_status((cancel_payload or {}).get("status") or self.remote_crawler_job_status):
                    if not self._wait_for_remote_crawler_job_stop():
                        raise UserError(
                            _("Remote crawler previous job is still stopping for %s. Wait a moment and try again.")
                            % self.name
                        )
            except requests.HTTPError as exc:
                if exc.response is not None and exc.response.status_code == 404:
                    payload = {
                        "job_id": self.remote_crawler_job_id,
                        "status": "cancelled",
                        "meta": {"progress_note": "Remote crawler job not found; treating as cancelled."},
                    }
                    self._apply_remote_crawler_response(payload, checked=True)
                else:
                    self.write({"remote_crawler_last_error": str(exc)})
                    raise UserError(_("Remote crawler cancel failed for %s: %s") % (self.name, exc))
            except Exception as exc:
                self.write({"remote_crawler_last_error": str(exc)})
                raise UserError(_("Remote crawler cancel failed for %s: %s") % (self.name, exc))
        try:
            response = requests.post(
                self.remote_crawler_trigger_url,
                json=self._remote_crawler_trigger_payload(clear_remote_resume_state=clear_remote_resume_state),
                headers=self._remote_crawler_headers(),
                timeout=self._remote_crawler_timeout(status_check=False),
            )
            response.raise_for_status()
            payload = response.json() if response.content else {}
        except Exception as exc:
            self.write({"remote_crawler_last_error": str(exc)})
            raise UserError(_("Remote crawler trigger failed for %s: %s") % (self.name, exc))
        return self._apply_remote_crawler_response(
            payload,
            requested=True,
            clear_previous_result=clear_previous_result,
        )

    def _refresh_remote_crawler_status(self, force_remote=False):
        self.ensure_one()
        if not force_remote and self._is_remote_crawler_result_fresh() and not self._remote_crawler_active_job_running():
            payload = {
                "job_id": self.remote_crawler_job_id,
                "status": self.remote_crawler_job_status or "done",
                "csv_url": self.feed_url or self.remote_crawler_result_url,
                "meta": {
                    "visited_pages": int(self.pg_remote_crawler_visited_pages or 0),
                    "discovered_products": int(self.pg_remote_crawler_discovered_products or 0),
                    "progress_note": self.pg_remote_crawler_progress_note or "",
                },
            }
            return self._apply_remote_crawler_response(payload, checked=True)
        if self._remote_crawler_job_is_stale():
            _logger.warning(
                "Remote crawler job considered stale vendor=%s code=%s job_id=%s last_requested=%s last_checked=%s timeout_minutes=%s",
                self.name,
                self.code,
                self.remote_crawler_job_id,
                self.remote_crawler_last_requested_at,
                self.remote_crawler_last_checked_at,
                self._pg_remote_crawler_stale_timeout_minutes,
            )
            return self._mark_remote_crawler_job_stale()
        if not self.remote_crawler_status_url:
            raise UserError(_("Remote crawler status URL is not configured for %s.") % self.name)
        if "{job_id}" in self.remote_crawler_status_url and not self.remote_crawler_job_id:
            raise UserError(_("Remote crawler job id is missing for %s.") % self.name)
        if not force_remote and not self._remote_crawler_active_job_running() and not self._remote_crawler_has_recent_job_reference():
            payload = {
                "job_id": self.remote_crawler_job_id,
                "status": self.remote_crawler_job_status or "idle",
                "csv_url": self.feed_url or self.remote_crawler_result_url,
                "meta": {
                    "visited_pages": int(self.pg_remote_crawler_visited_pages or 0),
                    "discovered_products": int(self.pg_remote_crawler_discovered_products or 0),
                    "progress_note": self.pg_remote_crawler_progress_note or "",
                },
            }
            return self._apply_remote_crawler_response(payload, checked=True)
        status_url = self.remote_crawler_status_url.format(job_id=self.remote_crawler_job_id or "")
        last_exc = None
        for attempt in range(2):
            try:
                response = requests.get(
                    status_url,
                    headers=self._remote_crawler_headers(),
                    timeout=self._remote_crawler_timeout(status_check=True),
                )
                response.raise_for_status()
                payload = response.json() if response.content else {}
                break
            except Exception as exc:
                last_exc = exc
                _logger.warning(
                    "Remote crawler status refresh attempt %s failed vendor=%s job_id=%s url=%s error=%s",
                    attempt + 1,
                    self.code,
                    self.remote_crawler_job_id,
                    status_url,
                    exc,
                )
                if attempt >= 1:
                    self.write({"remote_crawler_last_error": str(exc)})
                    raise UserError(_("Remote crawler status refresh failed for %s: %s") % (self.name, exc))
                time.sleep(0.5 * (2 ** attempt))
        return self._apply_remote_crawler_response(payload, checked=True)

    @api.model
    def cron_prepare_remote_crawlers(self):
        """Cron de "prewarm": dispara cada crawler remoto na hora UTC configurada.

        Executado por ``hiper_sync.ir_cron_pg_remote_crawler_prewarm`` (10 min).
        Para cada fornecedor com ``pg_remote_crawler_trigger_time`` definido e
        que ja passou a hora alvo no dia corrente (e cujo resultado anterior
        nao esta fresco), dispara um novo job e marca
        ``pg_remote_crawler_last_scheduled_trigger_at`` para evitar disparos
        duplicados no mesmo ciclo diario.
        """
        now = fields.Datetime.now()
        vendors = self.search(
            [
                ("active", "=", True),
                ("sync_active", "=", True),
                ("source_kind", "=", "csv_url"),
                ("remote_crawler_trigger_url", "!=", False),
                ("pg_remote_crawler_trigger_time", "!=", False),
            ]
        )
        if not vendors:
            _logger.info("Remote crawler prewarm cron found no configured suppliers.")
            return True
        triggered = self.browse()
        for vendor in vendors:
            if not vendor._is_scheduled_remote_crawler_due(now=now):
                continue
            try:
                payload = vendor._trigger_remote_crawler_job(
                    clear_previous_result=bool(vendor.feed_url or vendor.remote_crawler_result_url)
                )
                vendor.write({"pg_remote_crawler_last_scheduled_trigger_at": now})
                triggered |= vendor
                _logger.info(
                    "Remote crawler prewarm triggered vendor id=%s code=%s job_id=%s status=%s immediate_csv=%s",
                    vendor.id,
                    vendor.code,
                    payload.get("job_id") or vendor.remote_crawler_job_id,
                    payload.get("status") or vendor.remote_crawler_job_status,
                    bool(payload.get("csv_url") or vendor.feed_url),
                )
            except Exception as exc:
                vendor.write(
                    {
                        "pg_remote_crawler_last_scheduled_trigger_at": now,
                        "remote_crawler_last_error": str(exc),
                    }
                )
                _logger.exception(
                    "Remote crawler prewarm failed vendor id=%s code=%s: %s",
                    vendor.id,
                    vendor.code,
                    exc,
                )
        _logger.info("Remote crawler prewarm cron triggered %s supplier(s).", len(triggered))
        return True

    def action_trigger_remote_crawler(self):
        self.ensure_one()
        self._trigger_remote_crawler_job(
            clear_previous_result=bool(self.feed_url or self.remote_crawler_result_url),
            clear_remote_resume_state=True,
        )
        self.message_post(body=_("Remote crawler job triggered."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Supplier"),
            "res_model": "hiper.sync.vendor",
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
        }

    def action_refresh_remote_crawler(self):
        self.ensure_one()
        if (
            not self._is_remote_crawler_result_fresh()
            and not self._remote_crawler_active_job_running()
            and not self._remote_crawler_has_recent_job_reference()
        ):
            raise UserError(_("No active remote crawler job is running for %s. Trigger a new remote crawl first.") % self.name)
        self._refresh_remote_crawler_status(force_remote=True)
        message = _(
            "Remote crawler status refreshed. Status: %(status)s. Pages visited: %(pages)s. Products detected: %(products)s."
        ) % {
            "status": self.remote_crawler_job_status or _("unknown"),
            "pages": int(self.pg_remote_crawler_visited_pages or 0),
            "products": int(self.pg_remote_crawler_discovered_products or 0),
        }
        if self.pg_remote_crawler_progress_note:
            message = "%s %s" % (
                message,
                _("Progress: %s.") % self.pg_remote_crawler_progress_note,
            )
        self.message_post(body=message)
        return {
            "type": "ir.actions.act_window",
            "name": _("Supplier"),
            "res_model": "hiper.sync.vendor",
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
        }

    def action_pg_regenerate_remote_crawler_token(self):
        self.ensure_one()
        self.write({"remote_crawler_auth_token": str(uuid.uuid4())})
        self.message_post(body=_("Remote crawler token regenerated."))
        return {
            "type": "ir.actions.act_window",
            "name": _("Supplier"),
            "res_model": "hiper.sync.vendor",
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
        }

    def _run_sync_for_vendors(self, vendors):
        self._cancel_overlapping_runs(vendors)
        run = self.env["hiper.sync.run"].create(
            {
                "name": fields.Datetime.now().strftime("SYNC %Y-%m-%d %H:%M:%S"),
                "state": "running",
                "current_phase": "draft",
                "started_at": fields.Datetime.now(),
                "vendor_ids": [(6, 0, vendors.ids)],
                "total_vendors": len(vendors),
            }
        )
        self.env.cr.commit()
        publisher = HiperPublisher(self.env, run)
        stats = publisher.run(vendors)
        values = {
            "finished_at": fields.Datetime.now(),
            "notes": stats.get("notes"),
        }
        if run.started_at and values["finished_at"]:
            values["duration_seconds"] = max(int((values["finished_at"] - run.started_at).total_seconds()), 0)
        values["progress_updated_at"] = values["finished_at"]
        if stats.get("cancelled"):
            values["state"] = "cancelled"
            values["current_phase"] = "cancelled"
            values["progress_percent"] = 100.0
            values["progress_note"] = stats.get("notes") or _("Sync cancelled.")
        else:
            has_publish_errors = bool(stats.get("publish_error_count") or run.error_records)
            has_supplier_warnings = bool(stats.get("supplier_warning_count"))
            values["state"] = (
                "failed"
                if has_publish_errors
                else "done_warning" if has_supplier_warnings else "done"
            )
            values["current_phase"] = (
                "failed"
                if has_publish_errors
                else "done_warning" if has_supplier_warnings else "done"
            )
            values["progress_percent"] = 100.0
            values["progress_note"] = (
                _("Sync finished with warnings.")
                if has_supplier_warnings and not has_publish_errors
                else _("Sync finished.")
            )
        values["eta_seconds"] = 0
        values["current_vendor_id"] = False
        values["current_item_label"] = False
        run.write(values)
        self.env.cr.commit()
        return run

    def _cancel_overlapping_runs(self, vendors):
        overlapping_runs = self.env["hiper.sync.run"].search(
            [
                ("state", "in", ["queued", "running"]),
                ("vendor_ids", "in", vendors.ids),
            ]
        )
        if not overlapping_runs:
            return
        _logger.warning(
            "Cancelling overlapping runs for vendors=%s runs=%s",
            vendors.ids,
            overlapping_runs.ids,
        )
        now = fields.Datetime.now()
        for existing_run in overlapping_runs:
            if existing_run.state == "queued":
                existing_run.write(
                    {
                        "state": "cancelled",
                        "current_phase": "cancelled",
                        "finished_at": now,
                        "progress_percent": 100.0,
                        "progress_note": _("Cancelled by a newer sync request."),
                        "eta_seconds": 0,
                        "current_vendor_id": False,
                        "current_item_label": False,
                    }
                )
            else:
                existing_run.write(
                    {
                        "cancel_requested": True,
                        "progress_note": _("Cancellation requested by a newer sync request."),
                    }
                )
        self.env.cr.commit()

    def _enqueue_sync_for_vendors(self, vendors):
        """Cria um ``hiper.sync.run`` em estado ``queued`` e empurra o cron de fila.

        Cancela qualquer execucao em curso ou em fila para o mesmo conjunto de
        fornecedores (evita execucoes concorrentes sobre os mesmos produtos),
        cria o run, e re-arma o cron ``hiper_sync.ir_cron_hiper_sync_queue``
        com ``nextcall = now`` + ``_trigger()`` quando suportado, para que o
        worker pegue imediatamente em vez de esperar pelo proximo ciclo.
        """
        _logger.info("Enqueue requested for vendors=%s", vendors.ids)
        self._cancel_overlapping_runs(vendors)
        run = self.env["hiper.sync.run"].create(
            {
                "name": fields.Datetime.now().strftime("SYNC %Y-%m-%d %H:%M:%S"),
                "state": "queued",
                "current_phase": "queued",
                "started_at": fields.Datetime.now(),
                "vendor_ids": [(6, 0, vendors.ids)],
                "total_vendors": len(vendors),
                "progress_percent": 0.0,
                "progress_note": _("Queued. Waiting for background worker."),
            }
        )
        self.env.cr.commit()
        cron = self.env.ref("hiper_sync.ir_cron_hiper_sync_queue", raise_if_not_found=False)
        if cron:
            try:
                cron.sudo().write(
                    {
                        "active": True,
                        "nextcall": fields.Datetime.now(),
                    }
                )
                _logger.info(
                    "Scheduled Hiper queue cron id=%s nextcall=%s active=%s for new run id=%s",
                    cron.id,
                    cron.nextcall,
                    cron.active,
                    run.id,
                )
                self.env.cr.commit()
            except Exception:
                _logger.exception("Failed to update queue cron for run id=%s", run.id)
                pass
            if hasattr(cron, "_trigger"):
                try:
                    cron._trigger()
                    _logger.info("Triggered queue cron id=%s for run id=%s", cron.id, run.id)
                except Exception:
                    _logger.exception("Failed to trigger queue cron id=%s for run id=%s", cron.id, run.id)
                    pass
        else:
            _logger.error("Queue cron record hiper_sync.ir_cron_hiper_sync_queue was not found.")
        _logger.info("Queued sync run created id=%s vendors=%s", run.id, vendors.ids)
        return run

    @api.model
    def cron_full_sync(self):
        vendors = self.search([("sync_active", "=", True), ("active", "=", True)])
        if not vendors:
            return True
        self._run_sync_for_vendors(vendors)
        return True

    def action_run_sync(self):
        self.ensure_one()
        run = self._enqueue_sync_for_vendors(self)
        return {
            "type": "ir.actions.act_window",
            "name": _("Sync Run"),
            "res_model": "hiper.sync.run",
            "view_mode": "form",
            "res_id": run.id,
            "target": "current",
        }

    def action_run_full_sync(self):
        self.ensure_one()
        vendors = self.search([("sync_active", "=", True), ("active", "=", True)])
        if not vendors:
            return True
        run = self._enqueue_sync_for_vendors(vendors)
        return {
            "type": "ir.actions.act_window",
            "name": _("Sync Run"),
            "res_model": "hiper.sync.run",
            "view_mode": "form",
            "res_id": run.id,
            "target": "current",
        }

    def action_validate_configuration(self):
        for vendor in self:
            adapter = get_adapter(vendor)
            missing = adapter.validate_configuration()
            translation_warning = vendor._get_translation_warning()
            if translation_warning:
                missing.append(translation_warning)
            if missing:
                raise UserError(_("%s is missing configuration: %s") % (vendor.name, ", ".join(missing)))
        return True

    def action_pg_discover_protected_terms(self):
        self.ensure_one()
        query = (self.pg_translate_discovery_query or "").strip()
        if not query:
            raise UserError(_("Please set a discovery query first. Example: Smartphones or Star Wars."))
        mode = self.pg_translate_discovery_mode or "heuristic"
        service = PgTermDiscoveryService(
            query=query,
            mode=mode,
            preset=self.pg_translate_discovery_preset or "",
        )
        try:
            terms, stats = service.discover_terms()
        except Exception as exc:
            self.write(
                {
                    "pg_translate_discovery_status": "failed",
                    "pg_translate_discovery_last_run_at": fields.Datetime.now(),
                    "pg_translate_discovery_log": str(exc),
                }
            )
            raise UserError(_("Protected terms discovery failed: %s") % exc)
        existing_terms = []
        if self.translate_protected_terms:
            existing_terms = [item.strip() for item in self.translate_protected_terms.splitlines() if item.strip()]
        merged = self._merge_protected_terms(existing_terms, terms)
        log_lines = [
            "Query: %s" % query,
            "Mode: %s" % mode,
            "Preset: %s" % (self.pg_translate_discovery_preset or "none"),
            "Wikipedia EN titles: %s" % stats.wikipedia_en_count,
            "Wikipedia PT titles: %s" % stats.wikipedia_pt_count,
            "Wikidata labels: %s" % stats.wikidata_count,
            "GTIN results: %s" % stats.gtin_count,
            "Seeded terms: %s" % stats.seeded_count,
            "New terms added: %s" % max(len(merged) - len(existing_terms), 0),
            "Total protected terms: %s" % len(merged),
        ]
        sample = merged[:12]
        if sample:
            log_lines.append("Sample: %s" % ", ".join(sample))
        self.write(
            {
                "translate_protected_terms": "\n".join(merged),
                "pg_translate_discovery_status": "done",
                "pg_translate_discovery_last_run_at": fields.Datetime.now(),
                "pg_translate_discovery_log": "\n".join(log_lines),
            }
        )
        self.message_post(body=_("Protected terms discovery completed. Added %s terms.") % max(len(merged) - len(existing_terms), 0))
        return {
            "type": "ir.actions.act_window",
            "name": _("Supplier"),
            "res_model": "hiper.sync.vendor",
            "view_mode": "form",
            "res_id": self.id,
            "target": "current",
        }

    def _merge_protected_terms(self, existing_terms, new_terms):
        seen = set()
        merged = []
        for term in existing_terms + list(new_terms or []):
            value = (term or "").strip()
            if not value:
                continue
            key = value.casefold()
            if key in seen:
                continue
            seen.add(key)
            merged.append(value)
        merged.sort(key=len, reverse=True)
        return merged
