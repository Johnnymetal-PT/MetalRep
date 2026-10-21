"""
Hooks de instalacao/migracao do modulo legacy pg_phc_api_old.

Modulo: pg_phc_api_old.
Ficheiro: pg_phc_api_old\hooks.py.
Inclui criacao defensiva de colunas/campos necessarios para compatibilidade.
"""

from odoo import SUPERUSER_ID, api

# Manual field definitions to create when Studio fields are missing.
PHC_PARTNER_FIELD_SPECS = [
    {
        "name": "x_studio_country_code",
        "ttype": "char",
        "field_description": "Country Code",
        "size": 2,
        "required": True,
    },
    {
        "name": "x_studio_salesperson_id",
        "ttype": "integer",
        "field_description": "Salesperson (PHC)",
        "required": True,
    },
    {
        "name": "x_studio_tabela_precos",
        "ttype": "selection",
        "field_description": "Tabela de Preços",
        "required": True,
        "selection": "[(\"1\", \"1\"), (\"2\", \"2\"), (\"3\", \"3\"), (\"4\", \"4\"), (\"5\", \"5\")]",
        "size": 1,
    },
    {
        "name": "responsavel_interno",
        "ttype": "char",
        "field_description": "Responsável Interno",
        "size": 30,
        "required": True,
    },
]


def _add_partner_column_if_missing(cr, column_name, column_type):
    """Create a partner column if it is missing using a single SQL statement.

    Using ``ADD COLUMN IF NOT EXISTS`` avoids race conditions between the
    presence check and the creation itself, and works even if the ORM has not
    yet registered the field (common on Odoo SH restarts without upgrades).
    """

    cr.execute(
        f"ALTER TABLE res_partner ADD COLUMN IF NOT EXISTS {column_name} {column_type}"
    )


def ensure_phc_partner_columns(cr):
    """Ensure all PHC partner columns exist."""

    _add_partner_column_if_missing(cr, "x_studio_country_code", "varchar(2)")
    _add_partner_column_if_missing(cr, "x_studio_salesperson_id", "integer")
    _add_partner_column_if_missing(cr, "x_studio_tabela_precos", "varchar(1)")
    _add_partner_column_if_missing(cr, "responsavel_interno", "varchar(30)")


def ensure_phc_partner_fields(env):
    """Create PHC partner fields if Studio entries are missing.

    Some databases may lack the Studio custom field records. We recreate them
    via ``ir.model.fields`` so the ORM knows about the fields before reading
    partners. ``selection`` values are provided in the serialized format that
    ``ir.model.fields`` expects when created programmatically.
    """

    model = env["ir.model"].sudo().search([("model", "=", "res.partner")], limit=1)
    if not model:
        return

    fields_model = env["ir.model.fields"].sudo()
    for spec in PHC_PARTNER_FIELD_SPECS:
        if fields_model.search_count(
            [("model", "=", "res.partner"), ("name", "=", spec["name"])]
        ):
            continue

        values = {
            "name": spec["name"],
            "field_description": spec.get("field_description", spec["name"]),
            "model_id": model.id,
            "state": "manual",
            "ttype": spec["ttype"],
        }

        if spec.get("required"):
            values["required"] = True
        if spec.get("size"):
            values["size"] = spec["size"]
        if spec.get("selection"):
            values["selection"] = spec["selection"]

        fields_model.create(values)


def pre_init_hook(cr):
    # Run before module upgrade/install so registry setup does not fail on
    # missing columns.
    ensure_phc_partner_columns(cr)


def post_init_hook(cr, registry):
    env = api.Environment(cr, SUPERUSER_ID, {})
    # Ensure PHC-required fields exist even if the server skipped column creation
    # during an earlier module upgrade.
    with env.cr.savepoint():
        ensure_phc_partner_columns(env.cr)
        ensure_phc_partner_fields(env)
