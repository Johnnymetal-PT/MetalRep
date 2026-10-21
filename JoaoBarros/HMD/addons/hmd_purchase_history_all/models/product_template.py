import logging

from odoo import _, fields, models
from odoo.tools.safe_eval import safe_eval


_logger = logging.getLogger(__name__)


_OPERATORS = {"&", "|", "!"}


def _evaluate_domain(domain):
    """Return a tuple (domain_list, was_string) or (None, _)."""

    if domain is None:
        return [], False

    if isinstance(domain, (list, tuple)):
        return list(domain), False

    if isinstance(domain, str):
        try:
            return list(safe_eval(domain)), True
        except Exception:
            return None, True

    return None, False


def _serialize_domain(domain, to_string):
    if to_string:
        return repr(domain)
    return domain


def _is_state_filter(term):
    if not isinstance(term, (list, tuple)) or len(term) < 3:
        return False

    field_name = term[0]
    if not isinstance(field_name, str):
        return False

    normalized = field_name.replace(" ", "").lower()
    if "state" not in normalized:
        return False

    operator = term[1]
    comparable_operators = {
        "=",
        "!=",
        "<>",
        "in",
        "not in",
        "<=",
        ">=",
        "<",
        ">",
    }
    return isinstance(operator, str) and operator.lower() in comparable_operators


def _parse_domain_tokens(tokens):
    class _Stream:
        def __init__(self, values):
            self._values = list(values)
            self._index = 0

        def has_more(self):
            return self._index < len(self._values)

        def next(self):
            value = self._values[self._index]
            self._index += 1
            return value

    stream = _Stream(tokens)

    def _parse_expression():
        if not stream.has_more():
            return ("const", True)

        token = stream.next()
        if isinstance(token, str) and token in _OPERATORS:
            if token == "!":
                child = _parse_expression()
                return ("!", child)

            left = _parse_expression()
            right = _parse_expression()
            return (token, left, right)

        return ("leaf", token)

    tree = _parse_expression()

    while stream.has_more():
        additional = _parse_expression()
        tree = ("&", tree, additional)

    return tree


def _sanitize_domain_tree(node):
    node_type = node[0]

    if node_type == "leaf":
        term = node[1]
        if _is_state_filter(term):
            return ("const", True), [term]
        return node, []

    if node_type == "const":
        return node, []

    if node_type == "!":
        child, removed = _sanitize_domain_tree(node[1])
        return ("!", child), removed

    if node_type in {"&", "|"}:
        left, removed_left = _sanitize_domain_tree(node[1])
        right, removed_right = _sanitize_domain_tree(node[2])
        return (node_type, left, right), removed_left + removed_right

    return node, []


def _simplify_domain_tree(node):
    node_type = node[0]

    if node_type in {"leaf", "const"}:
        return node

    if node_type == "!":
        child = _simplify_domain_tree(node[1])
        if child[0] == "const":
            return ("const", not child[1])
        return ("!", child)

    left = _simplify_domain_tree(node[1])
    right = _simplify_domain_tree(node[2])

    if node_type == "&":
        if left[0] == "const" and not left[1]:
            return ("const", False)
        if right[0] == "const" and not right[1]:
            return ("const", False)
        if left[0] == "const" and left[1]:
            return right
        if right[0] == "const" and right[1]:
            return left
    elif node_type == "|":
        if left[0] == "const" and left[1]:
            return right if right[0] != "const" else ("const", True)
        if right[0] == "const" and right[1]:
            return left if left[0] != "const" else ("const", True)
        if left[0] == "const" and not left[1]:
            return right
        if right[0] == "const" and not right[1]:
            return left

    return (node_type, left, right)


def _tree_to_domain(node):
    node_type = node[0]

    if node_type == "const":
        return [] if node[1] else [(1, "=", 0)]

    if node_type == "leaf":
        return [node[1]]

    if node_type == "!":
        child = _tree_to_domain(node[1])
        if not child:
            return [(1, "=", 0)]
        return ["!"] + child

    left = _tree_to_domain(node[1])
    right = _tree_to_domain(node[2])

    if node_type == "&":
        if not left:
            return right
        if not right:
            return left
    elif node_type == "|":
        if not left and not right:
            return []
        if not left:
            return right
        if not right:
            return left

    return [node_type] + left + right


