# -*- coding: utf-8 -*-
import logging
from odoo import api, models

_logger = logging.getLogger(__name__)

# Modelos de documento contabilístico a NÃO espelhar para os grupos de consulta
# (a contabilidade vem só da coluna Contabilidade, não deve vazar por outras apps).
EXCL_ACC = [
    "account.move", "account.move.line", "account.payment",
    "account.bank.statement", "account.bank.statement.line",
]

# Matriz por login -> chaves de grupo (ver _apply_pg_access)
# "Editar" do cliente = nível Administrador da app (inclui menus de Configuração).
# Exceções: Contactos não tem tier admin (partner_mgr é o máximo);
# Contabilidade do Francisco fica vendor-only (acc_aux), não admin.
MATRIX = {
    "jose.silva@kyka.fr":      ["partner_mgr", "proj_mgr", "purch_mgr", "sale_mgr", "stock_mgr", "acc_mgr"],
    "francisco.rocha@kyka.fr": ["partner_mgr", "proj_ro",  "purch_mgr", "sale_ro",  "stock_mgr", "acc_aux"],
    "ana.sousa@kyka.fr":       ["partner_mgr", "proj_ro",  "purch_mgr", "sale_ro",  "stock_mgr", "acc_mgr"],
    "jessica.ferreira@kyka.fr": ["proj_mgr", "purch_ro", "sale_ro", "stock_ro"],
}

JOURNAL_RULE_NAME = "PG: Francisco - diarios sem venda (esconde cartao Clientes)"


