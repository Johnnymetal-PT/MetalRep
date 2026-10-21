from openupgradelib import openupgrade


@openupgrade.migrate()
def migrate(env, version):
    openupgrade.logged_query(
        env.cr,
        """
        UPDATE payment_transaction
        SET multibanco_entity = payment_acquirer.ifthenpay_entity
        FROM
            payment_acquirer
        WHERE
            payment_transaction.acquirer_id = payment_acquirer.id AND
            payment_transaction.multibanco_entity IS NULL AND
            payment_acquirer.provider = 'ifthenpay' AND
            payment_acquirer.pt_pay_method = 'mb'
        """,
    )
