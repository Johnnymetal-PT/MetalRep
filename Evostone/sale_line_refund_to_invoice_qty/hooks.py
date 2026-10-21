# Copyright 2025 ACSONE SA/NV
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).


def pre_init_hook(env):
    """
    Initialize 'sale_qty_to_reinvoice' field with sql default value
    for performance reasons as Odoo does it with an update instead.
    """
    env.cr.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'account_move_line'
        AND column_name = 'sale_qty_to_reinvoice'
    """)
    if env.cr.fetchone():
        return

    env.cr.execute("""
        ALTER TABLE account_move_line
        ADD COLUMN IF NOT EXISTS sale_qty_to_reinvoice BOOLEAN DEFAULT TRUE
    """)