class PgAccessConfig(models.AbstractModel):
    _name = "pg.access.config"
    _description = "PG Kyka - aplicação idempotente da matriz de acessos"

    # ------------------------------------------------------------------
    # helpers
    # ------------------------------------------------------------------
    def _model_id(self, model):
        return self.env["ir.model"]._get_id(model)

    def _group_by_name(self, name):
        Groups = self.env["res.groups"]
        g = Groups.search([("name", "=", name)], limit=1)
        return g or Groups.create({"name": name})

    def _mirror(self, src_group, tgt_group, exclude_model_ids=frozenset()):
        """Cria ACLs read-only no tgt_group para todos os modelos que o src_group
        (e implícitos, exceto Utilizador Interno) consegue aceder."""
        IMA = self.env["ir.model.access"]
        base_user = self.env.ref("base.group_user")
        scope = (src_group | src_group.trans_implied_ids).filtered(
            lambda x: x.id != base_user.id
        )
        model_ids = set(IMA.search([("group_id", "in", scope.ids)]).mapped("model_id").ids)
        model_ids -= set(exclude_model_ids)
        for mid in model_ids:
            name = "PG ROMIR g%s m%s" % (tgt_group.id, mid)
            existing = IMA.search([("name", "=", name)], limit=1)
            vals = {
                "name": name, "model_id": mid, "group_id": tgt_group.id,
                "perm_read": True, "perm_write": False,
                "perm_create": False, "perm_unlink": False,
            }
            existing.write(vals) if existing else IMA.create(vals)

    def _ensure_purchase_project_field(self):
        """Vista herdada que torna o campo project_id da encomenda de compra
        visível também a quem tem Compras (não só a Projeto/Utilizador)."""
        View = self.env["ir.ui.view"]
        parent = self.env.ref(
            "project_purchase.view_order_form_inherit_project_purchase",
            raise_if_not_found=False,
        )
        if not parent:
            _logger.info("pg_kyka_access: vista project_purchase ausente, passo ignorado.")
            return
        name = "PG Kyka: campo Projeto visivel em Compras"
        arch = (
            "<data>"
            "<xpath expr=\"//field[@name='project_id']\" position=\"attributes\">"
            "<attribute name=\"groups\">project.group_project_user,purchase.group_purchase_user</attribute>"
            "</xpath></data>"
        )
        vals = {
            "name": name, "model": "purchase.order", "inherit_id": parent.id,
            "mode": "extension", "type": "form", "arch": arch, "priority": 99,
        }
        existing = View.search([("name", "=", name)], limit=1)
        existing.write(vals) if existing else View.create(vals)

    def _ensure_partner_supplier_payment_term_field(self):
        """Vista herdada que torna o campo 'Condições de pagamento' de fornecedor
        (property_supplier_payment_term_id) do parceiro visível também a quem tem
        Compras. Por defeito a vista account.view_partner_property_form gateia-o por
        account.group_account_invoice/readonly; o perfil vendor-only (Francisco) não
        tem nenhum desses grupos, pelo que o campo desaparece ao criar/editar
        fornecedores. Só se alarga o campo de FORNECEDOR (não o de cliente)."""
        View = self.env["ir.ui.view"]
        parent = self.env.ref(
            "account.view_partner_property_form", raise_if_not_found=False,
        )
        if not parent:
            _logger.info("pg_kyka_access: vista account partner ausente, passo ignorado.")
            return
        name = "PG Kyka: Cond. pagamento fornecedor visivel em Compras"
        arch = (
            "<data>"
            "<xpath expr=\"//field[@name='property_supplier_payment_term_id']\" position=\"attributes\">"
            "<attribute name=\"groups\">account.group_account_invoice,account.group_account_readonly,purchase.group_purchase_user</attribute>"
            "</xpath></data>"
        )
        vals = {
            "name": name, "model": "res.partner", "inherit_id": parent.id,
            "mode": "extension", "type": "form", "arch": arch, "priority": 99,
        }
        existing = View.search([("name", "=", name)], limit=1)
        existing.write(vals) if existing else View.create(vals)

    # ------------------------------------------------------------------
    # entrypoint (chamado por data/apply.xml em cada install/update)
    # ------------------------------------------------------------------
    @api.model
    def apply_pg_access(self):
        env = self.env
        ref = env.ref
        IMA = env["ir.model.access"]
        Menu = env["ir.ui.menu"]
        Rule = env["ir.rule"]

        std = {
            "sale_user": ref("sales_team.group_sale_salesman"),
            "sale_all": ref("sales_team.group_sale_salesman_all_leads"),
            "sale_mgr": ref("sales_team.group_sale_manager"),
            "purch_user": ref("purchase.group_purchase_user"),
            "purch_mgr": ref("purchase.group_purchase_manager"),
            "stock_user": ref("stock.group_stock_user"),
            "stock_mgr": ref("stock.group_stock_manager"),
            "proj_user": ref("project.group_project_user"),
            "proj_mgr": ref("project.group_project_manager"),
            "acc_ro": ref("account.group_account_readonly"),
            "acc_inv": ref("account.group_account_invoice"),
            "acc_basic": ref("account.group_account_basic"),
            "acc_bk": ref("account.group_account_user"),
            "acc_mgr": ref("account.group_account_manager"),
            "partner_mgr": ref("base.group_partner_manager"),
        }

        # 1) grupos custom (adota por nome ou cria)
        cust = {
            "proj_ro": self._group_by_name("Projeto / Consulta (PG)"),
            "purch_ro": self._group_by_name("Compras / Consulta (PG)"),
            "sale_ro": self._group_by_name("Vendas / Consulta (PG)"),
            "stock_ro": self._group_by_name("Inventario / Consulta (PG)"),
            "acc_aux": self._group_by_name("Contabilidade / Consulta aux (PG)"),
        }

        excl_ids = set(env["ir.model"].search([("model", "in", EXCL_ACC)]).ids)

        # 2) espelhos read-only
        self._mirror(std["proj_user"], cust["proj_ro"], excl_ids)
        self._mirror(std["purch_user"], cust["purch_ro"], excl_ids)
        self._mirror(std["sale_user"], cust["sale_ro"], excl_ids)
        self._mirror(std["stock_user"], cust["stock_ro"], excl_ids)
        self._mirror(std["acc_inv"], cust["acc_aux"])  # aux inclui contabilidade

        # 3) visibilidade de menus para os grupos de consulta
        for ro_key, ug in [
            ("proj_ro", std["proj_user"]), ("purch_ro", std["purch_user"]),
            ("sale_ro", std["sale_user"]), ("stock_ro", std["stock_user"]),
        ]:
            menus = Menu.search([("groups_id", "in", ug.ids)])
            if menus:
                menus.write({"groups_id": [(4, cust[ro_key].id)]})

        # 4) override dos ACLs standard: tirar escrita (manter leitura)
        so = self._model_id("sale.order")
        pt = self._model_id("project.task")
        so_acls = IMA.search([
            ("model_id", "=", so), ("perm_write", "=", True),
            ("group_id", "in", [std["acc_inv"].id, std["acc_bk"].id, std["stock_user"].id]),
        ])
        pt_acls = IMA.search([
            ("model_id", "=", pt), ("perm_write", "=", True),
            ("group_id", "=", env.ref("base.group_user").id),
        ])
        (so_acls | pt_acls).write(
            {"perm_write": False, "perm_create": False, "perm_unlink": False}
        )

        # 5) menus de contabilidade do perfil Francisco (acc_aux)
        root = Menu.search(
            [("parent_id", "=", False), ("name", "in", ["Accounting", "Contabilidade"])],
            limit=1,
        )
        dash = ref("account.menu_board_journal_1", raise_if_not_found=False)
        cust_menu = ref("account.menu_finance_receivables", raise_if_not_found=False)
        if root:
            root.write({"groups_id": [(4, cust["acc_aux"].id)]})
        if dash:
            dash.write({"groups_id": [(4, cust["acc_aux"].id)]})
        if cust_menu:
            (cust_menu | cust_menu.child_id).write(
                {"groups_id": [(4, std["acc_inv"].id)]}
            )

        # 6) regra de diário sem venda (esconde cartão "Faturas a Clientes" do Painel)
        jrn = self._model_id("account.journal")
        rvals = {
            "name": JOURNAL_RULE_NAME, "model_id": jrn,
            "groups": [(6, 0, [cust["acc_aux"].id])], "global": False,
            "domain_force": "[('type','!=','sale')]",
            "perm_read": True, "perm_write": True, "perm_create": True, "perm_unlink": True,
        }
        existing = Rule.search([("name", "=", JOURNAL_RULE_NAME)], limit=1)
        existing.write(rvals) if existing else Rule.create(rvals)

        # 6b) campo Projeto visível em Compras
        # O campo project_id na encomenda de compra está protegido por
        # project.group_project_user (edição). Como o perfil de consulta não o tem,
        # o campo desaparece. Torna-se visível também a quem tem Compras, para poderem
        # associar projetos às encomendas sem ganhar edição de projetos.
        self._ensure_purchase_project_field()

        # 6c) campo Condições de pagamento (fornecedor) visível em Compras
        # A vista account gateia property_supplier_payment_term_id por
        # Faturação/Contab read-only. O Francisco é vendor-only (Compras + acc_aux)
        # e não tem esses grupos, pelo que não via o campo ao criar fornecedores.
        self._ensure_partner_supplier_payment_term_field()

        # 7) atribuição dos utilizadores segundo a matriz
        all_groups = {**std, **cust}
        clear = env["res.groups"].browse([
            std[k].id for k in (
                "sale_user", "sale_all", "sale_mgr", "purch_user", "purch_mgr",
                "stock_user", "stock_mgr", "proj_user", "proj_mgr", "acc_ro",
                "acc_inv", "acc_basic", "acc_bk", "acc_mgr", "partner_mgr",
            )
        ] + [cust[k].id for k in ("proj_ro", "purch_ro", "sale_ro", "stock_ro", "acc_aux")])

        Users = env["res.users"]
        for login, keys in MATRIX.items():
            user = Users.search([("login", "=", login)], limit=1)
            if not user:
                _logger.warning("pg_kyka_access: utilizador %s nao encontrado, ignorado.", login)
                continue
            target_ids = [all_groups[k].id for k in keys]
            user.write({"groups_id":
                        [(3, gid) for gid in clear.ids] + [(4, gid) for gid in target_ids]})

        _logger.info("pg_kyka_access: matriz de acessos aplicada/reaplicada com sucesso.")
