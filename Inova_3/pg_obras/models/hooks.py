from odoo import api, SUPERUSER_ID

def _ensure_xmlid(env, module, name, model, res_id, noupdate=True):
    """Cria ou atualiza ir.model.data para mapear um registo existente a um XML ID."""
    imd = env["ir.model.data"].sudo()
    existing = imd.search([("module", "=", module), ("name", "=", name)], limit=1)
    vals = {
        "module": module,
        "name": name,
        "model": model,
        "res_id": res_id,
        "noupdate": bool(noupdate),
    }
    if existing:
        existing.write(vals)
    else:
        imd.create(vals)

def pre_init_hook(cr):
    env = api.Environment(cr, SUPERUSER_ID, {})

    company = env.ref("base.main_company")

    # ---------------------------------------------------------------------
    # 1) Warehouse "Obras" (code OBR)
    # ---------------------------------------------------------------------
    wh = env["stock.warehouse"].sudo().search([
        ("code", "=", "OBR"),
        ("company_id", "=", company.id),
    ], limit=1)

    if wh:
        _ensure_xmlid(env, "pg_obras", "warehouse_obras", "stock.warehouse", wh.id)

    # ---------------------------------------------------------------------
    # 2) Locations: OBR (view) e OBR/Stock (internal)
    #    Tentativa de match por complete_name e company.
    # ---------------------------------------------------------------------
    loc_obr = env["stock.location"].sudo().search([
        ("usage", "=", "view"),
        ("name", "=", "OBR"),
        ("company_id", "=", company.id),
    ], limit=1)
    if loc_obr:
        _ensure_xmlid(env, "pg_obras", "location_obr", "stock.location", loc_obr.id)

    loc_obr_stock = env["stock.location"].sudo().search([
        ("usage", "=", "internal"),
        ("name", "=", "Stock"),
        ("location_id", "=", loc_obr.id if loc_obr else False),
        ("company_id", "=", company.id),
    ], limit=1)
    # fallback: procurar por complete_name
    if not loc_obr_stock:
        loc_obr_stock = env["stock.location"].sudo().search([
            ("complete_name", "=", "OBR/Stock"),
            ("company_id", "=", company.id),
        ], limit=1)

    if loc_obr_stock:
        _ensure_xmlid(env, "pg_obras", "location_obr_stock", "stock.location", loc_obr_stock.id)

    # ---------------------------------------------------------------------
    # 3) Picking Types:
    #    a) Obras: Receipts (incoming, warehouse Obras, barcode OBRIN se existir)
    #    b) Entrega em Obra (delivery/outgoing, barcode EOBR ou sequence_code EOBR)
    # ---------------------------------------------------------------------
    pt_model = env["stock.picking.type"].sudo()

    # a) Obras: Receipts
    pt_obras_in = pt_model.search([
        ("code", "=", "incoming"),
        ("warehouse_id", "=", wh.id if wh else False),
    ], limit=1)
    # fallback por nome / barcode
    if not pt_obras_in:
        pt_obras_in = pt_model.search([
            ("code", "=", "incoming"),
            ("barcode", "=", "OBRIN"),
            ("company_id", "in", [company.id, False]),
        ], limit=1)
    if not pt_obras_in:
        pt_obras_in = pt_model.search([
            ("name", "ilike", "Obras: Receipts"),
            ("code", "=", "incoming"),
        ], limit=1)

    if pt_obras_in:
        _ensure_xmlid(env, "pg_obras", "picking_type_obras_in", "stock.picking.type", pt_obras_in.id)

    # b) Entrega em Obra (EOBR)
    pt_eobr = pt_model.search([
        ("code", "=", "outgoing"),
        ("barcode", "=", "EOBR"),
        ("company_id", "in", [company.id, False]),
    ], limit=1)
    if not pt_eobr:
        pt_eobr = pt_model.search([
            ("code", "=", "outgoing"),
            ("sequence_code", "=", "EOBR"),
            ("company_id", "in", [company.id, False]),
        ], limit=1)
    if not pt_eobr:
        pt_eobr = pt_model.search([
            ("name", "ilike", "Entrega em Obra"),
            ("code", "=", "outgoing"),
        ], limit=1)

    if pt_eobr:
        _ensure_xmlid(env, "pg_obras", "picking_type_eobr", "stock.picking.type", pt_eobr.id)

    # ---------------------------------------------------------------------
    # 4) Sequences: mapear se já existirem (por prefixo)
    # ---------------------------------------------------------------------
    seq_model = env["ir.sequence"].sudo()

    seq_obras_in = seq_model.search([
        ("code", "=", "stock.picking"),
        ("prefix", "=", "OBR/IN/"),
        ("company_id", "=", company.id),
    ], limit=1)
    if seq_obras_in:
        _ensure_xmlid(env, "pg_obras", "seq_obras_in", "ir.sequence", seq_obras_in.id)

    seq_eobr = seq_model.search([
        ("code", "=", "stock.picking"),
        ("prefix", "=", "EOBR/"),
        ("company_id", "=", company.id),
    ], limit=1)
    if seq_eobr:
        _ensure_xmlid(env, "pg_obras", "seq_picking_type_entrega_obra", "ir.sequence", seq_eobr.id)
