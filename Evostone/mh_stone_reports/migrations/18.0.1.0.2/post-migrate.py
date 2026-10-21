"""Corrigir subject do mail template de recibo de pagamento.

Usa cast para lidar com campos jsonb/traduzidos do Odoo 18.
Substitui object.name por object.receipt_number or object.name.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    _logger.info("Corrigindo subject do mail template de recibo de pagamento...")

    cr.execute("""
        UPDATE mail_template
        SET subject = REPLACE(subject::text, 'object.name', 'object.receipt_number or object.name')::jsonb,
            body_html = REPLACE(body_html::text, 'object.name', 'object.receipt_number or object.name')::jsonb
        WHERE id = (
            SELECT res_id FROM ir_model_data
            WHERE module = 'account'
              AND name = 'mail_template_data_payment_receipt'
        )
    """)

    _logger.info("Done.")
