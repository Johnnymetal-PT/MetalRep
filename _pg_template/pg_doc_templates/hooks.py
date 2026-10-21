from odoo import api


WORKSPACE_XMLID = "pg_doc_templates.workspace_doc_templates"
WORKSPACE_NAME = "Doc Templates"
WORKSPACE_PARENT_NAME = "PG Framework"

TEMPLATE_SPECS = [
    ("TPL_LEVANTAMENTO_AMBITO", "TPL_LEVANTAMENTO_AMBITO.md"),
    ("TPL_EMAIL_CLIENTE", "TPL_EMAIL_CLIENTE.md"),
    ("TPL_PROPOSTA_TECNICA", "TPL_PROPOSTA_TECNICA.md"),
    ("TPL_PONTO_SITUACAO", "TPL_PONTO_SITUACAO.md"),
    ("TPL_ORCAMENTO", "TPL_ORCAMENTO.md"),
    ("TPL_ORCAMENTO_PPTX", "TPL_ORCAMENTO_PPTX.md"),
    ("TPL_MATRIZ_FUNCIONAL_RACI_EXECUTAVEL", "TPL_MATRIZ_FUNCIONAL_RACI_EXECUTAVEL.md"),
    ("TPL_STATUS_SEMANAL_V1", "TPL_STATUS_SEMANAL_V1.md"),
]


def _ensure_xmlid(env, record, xmlid):
    module, name = xmlid.split(".", 1)
    model_data = env["ir.model.data"].sudo()
    existing = model_data.search(
        [("module", "=", module), ("name", "=", name)], limit=1
    )
    vals = {
        "module": module,
        "name": name,
        "model": record._name,
        "res_id": record.id,
        "noupdate": True,
    }
    if existing:
        existing.write(vals)
        return existing
    return model_data.create(vals)


def _ensure_pg_framework_root(env):
    root = env["knowledge.article"].sudo().search(
        [("name", "=", WORKSPACE_PARENT_NAME), ("parent_id", "=", False)],
        limit=1,
    )
    if root:
        return root
    return env["knowledge.article"].sudo().create({"name": WORKSPACE_PARENT_NAME})


def _ensure_workspace(env):
    workspace = env.ref(WORKSPACE_XMLID, raise_if_not_found=False)
    if workspace:
        return workspace

    parent = _ensure_pg_framework_root(env)
    workspace = env["knowledge.article"].sudo().create(
        {"name": WORKSPACE_NAME, "parent_id": parent.id}
    )
    _ensure_xmlid(env, workspace, WORKSPACE_XMLID)
    return workspace


def _ensure_templates(env, workspace):
    article_model = env["knowledge.article"].sudo()
    for code, filename in TEMPLATE_SPECS:
        xmlid = f"pg_doc_templates.{code.lower()}"
        article = env.ref(xmlid, raise_if_not_found=False)
        base_vals = {
            "name": filename,
            "parent_id": workspace.id,
            "pg_is_template": True,
            "pg_template_code": code,
            "pg_template_version": "1.0.0",
            "pg_template_state": "published",
            "pg_template_body_md": f"# {code}\n\nTemplate inicial criado automaticamente.",
        }
        if article:
            article.sudo().write(base_vals)
            continue

        existing = article_model.search([("pg_template_code", "=", code)], limit=1)
        if existing:
            existing.write(base_vals)
            article = existing
        else:
            article = article_model.create(base_vals)
        _ensure_xmlid(env, article, xmlid)


def post_init_hook(env):
    if not isinstance(env, api.Environment):
        raise TypeError("post_init_hook expected odoo.api.Environment")
    workspace = _ensure_workspace(env)
    _ensure_templates(env, workspace)
