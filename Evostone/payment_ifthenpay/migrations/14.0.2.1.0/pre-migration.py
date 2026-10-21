from openupgradelib import openupgrade

field_renames = [
    ("payment.acquirer", "payment_acquirer", "multibanco_entity", "ifthenpay_entity"),
    (
        "payment.acquirer",
        "payment_acquirer",
        "multibanco_subentity",
        "ifthenpay_subentity",
    ),
]


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.rename_fields(env, field_renames)