def _prepare_purchase_orders_action(record, product_ids):
    action = record.env["ir.actions.actions"]._for_xml_id("purchase.purchase_form_action")
    base_context = action.get("context")
    if isinstance(base_context, str):
        try:
            base_context = safe_eval(base_context)
        except Exception:
            base_context = {}
    elif base_context is None:
        base_context = {}

    action_context = dict(base_context)
    action_context.update(record.env.context)
    action_context.update(
        {
            "search_default_draft": 0,
            "search_default_waiting": 0,
            "search_default_purchase": 0,
            "search_default_done": 0,
            "search_default_to_approve": 0,
            "search_default_my_purchases": 0,
        }
    )

    action.update(
        {
            "name": _("RFQs"),
            "domain": [("order_line.product_id", "in", list(product_ids))],
            "context": action_context,
        }
    )
    return action


def _sanitize_purchase_history_action(record, action):
    if not action:
        return action

    product_identifier = (
        f"{record.display_name} (id={record.id}, model={record._name})"
    )
    _logger.info(
        "Sanitizing purchase history action for %s with initial payload: domain=%s, context=%s",
        product_identifier,
        action.get("domain"),
        action.get("context"),
    )
    original_domain = action.get("domain")
    evaluated_domain, was_string = _evaluate_domain(original_domain)

    if evaluated_domain is None:
        _logger.warning(
            "Unable to evaluate purchase history domain %s for %s; leaving domain unchanged",
            original_domain,
            product_identifier,
        )
        return action

    _logger.info(
        "Original purchase history domain for %s: %s",
        product_identifier,
        evaluated_domain,
    )

    domain_tree = _parse_domain_tokens(evaluated_domain)
    sanitized_tree, removed_terms = _sanitize_domain_tree(domain_tree)
    simplified_tree = _simplify_domain_tree(sanitized_tree)
    sanitized_domain = _tree_to_domain(simplified_tree)

    if removed_terms:
        _logger.info(
            "Removed %s state restriction(s) from purchase history domain for %s: %s",
            len(removed_terms),
            product_identifier,
            removed_terms,
        )
        serialized_domain = _serialize_domain(sanitized_domain, was_string)
        action["domain"] = serialized_domain
        _logger.info(
            "Updated purchase history domain for %s: %s",
            product_identifier,
            serialized_domain,
        )
    else:
        _logger.info(
            "No state restriction found in purchase history domain for %s; domain kept as %s",
            product_identifier,
            evaluated_domain,
        )

    _logger.info(
        "Finished sanitizing purchase history action for %s; final domain=%s, context=%s",
        product_identifier,
        action.get("domain"),
        action.get("context"),
    )
    return action


class ProductTemplate(models.Model):
    _inherit = "product.template"

    hmd_purchase_rfq_count = fields.Integer(
        string="RFQs",
        compute="_compute_hmd_purchase_rfq_count",
    )

    def action_view_po(self):
        """Open the purchase history keeping every purchase order state visible."""

        self.ensure_one()
        _logger.info(
            "Calling product.template.action_view_po for template %s (id=%s)",
            self.display_name,
            self.id,
        )
        action = super().action_view_po()
        _logger.info(
            "Super purchase history action for template %s returned domain=%s, context=%s",
            self.display_name,
            action.get("domain") if action else None,
            action.get("context") if action else None,
        )
        return _sanitize_purchase_history_action(self, action)

    def _compute_hmd_purchase_rfq_count(self):
        variant_ids = self.mapped("product_variant_ids").ids
        counts = {}
        if variant_ids:
            group_data = self.env["purchase.order.line"].read_group(
                [("product_id", "in", variant_ids)],
                ["product_id", "order_id:count_distinct"],
                ["product_id"],
            )
            counts = {
                data["product_id"][0]: data.get("order_id_count_distinct", 0)
                for data in group_data
                if data.get("product_id")
            }

        for template in self:
            total = 0
            for variant in template.product_variant_ids:
                total += counts.get(variant.id, 0)
            template.hmd_purchase_rfq_count = total

    def action_view_rfq_purchase_orders(self):
        self.ensure_one()
        return _prepare_purchase_orders_action(
            self, self.product_variant_ids.ids or self.ids
        )
