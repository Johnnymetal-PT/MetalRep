def pre_init_hook(env):
    """
    Initialize 'purchase_qty_to_reinvoice' field with sql default value
    for performance reasons.
    """
    env.cr.execute("""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = 'account_move_line'
        AND column_name = 'purchase_qty_to_reinvoice'
    """)
    if env.cr.fetchone():
        return

    env.cr.execute("""
        ALTER TABLE account_move_line
        ADD COLUMN IF NOT EXISTS purchase_qty_to_reinvoice BOOLEAN DEFAULT TRUE
    """)
